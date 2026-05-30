import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./data/watchagent.db"
)

CITIES = {
    "Ottawa": (45.42, -75.69),
    "Toronto": (43.70, -79.42),
    "Vancouver": (49.25, -123.12),
}

HISTORICAL_DATA_DAYS = 90