#!/bin/bash

cd app
export FLASK_APP='app.py'
export FLASK_ENV='development'
export FLASK_KEY_PATH=''
export SERVER_HOST=''
export SERVER_PORT=

flask run