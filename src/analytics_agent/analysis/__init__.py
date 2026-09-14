"""The analysis package: nine analyses, one registry, one gate in front.

**Importing this package registers every analysis.** The registry is populated
by decorator at import time, so `catalogue()` is only as complete as whatever
happened to be imported first. Measured in Step 9: a tool layer that imported
`registry` and three analysis modules reported three available analyses in its
unknown-type refusal -- and the Phase 8 Done-When is that an unknown type
returns THE valid list. A list missing six of nine is a wrong answer that reads
like a right one.

So the modules are imported here, for their registration side effect, and
nothing else has to remember to. Ordered by tier, then by name.
"""

from __future__ import annotations

from . import cross_tab as _cross_tab  # noqa: F401
from . import distribution as _distribution  # noqa: F401
from . import frequency as _frequency  # noqa: F401
from . import summary_stats as _summary_stats  # noqa: F401
from . import group_compare as _group_compare  # noqa: F401
from . import pareto as _pareto  # noqa: F401
from . import ranking_shift as _ranking_shift  # noqa: F401
from . import calendar_coverage as _calendar_coverage  # noqa: F401
