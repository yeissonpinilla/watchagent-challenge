from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Float, Integer, UniqueConstraint

Base = declarative_base()

class HistoricalReading(Base):
    __tablename__ = "historical_readings"

    id = Column(Integer, primary_key=True)
    city = Column(String, index=True)
    timestamp = Column(String, index=True)

    temperature_2m = Column(Float)
    apparent_temperature = Column(Float)
    precipitation = Column(Float)
    wind_speed_10m = Column(Float)
    weather_code = Column(Integer)

    __table_args__ = (
        UniqueConstraint("city", "timestamp"),
    )

class LiveReading(Base):
    __tablename__ = "live_readings"

    id = Column(Integer, primary_key=True)
    city = Column(String, index=True)
    timestamp = Column(String, index=True)

    temperature_2m = Column(Float)
    apparent_temperature = Column(Float)
    precipitation = Column(Float)
    wind_speed_10m = Column(Float)
    weather_code = Column(Integer)

    __table_args__ = (
        UniqueConstraint("city", "timestamp"),
    )

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    city = Column(String, index=True)
    timestamp = Column(String, index=True)

    event_type = Column(String)
    reason = Column(String)
    value = Column(Float, nullable=True)

class MonthlyBaseline(Base):
    __tablename__ = "monthly_baselines"

    id = Column(Integer, primary_key=True)

    city = Column(String, index=True)
    month = Column(Integer, index=True)  # 1-12

    temp_mean = Column(Float)
    temp_std = Column(Float)
    temp_min = Column(Float)
    temp_max = Column(Float)
    temp_p5 = Column(Float)
    temp_p95 = Column(Float)

    wind_mean = Column(Float)
    wind_std = Column(Float)

    precip_mean = Column(Float)

    __table_args__ = (
        UniqueConstraint("city", "month"),
    )