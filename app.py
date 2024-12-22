from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from bson.objectid import ObjectId

app = Flask(__name__)


app.config["MONGO_URI"] = "mongodb://localhost:27017/digital_platform"
mongo = PyMongo(app)

@app.route('/landowner/requirement', methods=['POST'])
def create_requirement():
    data = request.json
    requirement_id = mongo.db.requirements.insert_one(data).inserted_id
    return jsonify(str(requirement_id)), 201

@app.route('/landowner/requirements', methods=['GET'])
def get_requirements():
    requirements = mongo.db.requirements.find()
    return jsonify([{"id": str(req["_id"]), **req} for req in requirements]), 200

@app.route('/landowner/requirement/<requirement_id>', methods=['PUT'])
def update_requirement(requirement_id):
    data = request.json
    mongo.db.requirements.update_one({"_id": ObjectId(requirement_id)}, {"$set": data})
    return jsonify({"message": "Requirement updated"}), 200

@app.route('/landowner/requirement/<requirement_id>', methods=['DELETE'])
def delete_requirement(requirement_id):
    mongo.db.requirements.delete_one({"_id": ObjectId(requirement_id)})
    return jsonify({"message": "Requirement deleted"}), 200

@app.route('/contractor/application', methods=['POST'])
def create_application():
    data = request.json
    application_id = mongo.db.applications.insert_one(data).inserted_id
    return jsonify(str(application_id)), 201

@app.route('/contractor/applications/<requirement_id>', methods=['GET'])
def get_applications(requirement_id):
    applications = mongo.db.applications.find({"requirement_id": ObjectId(requirement_id)})
    return jsonify([{"id": str(app["_id"]), **app} for app in applications]), 200

@app.route('/contractor/application/<application_id>', methods=['PUT'])
def update_application(application_id):
    data = request.json
    mongo.db.applications.update_one({"_id": ObjectId(application_id)}, {"$set": data})
    return jsonify({"message": "Application updated"}), 200

@app.route('/contractor/application/<application_id>', methods=['DELETE'])
def delete_application(application_id):
    mongo.db.applications.delete_one({"_id": ObjectId(application_id)})
    return jsonify({"message": "Application deleted"}), 200

@app.route('/contractor/applications/sort/<requirement_id>', methods=['GET'])
def sort_applications(requirement_id):
    sort_by = request.args.get('sort_by', 'cost_estimation')  
    applications = mongo.db.applications.find({"requirement_id": ObjectId(requirement_id)}).sort(sort_by)
    return jsonify([{"id": str(app["_id"]), **app} for app in applications]), 200

if __name__ == '__main__':
    app.run(debug=True)