from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################

@app.route("/health")
def health():
    return jsonify(dict(status="OK")), 200

@app.route("/count")
def count():
    """return length of data"""
    if songs_list:
        #return jsonify(length=len(songs)), 200
        count = length=len(songs_list)
        return {"count": count}, 200 

    return {"message": "Internal server error"}, 500

@app.route("/song", methods=["GET"])
def songs():
    print("DEBUG : error 71 XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
    try:
        data = db.songs.find()
        print("DEBUG : error 73 XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
        return {"songs": parse_json(data)}, 200
    except:
        return {"message": "Internal server error"}, 500


@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):
    for song in songs_list:
        if song["id"] == id:
            return parse_json(song), 200
    return {"message": "song with id not found"}, 404


@app.route("/song", methods=["POST"])
def create_song():
    try:
        request_body = request.get_json()
    except:
        return {"message": "Bad Request"}, 400
    for song in songs_list:
        if song["id"] == request_body["id"]:
            return {"Message": f"song with id {request_body['id']} already present"}, 302
    songs_list.append(request_body)
    return request_body, 201


@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    try:
        request_body = request.get_json()
    except:
        return {"message": "Bad Request"}, 400
    
    song = db.songs.find({"id": id})
    if song is None:
        return {"message": "song with id not found"}, 404
    
    update_result = db.songs.update_one({"id": id}, {"$set": request_body})
    song_updated = db.songs.find({"id": id})
    if not (update_result.modified_count > 0):
        return {"message": "song found, but nothing updated"}, 200
    
    return jsonify(parse_json(song_updated)), 201

@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):

    delete_result = db.songs.delete_one({"id": id})    
    if delete_result.deleted_count > 0:
        return {"": ""}, 204

    return {"message": "song not found"}, 404