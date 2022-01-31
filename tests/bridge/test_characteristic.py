import pytest

from smarthome_bridge.characteristic import *


C_TYPE = CharacteristicIdentifier.fan_speed
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
        _ = Characteristic(CharacteristicIdentifier.fan_speed,
                           30,
                           25,
                           3)

    with pytest.raises(CharacteristicInitError):
        _ = Characteristic(CharacteristicIdentifier.fan_speed,
                           0,
                           100,
                           0)

    c = Characteristic(CharacteristicIdentifier.fan_speed,
                       0,
                       100,
                       1)

    assert c.get_true_value() == c.get_min()


@pytest.mark.bridge
def test_characteristic_illegal_init():
    with pytest.raises(CharacteristicInitError):
        Characteristic(C_TYPE,
                       C_MIN,
                       C_MAX,
                       -1)
    with pytest.raises(CharacteristicInitError):
        Characteristic(C_TYPE,
                       C_MIN,
                       C_MAX,
                       C_STEPS,
                       C_STEPS + 1)


@pytest.mark.bridge
def test_characteristic_equal():
    c1 = Characteristic(C_TYPE,
                        C_MIN,
                        C_MAX,
                        C_STEPS,
                        0)
    c2 = Characteristic(C_TYPE,
                        C_MIN,
                        C_MAX,
                        C_STEPS,
                        C_STEPS)
    c3 = Characteristic(CharacteristicIdentifier.status,
                        C_MIN,
                        C_MAX,
                        C_STEPS)

    assert c1 == c1
    assert c1 == c2
    assert c1 != c3

    assert [c1, c2] == [c2, c1]


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

    # Test maximal step value
    characteristic.set_step_value(C_STEPS)
    assert characteristic.get_step_value() == C_STEPS
    assert characteristic.get_true_value() == C_MAX
    assert characteristic.get_percentage_value() == 100

    status = characteristic.set_step_value(C_STEPS)
    assert status is False

    # Test minimal step value
    characteristic.set_step_value(0)
    assert characteristic.get_step_value() == 0
    assert characteristic.get_true_value() == C_MIN
    assert characteristic.get_percentage_value() == 0


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
