from ontomem.properties import Property, WILDCARD
from pymongo import MongoClient

import json
import os


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

    output_dir = "%s/knowledge/properties" % os.getcwd()

    exporter = MongoPropertyExporter("localhost", 27016, "leia-ontology", "canonical-v.1.0.6", output_dir)
    exporter.run()