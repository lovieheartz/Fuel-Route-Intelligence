# Spotter AI - Production-Grade Fuel Routing API

## Overview

A robust, industry-standard API for optimal fuel stop routing across the USA. Built with Django REST Framework and designed for production deployments with comprehensive error handling, validation, caching, and monitoring.

### Key Features

- **Intelligent Route Planning**: Calculates optimal driving routes using OSRM
- **Fuel Cost Optimization**: Finds cheapest fuel stops along your route
- **Production-Ready**: Comprehensive error handling, retry logic, and validation
- **High Performance**: Multi-layer caching, optimized database queries
- **Rate Limited**: Built-in protection against API abuse
- **Fully Documented**: OpenAPI/Swagger documentation
- **Comprehensive Testing**: Unit, integration, and API tests
- **Monitoring**: Request logging, performance metrics, health checks

## Architecture

### Technology Stack

- **Framework**: Django 5.2.9 + Django REST Framework
- **Database**: SQLite (dev) / PostgreSQL (production recommended)
- **Caching**: In-memory cache (dev) / Redis (production recommended)
- **Routing Engine**: OSRM (Open Source Routing Machine)
- **Geocoding**: Nominatim (OpenStreetMap)
- **API Documentation**: drf-spectacular (OpenAPI 3.0)

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                    API Gateway                          │
│          (Rate Limiting, Request Logging)               │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│              Enhanced Views Layer                       │
│  (Comprehensive Error Handling, Validation)             │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│           Enhanced Services Layer                       │
│   ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│   │  Geocoding   │  │   Routing    │  │    Fuel     │ │
│   │   Service    │  │   Service    │  │ Optimization│ │
│   └──────────────┘  └──────────────┘  └─────────────┘ │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│              External Services                          │
│   ┌──────────────┐  ┌──────────────┐                   │
│   │  Nominatim   │  │     OSRM     │                   │
│   │  (Geocoding) │  │   (Routing)  │                   │
│   └──────────────┘  └──────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### Installation

```bash
# Clone repository
git clone <repo-url>
cd "Spotter AI"

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Import fuel station data
python manage.py import_fuel_stations

# Start development server
python manage.py runserver
```

### Basic Usage

```python
import requests

# Plan a route
response = requests.post('http://localhost:8000/api/plan-route/', json={
    'start_location': 'Los Angeles, CA',
    'end_location': 'San Francisco, CA'
})

route_data = response.json()
print(f"Distance: {route_data['summary']['total_distance_miles']} miles")
print(f"Fuel Cost: ${route_data['summary']['total_fuel_cost']}")
print(f"Stops: {route_data['summary']['number_of_stops']}")
```

## API Endpoints

### Base URL

**Development**: `http://localhost:8000/api/`
**Production**: `https://your-domain.com/api/`

### Authentication

Currently, the API is open. For production, implement token-based authentication using DRF's built-in auth or JWT.

---

### 1. Plan Route

Calculate optimal route with fuel stops.

**Endpoint**: `POST /api/plan-route/`

**Request Body**:
```json
{
  "start_location": "Los Angeles, CA",
  "end_location": "San Francisco, CA"
}
```

**Response** (200 OK):
```json
{
  "start_location": "Los Angeles, CA",
  "end_location": "San Francisco, CA",
  "start_coordinates": {
    "latitude": 34.0522,
    "longitude": -118.2437
  },
  "end_coordinates": {
    "latitude": 37.7749,
    "longitude": -122.4194
  },
  "route": {
    "geometry": "encoded_polyline_string",
    "distance_miles": 380.58,
    "duration_seconds": 25525.7
  },
  "fuel_stops": [
    {
      "station_id": 1420,
      "opis_id": 10085,
      "name": "BAKERSFIELD TRAVEL CENTER",
      "address": "I-5, EXIT 257",
      "city": "Bakersfield",
      "state": "CA",
      "latitude": 35.3733,
      "longitude": -119.0187,
      "price_per_gallon": 4.499,
      "gallons": 16.92,
      "cost": 76.14,
      "distance_from_start": 169.24
    }
  ],
  "summary": {
    "total_distance_miles": 380.58,
    "total_fuel_cost": 76.14,
    "total_fuel_gallons": 16.92,
    "number_of_stops": 1,
    "vehicle_mpg": 10.0,
    "vehicle_range_miles": 500.0,
    "stations_searched": 45
  }
}
```

**Error Responses**:

- **400 Bad Request**: Invalid location or validation error
- **404 Not Found**: Location not found or no route available
- **429 Too Many Requests**: Rate limit exceeded
- **503 Service Unavailable**: External routing service unavailable

**Example Errors**:

```json
{
  "error": "LocationNotFoundError",
  "message": "Could not find location: InvalidCity, XX",
  "details": {
    "location": "InvalidCity, XX"
  }
}
```

---

### 2. List Fuel Stations

Get paginated list of fuel stations.

**Endpoint**: `GET /api/stations/`

**Query Parameters**:
- `state` (optional): Filter by state code (e.g., "CA", "NY")
- `city` (optional): Filter by city name
- `search` (optional): Search by name, city, or address
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Results per page (default: 100)

**Response** (200 OK):
```json
{
  "count": 5000,
  "next": "http://localhost:8000/api/stations/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "opis_id": 10001,
      "name": "PILOT TRAVEL CENTER",
      "address": "I-5, EXIT 221",
      "city": "Los Angeles",
      "state": "CA",
      "latitude": 34.0522,
      "longitude": -118.2437,
      "retail_price": 3.499,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

### 3. Get Fuel Station Details

Get detailed information about a specific fuel station.

**Endpoint**: `GET /api/stations/{id}/`

**Response** (200 OK):
```json
{
  "id": 1,
  "opis_id": 10001,
  "name": "PILOT TRAVEL CENTER",
  "address": "I-5, EXIT 221",
  "city": "Los Angeles",
  "state": "CA",
  "latitude": 34.0522,
  "longitude": -118.2437,
  "retail_price": 3.499,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

---

### 4. Get Cheapest Stations

Get the cheapest fuel stations, optionally filtered by state.

**Endpoint**: `GET /api/stations/cheapest/`

**Query Parameters**:
- `state` (optional): Filter by state code
- `limit` (optional): Maximum results (default: 10, max: 100)

**Response** (200 OK):
```json
{
  "count": 10,
  "state_filter": "CA",
  "stations": [
    {
      "id": 42,
      "name": "COSTCO FUEL STATION",
      "city": "San Diego",
      "state": "CA",
      "retail_price": 3.199
    }
  ]
}
```

---

### 5. Health Check

Check API health and service availability.

**Endpoint**: `GET /api/health/`

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": 1704123456.789,
  "services": {
    "database": {
      "status": "connected",
      "total_stations": 5000,
      "active_stations": 4950
    },
    "cache": {
      "status": "available"
    }
  },
  "version": "2.0.0",
  "api": "Spotter AI Fuel Routing"
}
```

---

### 6. API Metrics

Get usage statistics and performance metrics.

**Endpoint**: `GET /api/metrics/`

**Response** (200 OK):
```json
{
  "requests": {
    "total": 10000,
    "successful": 9500,
    "failed": 500
  },
  "routes": {
    "planned": 2500,
    "cached": 1800
  },
  "cache": {
    "hit_rate": 72.0
  },
  "fuel_stations": {
    "total": 5000,
    "active": 4950
  }
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Per Minute**: 60 requests
- **Per Hour**: 1000 requests

Rate limit headers are included in all responses:

```
X-RateLimit-Limit-Minute: 60
X-RateLimit-Remaining-Minute: 45
X-RateLimit-Limit-Hour: 1000
X-RateLimit-Remaining-Hour: 856
```

When rate limited, you'll receive a **429 Too Many Requests** response:

```json
{
  "error": "RateLimitExceeded",
  "message": "Too many requests. Please try again later.",
  "retry_after": 60
}
```

## Error Handling

The API uses comprehensive error handling with descriptive messages:

### Error Response Format

```json
{
  "error": "ErrorType",
  "message": "Human-readable error description",
  "details": {
    "field": "additional context"
  }
}
```

### Common Errors

| Error Type | HTTP Status | Description |
|-----------|-------------|-------------|
| `ValidationError` | 400 | Invalid input data |
| `LocationNotFoundError` | 404 | Geocoding failed |
| `NoRouteFoundError` | 404 | No route between locations |
| `NoFuelStationsFoundError` | 404 | No stations along route |
| `InsufficientRangeError` | 400 | Vehicle can't complete route |
| `RouteServiceUnavailableError` | 503 | External service down |
| `RateLimitExceeded` | 429 | Too many requests |

## Data Validation

### Location Validation

Locations must be in format: `"City, ST"` where ST is a 2-letter state code.

**Valid**:
- `"Los Angeles, CA"`
- `"New York, NY"`
- `"Seattle, WA"`

**Invalid**:
- `"Los Angeles"` (missing state)
- `"LA, California"` (full state name)
- `"InvalidCity, XX"` (invalid state code)

### Coordinate Validation

- Latitude: -90 to 90
- Longitude: -180 to 180

### Vehicle Parameters

- MPG: 1-100
- Range: 1-2000 miles
- Tank Capacity: 1-500 gallons

## Performance & Optimization

### Caching Strategy

The API implements multi-layer caching:

1. **Geocoding Cache**: 24 hours
2. **Route Cache**: 1 hour
3. **Full Route Plan Cache**: 1 hour

### Database Optimization

- Indexed fields: `state`, `city`, `latitude`, `longitude`, `retail_price`
- Composite indexes for common queries
- Select related queries to minimize database hits

### Response Times

Typical response times (cached):

- Fuel stations list: < 100ms
- Route planning (cached): < 50ms
- Route planning (uncached): 2-5 seconds

## Deployment

### Production Checklist

- [ ] Set `DEBUG = False` in settings
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Use PostgreSQL database
- [ ] Set up Redis for caching
- [ ] Configure environment variables for secrets
- [ ] Enable HTTPS
- [ ] Set up proper CORS headers
- [ ] Configure logging to external service (e.g., Sentry)
- [ ] Set up monitoring (e.g., Prometheus, Datadog)
- [ ] Configure backup strategy
- [ ] Set up CI/CD pipeline
- [ ] Load test the API
- [ ] Configure rate limiting based on your needs

### Environment Variables

```bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database
DATABASE_URL=postgresql://user:pass@localhost/dbname

# Cache
REDIS_URL=redis://localhost:6379/0

# Vehicle Configuration
VEHICLE_RANGE_MILES=500
VEHICLE_MPG=10
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput
RUN python manage.py migrate

EXPOSE 8000
CMD ["gunicorn", "fuel_routing_api.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

## Testing

### Run Tests

```bash
# Run all tests
python manage.py test routing.tests_comprehensive

# Run with coverage
coverage run manage.py test routing.tests_comprehensive
coverage report
coverage html  # Generate HTML report
```

### Test Categories

- **Validation Tests**: Input validation for all data types
- **Service Tests**: Geocoding, routing, fuel optimization
- **API Tests**: Endpoint testing with various scenarios
- **Integration Tests**: Complete workflow testing

## Monitoring & Logging

### Log Files

- **Application Logs**: `logs/spotter_ai.log`
- **Error Logs**: `logs/errors.log`

### Log Levels

- **DEBUG**: Detailed debugging information
- **INFO**: General informational messages
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failures

### Metrics Collection

The API tracks:

- Request counts (total, successful, failed)
- Route planning statistics
- Cache hit rates
- Database query performance
- External service latency

## API Versioning

Current version: **2.0.0**

The API follows semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

## Support & Contributing

### Reporting Issues

Please report issues with:
- API endpoint and request details
- Error response
- Expected behavior
- Steps to reproduce

### Feature Requests

We welcome feature requests! Please include:
- Use case description
- Expected behavior
- Priority level

## License

[Your License Here]

## Credits

- **Routing**: OSRM (Open Source Routing Machine)
- **Geocoding**: Nominatim (OpenStreetMap)
- **Framework**: Django + Django REST Framework
- **Fuel Data**: OPIS Truckstop Data

---

## Example Client Code

### Python

```python
import requests

class SpotterAIClient:
    def __init__(self, base_url='http://localhost:8000/api'):
        self.base_url = base_url

    def plan_route(self, start, end):
        """Plan optimal route with fuel stops."""
        response = requests.post(
            f'{self.base_url}/plan-route/',
            json={'start_location': start, 'end_location': end}
        )
        response.raise_for_status()
        return response.json()

    def get_cheapest_stations(self, state=None, limit=10):
        """Get cheapest fuel stations."""
        params = {'limit': limit}
        if state:
            params['state'] = state

        response = requests.get(
            f'{self.base_url}/stations/cheapest/',
            params=params
        )
        response.raise_for_status()
        return response.json()

# Usage
client = SpotterAIClient()
route = client.plan_route('Los Angeles, CA', 'San Francisco, CA')
print(f"Total cost: ${route['summary']['total_fuel_cost']}")
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

class SpotterAIClient {
  constructor(baseURL = 'http://localhost:8000/api') {
    this.client = axios.create({ baseURL });
  }

  async planRoute(start, end) {
    const response = await this.client.post('/plan-route/', {
      start_location: start,
      end_location: end
    });
    return response.data;
  }

  async getCheapestStations(state = null, limit = 10) {
    const params = { limit };
    if (state) params.state = state;

    const response = await this.client.get('/stations/cheapest/', { params });
    return response.data;
  }
}

// Usage
const client = new SpotterAIClient();
const route = await client.planRoute('Los Angeles, CA', 'San Francisco, CA');
console.log(`Total cost: $${route.summary.total_fuel_cost}`);
```

---

**Built with excellence by Spotter AI Team**
