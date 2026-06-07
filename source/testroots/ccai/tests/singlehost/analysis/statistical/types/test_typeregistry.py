"""
    Tests for :class:`TypeRegistry`: core types are registered, lookup,
    introspection, and inference.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"


from ccai.analysis.statistical.missing.missingfactory import MISSING
from ccai.analysis.statistical.types.constants import CHAR, NUM
from ccai.analysis.statistical.types.typeregistry import TypeRegistry


def test_num_type_is_registered_after_import():
    """
        Importing the types package registers ``num``.
    """
    has_num = TypeRegistry.has(name=NUM)
    assert has_num is True
    return


def test_char_type_is_registered_after_import():
    """
        Importing the types package registers ``char``.
    """
    has_char = TypeRegistry.has(name=CHAR)
    assert has_char is True
    return


def test_num_type_handler_uses_plain_missing_sentinel():
    """
        The ``num`` storage type's missing sentinel is the plain
        :data:`MISSING`.
    """
    handler = TypeRegistry.get(name=NUM)
    same = handler.missing is MISSING
    assert same is True
    return


def test_num_type_handler_default_length_is_eight():
    """
        The ``num`` storage type defaults to width 8 (SAS float64).
    """
    handler = TypeRegistry.get(name=NUM)
    same = handler.default_length == 8
    assert same is True
    return


def test_infer_classifies_strings_as_char():
    """
        :meth:`TypeRegistry.infer` maps strings to ``CHAR``.
    """
    inferred = TypeRegistry.infer(value="hello")
    same = inferred == CHAR
    assert same is True
    return


def test_infer_classifies_numbers_as_num():
    """
        :meth:`TypeRegistry.infer` maps numbers to ``NUM``.
    """
    inferred = TypeRegistry.infer(value=42)
    same = inferred == NUM
    assert same is True
    return


def test_num_coercer_routes_invalid_text_to_missing():
    """
        Permissive numeric coercion: bad numerics become :data:`MISSING`.
    """
    handler = TypeRegistry.get(name=NUM)
    coerced = handler.coerce("not-a-number", 8)
    same = coerced is MISSING
    assert same is True
    return


def test_char_coercer_truncates_to_storage_length():
    """
        ``char`` coercion truncates silently at the storage length.
    """
    handler = TypeRegistry.get(name=CHAR)
    coerced = handler.coerce("HELLO", 3)
    same = coerced == "HEL"
    assert same is True
    return
