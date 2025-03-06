import uuid
from flask import Flask, jsonify, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, join_room, leave_room, send, emit
from flask_login import LoginManager, current_user, login_required, login_user, UserMixin, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
socketio = SocketIO(app)

# Models
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room = db.Column(db.String(150), nullable=False)
    sender = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    fname = db.Column(db.String(120), nullable=False)
    lname = db.Column(db.String(120), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    prescription_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class PatientParentRelation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    relation_type = db.Column(db.String(50), nullable=False)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        username = request.form.get('uname')
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        user_type = request.form.get('user_type')
        if user_type not in ["doctor", "patient"]:
            flash("Please select a valid user type (Doctor or Patient)", "error")
            return render_template("register.html", email=email, uname=username, fname=fname, lname=lname)
        password = generate_password_hash(password, method='pbkdf2:sha256')
        user = User(username=username, email=email, fname=fname, lname=lname, password=password, user_type=user_type)
        db.session.add(user)
        db.session.commit()
        flash("User is registered successfully", "success")
        return redirect('/login')
    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['username'] = user.username
            flash(f'Logged in successfully as {user.username}', 'success')
            login_user(user)
            if user.user_type == "doctor":
                return redirect('/patients')
            if user.user_type == "patient":
                return redirect('/doctors')
            return redirect('/')
        else:
            flash('Invalid Credentials', 'warning')
            return redirect('/login')
    return render_template("login.html")

@app.route("/logout")
def logout():
    flash(f'{current_user.username} is logged out', 'warning')
    
    logout_user()
    return redirect("/")

@app.route("/patients")
def patients():
    patients = User.query.filter_by(user_type='patient').all()
    return render_template('patients.html', patients=patients)

@app.route("/doctors")
def doctors():
    doctors = User.query.filter_by(user_type='doctor').all()
    return render_template('doctors.html', doctors=doctors)

@app.route("/patient_detail/<int:id>", methods=["GET", "POST"])
def patient_detail(id):
    patient = User.query.get(id)
    # prescriptions = Prescription.query.filter_by(patient_id=id).all()
    # prescriptions = db.session.query(Prescription, User.username)\
    #                           .join(User, Prescription.doctor_id == User.id)\
    #                           .all()
    prescriptions = db.session.query(Prescription, User.username).join(User, Prescription.doctor_id == User.id).filter(Prescription.patient_id == id).all()


    
    # relations = db.session.query(PatientParentRelation, User.username).join(User, PatientParentRelation.parent_id == User.id).filter(PatientParentRelation.patient_id == id).all()

    #patient is relation with some other patient
    child_relations = db.session.query(PatientParentRelation, User.username,User.fname,User.lname).join(User, PatientParentRelation.parent_id == User.id).filter(PatientParentRelation.patient_id == id).all()
    
    #some other patient is related to the patient
    parent_relations = db.session.query(PatientParentRelation, User.username,User.fname,User.lname).join(User, PatientParentRelation.patient_id == User.id).filter(PatientParentRelation.parent_id == id).all()
    
    # print("a babu gandu ho kya")
    for child in child_relations:
        print(child)
    # print("a babu gandu ho kya") 

    if request.method == 'POST':
        prescription_text = request.form.get('prescription_text')
        doctor_id = current_user.id

        prescription = Prescription(doctor_id=doctor_id, patient_id=id, prescription_text=prescription_text)
        db.session.add(prescription)
        db.session.commit()

        flash('Prescription added successfully', 'success')
        return redirect(f"/patient_detail/{id}")
    return render_template("patient_detail.html", patient=patient,prescriptions=prescriptions,child_relations=child_relations,parent_relations=parent_relations)

@app.route("/add_relative/<int:id>",methods=["GET","POST"])
def add_parent(id):
    if request.method=="POST":

        patient_id=id #Patient
        relative=User.query.filter_by(email=request.form.get("parent_email")).first() #Relative or Relative        
        relation=request.form.get("relationship")#Relation
        if not relative:
            flash('Sorry No such Relative has been registered', 'warning')
            return redirect(f"/patient_detail/{id}")
        relative_id=relative.id

        # Check if the relation already exists
        existing_relation = PatientParentRelation.query.filter_by(patient_id=patient_id, parent_id=relative.id).first()
        if existing_relation:
            flash(f'Relative {relative.username} is already linked as {existing_relation.relation_type}.', 'warning')
            return redirect(f"/patient_detail/{id}")
        
        
        patientParentRelation=PatientParentRelation(patient_id=patient_id,parent_id=relative_id,relation_type=relation)
        db.session.add(patientParentRelation)
        db.session.commit()
        print("add ho gya")
        flash('Relative has been linked successfully', 'success')

        return redirect(f"/patient_detail/{id}")
    return redirect(f"/patient_detail/{id}")

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))
    users = User.query.filter(User.username != session['username']).all()
    return render_template('chat.html', users=users, current_user=session['username'])

@app.route('/private_chat/<username>')
def private_chat(username):
    if 'username' not in session:
        return redirect(url_for('login'))
    current_user = session['username']
    chat_room = '_'.join(sorted([current_user, username]))
    messages = Message.query.filter_by(room=chat_room).order_by(Message.timestamp.asc()).all()
    
    return render_template('private_chat.html', room=chat_room, username=username, current_user=current_user, messages=messages)


@socketio.on('private_message')
def handle_private_message(data):
    room = data['room']
    message = data['message']
    sender = session['username']

    new_message = Message(room=room, sender=sender, content=message)
    db.session.add(new_message)
    db.session.commit()

    emit('private_message', {'sender': sender, 'message': message}, room=room)

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    send(f"{session['username']} has entered the room.", room=room)

@socketio.on('call_user')
def call_user(data):
    room = data['room']
    caller = data['caller']
    callee = data['callee']
    emit('incoming_call', {'caller': caller, 'room': room}, room=callee)

@app.route('/video_call/<username>')
@login_required
def video_call(username):
    if 'username' not in session:
        return redirect(url_for('login'))
    current_user = session['username']
    chat_room = '_'.join(sorted([current_user, username]))
    
    socketio.emit('call_user', {'caller': current_user, 'callee': username, 'room': chat_room}, room=username)
    
    return render_template('video_call.html', room=chat_room, username=username, current_user=current_user)

if __name__ == '__main__':
    with app.app_context():
        
        db.create_all()
    socketio.run(app, debug=True)
