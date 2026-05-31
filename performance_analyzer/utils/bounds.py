# AWARE-fix: shared sanity bounds for the typing metrics.
# Mirrors src/typing_metrics_v3.py SANITY_BOUNDS so legacy and v3 agree
# on what counts as a physically plausible value. When a metric falls
# outside these bounds we treat it as invalid and return 0 (keeping the
# library's existing return type; downstream pipelines decide whether
# to drop or impute these zeros).
from typing import Dict, Tuple

SANITY_BOUNDS: Dict[str, Tuple[float, float]] = {
    "wpm": (0.0, 250.0),
    "ksps": (0.0, 25.0),
    "kspc": (0.05, 20.0),
}
