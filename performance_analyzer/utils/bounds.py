# AWARE-fix: shared sanity bounds for the typing metrics.
# Mirrors src/typing_metrics_v3.py SANITY_BOUNDS so legacy and v3 agree
# on what counts as a physically plausible value. When a metric falls
# outside these bounds (or cannot be computed, e.g. zero duration / zero
# transcribed length) the calculators return NaN (an explicit invalid
# sentinel) instead of 0. This prevents impossible values from silently
# masquerading as real "0 WPM/KSPS/KSPC" targets; downstream pipelines
# decide whether to drop or impute these NaNs (e.g. eda._outlier_mask
# treats NaN targets as removable).
from typing import Dict, Tuple

SANITY_BOUNDS: Dict[str, Tuple[float, float]] = {
    "wpm": (0.0, 250.0),
    "ksps": (0.0, 25.0),
    "kspc": (0.05, 20.0),
}
