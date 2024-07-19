from ontomem.properties import Property, WILDCARD
from pymongo import MongoClient
from typing import Set, Tuple, Union

import json
import os


class MongoConceptExporter(object):

    def __init__(self, url: str, port: int, database: str, collection: str, output_dir: str):
        self.url = url
        self.port = port
        self.database = database
        self.collection = collection
        self.output_dir = output_dir

    def getclient(self):
        client = MongoClient(self.url, self.port)
        with client:
            return client

    def handle(self):
        client = self.getclient()
        db = client[self.database]
        return db[self.collection]

    def run(self):

        aggregation = [
            {
                "$graphLookup": {
                    "from": self.collection,
                    "startWith": "$parents",
                    "connectFromField": "parents",
                    "connectToField": "name",
                    "as": "ancestry"
                }
            }, {
                "$project": {
                    "name": 1,
                    "definition": 1,
                    "localProperties": 1,
                    "parents": 1,
                    "overriddenFillers": 1,
                    "ancestry": "$ancestry.name",
                    "_id": 0
                }
            }
        ]

        h = self.handle()
        entries = list(h.aggregate(aggregation))

        properties = set(map(lambda e: e["name"], filter(lambda e: e["name"] == "property" or "property" in e["ancestry"], entries)))
        literals = set(map(lambda e: e["name"], filter(lambda e: "literal-attribute" in e["ancestry"], entries)))
        concepts = list(filter(lambda e: e["name"] != "property" and "property" not in e["ancestry"], entries))

        concept_names = set(map(lambda c: c["name"], concepts))

        output_ontology = {}
        unknown_fillers = []
        unknown_blocked = []
        onto_instances = []

        for concept in concepts:
            name = concept["name"]
            definition = concept["definition"] if "definition" in concept else ""
            parents = concept["parents"]

            contents = {
                "name": "@%s" % name,
                "isa": list(map(lambda p: "@%s" % p, parents)),
                "def": definition,
                "local": [],
                "block": [],
                "private": {}
            }

            # Find any uses of default-measure and record the slot they are attached to
            # Later, they will be added to the metadata of any other filler of that slot
            default_measures = {}
            for prop in concept["localProperties"]:
                if prop["facet"] == "default-measure":
                    default_measures[prop["slot"]] = prop["filler"]

            # Iterate through the properties, building each row and adding it to the local field
            for prop in concept["localProperties"]:
                slot = prop["slot"]
                facet = prop["facet"]
                filler = prop["filler"]

                # Skip all default-measures; they are handled elsewhere
                if facet == "default-measure":
                    continue
                # Skip all "onto-instances", this is a pointer that isn't needed
                if slot == "onto-instances":
                    continue
                # Skip all "is-onto-instance", we'll be adding the frame directly to the private field
                if slot == "is-onto-instance":
                    continue

                try:
                    filler = self.parse_filler(slot, filler, concept_names, literals, properties)
                    if filler is None:
                        continue
                except:
                    unknown_fillers.append((name, prop))

                if facet not in {"value", "default", "sem", "relaxable-to", "not"}:
                    unknown_fillers.append((name, prop))
                    continue

                prop = {
                    "slot": slot,
                    "facet": facet,
                    "filler": filler,
                }

                if slot in default_measures:
                    prop["meta"] = {
                        "measured-in": default_measures[slot]
                    }

                contents["local"].append(prop)

            for prop in concept["overriddenFillers"]:
                slot = prop["slot"]
                facet = prop["facet"]
                filler = prop["filler"]

                # Skip all default-measures; they are handled elsewhere
                if facet == "default-measure":
                    continue
                # Skip all "onto-instances", this is a pointer that isn't needed
                if slot == "onto-instances":
                    continue

                try:
                    filler = self.parse_filler(slot, filler, concept_names, literals, properties)
                    if filler is None:
                        continue
                except:
                    unknown_blocked.append((name, prop))

                if facet not in {"value", "default", "sem", "relaxable-to", "not"}:
                    unknown_blocked.append((name, prop))
                    continue

                prop = {
                    "slot": slot,
                    "facet": facet,
                    "filler": filler,
                }

                contents["block"].append(prop)

            # Add the concept to the ontology
            if len(list(filter(lambda p: p["slot"] == "is-onto-instance", concept["localProperties"]))):
                onto_instances.append(contents)
            else:
                output_ontology[name] = contents

        # Now we find where to put onto-instances
        onto_instance_map = []          # A list of tuples owner -> private frame
        unmapped_onto_instances = []    # A list of onto instances whose owner is unknown

        # Go through each onto instance, find any frame that references it, and consider that the owner.
        # Any onto instance whose owner is unknown, add to the unmapped list.
        for oi in onto_instances:
            name = oi["name"]
            concept = self.find_root_of_onto_instance(name, output_ontology.values())

            if concept is not None:
                concept["private"][name] = oi
                onto_instance_map.append((concept["name"], name))
                continue

            unmapped_onto_instances.append(oi)

        # Go through the unmapped list (basically a second pass).
        # This time, look for owners amongst the other onto instances.
        # If found, use the onto instance map to find their respective owners, and redirect the unmapped entity
        # to the actual root.  (Onto instances can't own other onto instances, so those "grandchildren" are handed
        # off to the root concept.)
        for oi in list(unmapped_onto_instances):
            name = oi["name"]
            concept = self.find_root_of_onto_instance(name, onto_instances)
            if concept is not None:
                for m in onto_instance_map:
                    if m[1] == concept["name"]:
                        concept = output_ontology[m[0][1:]]
                        concept["private"][name] = oi
                        unmapped_onto_instances.remove(oi)

        print("Total onto-instances with unknown owners: %d" % len(unmapped_onto_instances))
        for oi in unmapped_onto_instances:
            print("-- %s" % oi["name"])

        print("Total unknown fillers: %d" % len(unknown_fillers))
        for uf in unknown_fillers:
            print("-- %s" % str(uf))

        print("Total unknown blocked: %d" % len(unknown_blocked))
        for ub in unknown_blocked:
            print("-- %s" % str(ub))

    def parse_filler(self, slot: str, filler, concept_names: Set[str], literals: Set[str], properties: Set[str]):
        # Now map each filler into something valid
        as_scalar_range = self.parse_scalar_range(filler)

        if isinstance(filler, str) and filler in concept_names:
            return "@%s" % filler
        elif isinstance(filler, str) and slot in literals:
            # Known literals can just be passed through for now; if any of the values are actually out
            # of range, we will deal with them later (not a big deal)
            return filler
        elif as_scalar_range is not None:
            return as_scalar_range
        elif filler == "yes":
            # There are only a handful of cases, and for each, both yes and no are present, so just merge them
            # into one.
            return "!AnyBool"
        elif filler == "no":
            # Since we get "yes" above, we can skip the "no" fillers (we only need one)
            return None
        elif filler in properties:
            return "$%s" % filler
        elif filler == "(any-number)":
            return "!AnyNum"
        elif slot == "has-sports-activity" and filler == "rise":
            # This looks like bad data; pruning it here (too many instances in the database)
            return None
        else:
            raise Exception

    def parse_scalar_range(self, value) -> Union[Tuple[str, Union[float, int]], Tuple[str, Union[float, int], Union[float, int]], None]:
        # Handle a few special cases that are too numerous in the database to easily fix
        if value == "(>0)":
            return (">", 0)
        if value == "(>=0)":
            return (">=", 0)

        value_as_number = self.as_number(value)
        if value_as_number is not None:
            return ("=>=<", value_as_number)

        # LISP style ranges
        if isinstance(value, str):
            lisp_value = value
            if lisp_value[0] == "(" and lisp_value[-1] == ")":
                lisp_value = value[1:-1]

            lisp_parts = lisp_value.split(" ")

            if len(lisp_parts) < 2:
                return None

            comparator = lisp_parts[0]
            value1 = lisp_parts[1]
            value2 = lisp_parts[2] if len(lisp_parts) > 2 else None

            if comparator not in {">", ">=", "<", "<=", "><", ">=<", "><=", "=>=<"}:
                return None

            value1 = self.as_number(value1)
            if value1 is None:
                return None

            if value2 is None:
                return (comparator, value1)

            value2 = self.as_number(value2)
            if value2 is None:
                return None

            return (comparator, value2)

        return None

    def as_number(self, value) -> Union[float, int, None]:
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return value
        if isinstance(value, str):
            try:
                return int(value)
            except: pass
            try:
                return float(value)
            except: pass
        return None

    def find_root_of_onto_instance(self, name: str, concepts) -> Union[dict, None]:
        for concept in concepts:
            for prop in concept["local"]:
                if prop["slot"] == "onto-instances":
                    continue

                if prop["filler"] == name:
                    return concept

        return None


class MongoPropertyExporter(object):

    def __init__(self, url: str, port: int, database: str, collection: str, output_dir: str):
        self.url = url
        self.port = port
        self.database = database
        self.collection = collection
        self.output_dir = output_dir

    def getclient(self):
        client = MongoClient(self.url, self.port)
        with client:
            return client

    def handle(self):
        client = self.getclient()
        db = client[self.database]
        return db[self.collection]

    def run(self):

        aggregation = [
            {
                "$graphLookup": {
                    "from": self.collection, 
                    "startWith": "$parents", 
                    "connectFromField": "parents", 
                    "connectToField": "name", 
                    "as": "properties"
                }
            }, {
                "$match": {
                    "properties.name": "property"
                }
            }, {
                "$project": {
                    "name": 1,
                    "definition": 1,
                    "localProperties": 1,
                    "properties.name": 1,
                    "parents": 1,
                    "_id": 0
                }
            }
        ]

        h = self.handle()

        skipped = []

        for property in h.aggregate(aggregation):
            name = property["name"]
            ancestry = set(map(lambda parent: parent["name"], property["properties"]))
            container = property["parents"][0]
            definition = property["definition"]

            # Filter out some properties that we no longer need:
            filter_out = {"ontology-slot", "second-order-property", "parametrics", "fr-property"}
            if name in filter_out or len(ancestry.intersection(filter_out)) > 0:
                skipped.append(name)
                continue

            if "is-onto-instance" in set(map(lambda p: p["slot"], property["localProperties"])):
                skipped.append(name)
                continue

            if name in {"attribute", "extra-ontological"}:
                skipped.append(name)
                continue

            property_type = None
            for landmark in ["case-role", "relation", "literal-attribute", "scalar-attribute", "temporal-attribute", "naming-data"]:
                if landmark in ancestry or name == landmark:
                    property_type = landmark
                    break

            if property_type is None:
                print("Unknown property type for %s" % name)
                continue

            # Update certain attributes to be contained by literals
            if property_type in {"naming-data", "temporal-attribute"}:
                container = "literal-attribute"

            property_type = {   # Boolean isn't a type in the current ontology, so need to map it
                "case-role": Property.TYPE.CASE_ROLE,
                "literal-attribute": Property.TYPE.LITERAL,
                "naming-data": Property.TYPE.LITERAL,           # Map these to literals (for now at least)
                "relation": Property.TYPE.RELATION,
                "scalar-attribute": Property.TYPE.SCALAR,
                "temporal-attribute": Property.TYPE.SCALAR,     # Map these to scalars (for now at least)
            }[property_type]

            property_range = {
                Property.TYPE.CASE_ROLE: WILDCARD.ANYTYPE,
                Property.TYPE.LITERAL: WILDCARD.ANYLIT,
                Property.TYPE.RELATION: WILDCARD.ANYTYPE,
                Property.TYPE.SCALAR: WILDCARD.ANYNUM,
            }[property_type]

            inverse = None
            measured_in = []

            for property in property["localProperties"]:
                if property["slot"] == "domain":
                    # This is unneeded
                    continue
                if property["slot"] == "onto-instances":
                    # This is unneeded
                    continue

                if property["slot"] == "inverse":
                    inverse = property["filler"]
                elif property["slot"] == "measured-in":
                    # Just make a new concept now; it just needs to be a valid type with the right name; nothing
                    # else matters for this conversion process.
                    measured_in.append("@%s" % property["filler"])
                elif property["filler"] in {"yes", "no"}:
                    property_type = Property.TYPE.BOOLEAN
                # Handle very special cases
                elif name == "bulb-color" and property["slot"] == "range":
                    if not isinstance(property_range, set):
                        property_range = set()
                    property_range.add(property["filler"])
                elif name == "intersection-shape" and property["slot"] == "range":
                    if not isinstance(property_range, set):
                        property_range = set()
                    property_range.add(property["filler"])
                elif name == "road-segment-shape" and property["slot"] == "range":
                    if not isinstance(property_range, set):
                        property_range = set()
                    property_range.add(property["filler"])
                else:
                    print("-- %s has extra property %s" % (name, property))

            if isinstance(property_range, WILDCARD):
                property_range = property_range.value
            elif isinstance(property_range, set):
                property_range = list(property_range)

            contents = {
                "name": "$%s" % name,
                "def": definition,
                "type": property_type.value.lower(),
                "range": property_range,
                "inverse": "$%s" % inverse if isinstance(inverse, str) else inverse,
                "measured-in": list(map(lambda c: str(c), measured_in)),
                "container": "$%s" % container
            }

            file = "%s/%s.prop" % (output_dir, name)
            with open(file, "w") as f:
                json.dump(contents, f, indent=2)

        print("======")
        for s in skipped:
            print("Skipped %s" % s)


if __name__ == "__main__":

    import sys

    if sys.argv[1] == "properties":
        output_dir = "%s/knowledge/properties" % os.getcwd()
        exporter = MongoPropertyExporter("localhost", 27016, "leia-ontology", "canonical-v.1.0.6", output_dir)
        exporter.run()
    elif sys.argv[1] == "concepts":
        output_dir = "%s/knowledge/concepts" % os.getcwd()
        exporter = MongoConceptExporter("localhost", 27016, "leia-ontology", "canonical-v.1.0.6", output_dir)
        exporter.run()