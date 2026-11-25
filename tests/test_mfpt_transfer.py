import numpy as np
import pytest

from research.mfpt_transfer import FILES, FLOOR, MARGIN, RATE, WINDOW, WINDOWS, effective_signal, compare
from research.cwru_selective import decide


def test_frozen_population_and_policy():
    assert len(FILES)==17 and len({name for name,_ in FILES})==17
    assert sum(kind=="normal" for _,kind in FILES)==3
    assert sum(kind=="inner" for _,kind in FILES)==7
    assert sum(kind=="outer" for _,kind in FILES)==7
    assert FLOOR==0.00974446327636002 and MARGIN==.8


def test_metadata_and_resampling():
    t=np.arange(48828*3)/48828
    raw=np.sin(2*np.pi*100*t)+np.sin(2*np.pi*10000*t)
    data={"bearing":{"gs":raw,"sr":48828,"rate":25,"load":50},
          "BPFI":118.875,"BPFO":81.125,"BSF":63.91}
    y,centers,meta=effective_signal(data,"inner")
    assert len(y)==36000
    assert centers=={"inner":118.875,"outer":81.125,"ball":127.82}
    assert meta["source_rate_hz"]==48828
    expected=np.sin(2*np.pi*100*np.arange(len(y))/RATE)
    assert np.sqrt(np.mean((y[100:-100]-expected[100:-100])**2))<.02
    with pytest.raises(ValueError,match="Unexpected source frequency"):
        effective_signal({**data,"BPFI":200},"inner")
    with pytest.raises(ValueError,match="Unexpected source sampling"):
        effective_signal(data,"normal")


def test_known_outer_modulation():
    t=np.arange(WINDOW)/RATE
    centers={"inner":118.875,"outer":81.125,"ball":127.82}
    x=(1+.5*np.cos(2*np.pi*centers["outer"]*t))*np.sin(2*np.pi*3000*t)
    result=compare(x,centers)
    assert result["envelope"]["outer"]>.85
    assert decide(result["envelope"],FLOOR,MARGIN)["suggestion"]=="outer"
