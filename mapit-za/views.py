from itertools import chain

from django.shortcuts import render
from django.contrib.gis.geos import Point
from django.conf import settings
from django.utils.translation import ugettext as _

from mapit.middleware import ViewException
from mapit.views.areas import add_codes, PYGDAL, query_args, output_html, output_json
from mapit.ratelimitcache import ratelimit
from mapit.models import Area, Geometry
from mapit.iterables import iterdict

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

    # this is a copy from mapit.views.areas.areas_by_point
    # because it's hard to reuse their code :(

    if PYGDAL:
        from osgeo import gdal
        gdal.UseExceptions()

    # we find areas for every lat/long coord we got back
    areas = []
    type = request.GET.get('type', '')
    for coords in locations:
        location = Point(float(coords['lng']), float(coords['lat']), srid=4326)
        try:
            location.transform(settings.MAPIT_AREA_SRID, clone=True)
        except:
            raise ViewException(format, _('Point outside the area geometry'), 400)

        args = query_args(request, format)
        if type:
            args = dict(("area__%s" % k, v) for k, v in args.items())
            # So this is odd. It doesn't matter if you specify types, PostGIS will
            # do the contains test on all the geometries matching the bounding-box
            # index, even if it could be much quicker to filter some out first
            # (ie. the EUR ones).
            coords['areas'] = []
            args['polygon__bbcontains'] = location
            shapes = Geometry.objects.filter(**args).defer('polygon')
            for shape in shapes:
                try:
                    area = Area.objects.get(polygons__id=shape.id, polygons__polygon__contains=location)
                    coords['areas'].append(str(area.id))
                    areas.append(area)
                except:
                    pass
        else:
            geoms = list(Geometry.objects.filter(polygon__contains=location).defer('polygon'))
            args['polygons__in'] = geoms
            matches = Area.objects.filter(**args).all()
            coords['areas'] = [str(m.id) for m in matches]
            areas.extend(matches)

    areas = add_codes(areas)
    if format == 'html':
        return output_html(request, _("Areas matching the address '{0}'").format(address), areas, indent_areas=True)

    # hack to include the geocoded addresses in the results
    data = iterdict(chain(
        ((area.id, area.as_dict()) for area in areas),
        [("addresses", locations)]))
    return output_json(data)
