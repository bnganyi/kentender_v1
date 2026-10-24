# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The synthetic sources live in `simulation/sources.py` (development only); tests import them from here for brevity."""

from kentender_contracts.simulation.sources import *  # noqa: F401,F403
from kentender_contracts.simulation.sources import Provider, award_package, missing_from_real_handoff, source_handoff, SOURCES, REAL_TODAY, CASE, TERMS, SUPPLIER, LAPTOPS, UNIT_PRICE  # noqa: F401
