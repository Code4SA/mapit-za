Code4SA's MapIt API
===================

MapIt is a service that maps geographical points to administrative areas. It’s useful for anyone who has the co-ordinates of a particular point, and needs to find out what regions it lies within. It’s also great for looking up the shapes of all those boundaries.

Local development
-----------------

1. clone the repo
2. ``cd mapit-za``
3. ``virtualenv --no-site-packages env``
4. ``source env/bin/activate``

You'll need to install the GDAL and related libraries for your platform, see the [GeoDjango documentation](https://docs.djangoproject.com/en/1.8/ref/contrib/gis/).

5. ``pip install -r requirements.txt``
6. ``./manage.py runserver``

Production deployment
---------------------

This app runs on Dokku (or Heroku).

Be sure to set these environment variables:

* ``DJANGO_DEBUG=false``
* ``DJANGO_SECRET_KEY=some-secret-key``
* ``BUILDPACK_URL=https://github.com/ddollar/heroku-buildpack-multi.git``
* ``NEW_RELIC_APP_NAME=Mapit``
* ``NEW_RELIC_LICENSE_KEY=some-license-key``
