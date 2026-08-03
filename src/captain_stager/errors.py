class StagerError(Exception):
    """Base error for expected Stager failures."""
class ManifestError(StagerError):
    """Raised when a manifest is invalid."""
