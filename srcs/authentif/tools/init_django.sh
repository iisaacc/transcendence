#!/bin/sh

sleep 1
until nc -z -v -w30 postgres 5432 > /dev/null 2>&1; do
  sleep 1
done

# ex: 
# PROJECT_NAME: gateway
# APP_NAME: gateway_app
# CONTAINER_DIR: /usr/src/app
# APP_DIR: /usr/src/app/gateway_app
# PROJECT_DIR: /usr/src/app/gateway_app/gateway
# SETTINGS_FILE: /usr/src/app/gateway_app/gateway/settings.py

PROJECT_NAME="${SERVICE_NAME}"
APP_NAME="${PROJECT_NAME}_app"
CONTAINER_DIR="/usr/src/app"
APP_DIR="$CONTAINER_DIR/$APP_NAME"
PROJECT_DIR="$APP_DIR/$PROJECT_NAME"
SETTINGS_FILE="$PROJECT_DIR/settings.py"

# echo "mkdir -p $APP_DIR"
mkdir -p $APP_DIR

# echo "PROJECT_NAME: $PROJECT_NAME"
# echo "APP_NAME: $APP_NAME"
# echo "APP_DIR: $APP_DIR"
echo "PROJECT_DIR: $PROJECT_DIR"
# echo "SETTINGS_FILE: $SETTINGS_FILE"
# echo ""

# Check if Django project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
  # Create a new Django project with name '$PROJECT_NAME'
  echo "--Django project directory not found. Creating project..."
  django-admin startproject $PROJECT_NAME $APP_DIR
  sleep 2
else
  echo "--Django project already exists."
fi

mv -f /tmp/manage.py $APP_DIR

echo "--Checking for STATIC_ROOT in $SETTINGS_FILE..."
if ! grep -q "STATIC_ROOT = '/usr/src/frontend/'" "$SETTINGS_FILE"; then
    # Append STATIC_ROOT after STATIC_URL
    echo "--Adding STATIC_ROOT to settings.py..."
    sed -i "/STATIC_URL = 'static\/'/a STATIC_ROOT = '\/usr\/src\/frontend\/'" "$SETTINGS_FILE"
else
    echo "--STATIC_ROOT is already present in $SETTINGS_FILE."
fi

# Create super user with env variables
# echo "--Creating super user..."
# python manage.py createsuperuser --noinput

# Migrate the database
echo "--Making migrations..."
python manage.py makemigrations authentif
python manage.py makemigrations

echo "--Applying migrations..."
python manage.py migrate

# # Collect static files
# echo "--Collecting static files..."
# python manage.py collectstatic --noinput

echo "Django initialised successfully. Executing "$@""
exec "$@"
