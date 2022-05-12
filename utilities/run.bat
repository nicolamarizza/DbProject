cd ../app
set FLASK_APP=app.py
set FLASK_ENV=development
set FLASK_KEY_PATH=../utilities/FLASK_SECRET_KEY.txt
set SERVER_HOST=home.dariomarizza.com
set SERVER_PORT=42511

flask run