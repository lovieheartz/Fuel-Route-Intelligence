"""
Models for fuel stations and routing data.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class FuelStation(models.Model):
    """
    Represents a fuel station with location and pricing information.
    Optimized for fast geospatial queries using database indexes.
    """

    # Station Identification
    opis_id = models.IntegerField(
        unique=True,
        db_index=True,
        help_text="OPIS Truckstop ID"
    )
    name = models.CharField(max_length=255, db_index=True)

    # Location Information
    address = models.CharField(max_length=500)
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=2, db_index=True)

    # Geographic Coordinates (Critical for routing)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        db_index=True
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        db_index=True
    )

    # Pricing Information
    rack_id = models.IntegerField(null=True, blank=True)
    retail_price = models.DecimalField(
        max_digits=6,
        decimal_places=5,
        validators=[MinValueValidator(0)],
        help_text="Fuel price per gallon in USD"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = 'fuel_stations'
        ordering = ['state', 'city', 'name']
        indexes = [
            models.Index(fields=['latitude', 'longitude'], name='idx_lat_lon'),
            models.Index(fields=['state', 'city'], name='idx_state_city'),
            models.Index(fields=['retail_price'], name='idx_price'),
            models.Index(fields=['is_active', 'state'], name='idx_active_state'),
        ]
        verbose_name = 'Fuel Station'
        verbose_name_plural = 'Fuel Stations'

    def __str__(self):
        return f"{self.name} - {self.city}, {self.state}"

    @property
    def coordinates(self):
        """Return coordinates as tuple (lat, lon)"""
        if self.latitude and self.longitude:
            return (float(self.latitude), float(self.longitude))
        return None

    @property
    def location_dict(self):
        """Return location as dictionary for JSON serialization"""
        return {
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
        }


class RouteCache(models.Model):
    """
    Cache for computed routes to improve API performance.
    Stores routing results to avoid redundant calculations.
    """

    start_location = models.CharField(max_length=255, db_index=True)
    end_location = models.CharField(max_length=255, db_index=True)

    # Cached route data (stored as JSON)
    route_geometry = models.JSONField(help_text="GeoJSON route geometry")
    fuel_stops = models.JSONField(help_text="List of optimal fuel stops")
    total_distance_miles = models.FloatField()
    total_fuel_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_fuel_gallons = models.FloatField()

    # Cache metadata
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    hit_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'route_cache'
        ordering = ['-created_at']
        indexes = [
            models.Index(
                fields=['start_location', 'end_location'],
                name='idx_route_locations'
            ),
        ]
        unique_together = ['start_location', 'end_location']
        verbose_name = 'Route Cache'
        verbose_name_plural = 'Route Caches'

    def __str__(self):
        return f"Route: {self.start_location} -> {self.end_location}"
