import numpy as np
import pytest
from research.paderborn_intake import inventory,named_channels,CONDITIONS,EXPECTED_SAMPLES


def members():
    return [(f"K001/{c}_K001_{i}.mat",1024) for c in CONDITIONS for i in range(1,21)]


def test_complete_named_inventory():
    assert len(inventory("K001",members()))==80


@pytest.mark.parametrize("extra",[("../secret.mat",1),("/tmp/bad.mat",1),("K001/N15_M07_F10_K001_1.mat",1),("alien.mat",1)])
def test_unsafe_or_unexpected_members_rejected(extra):
    with pytest.raises(ValueError):
        inventory("K001",members()+[extra])


def test_incomplete_inventory_rejected():
    with pytest.raises(ValueError,match="Incomplete"):
        inventory("K001",members()[:-1])


def test_named_vibration_channel_not_positional():
    record={"Y":[{"Name":"current","Data":np.arange(3)},
                 {"Name":"vibration_1","Data":np.arange(EXPECTED_SAMPLES),"Unit":"m/s2"}]}
    result=named_channels(record)
    assert result["sample_count"]==EXPECTED_SAMPLES
    assert result["vibration_name"]=="vibration_1"


@pytest.mark.parametrize("data",[np.ones(EXPECTED_SAMPLES),np.arange(1),np.full(EXPECTED_SAMPLES,np.nan)])
def test_invalid_waveform_rejected(data):
    with pytest.raises(ValueError):
        named_channels({"Y":[{"Name":"vibration_1","Data":data}]})


def test_current_only_not_substituted():
    with pytest.raises(ValueError,match="vibration_1"):
        named_channels({"Y":[{"Name":"current","Data":np.arange(EXPECTED_SAMPLES)}]})


def test_non_nominal_count_is_reported_not_repaired():
    result=named_channels({"Y":[{"Name":"vibration_1","Data":np.arange(EXPECTED_SAMPLES+1)}]})
    assert result["sample_count"]==EXPECTED_SAMPLES+1
    assert result["expected_nominal_samples"]==EXPECTED_SAMPLES
    assert not result["nominal_sample_count_matches"]
