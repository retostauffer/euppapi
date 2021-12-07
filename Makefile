

APP_NAME=euppapi

# Touching wsgi.py to trigger 'reload/restart' of the app
# without the need of restarting the service
restart:
	touch ${APP_NAME}/wsgi.py

# Create css
css: ${APP_NAME}/static/package.json ${APP_NAME}/static/scss/euppapi_bootstrap.scss
	npm run --prefix ./${APP_NAME}/static css:all

# Installing API dependencies via npm
npm: ${APP_NAME}/static/package.json
	#npm cache clean --force
	npm install --prefix ./${APP_NAME}/static
	make css

# Create virtual environment with whaever we need
venv: requirements.txt
	-rm -rf venv
	virtualenv venv
	venv/bin/pip install --upgrade pip
	venv/bin/python -m pip install -r requirements.txt

# Run development server
run: manage.py
	venv/bin/python manage.py runserver

# Start migrate
migrate:
	#make killdb
	-rm -rf ${APP_NAME}/migrations/*
	# Clearing db first
	venv/bin/python manage.py makemigrations ${APP_NAME} && \
	venv/bin/python manage.py migrate --fake ${APP_NAME} zero && \
	venv/bin/python manage.py migrate

killdb:
	venv/bin/python manage.py migrate euppapi zero

# Access django shell
shell:
	venv/bin/python manage.py shell


