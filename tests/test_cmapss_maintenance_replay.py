import pytest

from research.cmapss_maintenance_replay import terminal_outcome, summarize


def test_first_alert_only_and_unused_life():
    result = terminal_outcome([20,30,40], [40,19,3], 50,20,lead=5)
    assert result == dict(status="planned_maintenance",alert_cycle=30.,
                          lead_cycles=20.,unused_cycles=15.)


def test_late_alert_and_no_alert():
    assert terminal_outcome([20,30],[50,5],35,10)["status"] == "late_alert"
    assert terminal_outcome([20,30],[50,15],35,10)["status"] == "unplanned_failure"
    assert terminal_outcome([],[],10,10)["status"] == "unplanned_failure"


def test_cost_sensitivity():
    outcomes = [terminal_outcome([20],[5],40,10),
                terminal_outcome([20],[50],40,10),
                terminal_outcome([20],[5],25,10)]
    report = summarize(outcomes,10)
    assert report["planned"] == 1
    assert report["late_alerts"] == report["no_alerts"] == 1
    assert report["total_cost"] == pytest.approx(21.15)
    assert summarize(outcomes,25)["total_cost"] == pytest.approx(51.15)


@pytest.mark.parametrize("cycles,predictions", [([30,20],[2,3]),([40],[1]),([20],[-1]),([20],[])])
def test_reject_invalid_replay(cycles,predictions):
    with pytest.raises(ValueError):
        terminal_outcome(cycles,predictions,40,10)
