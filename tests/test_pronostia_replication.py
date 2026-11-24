import io
import zipfile

import numpy as np
import pandas as pd
import pytest

from research.pronostia_replication import FIT, TEST, COUNTS, decode_snapshot, extract_archive, evaluate


@pytest.mark.parametrize("sep", [",",";"])
def test_acceleration_decoder(sep):
    raw=(sep.join(["1","2","3","4","2","-3"])+"\n").encode()*2560
    features=decode_snapshot(raw)
    assert features["horizontal_rms"]==2
    assert features["vertical_rms"]==3
    with pytest.raises(ValueError):
        decode_snapshot(raw[:100])


def test_nested_archive_excludes_truncated_test():
    raw=b"1,2,3,4,2,-3\n"*2560
    inner=io.BytesIO()
    with zipfile.ZipFile(inner,"w") as z:
        z.writestr("Learning_set/Bearing1_1/acc_00001.csv",raw)
        z.writestr("Test_set/Bearing1_3/acc_00001.csv",raw)
        z.writestr("Full_Test_Set/Bearing1_3/acc_00001.csv",raw)
    outer=io.BytesIO()
    with zipfile.ZipFile(outer,"w") as z:
        z.writestr("data.zip",inner.getvalue())
    rows,seen=[],set()
    with zipfile.ZipFile(outer) as z:
        extract_archive(z,rows,seen)
    assert seen=={("Bearing1_1",1),("Bearing1_3",1)}
    assert len(rows)==2


def test_independent_bearings():
    assert len(FIT)==6 and len(TEST)==11 and not FIT & TEST
    assert set(COUNTS)==FIT|TEST
    data=pd.DataFrame([{"bearing":b,"condition":int(b[7]),"age":a,
                        "horizontal_rms":float(a),"vertical_rms":float(a*2)}
                       for b in sorted(FIT|TEST) for a in range(1,13)])
    report=evaluate(data)
    assert report["primary"]=="switch_2x"
    assert set(report["fit_bearings"])==FIT
    assert set(report["evaluation_bearings"])==TEST
    assert {r["bearing"] for r in report["predictions"]}==TEST
    assert report["summary"]["stage"]["all"]["switch_2x"]["endpoints"]==44
