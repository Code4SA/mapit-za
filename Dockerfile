FROM python:2.7.18

ENV PYTHONUNBUFFERED 1

RUN set -ex; \
  apt-get update; \
  # dependencies for building Python packages \
  apt-get install -y build-essential; \
  # psycopg2 dependencies \
  apt-get install -y libpq-dev; \
  apt-get install -y binutils libproj-dev gdal-bin; \
  # git for codecov file listing \
  apt-get install -y git; \
  # cleaning up unused files \
  apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false; \
  rm -rf /var/lib/apt/lists/*

# Copy, then install requirements before copying rest for a requirements cache layer.
RUN mkdir /app
COPY requirements.txt /app
RUN pip install -r /app/requirements.txt

COPY . /app

WORKDIR /app

EXPOSE 5000

# Fix
RUN sed -i "s|ver = geos_version().decode()|ver = geos_version().decode().split(' ')[0]|g" /usr/local/lib/python2.7/site-packages/django/contrib/gis/geos/libgeos.py

RUN python manage.py collectstatic --noinput

CMD gunicorn mapit-za.wsgi:application --log-file - --bind 0.0.0.0:5000