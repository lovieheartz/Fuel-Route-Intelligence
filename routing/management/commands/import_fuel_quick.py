"""
Quick import command for fuel stations without geocoding.
Uses pre-defined state coordinates for fast setup.
"""
import csv
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from routing.models import FuelStation


# Approximate coordinates for US states (state center)
STATE_COORDS = {
    'AL': (32.806671, -86.791130), 'AK': (61.370716, -152.404419),
    'AZ': (33.729759, -111.431221), 'AR': (34.969704, -92.373123),
    'CA': (36.116203, -119.681564), 'CO': (39.059811, -105.311104),
    'CT': (41.597782, -72.755371), 'DE': (39.318523, -75.507141),
    'FL': (27.766279, -81.686783), 'GA': (33.040619, -83.643074),
    'HI': (21.094318, -157.498337), 'ID': (44.240459, -114.478828),
    'IL': (40.349457, -88.986137), 'IN': (39.849426, -86.258278),
    'IA': (42.011539, -93.210526), 'KS': (38.526600, -96.726486),
    'KY': (37.668140, -84.670067), 'LA': (31.169546, -91.867805),
    'ME': (44.693947, -69.381927), 'MD': (39.063946, -76.802101),
    'MA': (42.230171, -71.530106), 'MI': (43.326618, -84.536095),
    'MN': (45.694454, -93.900192), 'MS': (32.741646, -89.678696),
    'MO': (38.456085, -92.288368), 'MT': (46.921925, -110.454353),
    'NE': (41.125370, -98.268082), 'NV': (38.313515, -117.055374),
    'NH': (43.452492, -71.563896), 'NJ': (40.298904, -74.521011),
    'NM': (34.840515, -106.248482), 'NY': (42.165726, -74.948051),
    'NC': (35.630066, -79.806419), 'ND': (47.528912, -99.784012),
    'OH': (40.388783, -82.764915), 'OK': (35.565342, -96.928917),
    'OR': (44.572021, -122.070938), 'PA': (40.590752, -77.209755),
    'RI': (41.680893, -71.511780), 'SC': (33.856892, -80.945007),
    'SD': (44.299782, -99.438828), 'TN': (35.747845, -86.692345),
    'TX': (31.054487, -97.563461), 'UT': (40.150032, -111.862434),
    'VT': (44.045876, -72.710686), 'VA': (37.769337, -78.169968),
    'WA': (47.400902, -121.490494), 'WV': (38.491226, -80.954453),
    'WI': (44.268543, -89.616508), 'WY': (42.755966, -107.302490),
}


class Command(BaseCommand):
    help = 'Quick import fuel stations from CSV without geocoding'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-file',
            type=str,
            default='fuel-prices-for-be-assessment.csv',
            help='Path to CSV file'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']

        self.stdout.write(self.style.SUCCESS(f'Importing from {csv_file}...'))

        stations = []
        total = 0
        errors = 0

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    total += 1

                    try:
                        state = row['State'].strip()

                        # Use state center coordinates
                        lat, lon = STATE_COORDS.get(state, (None, None))

                        # Add small random offset to spread stations
                        if lat and lon:
                            import random
                            lat += random.uniform(-2, 2)
                            lon += random.uniform(-2, 2)

                        station = FuelStation(
                            opis_id=int(row['OPIS Truckstop ID']),
                            name=row['Truckstop Name'].strip(),
                            address=row['Address'].strip(),
                            city=row['City'].strip(),
                            state=state,
                            latitude=lat,
                            longitude=lon,
                            rack_id=int(row['Rack ID']) if row['Rack ID'] else None,
                            retail_price=Decimal(row['Retail Price']),
                        )

                        stations.append(station)

                        # Bulk create in batches
                        if len(stations) >= 500:
                            with transaction.atomic():
                                FuelStation.objects.bulk_create(
                                    stations,
                                    ignore_conflicts=True
                                )
                            self.stdout.write(f'Imported {total} stations...')
                            stations = []

                    except Exception as e:
                        errors += 1
                        continue

                # Import remaining
                if stations:
                    with transaction.atomic():
                        FuelStation.objects.bulk_create(
                            stations,
                            ignore_conflicts=True
                        )

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found: {csv_file}'))
            return

        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS(f'Total Processed: {total}'))
        self.stdout.write(self.style.SUCCESS(f'Total Imported: {total - errors}'))
        self.stdout.write(self.style.SUCCESS(f'Errors: {errors}'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
