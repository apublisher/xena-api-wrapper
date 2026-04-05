from __future__ import annotations

# Verified by capture/testing in this workspace:
# - EHF can be sent through API-key based generated client flow.
# - Email send endpoint may require bearer/session auth in this tenant.
EMAIL_SEND_SUPPORTED_VIA_API_KEY = False

DEFAULT_EHF_RECIPIENT_ADDRESS_TYPE = "NOORG"
SUPPORTED_DISTRIBUTION_MODES = frozenset({"none", "email", "ehf"})
