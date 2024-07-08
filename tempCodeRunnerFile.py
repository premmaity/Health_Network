# app.py
# from flask import Flask, render_template, redirect, url_for, request, session
# from flask_sqlalchemy import SQLAlchemy
# from flask_socketio import SocketIO, join_room, leave_room, send, emit

# app = Flask(__name__)
# app.config['SECRET_KEY'] = 'your_secret_key'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# db = SQLAlchemy(app)
# socketio = SocketIO(app)

# class User(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(150), nullable=False, unique=True)
#     password = db.Column(db.String(150), nullable=False)

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
#         user = User(username=username, password=password)
#         db.session.add(user)
#         db.session.commit()
#         return redirect(url_for('login'))
#     return render_template('register.html')

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
#         user = User.query.filter_by(username=username, password=password).first()
#         if user:
#             session['username'] = username
#             return redirect(url_for('chat'))
#     return render_template('login.html')

# @app.route('/chat')
# def chat():
#     if 'username' not in session:
#         return redirect(url_for('login'))
#     users = User.query.filter(User.username != session['username']).all()
#     return render_template('chat.html', users=users, current_user=session['username'])

# @socketio.on('private_message')
# def handle_private_message(data):
#     recipient = data['recipient']
#     message = data['message']
#     sender = session['username']
#     room = data['room']
#     emit('private_message', {'sender': sender, 'message': message}, room=room)

# @socketio.on('join_room')
# def on_join(data):
#     room = data['room']
#     join_room(room)

# @socketio.on('leave_room')
# def on_leave(data):
#     room = data['room']
#     leave_room(room)

# if __name__ == '__main__':
#     with app.app_context():
#         db.drop_all()
#         db.create_all()
#     socketio.run(app, debug=True)