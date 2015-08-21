from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import TemplateView

from views import a2w

urlpatterns = patterns('',
    url(r'^address', a2w, name='a2w'),
    url(r'', include('mapit.urls')),
    url(r'^robots.txt$', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),

    url(r'^admin/', include(admin.site.urls)),
)
