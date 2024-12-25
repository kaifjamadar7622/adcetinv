from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from bson.objectid import ObjectId

app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///digital_platform.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'  # Folder to save uploaded files
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit upload size to 16 MB
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}  # Allowed file types

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

class Requirement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    file_path = db.Column(db.String(500), nullable=True)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requirement_id = db.Column(db.Integer, db.ForeignKey('requirement.id'), nullable=False)
    # Add other fields as necessary


with app.app_context():
    db.create_all()


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"message": "Missing fields in request"}), 400

    
    existing_user = User.query.filter_by(username=data['username']).first()
    if existing_user:
        return jsonify({"message": "User  already exists"}), 409

    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')

    new_user = User(username=data['username'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User  created successfully!"}), 201

@app.route('/user/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    
    data = request.json
    if 'username' in data:
        user.username = data['username']
    if 'password' in data:
        user.password = bcrypt.generate_password_hash(data['password']).decode('utf-8')

    db.session.commit()
    return jsonify({"message": "Profile updated successfully!"}), 200

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"message": "Missing fields in request"}), 400

    user = User.query.filter_by(username=data['username']).first()
    if user and bcrypt.check_password_hash(user.password, data['password']):

        access_token = create_access_token(identity=user.username)
        return jsonify(access_token=access_token), 200

    return jsonify({"message": "Invalid username or password"}), 401


@app.route('/landowner/requirement', methods=['POST'])
def create_requirement():
    data = request.form
    if not data or 'title' not in data or 'description' not in data or 'username' not in data:
        return jsonify({"message": "Missing fields in request"}), 400

    user = User.query.filter_by(username=data['username']).first()
    if not user:
        return jsonify({"message": "User  not found"}), 404
    
    file_path = None
    if 'file' in request.files:
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

    new_requirement = Requirement(title=data['title'], description=data['description'], user_id=user.id,file_path=file_path)
    db.session.add(new_requirement)
    db.session.commit()

    return jsonify({"id": new_requirement.id}), 201

@app.route('/landowner/requirements', methods=['GET'])
def get_requirements():
    requirements = Requirement.query.all()
    return jsonify([{"id": req.id, "title": req.title, "description": req.description, "user_id": req.user_id,"file_path":req.file_path} for req in requirements]), 200


@app.route('/landowner/requirement/<int:requirement_id>', methods=['PUT'])
def update_requirement(requirement_id):
    data = request.json
    requirement = Requirement.query.get(requirement_id)
    if not requirement:
        return jsonify({"message": "Requirement not found"}), 404

    if 'title' in data:
        requirement.title = data['title']
    if 'description' in data:
        requirement.description = data['description']

    db.session.commit()
    return jsonify({"message": "Requirement updated"}), 200


@app.route('/landowner/requirement/<int:requirement_id>', methods=['DELETE'])
def delete_requirement(requirement_id):
    requirement = Requirement.query.get(requirement_id)
    if not requirement:
        return jsonify({"message": "Requirement not found"}), 404

    db.session.delete(requirement)
    db.session.commit()
    return jsonify({"message": "Requirement deleted"}), 200

@app.route('/contractor/application', methods=['POST'])
def create_application():
    data = request.json
    if not data or 'requirement_id' not in data:
        return jsonify({"message": "Missing fields in request"}), 400

    new_application = Application(requirement_id=data['requirement_id'])
    db.session.add(new_application)
    db.session.commit()

    return jsonify({"id": new_application.id}), 201

@app.route('/contractor/applications/<int:requirement_id>', methods=['GET'])
def get_applications(requirement_id):
    applications = Application.query.filter_by(requirement_id=requirement_id).all()
    return jsonify([{"id": app.id, "requirement_id": app.requirement_id} for app in applications]), 200

@app.route('/contractor/application/<int:application_id>', methods=['PUT'])
def update_application(application_id):
    data = request.json
    application = Application.query.get(application_id)
    if not application:
        return jsonify({"message": "Application not found"}), 404

    if 'requirement_id' in data:
        application.requirement_id = data['requirement_id']


    db.session.commit()
    return jsonify({"message": "Application updated"}), 200


@app.route('/contractor/application/<int:application_id>', methods=['DELETE'])
def delete_application(application_id):
    application = Application.query.get(application_id)
    if not application:
        return jsonify({"message": "Application not found"}), 404

    db.session.delete(application)
    db.session.commit()
    return jsonify({"message": "Application deleted"}), 200


if __name__ == '__main__':
    app.run(debug=True)