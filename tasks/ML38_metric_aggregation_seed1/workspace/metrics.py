"""Metric computation for ad impressions — BUG: raw count CTR."""
import numpy as np
from typing import List


def compute_ctr(session_clicks: List[int], session_impressions: List[int]) -> float:
    """Ad Click-Through Rate computation.

    BUG: Uses raw aggregate counts instead of per-session rate averaging.
    This is susceptible to Simpson\'s paradox: sessions with many impressions
    (heavy users) dominate the aggregate, hiding the true per-user rate.

    Fix: Compute per-session CTR and average across sessions.
    """
    if not session_clicks or not session_impressions:
        return 0.0

    total_clicks = sum(session_clicks)
    total_impressions = sum(session_impressions)

    # BUG: raw aggregate — dominated by heavy sessions
    if total_impressions == 0:
        return 0.0
    return total_clicks / total_impressions  # BUG: not per-session average


def compute_ctr_correct(session_clicks: List[int], session_impressions: List[int]) -> float:
    """Reference implementation: per-session CTR (not used in pipeline — BUG)."""
    if not session_clicks or not session_impressions:
        return 0.0
    per_session = [c / i for c, i in zip(session_clicks, session_impressions) if i > 0]
    if not per_session:
        return 0.0
    return float(np.mean(per_session))


def compare_groups(
    control_clicks: List[int], control_impressions: List[int],
    treatment_clicks: List[int], treatment_impressions: List[int],
) -> dict:
    """Compare CTR between control and treatment groups.

    BUG: Uses raw-count CTR for the comparison — susceptible to Simpson\'s paradox.
    The treatment may show higher raw CTR even if per-session CTR is lower,
    because treatment users happen to have fewer impressions per session.
    """
    ctrl_ctr = compute_ctr(control_clicks, control_impressions)
    trt_ctr = compute_ctr(treatment_clicks, treatment_impressions)
    lift = trt_ctr - ctrl_ctr
    return {
        "control_ctr": round(ctrl_ctr, 6),
        "treatment_ctr": round(trt_ctr, 6),
        "absolute_lift": round(lift, 6),
        "relative_lift": round(lift / ctrl_ctr if ctrl_ctr > 0 else 0, 4),
        "method": "raw_counts",  # BUG: should be "per_session_average"
    }
