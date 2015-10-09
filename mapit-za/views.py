from django.shortcuts import render

from mapit.middleware import ViewException
from mapit.views.areas import areas_by_point
from mapit.ratelimitcache import ratelimit

from .address import AddressConverter


def home(request):
    return render(request, 'index.html')


@ratelimit(minutes=3, requests=100)
def convert_address(request, format='json'):
    address = request.GET.get('address')
    if not address:
        raise ViewException(format, 'No address was provided.', 400)

    converter = AddressConverter()
    locations = converter.resolve_address(address, partial=bool(request.GET.get('partial')))

    if not locations:
        # TODO: something better than this
        raise ViewException(format, 'No areas could be found.', 404)


    # TODO: also return the formatted address
    # TODO: use all points
    # When would multiple results be returned?
    location = locations[0]
    return areas_by_point(request, 4326, location['lng'], location['lat'], format=format)
