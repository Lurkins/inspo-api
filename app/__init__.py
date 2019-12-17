from flask import Flask
from flask_cors import CORS
from flask import jsonify
from flask import request
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager, jwt_required, jwt_refresh_token_required, create_access_token, create_refresh_token, get_jwt_identity
from flask_bcrypt import Bcrypt
import datetime
from bson.objectid import ObjectId
from bson.json_util import dumps
import json
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from jsonschema.exceptions import SchemaError

app = Flask(__name__)

from app import views