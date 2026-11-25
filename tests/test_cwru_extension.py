import numpy as np
import pytest

from research.cwru_extension import FILES, ORDERS, WINDOW, WINDOWS, RATE, compare, effective_signal, summarize


def test_new_population():
    ids = {x[0] for x in FILES}
    assert len(ids) == len(FILES) == 20
    assert not ids & (set(range(105,109)) | set(range(130,134)))
    assert sum(x[1] == "normal" for x in FILES) == 4


def test_normal_rate_conversion():
    t = np.arange(WINDOW * WINDOWS * 4) / 48000
    x = np.sin(2*np.pi*100*t) + np.sin(2*np.pi*10000*t)
    y = effective_signal(x[:,None], "normal")
    assert len(y) == WINDOW * WINDOWS
    # Ignore filter boundaries; the 10 kHz tone must not alias to 2 kHz.
    expected = np.sin(2*np.pi*100*np.arange(len(y))/RATE)
    assert np.sqrt(np.mean((y[100:-100]-expected[100:-100])**2)) < .01
    with pytest.raises(ValueError, match="Incomplete"):
        effective_signal(x[:100,None], "normal")


def test_rolling_element_modulation():
    t = np.arange(WINDOW)/RATE
    rpm = 1800
    x = (1+.5*np.cos(2*np.pi*ORDERS["ball"]*rpm/60*t))*np.sin(2*np.pi*3000*t)
    result = compare(x,rpm)
    assert result["envelope"]["ball"] > .85
    assert result["envelope"]["ball"] > max(result["envelope"]["inner"],result["envelope"]["outer"])


def test_summary_counts_ties_as_not_first_and_auc_half():
    def row(kind, fractions):
        return {"fault":kind,"diameter_in":.007,"median_fractions":{"raw":fractions,"envelope":fractions}}
    rows = [row("normal",{"inner":.2,"outer":.1,"ball":.1}),
            row("inner",{"inner":.3,"outer":.1,"ball":.1}),
            row("ball",{"inner":.2,"outer":.1,"ball":.2})]
    result = summarize(rows)
    assert result["representations"]["raw"]["expected_first_count"] == 1
    assert result["representations"]["raw"]["normal_fault_pairwise_auc"] == .75
    assert sum(result["expected_fraction_improvements_by_group"].values()) == 0
