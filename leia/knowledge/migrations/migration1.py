"""
This migration converts all instances of properties into instances of ABSTRACT-OBJECT.
Changes will be applied to the lexicon sem-strucs, as well as to any private concepts in the ontology.
"""

from typing import Union

import copy
import json
import os
import re
import sys


class PropInstancesToAOsMigration(object):

    def __init__(self, knowledge_root: str):
        self.contents_dir = "%s/words" % knowledge_root
        self.properties = set(
            map(lambda p: p[0:-5], os.listdir("%s/properties" % knowledge_root))
        )

    def run(self, dry_run: bool = True):
        files = os.listdir(self.contents_dir)

        migrations = []

        for file in files:
            with open("%s/%s" % (self.contents_dir, file), "r") as f:
                content = json.load(f)
                migrated = self.migrate_word(content)
                if migrated is not None:
                    migrations.append((file, content, migrated))

        print("Migrations detected: %d" % len(migrations))
        if not dry_run:
            for migration in migrations:
                file = "%s/%s" % (self.contents_dir, migration[0])
                print("Saving to %s" % file)
                with open(file, "w") as f:
                    json.dump(migration[2], f)

        print("Done!")

    def migrate_word(self, word: dict) -> Union[dict, None]:
        migrated = copy.deepcopy(word)

        for name, sense in migrated["senses"].items():
            semstruc = sense["SEM-STRUC"]

            if isinstance(semstruc, str):
                if semstruc in self.properties:
                    sense["SEM-STRUC"] = {
                        "ABSTRACT-OBJECT": {
                            "REPRESENTS": semstruc,
                        }
                    }

            elif isinstance(semstruc, dict):
                for k, v in semstruc.items():
                    if k.startswith("REFSEM"):
                        # There are no senses in the lexicon where the refsem is just a str, and represents a variable.
                        if isinstance(v, str):
                            continue

                        # The senses where refsems are lists are wrong, and should be fixed in another migration.
                        if isinstance(v, list):
                            continue

                        # Any dictionary refsems with more than one element are wrong, and should be fixed in another migration.
                        if len(v) != 1:
                            continue

                        refsem, content = list(v.items())[0]
                        if refsem in self.properties:
                            # Any refsem content that is not a dict is wrong, and should be fixed in another migration.
                            if not isinstance(content, dict):
                                continue

                            migrated_refsem = copy.deepcopy(content)
                            migrated_refsem["REPRESENTS"] = refsem

                            semstruc[k] = {"ABSTRACT-OBJECT": migrated_refsem}

                    if k.startswith("^$VAR"):
                        # Nothing needs to happen here.  In some cases, the SEM field of the variable
                        # can require a property.  But this is a constraint, and it is the job of the scorer
                        # to recognize that constraint must be applied to an AO instead.
                        continue

                    # Rarely, semstruc elements are repeated, and have an index, e.g., ATTRIBUTE and ATTRIBUTE-1
                    # See and-conj9 for an example.  Here we remove the indexing for now.
                    optional_index = re.findall("-[0-9]+", k)
                    k_unindexed = (
                        k
                        if len(optional_index) == 0
                        else k.replace(optional_index[0], "")
                    )

                    if k_unindexed in self.properties:
                        # Copy the entire semstruc element contents, and add the REPRESENTS field
                        migrated_v = copy.deepcopy(v)
                        migrated_v["REPRESENTS"] = k_unindexed

                        # Rebuild the new semstruc key as an AO with the same optional index
                        k_indexed = (
                            "ABSTRACT-OBJECT%s" % ""
                            if len(optional_index) == 0
                            else optional_index[0]
                        )

                        # Add the migrated element to the semstruc, and remove the old one
                        semstruc[k_indexed] = migrated_v
                        del semstruc[k]

        if word == migrated:
            return None

        return migrated


if __name__ == "__main__":
    knowledge_root = sys.argv[1]

    migration = PropInstancesToAOsMigration(knowledge_root)
    migration.run(dry_run=False)
