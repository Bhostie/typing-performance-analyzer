"""Tests for TypingSpeedCalculator and ErrorRateCalculator.

Recreated from the original (deleted) ``tests/test_calculators.py`` and
extended to cover the AWARE-fix "Option A" behaviour: when a metric is
out of its sanity bounds *or* cannot be computed (zero duration / zero
transcribed length), the calculators now return ``NaN`` instead of ``0``.

KSPC is exercised through ``object.__new__(ErrorRateCalculator)`` so the
tests do not pay the cost of the lingua language detector in ``__init__``;
``kspc()`` only depends on ``self.data_list`` and ``self.sessions``. This
mirrors the fast path used in ``src/event_based_segmentation._fast_kspc``.
"""

import math
from typing import Dict, List

import sys
from pathlib import Path

# The vendored spellcheck module uses `from utils.string import ...`, which
# only resolves when the inner package dir is on sys.path. The main pipeline
# does the same (see src/event_based_segmentation.py).
_PKG_DIR = Path(__file__).resolve().parent.parent / "performance_analyzer"
if str(_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(_PKG_DIR))

from performance_analyzer.typing_speed import TypingSpeedCalculator
from performance_analyzer.error_rate import ErrorRateCalculator
from performance_analyzer.utils.session import SessionUtil
from performance_analyzer.utils.bounds import SANITY_BOUNDS


def _row(ts: int, before: str, current: str) -> Dict[str, str]:
    return {"timestamp": str(ts), "before_text": before, "current_text": current}


def _kspc(data_list: List[Dict[str, str]]) -> float:
    """Compute KSPC without triggering the heavy lingua/spellcheck init."""
    calc = object.__new__(ErrorRateCalculator)
    calc.data_list = data_list
    calc.sessions = SessionUtil.split_into_sessions(data_list)
    return calc.kspc()


# --------------------------------------------------------------------------- #
# Valid, in-bounds typing -> finite values                                    #
# --------------------------------------------------------------------------- #

def _normal_sequence() -> List[Dict[str, str]]:
    # "" -> H -> He -> Hel -> Hell -> Hello over 2.0 s.
    return [
        _row(1000, "", "H"),
        _row(1500, "H", "He"),
        _row(2000, "He", "Hel"),
        _row(2500, "Hel", "Hell"),
        _row(3000, "Hell", "Hello"),
    ]


def test_wpm_normal_is_finite_and_in_bounds():
    wpm = TypingSpeedCalculator(_normal_sequence()).wpm()
    lo, hi = SANITY_BOUNDS["wpm"]
    assert not math.isnan(wpm)
    assert lo <= wpm <= hi
    # (5 produced chars - 1) / 2.0 s * 12 = 24.0
    assert wpm == 24.0


def test_ksps_normal_is_finite_and_in_bounds():
    ksps = TypingSpeedCalculator(_normal_sequence()).ksps()
    lo, hi = SANITY_BOUNDS["ksps"]
    assert not math.isnan(ksps)
    assert lo <= ksps <= hi
    # (5 events - 1) / 2.0 s = 2.0
    assert ksps == 2.0


def test_kspc_normal_is_finite_and_in_bounds():
    kspc = _kspc(_normal_sequence())
    lo, hi = SANITY_BOUNDS["kspc"]
    assert not math.isnan(kspc)
    assert lo <= kspc <= hi
    # 5 events / 5 transcribed chars = 1.0
    assert kspc == 1.0


# --------------------------------------------------------------------------- #
# Out-of-bounds -> NaN (Option A)                                             #
# --------------------------------------------------------------------------- #

def test_wpm_and_ksps_above_bounds_return_nan():
    # 1000 chars produced in 1 ms -> absurd WPM and KSPS.
    seq = [_row(0, "", ""), _row(1, "", "X" * 1000)]
    calc = TypingSpeedCalculator(seq)
    assert math.isnan(calc.wpm())
    assert math.isnan(calc.ksps())


def test_kspc_above_upper_bound_returns_nan():
    # 50 keystrokes but only 1 transcribed character -> KSPC = 50 (> 20).
    seq = [_row(0, "", "a")] + [_row(i, "a", "a") for i in range(1, 50)]
    assert math.isnan(_kspc(seq))


def test_kspc_below_lower_bound_returns_nan():
    # 2 keystrokes, 100 transcribed characters -> KSPC = 0.02 (< 0.05).
    seq = [_row(0, "", ""), _row(1, "", "a" * 100)]
    assert math.isnan(_kspc(seq))


# --------------------------------------------------------------------------- #
# Cannot-compute (degenerate) -> NaN (Option A)                               #
# --------------------------------------------------------------------------- #

def test_wpm_zero_duration_returns_nan():
    seq = [_row(1000, "", "Hello"), _row(1000, "Hello", "Hello!")]
    assert math.isnan(TypingSpeedCalculator(seq).wpm())


def test_ksps_zero_duration_returns_nan():
    seq = [_row(1000, "", "Hello"), _row(1000, "Hello", "Hello!")]
    assert math.isnan(TypingSpeedCalculator(seq).ksps())


def test_wpm_no_produced_characters_returns_nan():
    # Net zero produced text over a real duration -> NaN, not 0.
    seq = [_row(1000, "", ""), _row(2000, "", "")]
    assert math.isnan(TypingSpeedCalculator(seq).wpm())


def test_kspc_zero_transcribed_returns_nan():
    seq = [_row(1000, "", ""), _row(2000, "", "")]
    assert math.isnan(_kspc(seq))
