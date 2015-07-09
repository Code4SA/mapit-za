from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic.base import RedirectView

urlpatterns = patterns('',
    url(r'', include('mapit.urls')),

    url(r'^admin/', include(admin.site.urls)),
)
