from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import TemplateView

from views import convert_address

urlpatterns = patterns('',
    url(r'^address(?:\.(?P<format>html|json))?', convert_address, name='convert_address'),
    url(r'', include('mapit.urls')),
    url(r'^robots.txt$', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),

    url(r'^admin/', include(admin.site.urls)),
)
