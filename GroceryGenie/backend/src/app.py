import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from pymongo import MongoClient
import openai
from dotenv import load_dotenv
from config import MONGO_URI, SECRET_KEY

# Load environment variables first
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='../../frontend/static', template_folder='../../frontend/templates')

# Set secret_key
app.secret_key = SECRET_KEY

# Initialize MongoDB client
client = MongoClient(MONGO_URI)
db = client.get_database("GroceryGenieDB")
users_collection = db.users  # Collection for storing user data

# In-memory storage for grocery items (can be migrated to MongoDB if needed)
inventory = []

# Root route: displays different pages based on the user's login status
@app.route("/")
def dashboard():
    if 'username' in session:
        return render_template("dashborad.html", username=session['username'])
    else:
        return render_template("dashboard.html")

# User login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Retrieve email and password from the form
        email = request.form['email']
        password = request.form['password']
        
        # Find the user in the database
        user = users_collection.find_one({"email": email})
        if user and user.get("password") == password:
            session['email'] = email
            flash('Login Successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid Credentials, Try Again.', 'danger')
    return render_template('login.html')

# User registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Retrieve email and password from the form
        email = request.form['email']
        password = request.form['password']

        # Check if the email already exists in the database
        if users_collection.find_one({"email": email}):
            flash('Email already registered!', 'warning')
        else:
            # For production, use password hashing (e.g., bcrypt)
            user = {"email": email, "password": password}
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
    # analysis_result = analyze_image_with_openai(image_url)
    # session['recipe_suggestions'] = analysis_result.get('recipes', [])
    # return redirect(url_for('suggestion'))

@app.route("/recipe_details", methods=["POST"])
def recipe_details():
    recipe_name = request.js
