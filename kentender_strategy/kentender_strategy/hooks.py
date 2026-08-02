# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""kentender_strategy app shell after MVP-1 preparatory teardown.

Old Strategy DocTypes/APIs/UI were removed. Rebuild lands in a later pass
(STRATEGY-MVP1-REQ-1.0). Keep the app installable for dependency order only.
"""

app_name = "kentender_strategy"
app_title = "Kentender Strategy"
app_publisher = "KenTender"
app_description = "KenTender strategy and planning module (MVP-1 rebuild pending)."
app_email = "dev@kentender.local"
app_license = "mit"

required_apps = ["kentender_core"]
