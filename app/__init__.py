from flask import Flask
from flask_cors import CORS

from config import Config

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = Config.SECRET_KEY

from app.api import blueprint_api
from app.admin import blueprint_admin

app.register_blueprint(blueprint_api)
app.register_blueprint(blueprint_admin)

