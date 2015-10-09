import logging

import requests
from django.conf import settings


log = logging.getLogger(__name__)


class AddressConverter(object):
    def reject_partial_match(self, result):
        if "partial_match" in result and result["partial_match"]:
            return True
        return False

    def resolve_address_google(self, address, partial):
        if type(address) == unicode:
            address = address.encode('utf8')

        url = 'https://maps.googleapis.com/maps/api/geocode/json'
        params = {
            'address': address,
            'sensor': 'false',
            'region': 'za',
            'key': settings.GOOGLE_API_KEY}

        response = requests.get(url, params=params)
        js = response.json()

        if js.get('status') == 'ZERO_RESULTS':
            return []

        if js.get('status') == 'OK':
            results = []

            for result in js["results"]:
                # reject partial matches?
                if not partial and 'partial_match' in result:
                    continue

                geom = result["geometry"]["location"]
                results.append({
                    "lat": geom["lat"],
                    "lng": geom["lng"],
                    "formatted_address": result["formatted_address"],
                    "source": "Google Geocoding API",
                })

            return results

        log.error("Bad response from Google: %s" % js)
        raise ValueError("Couldn't geocode the address: %s" % js['status'])

    def resolve_address(self, address, partial=False):
        address = address.strip()
        if address == "":
            return []

        if "south africa" not in address.lower():
            address = address + ", South Africa"

        return self.resolve_address_google(address, partial)
