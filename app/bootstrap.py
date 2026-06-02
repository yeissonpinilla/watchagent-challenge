import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    Path("data").mkdir(parents=True, exist_ok=True)

    from app.db.initialize import initialize_database

    initialize_database()
    logger.info("database_initialized")

    from app.db.session import SessionLocal
    from app.db.models import MonthlyBaseline

    db = SessionLocal()
    try:
        if db.query(MonthlyBaseline).count() == 0:
            logger.info("seeding_historical_data_and_baselines")
            from app.services.historical_ingestor import run as ingest_historical
            from app.services.baseline_builder import build_baselines

            ingest_historical()
            build_baselines()
            logger.info("baselines_ready")
    finally:
        db.close()


if __name__ == "__main__":
    main()
