cd ../app
set FLASK_KEY_PATH="$(pwd)/utilities/flask.key"
set DB_HOST=home.dariomarizza.com
set DB_PORT=42511
set ZOOM_CLIENT_ID=
set ZOOM_CLIENT_SECRET=
set ZOOM_REDIRECT_URI=

python app.py --zoom