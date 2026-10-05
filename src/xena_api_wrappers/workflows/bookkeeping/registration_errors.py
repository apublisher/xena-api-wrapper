class VoucherRegistrationError(ValueError):
    """Invalid registration input or an unexpected API response."""


class RegistrationInboxError(VoucherRegistrationError):
    """Invalid registration inbox input or an unexpected inbox response."""
