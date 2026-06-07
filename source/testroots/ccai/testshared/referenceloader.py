"""
    Out-of-tree loader for the reference SAS DATA-step implementation modules
    in ``source/examples/``. These modules are the documented correctness
    oracle for the production package. Tests use the :class:`ReferenceLoader`
    to obtain the reference modules and run the same user logic through both
    engines side by side.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


import importlib
import os
import sys


class ReferenceLoader:
    """
        Load the reference modules from ``source/examples/`` into a private
        namespace. The modules are not packaged and import each other by
        bare name (``from sasstep import ...``), so the loader prepends the
        examples directory to ``sys.path`` exactly once before importing.
    """

    _examples_path: str = ""
    _modules: dict = {}

    @classmethod
    def load(cls) -> dict:
        """
            Return a dictionary of the loaded reference modules.

            :returns: A mapping with keys ``"engine"``, ``"db"``, ``"ir"``,
                      ``"exec"``, ``"columnar"``, ``"report"`` whose values
                      are the imported reference module objects.
        """
        if len(cls._modules) > 0:
            rtnval = cls._modules
        else:
            cls._examples_path = cls._discover_examples_path()
            if cls._examples_path not in sys.path:
                sys.path.insert(0, cls._examples_path)
            cls._modules = {
                "engine": importlib.import_module("sasstep"),
                "db": importlib.import_module("sasstep_db"),
                "ir": importlib.import_module("sasstep_ir"),
                "exec": importlib.import_module("sasstep_exec"),
                "columnar": importlib.import_module("sasstep_columnar"),
                "report": importlib.import_module("sasstep_report"),
            }
            rtnval = cls._modules
        return rtnval

    @classmethod
    def _discover_examples_path(cls) -> str:
        """
            Walk up from this file to the repository root and locate
            ``source/examples``.

            :returns: An absolute path to ``source/examples``.

            :raises FileNotFoundError: When ``source/examples`` cannot be
                                       located under any parent.
        """
        here = os.path.abspath(os.path.dirname(__file__))
        current = here
        while True:
            candidate = os.path.join(current, "source", "examples")
            if os.path.isdir(candidate):
                rtnval = candidate
                return rtnval
            parent = os.path.dirname(current)
            if parent == current:
                err_msg_lines = [
                    "Unable to locate the source/examples reference modules.",
                    "    walked from: {}".format(here),
                ]
                err_msg = os.linesep.join(err_msg_lines)
                raise FileNotFoundError(err_msg)
            current = parent
