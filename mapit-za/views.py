import urllib2, urllib
import json

from django.shortcuts import render
from django.conf import settings

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
        import ipdb; ipdb.set_trace()
        encoded_address = encode(address)
        address = urllib.quote(encoded_address)

        url = "https://maps.googleapis.com/maps/api/geocode/json?address=%s&sensor=false&region=za&key=%s" % (address, settings.GOOGLE_API_KEY)
        response = urllib2.urlopen(url)
        js = response.read()
        try:
            js = json.loads(js)
        except ValueError as e:
            # logger.exception("Error trying to resolve %s" % address)
            raise StandardError("Couldn't resolve %s: %s" % (address, e.message))

        results = []
        if "status" in js and js["status"] not in ("OK", "ZERO_RESULTS"):
            # logger.error("Error trying to resolve %s - %s (%s)" % (address, js.get("error_message", "Generic Error"), js))
            raise StandardError("Couldn't resolve %s: %s" % (address, js.get("error_message")))

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


    def convert_address(self, address, **kwargs):
        address = address.strip()
        if address == "": return None

        if not "south africa" in address.lower():
            address = address + ", South Africa"

        return self.resolve_address_google(address, **kwargs)


def a2w(request):
    address = request.GET['address']

    params = dict(request.GET)
    if "address" in params:
        del params["address"]
    import ipdb; ipdb.set_trace()
    converter = AddressConverter()
    lat_long = converter.convert_address(address, **params)

    if lat_long is None:
        # Return an error: No address or no results
        pass

