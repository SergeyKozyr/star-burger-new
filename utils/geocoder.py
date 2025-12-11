import logging

import requests
from django.conf import settings
from geopy import distance
from requests import RequestException

logger = logging.getLogger(__name__)


def fetch_coordinates(apikey: str, address: str) -> tuple[str, str] | None:
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(
        base_url,
        params={
            "geocode": address,
            "apikey": apikey,
            "format": "json",
        },
    )

    try:
        response.raise_for_status()
    except RequestException:
        logger.warning(
            f"Failed to fetch coordinates for {address}: {response.status_code=} {response.text=}"
        )
        return None

    found_places = response.json()["response"]["GeoObjectCollection"]["featureMember"]

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant["GeoObject"]["Point"]["pos"].split(" ")
    return lat, lon


def get_distance_between_addresses(first_address: str, second_address: str) -> float | None:
    api_key = settings.YANDEX_GEOCODER_API_KEY
    first_coords = fetch_coordinates(api_key, first_address)
    second_coords = fetch_coordinates(api_key, second_address)

    if first_coords and second_coords:
        return round(distance.distance(first_coords, second_coords).km, 2)
