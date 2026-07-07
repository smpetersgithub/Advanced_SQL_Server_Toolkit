# Changes Applied — Database Access Conformance Analysis
**Date:** 2026-06-26  
**Source analysis:** `AI_Output_Database_Access_Conformance_Analysis_20260626_000000.md`

---

## Change 4 — Fix silent `database` default in Query Store ConfigLoader

**File modified:**
```
C:\Advanced_SQL_Server_Toolkit\Query_Store_Analysis_Utility\Core\Python\config_loader.py
```

**Issue:** Three methods in the Query Store `ConfigLoader` treated the `database` key in `database-config.json` as optional, silently falling back to `'master'` when it was absent. `get_server()` duplicated a validation check that belonged in the loader. This diverged from the pattern in Normalization and Dependency, which raise a `ValueError` for any missing required field as soon as the config is loaded.

---

### Method 1 — `_load_database_config()`: centralised validation added

Added validation for all required fields immediately after the JSON file is parsed, and added `json.JSONDecodeError` handling (this method previously also lacked it). Validation now mirrors the Dependency utility pattern exactly:

- `servername` and `database` are required; a `ValueError` naming the missing field(s) is raised if either is absent.
- When `windows_auth` is `False` (or absent), `username` and `password` are also required; a `ValueError` is raised if either is absent.

**Before:**
```python
def _load_database_config(self):
    """Load database configuration (lazy loading)."""
    if self.database_config is None:
        db_config_path = self.project_root / self.config['paths']['database_config']
        if not db_config_path.exists():
            raise FileNotFoundError(f"Database config not found: {db_config_path}")

        with open(db_config_path, 'r', encoding='utf-8') as f:
            self.database_config = json.load(f)

    return self.database_config
```

**After:**
```python
def _load_database_config(self):
    """Load and validate database configuration (lazy loading).

    Raises:
        FileNotFoundError: If database-config.json does not exist
        json.JSONDecodeError: If database-config.json contains invalid JSON
        ValueError: If required fields are missing from the configuration
    """
    if self.database_config is None:
        db_config_path = self.project_root / self.config['paths']['database_config']
        if not db_config_path.exists():
            raise FileNotFoundError(f"Database config not found: {db_config_path}")

        try:
            with open(db_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in database config file: {e.msg}", e.doc, e.pos
            )

        # Validate required fields
        required_keys = ['servername', 'database']
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            raise ValueError(
                f"Database configuration missing required field(s): {', '.join(missing_keys)}. "
                f"Please check Config/database-config.json"
            )

        # Validate authentication fields when not using Windows auth
        use_windows_auth = config.get('windows_auth', False)
        if not use_windows_auth:
            auth_keys = ['username', 'password']
            missing_auth = [key for key in auth_keys if key not in config]
            if missing_auth:
                raise ValueError(
                    f"Database configuration missing required field(s): {', '.join(missing_auth)} "
                    f"(required when 'windows_auth' is not set). "
                    f"Please check Config/database-config.json"
                )

        self.database_config = config

    return self.database_config
```

---

### Method 2 — `get_connection_string()`: removed redundant inline check and silent default

Removed the duplicated `if 'servername' not in db_config` guard (now handled in `_load_database_config()`).  
Replaced `db_config.get('database', 'master')` with `db_config['database']`.

**Before (relevant lines):**
```python
# Validate required fields
if 'servername' not in db_config:
    raise ValueError(
        "Database configuration is missing required field 'servername'. "
        "Please check Config/database-config.json"
    )

server = db_config['servername']
database = db_config.get('database', 'master')
```

**After:**
```python
server = db_config['servername']
database = db_config['database']
```

---

### Method 3 — `get_server()`: removed redundant inline check

**Before:**
```python
def get_server(self) -> str:
    db_config = self._load_database_config()
    if 'servername' not in db_config:
        raise ValueError(
            "Database configuration is missing required field 'servername'. "
            "Please check Config/database-config.json"
        )
    return db_config['servername']
```

**After:**
```python
def get_server(self) -> str:
    return self._load_database_config()['servername']
```

---

### Method 4 — `get_database()`: removed silent default

**Before:**
```python
def get_database(self) -> str:
    """Get the database name."""
    return self._load_database_config().get('database', 'master')
```

**After:**
```python
def get_database(self) -> str:
    """Get the database name.

    Raises:
        ValueError: If 'database' field is missing from database config
    """
    return self._load_database_config()['database']
```

---

### Behaviour after fix

A `database-config.json` missing `servername`, `database`, `username`, or `password` (where applicable) now raises a `ValueError` with a clear message naming the absent field(s), identical to the behaviour of the Normalization and Dependency utilities. The `ValueError` propagates to each script's `main()` `except (FileNotFoundError, ValueError, KeyError)` guard and exits with `sys.exit(1)`.

---

*No other files were modified.*

