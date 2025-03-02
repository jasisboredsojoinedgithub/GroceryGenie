from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import os

load_dotenv()# Load .env variables

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Change this for security
app.config["MONGO_URI"] = os.getenv("MONGO_URI")

mongo = PyMongo(app)



@app.route('/')
def home():
    if 'username' in session:
        return render_template('dashborad.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users and users[username] == password:
            session['username'] = username
            flash('Login Successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid Credentials, Try Again.', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users:
            flash('Username already exists!', 'warning')
        else:
            users[username] = password
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)