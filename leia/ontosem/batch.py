# NOTE: THIS HAS NOT BEEN PORTED OVER YET

from leia.ontosem.config import OntoSemConfig
from leia.ontosem.runner import OntoSemRunner
from leia.ontosem.service.repository import TMRRepository

import git
import os
import time
import traceback


if __name__ == "__main__":
    clear_db = False

    # 1) Connect to the repository

    MONGODB_CLOUD_SHARED_URL = (
        "mongodb://leia-admin:bgdWkMhfKSHeXAKc@ec2-3-83-217-159.compute-1.amazonaws.com"
    )
    MONGO_URL = (
        os.environ["MONGO_URL"]
        if "MONGO_URL" in os.environ
        else MONGODB_CLOUD_SHARED_URL
    )
    MONGO_DATABASE = (
        os.environ["MONGO_DATABASE"]
        if "MONGO_DATABASE" in os.environ
        else "leia-analyses"
    )
    MONGO_COLLECTION = (
        os.environ["MONGO_COLLECTION"]
        if "MONGO_COLLECTION" in os.environ
        else "analyses"
    )

    repository = TMRRepository(MONGO_URL, MONGO_DATABASE, MONGO_COLLECTION)

    # 2) Optionally clear the database

    if clear_db:
        repository.clear()

    # 3) Build a list of sentences to run

    sentences = []

    # 4) Process and save each sentence

    config = OntoSemConfig()
    config.init_ontomem()

    runner = OntoSemRunner(config)

    for sentence in sentences:
        print(sentence)
        runtime = -1
        try:
            start = time.time()
            results = runner.run([sentence])
            runtime = time.time() - start

            results = results.to_dict()
        except Exception:
            results = {
                "config": config.to_dict(),
                "sentences": [{"text": sentence}],
                "errors": [traceback.format_exc()],
            }

        try:
            repo = git.Repo(search_parent_directories=True)
            sha = repo.head.object.hexsha
        except:
            try:
                with open("sha.git", "r") as file:
                    sha = file.read()
            except:
                sha = "UNKNOWN"

        results["metadata"] = {
            "timestamp": time.time(),
            "runtime": runtime,
            "git": sha,
        }

        repository.save(results)
