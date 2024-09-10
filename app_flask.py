from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
import os
import bcrypt
import json

# template_dir = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
# template_dir = os.path.join(template_dir, 'templates')

# Database setup
engine = create_engine('sqlite:///users.db')
Base = declarative_base()

# app = Flask(__name__, template_folder=template_dir)
app = Flask(__name__)
app.secret_key = 'made_by_screed'

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session_db = Session()

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(hashed_password, user_password):
    return bcrypt.checkpw(user_password.encode('utf-8'), hashed_password)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)

def login_user(username, password):
    user = session_db.query(User).filter_by(username=username).first()
    if user and check_password(user.password, password):
        return True
    return False

def register_user(username, password):
    if session_db.query(User).filter_by(username=username).first():
        return False
    user = User(username=username, password=hash_password(password))
    session_db.add(user)
    session_db.commit()
    return True

username_global = ''

@app.route('/get_current_user', methods=['GET'])
def get_current_user():
	username = session.get('username')
	if username:
		data = {"username": username}
		# Define the file path
		json_file_path = 'user_login.json'

	    # Save the data to a JSON file
		with open(json_file_path, 'w') as json_file:
			json.dump(data, json_file)

		return jsonify(data)
	else:
		return jsonify({"error": "User not logged in"}), 401

@app.route('/', methods=['GET', 'POST'])
def main_home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if login_user(username, password):
            session['username'] = username
            username_global = username
            return redirect("http://localhost:8501")
        else:
            return "Invalid username or password"

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
	if request.method == 'POST':
		new_username = request.form['username']
		new_password = request.form['password']
		confirm_password = request.form['confirm_password']

		if new_password == confirm_password:
			if register_user(new_username, new_password):
				flash('User Created!', 'failed')
			else:
				flash('Username Already Exists!', 'failed')
		else:
			flash('Passwords Do Not Match!', 'failed')
	
	return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)