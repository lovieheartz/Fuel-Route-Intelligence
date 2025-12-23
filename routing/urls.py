"""
URL configuration for routing app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FuelStationViewSet, PlanRouteView, HealthCheckView

app_name = 'routing'

# Router for viewsets
router = DefaultRouter()
router.register(r'stations', FuelStationViewSet, basename='station')

urlpatterns = [
    # API endpoints
    path('plan/', PlanRouteView.as_view(), name='plan-route'),
    path('health/', HealthCheckView.as_view(), name='health-check'),

    # ViewSet routes
    path('', include(router.urls)),
]
