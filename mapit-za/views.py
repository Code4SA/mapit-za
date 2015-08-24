import urllib2, urllib
import json
import requests

from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest

def encode(s, encoding="utf8"):
    if type(s) == unicode:
        return s.encode(encoding)
    return s


def home(request):
    return render(request, 'index.html')


class AddressConverter(object):

    def reject_partial_match(self, result):
        if "partial_match" in result and result["partial_match"]:
            return True
        return False

    def resolve_address_google(self, address, **kwargs):
        # Is this still needed?
        encoded_address = encode(address)
        url = 'https://maps.googleapis.com/maps/api/geocode/json'
        params = {
            'address': encoded_address,
            'sensor': 'false',
            'region': 'za',
            'key': settings.GOOGLE_API_KEY}

        response = requests.get(url, params=params)
        js = response.json()

        results = []
        if "status" in js and js["status"] not in ("OK", "ZERO_RESULTS"):
            # raise StandardError("Couldn't resolve %s: %s" % (address, js.get("error_message")))
            return {'error': "Couldn't resolve %s: %s" % (address, js.get("error_message"))}

        if "results" in js and len(js["results"]) > 0:
            for result in js["results"]:

                res = self.reject_partial_match(result)
                if res: continue

                geom = result["geometry"]["location"]
                results.append({
                    "lat" : geom["lat"],
                    "lng" : geom["lng"],
                    "formatted_address" : result["formatted_address"],
                    "source" : "Google Geocoding API",
                })

            if len(results) == 0: return None
            return results

    def resolve_address(self, address, **kwargs):
        address = address.strip()
        if address == "": return None

        if not "south africa" in address.lower():
            address = address + ", South Africa"

        return self.resolve_address_google(address, **kwargs)


def convert_address(request):
    address = request.GET.get('address')
    if address is None:
        return HttpResponseBadRequest()
        # return JsonResponse({'error': 'No address provided.'})

    params = dict(request.GET)
    if "address" in params:
        del params["address"]

    converter = AddressConverter()
    lat_long = converter.resolve_address(address, **params)

    if lat_long is None:
        # Return an error: No address or no results
        pass
