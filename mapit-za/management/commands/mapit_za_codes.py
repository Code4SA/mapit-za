from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from django.db import connection

from mapit.models import Area, CodeType, Generation
from ..za_metadata import MUNIS_TO_DISTRICT, METROS_TO_PROVINCE, WARDS_TO_MUNI, DISTRICTS_TO_PROVINCE


def muni_to_province(muni):
    if muni in MUNIS_TO_DISTRICT:
        return DISTRICTS_TO_PROVINCE[MUNIS_TO_DISTRICT[muni]]
    else:
        return METROS_TO_PROVINCE[muni]


class Command(BaseCommand):
    help = 'Attaches MDB-level codes to ZA areas'

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--mdb-levels-global',
            action='store_true',
            dest='levels_global',
            default=False,
            help='Setup global MDB level codes')
        parser.add_argument(
            '--generation',
            action='store',
            dest='generation',
            default=None,
            help='Generation to use (default is most recent')

    def handle(self, *args, **options):
        self.generation = options.get('generation') or Generation.objects.current().id
        self.generation = Generation.objects.get(id=self.generation)
        self.stdout.write("Using generation %s" % self.generation)

        self.mdb_level_code = CodeType.objects.get(id=2)

        self.all_areas = list(Area.objects.filter(country__code='ZA', generation_high=self.generation))
        self.all_areas = {a.all_codes['MDB']: a for a in self.all_areas}

        if options['levels_global']:
            self.setup_global_level_codes()

        self.setup_district_parents()
        #self.setup_district_codes()

        self.setup_muni_parents()
        #self.setup_muni_codes()

        #self.setup_ward_parents()
        #self.setup_ward_codes()

    def setup_global_level_codes(self):
        self.stdout.write('Setting global level codes')
        cursor = connection.cursor()
        cursor.execute("""
        INSERT INTO mapit_code (area_id, code, type_id)
        SELECT a.id, CONCAT('CY-ZA|', t.code), 2
        FROM mapit_area a
        INNER JOIN mapit_type t ON a.type_id = t.id
        WHERE a.generation_high_id == %s
        """ % self.generation.id)
        self.stdout.write('Done')

    def setup_district_parents(self):
        self.stdout.write('Setting district parent provinces')
        for d in self.get_areas('DC'):
            if not d.parent_area:
                d.parent_area = self.all_areas[DISTRICTS_TO_PROVINCE[d.all_codes['MDB']]]
                self.stdout.write("%s is in %s" % (d, d.parent_area))
                d.save()
            code, _ = d.codes.get_or_create(type=self.mdb_level_code, code='PR-%s|DC' % d.parent_area.all_codes['MDB'])
            code.save()
        self.stdout.write('Done')

    def setup_district_codes(self):
        self.stdout.write('Setting district level codes')
        for d in self.get_areas('DC'):
            code, created = d.codes.get_or_create(type=self.mdb_level_code, code='PR-%s|DC' % d.parent_area.all_codes['MDB'])
            if created:
                code.save()
        self.stdout.write('Done')

    def setup_muni_parents(self):
        self.stdout.write('Setting muni parents')
        # set muni parents and codes
        for m in self.get_areas('MN'):
            if not m.parent_area:
                # local munis have districts as a parent, metros have provinces
                muni = m.all_codes['MDB']
                if muni in MUNIS_TO_DISTRICT:
                    # local
                    m.parent_area = self.all_areas[MUNIS_TO_DISTRICT[muni]]
                else:
                    # province
                    m.parent_area = self.all_areas[METROS_TO_PROVINCE[muni]]
                self.stdout.write("%s is in %s" % (m, m.parent_area))
                m.save()
        self.stdout.write('Done')

    def setup_muni_codes(self):
        self.stdout.write('Setting muni level codes')
        # set muni parents and codes
        for m in self.get_areas('MN'):
            code, created = m.codes.get_or_create(type=self.mdb_level_code, code='PR-%s|MN' % m.parent_area.all_codes['MDB'])
            if created:
                code.save()
        self.stdout.write('Done')

    def setup_ward_parents(self):
        self.stdout.write('Setting ward parent munis')
        muni_lookup = dict((m.all_codes['MDB'], m) for m in self.get_areas('WD'))

        for w in self.get_areas('WD'):
            muni = WARDS_TO_MUNI[w.all_codes['MDB']]
            try:
                w.parent_area = muni_lookup[muni]
                self.stdout.write("%s is in %s" % (w, w.parent_area))
            except KeyError:
                continue
            w.save()
        self.stdout.write('Done')

    def setup_ward_codes(self):
        self.stdout.write('Setting ward level codes')
        wards = list(Area.objects.filter(type__code='WD', country__code='ZA', generation=self.generation))
        for w in wards:
            muni = WARDS_TO_MUNI[w.all_codes['MDB']]
            prov = muni_to_province(muni)

            code, created = w.codes.get_or_create(type=self.mdb_level_code, code='MN-%s|WD' % muni)
            if created:
                code.save()
            code, created = w.codes.get_or_create(type=self.mdb_level_code, code='PR-%s|WD' % prov)
            if created:
                code.save()

        self.stdout.write('Done')

    def get_areas(self, typ):
        return [a for a in self.all_areas.itervalues() if a.type.code == typ]
