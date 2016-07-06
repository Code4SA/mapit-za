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

Importing new boundaries
------------------------

Every now and then you need to import new boundaries into Mapit. Generally this is after the [Demarcation Board](http://www.demarcation.org.za/) adjusts boundaries. For more information on importing data into Mapit, [read the import documentation](http://mapit.poplus.org/docs/self-hosted/import/boundaries/).

1. Get the SHP files with the new dataset
2. **Important:** If you're importing districts, you MUST remove the metro municipalities from the district shapefile first. Otherwise, because the MDB includes metros in both district and municipality shapefiles, the same district will be imported twice with the same codes but different municipality types.
2. Create a new generation (without activating it)

        python manage.py mapit_generation_create --desc "2016 electoral boundaries" --commit

3. Take note of the ID of the generation you just created, you'll need it later.
4. Import the shapes for each area type (ward, province, etc) separately, specifying the new generation ID. For each shapefile you need to tell Mapit which fields from the shapefile to use for the **name** and **code** fields in the database.

        python manage.py mapit_import --generation_id=XXX --country_code=ZA --name_type_code=common --code_type=MDB --area_type_code=WD --name_field=WardID --cade_field=WardID -v 2 --preserve shapefile.shp``

5. That WON'T make any changes since you haven't specified ``--commit`` but it lets you sanity check what's going on. Run it again with ``--commit``.
6. Ensure that mapit-za/management/za_metadata.py is up to date with the latest mappings between different levels.
7. Update the MDB-level codes:

        python manage.py mapit_za_codes --generation=2

8. Only activate the new generation once all the data has been imported:

        python manage.py mapit_generation_activate


Production deployment
---------------------

This app runs on Dokku (or Heroku).

Be sure to set these environment variables:

* ``DJANGO_DEBUG=false``
* ``DJANGO_SECRET_KEY=some-secret-key``
* ``BUILDPACK_URL=https://github.com/ddollar/heroku-buildpack-multi.git``
* ``NEW_RELIC_APP_NAME=Mapit``
* ``NEW_RELIC_LICENSE_KEY=some-license-key``
