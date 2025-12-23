web: gunicorn fuel_routing_api.wsgi --log-file -
release: python manage.py migrate && python manage.py import_fuel_quick
