"""
Serializers for API requests and responses.
"""
from rest_framework import serializers
from .models import FuelStation


class FuelStationSerializer(serializers.ModelSerializer):
    """Serializer for FuelStation model"""

    class Meta:
        model = FuelStation
        fields = [
            'id',
            'opis_id',
            'name',
            'address',
            'city',
            'state',
            'latitude',
            'longitude',
            'retail_price',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RouteRequestSerializer(serializers.Serializer):
    """Serializer for route planning request"""

    start_location = serializers.CharField(
        max_length=255,
        help_text="Start location (e.g., 'New York, NY' or 'Los Angeles, CA')"
    )
    end_location = serializers.CharField(
        max_length=255,
        help_text="End location (e.g., 'Miami, FL' or 'Seattle, WA')"
    )

    def validate_start_location(self, value):
        """Validate start location is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Start location cannot be empty")
        return value.strip()

    def validate_end_location(self, value):
        """Validate end location is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("End location cannot be empty")
        return value.strip()

    def validate(self, data):
        """Validate that start and end locations are different"""
        if data['start_location'].lower() == data['end_location'].lower():
            raise serializers.ValidationError(
                "Start and end locations must be different"
            )
        return data


class CoordinateSerializer(serializers.Serializer):
    """Serializer for geographic coordinates"""

    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class RouteGeometrySerializer(serializers.Serializer):
    """Serializer for route geometry"""

    geometry = serializers.CharField(help_text="Encoded polyline geometry")
    distance_miles = serializers.FloatField()
    duration_seconds = serializers.FloatField()  # Changed to FloatField to accept OSRM's float values


class FuelStopSerializer(serializers.Serializer):
    """Serializer for individual fuel stop"""

    station_id = serializers.IntegerField()
    opis_id = serializers.IntegerField()
    name = serializers.CharField()
    address = serializers.CharField()
    city = serializers.CharField()
    state = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    price_per_gallon = serializers.FloatField()
    gallons = serializers.FloatField()
    cost = serializers.FloatField()
    distance_from_start = serializers.FloatField()


class RouteSummarySerializer(serializers.Serializer):
    """Serializer for route summary"""

    total_distance_miles = serializers.FloatField()
    total_fuel_cost = serializers.FloatField()
    total_fuel_gallons = serializers.FloatField()
    number_of_stops = serializers.IntegerField()
    vehicle_mpg = serializers.FloatField()
    vehicle_range_miles = serializers.FloatField()


class RouteResponseSerializer(serializers.Serializer):
    """Serializer for complete route response"""

    start_location = serializers.CharField()
    end_location = serializers.CharField()
    start_coordinates = CoordinateSerializer()
    end_coordinates = CoordinateSerializer()
    route = RouteGeometrySerializer()
    fuel_stops = FuelStopSerializer(many=True)
    summary = RouteSummarySerializer()
