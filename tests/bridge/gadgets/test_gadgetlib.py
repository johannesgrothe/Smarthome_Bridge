import pytest
from gadgetlib import *


@pytest.mark.bridge
def test_gadget_lib_gadget_identifier():
    assert GadgetIdentifier(0) == GadgetIdentifier.any_gadget
    assert gadget_identifier_to_str(GadgetIdentifier.any_gadget) == "any_gadget"
    assert str_to_gadget_identifier("any_gadget") == GadgetIdentifier.any_gadget


@pytest.mark.bridge
def test_gadget_lib_characteristic_identifier():
    assert CharacteristicIdentifier(0) == CharacteristicIdentifier.err_type
    assert characteristic_identifier_to_str(CharacteristicIdentifier.err_type) == "err_type"
    assert str_to_characteristic_identifier("err_type") == CharacteristicIdentifier.err_type


@pytest.mark.bridge
def test_gadget_lib_characteristic_update_status():
    assert CharacteristicUpdateStatus(0) == CharacteristicUpdateStatus.general_error
    assert characteristic_update_status_to_str(CharacteristicUpdateStatus.general_error) == "general_error"
    assert str_to_characteristic_update_status("general_error") == CharacteristicUpdateStatus.general_error


@pytest.mark.bridge
def test_gadget_lib_gadget_method():
    assert GadgetMethod(0) == GadgetMethod.err_type
    assert gadget_method_to_str(GadgetMethod.err_type) == "err_type"
    assert str_to_gadget_method("err_type") == GadgetMethod.err_type
