# Deployment Guide

This guide covers deploying the Fuel Routing API to production.

## Pre-Deployment Checklist

### 1. Environment Configuration

Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Update the following variables:

```env
SECRET_KEY=your-production-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Get free API key from https://openrouteservice.org/dev/#/signup
ROUTING_API_KEY=your-openrouteservice-api-key

# Optional: PostgreSQL for production
DATABASE_URL=postgresql://user:password@localhost:5432/fuel_routing_db
```

### 2. Database Setup

**For Production (PostgreSQL recommended):**

```bash
# Install PostgreSQL adapter
pip install psycopg2-binary

# Update settings.py to use DATABASE_URL
# Run migrations
python manage.py migrate

# Import fuel station data
python manage.py import_fuel_quick
```

### 3. Static Files

```bash
# Collect static files
python manage.py collectstatic --no-input
```

### 4. Security Settings

Update `settings.py` for production:

```python
# settings.py
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# HTTPS Settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HSTS
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

## Deployment Options

### Option 1: Railway.app (Easiest)

1. **Create account at Railway.app**
2. **Create new project from GitHub**
3. **Add PostgreSQL database**
4. **Set environment variables**
5. **Deploy**

Railway automatically detects Django and deploys.

### Option 2: Heroku

```bash
# Install Heroku CLI
heroku create fuel-routing-api

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set ROUTING_API_KEY=your-api-key

# Deploy
git push heroku main

# Run migrations
heroku run python manage.py migrate
heroku run python manage.py import_fuel_quick
```

### Option 3: DigitalOcean/AWS/Azure

**Server Setup:**

```bash
# Install dependencies
sudo apt update
sudo apt install python3.11 python3-pip nginx postgresql

# Clone repository
git clone your-repo-url
cd fuel-routing-api

# Install Python packages
pip install -r requirements.txt
pip install gunicorn

# Setup PostgreSQL
sudo -u postgres createdb fuel_routing_db
sudo -u postgres createuser fuel_user

# Run migrations
python manage.py migrate
python manage.py import_fuel_quick
python manage.py collectstatic
```

**Gunicorn Setup:**

```bash
# Run with Gunicorn
gunicorn fuel_routing_api.wsgi:application --bind 0.0.0.0:8000
```

**Nginx Configuration:**

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location /static/ {
        alias /path/to/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Systemd Service:**

Create `/etc/systemd/system/fuel-routing-api.service`:

```ini
[Unit]
Description=Fuel Routing API
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/fuel-routing-api
ExecStart=/usr/bin/gunicorn fuel_routing_api.wsgi:application --bind 127.0.0.1:8000 --workers 4

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable fuel-routing-api
sudo systemctl start fuel-routing-api
```

## Production Optimizations

### 1. Use PostgreSQL with PostGIS

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'fuel_routing_db',
        'USER': 'fuel_user',
        'PASSWORD': 'your-password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 2. Add Redis for Caching

```bash
# Install Redis
sudo apt install redis-server

# Install Python client
pip install django-redis
```

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### 3. Setup Logging

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/fuel-routing-api/debug.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### 4. Add Monitoring

Install Sentry for error tracking:

```bash
pip install sentry-sdk
```

```python
# settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
)
```

## Performance Tuning

### 1. Database Connection Pooling

```python
# settings.py
DATABASES = {
    'default': {
        # ... other settings
        'CONN_MAX_AGE': 600,  # 10 minutes
    }
}
```

### 2. Gunicorn Workers

```bash
# Calculate workers: (2 x CPU cores) + 1
gunicorn fuel_routing_api.wsgi:application \
    --workers 5 \
    --worker-class=gthread \
    --threads=2 \
    --worker-connections=1000 \
    --max-requests=1000 \
    --max-requests-jitter=100
```

### 3. Enable Compression

```python
# settings.py
MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',
    # ... other middleware
]
```

## Monitoring & Maintenance

### Health Checks

Setup automated health checks:

```bash
# Cron job to check API health
*/5 * * * * curl -f http://localhost:8000/api/v1/health/ || echo "API DOWN"
```

### Database Backups

```bash
# Backup PostgreSQL
pg_dump fuel_routing_db > backup_$(date +%Y%m%d).sql

# Automate with cron
0 2 * * * pg_dump fuel_routing_db > /backups/backup_$(date +\%Y\%m\%d).sql
```

### Log Rotation

```bash
# /etc/logrotate.d/fuel-routing-api
/var/log/fuel-routing-api/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
}
```

## SSL Certificate

### Using Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal is setup automatically
```

## Scaling Considerations

### Horizontal Scaling

- Use load balancer (nginx, HAProxy, AWS ELB)
- Shared Redis cache across instances
- Centralized PostgreSQL database
- Sticky sessions for Django admin

### Vertical Scaling

- Increase server resources (CPU, RAM)
- Optimize database queries
- Add database read replicas
- Use CDN for static files

## Troubleshooting

### API is slow

1. Check database indexes: `python manage.py sqlmigrate routing 0001`
2. Enable query logging: `settings.LOGGING`
3. Check Redis connection: `redis-cli ping`
4. Monitor external API calls: Check cache hit rate

### High memory usage

1. Reduce Gunicorn workers
2. Enable connection pooling
3. Optimize queryset usage
4. Add pagination to API responses

### Database connection errors

1. Check `CONN_MAX_AGE` setting
2. Verify PostgreSQL max_connections
3. Use connection pooling (pgbouncer)

## Cost Optimization

### Free Tier Options

- **Railway**: $5/month for 500 hours
- **Heroku**: Free tier available (limited)
- **OpenRouteService**: Free tier (2000 requests/day)
- **Nominatim**: Free (respect usage policy)

### Production Costs (Estimated)

- **Server**: $5-20/month (DigitalOcean Droplet)
- **Database**: $15/month (Managed PostgreSQL)
- **Redis**: $5/month or free
- **Domain**: $12/year
- **SSL**: Free (Let's Encrypt)
- **Total**: ~$25-50/month

## Post-Deployment Verification

```bash
# 1. Check health endpoint
curl https://yourdomain.com/api/v1/health/

# 2. Test route planning
curl -X POST https://yourdomain.com/api/v1/plan/ \
  -H "Content-Type: application/json" \
  -d '{"start_location": "Los Angeles, CA", "end_location": "San Francisco, CA"}'

# 3. Check API documentation
# Visit https://yourdomain.com/api/docs/

# 4. Verify database
python manage.py dbshell
SELECT COUNT(*) FROM fuel_stations;

# 5. Check logs
tail -f /var/log/fuel-routing-api/debug.log
```

## Rollback Plan

If deployment fails:

```bash
# 1. Rollback database migrations
python manage.py migrate routing 0001

# 2. Restore from backup
pg_restore -d fuel_routing_db backup_YYYYMMDD.sql

# 3. Restart services
sudo systemctl restart fuel-routing-api
sudo systemctl restart nginx

# 4. Check health
curl http://localhost:8000/api/v1/health/
```

---

**Need Help?** Check the logs first, then review this guide. Most issues are configuration-related.
