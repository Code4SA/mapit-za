from django.core.management.base import BaseCommand
from django.db import connection

from mapit.models import Area, CodeType
from ..za_metadata import MUNIS_TO_PROVINCE, WARDS_TO_MUNI_PROVINCE, DISTRICTS_TO_PROVINCE


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

    def handle(self, *args, **options):
        self.mdb_level_code = CodeType.objects.get(id=2)

        self.provinces = list(Area.objects.filter(type__code='PR', country__code='ZA'))
        self.provinces_by_code = dict((p.all_codes['MDB'], p) for p in self.provinces)

        if options['levels_global']:
            self.setup_global_level_codes()

        self.setup_district_parents()
        self.setup_district_codes()

        self.setup_muni_parents()
        self.setup_muni_codes()

        self.setup_ward_parents()
        self.setup_ward_codes()

    def setup_global_level_codes(self):
        self.stdout.write('Setting global level codes')
        cursor = connection.cursor()
        cursor.execute("""
        INSERT INTO mapit_code (area_id, code, type_id)
        SELECT a.id, CONCAT('CY-ZA|', t.code), 2
        FROM mapit_area a
        INNER JOIN mapit_type t ON a.type_id = t.id
        """)
        self.stdout.write('Done')

    def setup_district_parents(self):
        self.stdout.write('Setting district parent provinces')
        districts = list(Area.objects.filter(type__code='DC', country__code='ZA'))
        for d in districts:
            if not d.parent_area:
                d.parent_area = self.provinces_by_code[DISTRICTS_TO_PROVINCE[d.all_codes['MDB']]]
                d.save()
            code, _ = d.codes.get_or_create(type=self.mdb_level_code, code='PR-%s|DC' % d.parent_area.all_codes['MDB'])
            code.save()
        self.stdout.write('Done')

    def setup_district_codes(self):
        self.stdout.write('Setting district level codes')
        districts = list(Area.objects.filter(type__code='DC', country__code='ZA'))
        for d in districts:
            code, created = d.codes.get_or_create(type=self.mdb_level_code, code='PR-%s|DC' % d.parent_area.all_codes['MDB'])
            if created:
                code.save()
        self.stdout.write('Done')

    def setup_muni_parents(self):
        self.stdout.write('Setting muni parent provinces')
        # set muni parents and codes
        munis = list(Area.objects.filter(type__code='MN', country__code='ZA'))
        for m in munis:
            if not m.parent_area:
                m.parent_area = self.provinces_by_code[MUNIS_TO_PROVINCE[m.all_codes['MDB']]]
                m.save()
        self.stdout.write('Done')

    def setup_muni_codes(self):
        self.stdout.write('Setting muni level codes')
        # set muni parents and codes
        munis = list(Area.objects.filter(type__code='MN', country__code='ZA'))
        for m in munis:
            code, created = m.codes.get_or_create(type=self.mdb_level_code, code='PR-%s|MN' % m.parent_area.all_codes['MDB'])
            if created:
                code.save()
        self.stdout.write('Done')

    def setup_ward_parents(self):
        self.stdout.write('Setting ward parent munis')
        munis = list(Area.objects.filter(type__code='MN', country__code='ZA'))
        muni_lookup = dict((m.all_codes['MDB'], m) for m in munis)

        wards = list(Area.objects.filter(type__code='WD', country__code='ZA'))
        for w in wards:
            muni, prov = WARDS_TO_MUNI_PROVINCE[w.all_codes['MDB']]
            try:
                w.parent_area = muni_lookup[muni]
            except KeyError:
                continue
            w.save()
        self.stdout.write('Done')

    def setup_ward_codes(self):
        self.stdout.write('Setting ward level codes')
        wards = list(Area.objects.filter(type__code='WD', country__code='ZA'))
        for w in wards:
            muni, prov = WARDS_TO_MUNI_PROVINCE[w.all_codes['MDB']]

            code, created = w.codes.get_or_create(type=self.mdb_level_code, code='MN-%s|WD' % muni)
            if created:
                code.save()
            code, created = w.codes.get_or_create(type=self.mdb_level_code, code='PR-%s|WD' % prov)
            if created:
                code.save()

        self.stdout.write('Done')
