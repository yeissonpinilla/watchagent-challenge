from unittest.mock import MagicMock, patch

import requests

from app.services.poller import fetch_current, parse_current, store_if_new


def test_parse_current_returns_reading_dict():
    data = {
        "current": {
            "time": "2026-05-30T10:00",
            "temperature_2m": 18.5,
            "apparent_temperature": 17.0,
            "precipitation": 0.0,
            "wind_speed_10m": 12.0,
            "weather_code": 0,
        }
    }

    result = parse_current(data, "Toronto")

    assert result == {
        "city": "Toronto",
        "timestamp": "2026-05-30T10:00",
        "temperature_2m": 18.5,
        "apparent_temperature": 17.0,
        "precipitation": 0.0,
        "wind_speed_10m": 12.0,
        "weather_code": 0,
    }


def test_parse_current_returns_none_when_current_missing():
    assert parse_current({}, "Toronto") is None


@patch("app.services.poller.requests.get")
def test_fetch_current_returns_json_on_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"current": {"time": "2026-05-30T10:00"}}
    mock_get.return_value = mock_response

    result = fetch_current("Toronto", 43.70, -79.42)

    assert result == {"current": {"time": "2026-05-30T10:00"}}
    mock_get.assert_called_once()


@patch("app.services.poller.requests.get")
def test_fetch_current_returns_none_on_timeout(mock_get):
    mock_get.side_effect = requests.exceptions.Timeout()

    assert fetch_current("Toronto", 43.70, -79.42) is None


def test_store_if_new_persists_first_reading():
    mock_db = MagicMock()
    mock_db.query.return_value.filter_by.return_value.first.return_value = None
    mock_db.refresh = MagicMock()

    reading_data = {
        "city": "Toronto",
        "timestamp": "2026-05-30T10:00",
        "temperature_2m": 18.0,
        "apparent_temperature": 17.0,
        "precipitation": 0.0,
        "wind_speed_10m": 10.0,
        "weather_code": 0,
    }

    result = store_if_new(mock_db, reading_data)

    assert result is not None
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


def test_store_if_new_skips_duplicate_city_timestamp():
    mock_db = MagicMock()
    mock_db.query.return_value.filter_by.return_value.first.return_value = MagicMock()

    reading_data = {
        "city": "Toronto",
        "timestamp": "2026-05-30T10:00",
        "temperature_2m": 18.0,
        "apparent_temperature": 17.0,
        "precipitation": 0.0,
        "wind_speed_10m": 10.0,
        "weather_code": 0,
    }

    result = store_if_new(mock_db, reading_data)

    assert result is None
    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()
