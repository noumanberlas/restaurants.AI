from __future__ import annotations

import os

# Keep tests on the local SQLite layer instead of writing to live Azure Table Storage
os.environ["TABLE_STORAGE_CONNECTION_STRING"] = ""
