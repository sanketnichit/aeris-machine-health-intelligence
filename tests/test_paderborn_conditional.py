import numpy as np
from research.paderborn_documents import technical_candidates,summarize_fields
from research.paderborn_conditional import evaluate,counts,score
from src.paderborn_preprocessing import effective_orders,WINDOW,WINDOWS


def test_pc_abbreviation_is_explicit_count():
    assert summarize_fields(technical_candidates("Number of rolling elements pc. 8"))["rolling_elements"]["value"]==8


def test_missing_geometry_never_loads_waveform():
    result=evaluate(b"invalid","example.mat","N15_M07_F10",None)
    assert result["nominal"]["suggestion"] is None
    assert result["stored_time"]["reason"]=="geometry_candidate_unresolved"


def test_conditional_summary_preserves_abstentions_and_healthy_false_suggestions():
    rows=[{"truth":"inner","nominal":{"suggestion":"inner","reason":"accepted"}},
          {"truth":"outer","nominal":{"suggestion":None,"reason":"withheld"}},
          {"truth":"normal","nominal":{"suggestion":"outer","reason":"accepted"}}]
    result=counts(rows,"nominal")
    assert result["correct_accepted"]==1 and result["fault_abstained"]==1
    assert result["normal_incorrect_accepted"]==1


def test_frozen_score_returns_research_suggestion_or_abstention():
    t=np.arange(WINDOW*WINDOWS)/12000
    orders=effective_orders(8,29.05,6.75,0.)
    x=(1+.7*np.sin(2*np.pi*25*orders["outer"]*t))*np.sin(2*np.pi*3000*t)
    result=score(x,orders,"N15_M07_F10")
    assert result["suggestion"]=="outer"
