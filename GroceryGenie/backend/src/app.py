import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from pymongo import MongoClient
import openai

app = Flask(__name__, static_folder='../../frontend/static', template_folder='../../frontend/templates')
app.secret_key = 'supersecretkey'  # Change the secret key as needed

# Load MONGO_URI from environment variable
MONGO_URI = os.environ.get("MONGO_URI")

# Initialize MongoDB client
client = MongoClient(MONGO_URI)
db = client.get_database("grocery_genie")
users_collection = db.users  # Collection for storing user data

# In-memory storage for grocery items (can be migrated to MongoDB if needed)
inventory = []

# Root route: displays different pages based on the user's login status
@app.route("/")
def index():
    if 'username' in session:
        return render_template("dashborad.html", username=session['username'])
    else:
        return render_template("dashboard.html")

# User login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Retrieve username and password from the form
        username = request.form['username']
        password = request.form['password']
        
        # Find the user in the database
        user = users_collection.find_one({"username": username})
        if user and user.get("password") == password:
            session['username'] = username
            flash('Login Successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid Credentials, Try Again.', 'danger')
    return render_template('login.html')

# User registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Retrieve username and password from the form
        username = request.form['username']
        password = request.form['password']

        # Check if the username already exists in the database
        if users_collection.find_one({"username": username}):
            flash('Username already exists!', 'warning')
        else:
            # For production, use password hashing (e.g., bcrypt)
            user = {"username": username, "password": password}
            users_collection.insert_one(user)
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

# User logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Profile page route
@app.route("/profile", methods=['GET', 'POST'])
def profile():
    if 'username' not in session:
         flash('Please log in first', 'warning')
         return redirect(url_for('login'))
    user = users_collection.find_one({"username": session['username']})
    return render_template("profile.html", user=user)

@app.route("/suggestion")
def suggestion():
    recipes = session.get('recipe_suggestions', [])
    return render_template("suggestion.html", recipes=recipes)

@app.route("/analyze", methods=["POST"])
def analyze():
    # Example image URL; replace with your actual image or processing logic
    image_url = "https://media.istockphoto.com/id/842160124/photo-refrigerator-with-fruits-and-vegetables.jpg"
    analysis_result = analyze_image_with_openai(image_url)
    session['recipe_suggestions'] = analysis_result.get('recipes', [])
    return redirect(url_for('suggestion'))

@app.route("/recipe_details", methods=["POST"])
def recipe_details():
    recipe_name = request.js
