"""
Admin configuration for routing models.
"""
from django.contrib import admin
from .models import FuelStation, RouteCache


@admin.register(FuelStation)
class FuelStationAdmin(admin.ModelAdmin):
    """Admin interface for FuelStation model"""

    list_display = [
        'opis_id',
        'name',
        'city',
        'state',
        'retail_price',
        'latitude',
        'longitude',
        'is_active',
    ]
    list_filter = ['state', 'is_active', 'created_at']
    search_fields = ['name', 'city', 'state', 'address']
    ordering = ['state', 'city', 'retail_price']
    list_per_page = 50

    fieldsets = (
        ('Station Information', {
            'fields': ('opis_id', 'name', 'address', 'city', 'state')
        }),
        ('Geographic Location', {
            'fields': ('latitude', 'longitude')
        }),
        ('Pricing', {
            'fields': ('retail_price', 'rack_id')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']


@admin.register(RouteCache)
class RouteCacheAdmin(admin.ModelAdmin):
    """Admin interface for RouteCache model"""

    list_display = [
        'start_location',
        'end_location',
        'total_distance_miles',
        'total_fuel_cost',
        'hit_count',
        'created_at',
    ]
    list_filter = ['created_at']
    search_fields = ['start_location', 'end_location']
    ordering = ['-created_at']
    list_per_page = 50

    readonly_fields = ['created_at', 'hit_count']
