import pytest

from smarthome_bridge.characteristic import *


C_TYPE = CharacteristicIdentifier.fanSpeed
C_MIN = 20
C_MAX = 100
C_STEPS = 4

C_STEP_VAL_INIT = 0
C_TRUE_VAL_INIT = 20
C_PERCENTAGE_VAL_INIT = 0

C_STEP_VAL_OK1 = 1
C_STEP_VAL_OK1_TRUE = 40
C_STEP_VAL_OK1_PERCENTAGE = 25

C_STEP_VAL_OK2 = C_STEPS
C_STEP_VAL_ERR1 = -3
C_STEP_VAL_ERR2 = C_STEPS + 1

C_TRUE_VAL_OK1 = 40
C_TRUE_VAL_OK1_STEP = 1

C_TRUE_VAL_OK2 = C_MAX
C_TRUE_VAL_OK2_STEP = C_STEPS

C_TRUE_VAL_ADJUST = 45
C_TRUE_VAL_ADJUST_STEP = 1
C_TRUE_VAL_ADJUST_TRUE = 40

C_TRUE_VAL_ERR1 = C_MIN - 5
C_TRUE_VAL_ERR2 = C_MAX + 5


@pytest.fixture()
def characteristic():
    c = Characteristic(C_TYPE,
                       C_MIN,
                       C_MAX,
                       C_STEPS,
                       C_STEP_VAL_INIT)
    yield c
    # c.__del__()


@pytest.mark.bridge
def test_characteristic_constructor():
    with pytest.raises(CharacteristicInitError):
        _ = Characteristic(CharacteristicIdentifier.fanSpeed,
                           30,
                           25,
                           3)

    with pytest.raises(CharacteristicInitError):
        _ = Characteristic(CharacteristicIdentifier.fanSpeed,
                           0,
                           100,
                           0)

    c = Characteristic(CharacteristicIdentifier.fanSpeed,
                       0,
                       100,
                       1)

    assert c.get_true_value() == c.get_min()


@pytest.mark.bridge
def test_characteristic_init_values(characteristic: Characteristic):
    assert characteristic.get_type() == C_TYPE
    assert characteristic.get_min() == C_MIN
    assert characteristic.get_max() == C_MAX
    assert characteristic.get_steps() == C_STEPS

    assert characteristic.get_step_value() == C_STEP_VAL_INIT
    assert characteristic.get_true_value() == C_TRUE_VAL_INIT
    assert characteristic.get_percentage_value() == C_PERCENTAGE_VAL_INIT


@pytest.mark.bridge
def test_characteristic_set_step_value(characteristic: Characteristic):
    assert characteristic.get_step_value() == C_STEP_VAL_INIT

    status = characteristic.set_step_value(C_STEP_VAL_OK1)

    assert status is True
    assert characteristic.get_step_value() == C_STEP_VAL_OK1
    assert characteristic.get_true_value() == C_STEP_VAL_OK1_TRUE
    assert characteristic.get_percentage_value() == C_STEP_VAL_OK1_PERCENTAGE

    with pytest.raises(CharacteristicUpdateError):
        characteristic.set_step_value(C_STEP_VAL_ERR1)

    with pytest.raises(CharacteristicUpdateError):
        characteristic.set_step_value(C_STEP_VAL_ERR2)

    assert characteristic.get_step_value() == C_STEP_VAL_OK1
    assert characteristic.get_true_value() == C_STEP_VAL_OK1_TRUE
    assert characteristic.get_percentage_value() == C_STEP_VAL_OK1_PERCENTAGE

    characteristic.set_step_value(C_STEP_VAL_OK2)

    assert characteristic.get_step_value() == C_STEP_VAL_OK2

    status = characteristic.set_step_value(C_STEP_VAL_OK2)

    assert status is False


@pytest.mark.bridge
def test_characteristic_set_true_value(characteristic: Characteristic):
    assert characteristic.get_true_value() == C_TRUE_VAL_INIT

    status = characteristic.set_true_value(C_TRUE_VAL_OK1)

    assert status is True
    assert characteristic.get_step_value() == C_TRUE_VAL_OK1_STEP
    assert characteristic.get_true_value() == C_TRUE_VAL_OK1

    with pytest.raises(CharacteristicUpdateError):
        characteristic.set_true_value(C_TRUE_VAL_ERR1)

    with pytest.raises(CharacteristicUpdateError):
        characteristic.set_true_value(C_TRUE_VAL_ERR2)

    assert characteristic.get_step_value() == C_TRUE_VAL_OK1_STEP
    assert characteristic.get_true_value() == C_TRUE_VAL_OK1

    characteristic.set_true_value(C_TRUE_VAL_OK2)

    assert characteristic.get_true_value() == C_TRUE_VAL_OK2
    assert characteristic.get_step_value() == C_TRUE_VAL_OK2_STEP

    status = characteristic.set_true_value(C_TRUE_VAL_OK2)

    assert status is False

    characteristic.set_true_value(C_TRUE_VAL_ADJUST)

    assert characteristic.get_true_value() == C_TRUE_VAL_ADJUST_TRUE
    assert characteristic.get_step_value() == C_TRUE_VAL_ADJUST_STEP
