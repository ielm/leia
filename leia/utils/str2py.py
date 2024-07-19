# A collection of utilities that load python class definitions and functions from string pointers.

from typing import Type

import importlib


def import_class(reference: str) -> Type:

    # To find the class, parse the provided path
    class_path = reference
    if class_path.startswith("*"):
        class_path = class_path[1:]

        class_path = class_path.split(".")

    # First, find the package; stopping once the path no longer leads to a package
    current_package = None
    for node in class_path:
        if current_package is None:
            current_package = importlib.import_module(node)
        elif current_package is not None:
            try:
                current_package = importlib.import_module("%s.%s" % (current_package.__name__, node))
            except ModuleNotFoundError:
                break

    # Next, trim the path to remove the package, and then find the class (or subclass)
    executable_path = class_path[len(current_package.__name__.split(".")):]
    current_class = None
    for node in executable_path:
        if current_class is None:
            current_class = getattr(current_package, node)
        elif current_class is not None:
            current_class = getattr(current_class, node)

    return current_class