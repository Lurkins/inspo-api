from app import app

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

user_schema = {
    "type": "object",
    "properties": {
        "username": {
            "type": "string",
        },
        "password": {
            "type": "string",
            "minLength": 5
        }
    },
    "required": ["username", "password"],
    "additionalProperties": False
}

# validate user
def validate_user(data):
    try:
        validate(data, user_schema)
    except ValidationError as e:
        return {'ok': False, 'message': e}
    except SchemaError as e:
        return {'ok': False, 'message': e}
    return {'ok': True, 'data': data}

class JSONEncoder(json.JSONEncoder):
    ''' extend json-encoder class'''
    def default(self, o): # pylint: disable=E0202
      if isinstance(o, ObjectId):
          return str(o)
      if isinstance(o, set):
          return list(o)
      if isinstance(o, datetime.datetime):
          return str(o)
      return json.JSONEncoder.default(self, o)

# Setup the Flask-JWT-Extended extension
app.config['JWT_SECRET_KEY'] = 'super-secret'  # Change this!
jwt = JWTManager(app)
flask_bcrypt = Bcrypt(app)
app.json_encoder = JSONEncoder

app.config['MONGO_DBNAME'] = 'restdb'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/restdb'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=1)
                                   
mongo = PyMongo(app)

CORS(app, resources={r'/*': {'origins': '*'}})


#API Root route
@app.route("/")
def hello():
    return "Welcome to my Python API"

#Testing
@app.route('/test', methods=['GET'])
@jwt_required
def test_route():
    return jsonify('Success!') 

# unauthorized response 
@jwt.unauthorized_loader
def unauthorized_response(callback):
    return jsonify({
        'ok': False,
        'message': 'Missing Authorization Header'
    }), 401

# Register user 
@app.route('/register', methods=['POST'])
def register():
  ''' register user endpoint '''
  data = validate_user(request.get_json())
  if data['ok']:
      data = data['data']
      data['password'] = flask_bcrypt.generate_password_hash(data['password'])
      mongo.db.users.insert_one(data)
      #use .inseted_id ?
      user = mongo.db.users.find_one({'username': data['username']}, {"_id": 0})
      del user['password']
      access_token = create_access_token(identity=data)
      refresh_token = create_refresh_token(identity=data)
      user['token'] = access_token
      user['refresh'] = refresh_token
      return jsonify({'ok': True, 'data': user, 'message': 'User registered successfully!'}), 200
  else:
      return jsonify({'ok': False, 'message': 'Bad request parameters: {}'.format(data['message'])}), 400

# login user
@app.route('/auth', methods=['POST'])
def auth_user():
    ''' auth endpoint '''
    data = validate_user(request.get_json())
    if data['ok']:
        data = data['data']
        user = mongo.db.users.find_one({'username': data['username']}, {"_id": 0})#What is id 0?
        if user and flask_bcrypt.check_password_hash(user['password'], data['password']):
            del user['password']
            access_token = create_access_token(identity=data)
            refresh_token = create_refresh_token(identity=data)
            user['token'] = access_token
            user['refresh'] = refresh_token
            return jsonify({'ok': True, 'data': user}), 200
        else:
            return jsonify({'ok': False, 'message': 'invalid username or password'}), 401
    else:
        return jsonify({'ok': False, 'message': 'Bad request parameters: {}'.format(data['message'])}), 400

# refresh the token
@app.route('/refresh', methods=['POST'])
@jwt_refresh_token_required
def refresh():
    ''' refresh token endpoint '''
    current_user = get_jwt_identity()
    ret = {
        'token': create_access_token(identity=current_user)
    }
    return jsonify({'ok': True, 'data': ret}), 200

#Testing protected route
@app.route('/protected', methods=['GET'])
@jwt_required
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200   

# User info: get, update, delete
@app.route('/users/<username>', methods=['GET', 'DELETE', 'PATCH'])
# @jwt_required
def user(username):
    ''' route read user '''
    if request.method == 'GET':
        data = mongo.db.users.find_one({"username": username})
        return jsonify({'ok': True, 'data': data}), 200

    data = request.json()
    if request.method == 'DELETE':
        if data.get('email', None) is not None:
            db_response = mongo.db.users.delete_one({'email': data['email']})
            if db_response.deleted_count == 1:
                response = {'ok': True, 'message': 'record deleted'}
            else:
                response = {'ok': True, 'message': 'no record found'}
            return jsonify(response), 200
        else:
            return jsonify({'ok': False, 'message': 'Bad request parameters!'}), 400

    if request.method == 'PATCH':
        if data.get('query', {}) != {}:
            mongo.db.users.update_one(
                data['query'], {'$set': data.get('payload', {})})
            return jsonify({'ok': True, 'message': 'record updated'}), 200
        else:
            return jsonify({'ok': False, 'message': 'Bad request parameters!'}), 400

#Get all the users
@app.route('/todo/api/users', methods=['GET'])
def get_all_users():
  user = mongo.db.users
  try:
    if user.find().count > 0:
      #Add del the password here
      return dumps(user.find())
    else:
      return jsonify([])
  except:
    return "Error fetching the items", 500

#Get a user's items
@app.route('/todo/api/item/thisuser', methods=['GET'])
@jwt_required
def get_users_items():
  item = mongo.db.items
  current_user = get_jwt_identity()
  if current_user:
    user = mongo.db.users
    user_name = current_user['username']
    user_obj = user.find_one({'username': user_name})
    user_id = user_obj['_id']
    t = item.find({'user_id' : ObjectId(user_id)})
    resp = dumps(t)
    return resp
  else:
    resp = "Error, missing user id", 500
    return resp

#Get all the items
@app.route('/todo/api/item', methods=['GET'])
def get_all_items():
  item = mongo.db.items
  try:
    if item.find().count > 0:
      return dumps(item.find())
    else:
      return jsonify([])
  except:
    return "Error fetching the items", 500

#Get a single item by ID
@app.route('/todo/api/item/id/<ObjectId:item_id>', methods=['GET'])
def get_one_item_by_id(item_id):
  item = mongo.db.items
  try:
    if item_id:
      t = item.find_one({'_id' : ObjectId(item_id)})
      resp = dumps(t)
      return resp
    else:
      resp = "missing item id"
  except:
    return "Error fetching the item", 500

#Get a single item by title
@app.route('/todo/api/item/<title>', methods=['GET'])
def get_one_item(title):
  item = mongo.db.items
  t = item.find_one({'title' : title})
  if t:
    resp = dumps(t)
  else:
    resp = "this item does not exist"
  return resp

#Post a single item
@app.route('/todo/api/item', methods=['POST'])
@jwt_required
def add_item():
  item = mongo.db.items
  user = mongo.db.users
  title = request.json['title']
  description = request.json['description']
  done = False
  if title and description:
    current_user = get_jwt_identity()
    user_name = current_user['username']
    user_obj = user.find_one({'username': user_name})
    user_id = user_obj['_id']
    item_id = item.insert({'title': title, 'description': description, 'done': done, 'user_id': user_id})
    new_item = item.find_one({'_id': item_id })
    output = {'title' : new_item['title'], 'description' : new_item['description'], 'done': new_item['done']}
    return jsonify({'result' : output})
  else:
    return "Error: no item provided", 500

#Update a item by id - done: true or false
@app.route('/todo/api/item/<ObjectId:item_id>', methods=['PUT'])
@jwt_required
def update_item(item_id):
  item = mongo.db.items
  user = mongo.db.users
  updated_item = item.update({'_id' : item_id}, {"$set": {'done': True}})
  if updated_item:
    current_user = get_jwt_identity()
    user_name = current_user['username']
    user_obj = user.find_one({'username': user_name})
    user_id = user_obj['_id']
    t = item.find({'user_id' : ObjectId(user_id)})
    resp = dumps(t)
  else:
    resp = "Error updating item", 500
  return resp

#Update a item by title - done: true or false
@app.route('/todo/api/item/complete/<title>', methods=['PUT'])
def update_item_by_title(title):
  item = mongo.db.items
  t = item.find_one({'title' : title})
  if t:
    item.update({'title' : title}, {"$set": {'done': True}})
    updated_item = item.find_one({'title': title })
    resp = {'title' : updated_item['title'], 'description' : updated_item['description'], 'done': updated_item['done']}
    #Optionally return the individual item:
    # resp = dumps(t)
  else:
    resp = "this item does not exist"
  return resp

#Update a item by id - done: change title, description
@app.route('/todo/api/item/edit/<ObjectId:item_id>', methods=['PUT'])
def update_item_info(item_id):
  if item_id:
    item = mongo.db.items
    title = request.json['title']
    description = request.json['description']
    item.update({'_id' : item_id}, {"$set": {'title': title, 'description': description}})
    new_item = item.find_one({'_id': item_id })
    output = {'title' : new_item['title'], 'description' : new_item['description'], 'done': new_item['done']}
    return jsonify({'result' : output})
  else:
    return "Error: no item ID provided", 500

#Delete a item by ID
@app.route('/todo/api/item/delete/<ObjectId:item_id>', methods=['DELETE'])
@jwt_required
def delete_item(item_id):
  item = mongo.db.items
  deleted_item = item.delete_one({'_id': ObjectId(item_id)})
  if deleted_item:
    user = mongo.db.users
    current_user = get_jwt_identity()
    user_name = current_user['username']
    user_obj = user.find_one({'username': user_name})
    user_id = user_obj['_id']
    t = item.find({'user_id' : ObjectId(user_id)})
    resp = dumps(t)
  else:
    resp = "Error deleting item", 500
  return resp

#Photo upload
@app.route('/todo/api/photo/<ObjectId:item_id>', methods=['POST'])
def upload(item_id):
  item = mongo.db.items
  if 'file' in request.files:
    file = request.files['file']
    mongo.save_file(file.filename, file)
    item.update({'_id' : item_id}, {"$set": {'image_name': file.filename}})
    uploaded = file.filename
  return jsonify(uploaded)
  
@app.route('/file/<filename>')
def file(filename):
  return mongo.send_file(filename)