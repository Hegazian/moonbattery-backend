"""Application settings loaded from environment variables."""

import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://moonbattery:moonbattery@localhost:5432/moonbattery",
)
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
