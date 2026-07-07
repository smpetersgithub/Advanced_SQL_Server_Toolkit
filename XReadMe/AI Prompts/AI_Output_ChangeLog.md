## Fix #10 — Dead code: removed unused LOG_LEVEL_MAP constant (DDL Generator)
**Date:** 2026-06-26
**File:** DDL_Generator_Utility\Core\Python\config_loader.py
### Change
Removed the unused LOG_LEVEL_MAP class-level constant from ConfigLoader.
The constant mapped string level names to logging.* integer values, but
setup_logging() already used getattr(logging, self.get_log_level().upper(), logging.INFO)
to resolve the level — making LOG_LEVEL_MAP unreachable dead code.
A comment ("retained for reference only") had been added to justify keeping it,
but dead constants with justification comments are themselves a code smell.
### Before
`python
class ConfigLoader:
    """Centralized configuration loader for DDL Generator Utility."""
    # Log level mapping constant — retained for reference only (getattr() is used in setup_logging)
    LOG_LEVEL_MAP = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    def __init__(self, ...):
`
### After
`python
class ConfigLoader:
    """Centralized configuration loader for DDL Generator Utility."""
    def __init__(self, ...):
`
### Verification
Select-String scan of all DDL Generator Python scripts confirmed zero
references to LOG_LEVEL_MAP outside its own definition before removal.
