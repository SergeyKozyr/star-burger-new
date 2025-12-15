from decimal import Decimal

import requests
from django.db import IntegrityError
from geopy import distance
from requests import RequestException

from location.models import Location


class LocationService:
    def __init__(self, geocoder_api_key: str) -> None:
        self._geocoder_api_key = geocoder_api_key
        self._addresses_coordinates = {
            location.address: (location.latitude, location.longitude)
            for location in Location.objects.iterator()
        }

    def _get_coordinates_from_db(
        self, address: str
    ) -> tuple[Decimal | None, Decimal | None] | None:
        return self._addresses_coordinates.get(address)

    def _save_coordinates_in_db(self, address: str, latitude: Decimal, longitude: Decimal) -> None:
        try:
            Location.objects.create(address=address, latitude=latitude, longitude=longitude)
            self._addresses_coordinates[address] = (latitude, longitude)
        except IntegrityError:
            pass

    def get_distance_between_addresses(
        self, first_address: str, second_address: str
    ) -> float | None:
        lat_1, lon_1 = self.get_coordinates(first_address)
        lat_2, lon_2 = self.get_coordinates(second_address)

        if all((lat_1, lon_1, lat_2, lon_2)):
            return round(distance.distance((lat_1, lon_1), (lat_2, lon_2)).km, 2)

    def get_coordinates(self, address: str) -> tuple[Decimal | None, Decimal | None] | None:
        if coordinates_from_db := self._get_coordinates_from_db(address):
            return coordinates_from_db

        latitude, longitude = self.fetch_coordinates_from_geocoder(address)
        self._save_coordinates_in_db(address, latitude, longitude)
        return latitude, longitude

    def fetch_coordinates_from_geocoder(
        self, address: str
    ) -> tuple[Decimal | None, Decimal | None]:
        base_url = "https://geocode-maps.yandex.ru/1.x"
        response = requests.get(
            base_url,
            params={"geocode": address, "apikey": self._geocoder_api_key, "format": "json"},
        )

        try:
            response.raise_for_status()
        except RequestException:
            return None, None

        found_places = response.json()["response"]["GeoObjectCollection"]["featureMember"]

        if not found_places:
            return None, None

        most_relevant = found_places[0]
        lon, lat = most_relevant["GeoObject"]["Point"]["pos"].split(" ")
        return Decimal(lat), Decimal(lon)
