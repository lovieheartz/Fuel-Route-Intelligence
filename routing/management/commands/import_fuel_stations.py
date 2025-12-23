"""
Management command to import fuel stations from CSV file with geocoding.
Optimized for bulk import with progress tracking and error handling.
"""
import csv
import time
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from routing.models import FuelStation


class Command(BaseCommand):
    help = 'Import fuel stations from CSV file with geocoding'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to the CSV file containing fuel station data'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of records to process in each batch (default: 100)'
        )
        parser.add_argument(
            '--skip-geocoding',
            action='store_true',
            help='Skip geocoding (faster but no coordinates)'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        batch_size = options['batch_size']
        skip_geocoding = options['skip_geocoding']

        self.stdout.write(self.style.SUCCESS(f'Starting import from {csv_file}'))

        # Initialize geocoder
        if not skip_geocoding:
            self.geolocator = Nominatim(user_agent="fuel_routing_api", timeout=10)
            self.geocode_cache = {}

        stations_to_create = []
        total_processed = 0
        total_created = 0
        total_geocoded = 0
        total_errors = 0

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    total_processed += 1

                    try:
                        # Parse data
                        opis_id = int(row['OPIS Truckstop ID'])
                        name = row['Truckstop Name'].strip()
                        address = row['Address'].strip()
                        city = row['City'].strip()
                        state = row['State'].strip()
                        rack_id = int(row['Rack ID']) if row['Rack ID'] else None
                        retail_price = Decimal(row['Retail Price'])

                        # Geocode location if enabled
                        latitude = None
                        longitude = None

                        if not skip_geocoding:
                            lat, lon = self.geocode_location(city, state, address)
                            if lat and lon:
                                latitude = lat
                                longitude = lon
                                total_geocoded += 1

                        # Create station object
                        station = FuelStation(
                            opis_id=opis_id,
                            name=name,
                            address=address,
                            city=city,
                            state=state,
                            latitude=latitude,
                            longitude=longitude,
                            rack_id=rack_id,
                            retail_price=retail_price,
                        )

                        stations_to_create.append(station)

                        # Bulk create in batches
                        if len(stations_to_create) >= batch_size:
                            created = self.bulk_create_stations(stations_to_create)
                            total_created += created
                            stations_to_create = []

                            self.stdout.write(
                                f'Processed: {total_processed} | '
                                f'Created: {total_created} | '
                                f'Geocoded: {total_geocoded} | '
                                f'Errors: {total_errors}'
                            )

                    except Exception as e:
                        total_errors += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'Error processing row {total_processed}: {str(e)}'
                            )
                        )
                        continue

                # Create remaining stations
                if stations_to_create:
                    created = self.bulk_create_stations(stations_to_create)
                    total_created += created

        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'File not found: {csv_file}')
            )
            return

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Import failed: {str(e)}')
            )
            return

        # Final summary
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('Import Summary:'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'Total Processed: {total_processed}')
        self.stdout.write(f'Total Created: {total_created}')
        self.stdout.write(f'Total Geocoded: {total_geocoded}')
        self.stdout.write(f'Total Errors: {total_errors}')
        self.stdout.write(self.style.SUCCESS('=' * 60))

    def geocode_location(self, city, state, address):
        """
        Geocode a location using Nominatim.
        Uses caching to avoid duplicate API calls.
        """
        # Create cache key
        cache_key = f"{city}, {state}"

        # Check cache first
        if cache_key in self.geocode_cache:
            return self.geocode_cache[cache_key]

        # Try geocoding with city and state
        try:
            location = self.geolocator.geocode(f"{city}, {state}, USA")

            if location:
                coords = (location.latitude, location.longitude)
                self.geocode_cache[cache_key] = coords
                time.sleep(1)  # Respect rate limits
                return coords

        except (GeocoderTimedOut, GeocoderServiceError) as e:
            self.stdout.write(
                self.style.WARNING(f'Geocoding failed for {cache_key}: {str(e)}')
            )

        # Cache negative result
        self.geocode_cache[cache_key] = (None, None)
        return None, None

    def bulk_create_stations(self, stations):
        """
        Bulk create stations with error handling.
        """
        try:
            with transaction.atomic():
                FuelStation.objects.bulk_create(
                    stations,
                    ignore_conflicts=True,
                    batch_size=100
                )
                return len(stations)
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Bulk create error: {str(e)}')
            )
            return 0
