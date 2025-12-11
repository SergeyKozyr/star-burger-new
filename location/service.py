import logging

import requests
from django.db import IntegrityError
from geopy import distance
from requests import RequestException

from location.models import Location

logger = logging.getLogger(__name__)


class LocationService:
    def __init__(self, geocoder_api_key: str) -> None:
        self._geocoder_api_key = geocoder_api_key

    @staticmethod
    def _get_coordinates_from_db(address: str) -> tuple[str, str] | None:
        location = Location.objects.filter(address=address).first()
        return (str(location.latitude), str(location.longitude)) if location else None

    @staticmethod
    def _save_coordinates_in_db(address: str, latitude: str, longitude: str) -> None:
        try:
            Location.objects.create(address=address, latitude=latitude, longitude=longitude)
        except IntegrityError:
            logger.warning(f"Duplicate address: {address}")

    def get_distance_between_addresses(
        self, first_address: str, second_address: str
    ) -> float | None:
        first_coords = self.get_coordinates(first_address)
        second_coords = self.get_coordinates(second_address)

        if first_coords and second_coords:
            return round(distance.distance(first_coords, second_coords).km, 2)

    def get_coordinates(self, address: str) -> tuple[str, str] | None:
        if coordinates_from_db := self._get_coordinates_from_db(address):
            return coordinates_from_db

        latitude, longitude = self.fetch_coordinates_from_geocoder(address)
        self._save_coordinates_in_db(address, latitude, longitude)
        return latitude, longitude

    def fetch_coordinates_from_geocoder(self, address: str) -> tuple[str, str] | None:
        base_url = "https://geocode-maps.yandex.ru/1.x"
        response = requests.get(
            base_url,
            params={
                "geocode": address,
                "apikey": self._geocoder_api_key,
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
