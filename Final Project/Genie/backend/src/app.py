from dotenv import load_dotenv
from pathlib import Path
import os

import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from pymongo import MongoClient
import openai
from bcrypt import hashpw, gensalt, checkpw
from werkzeug.utils import secure_filename
from azure.storage.blob import BlobServiceClient
import uuid

from dotenv import load_dotenv
from pathlib import Path
import os


# Load environment variables from .env file
env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)

# Fetch environment variables
MONGO_URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv("SECRET_KEY", "GroceryGenieSuperSecretKey123")
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_STORAGE_CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "groceryimages")

# Initialize Flask app
app = Flask(__name__, static_folder='../../frontend/static', template_folder='../../frontend/templates')
app.secret_key = SECRET_KEY

# Validate and connect to MongoDB
if not MONGO_URI:
    raise ValueError("MONGO_URI is not set. Please check your .env file.")

try:
    client = MongoClient(MONGO_URI)
    client.admin.command('ping')
    print("✅ MongoDB connection successful.")
except Exception as e:
    print("❌ MongoDB connection failed:", e)

# Initialize Azure Blob Storage
blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
container_name = AZURE_STORAGE_CONTAINER_NAME

# Connect to database and collections
db = client.get_database("GroceryGenieDB")
users_collection = db.users
profiles_collection = db.profiles

inventory = []  # Temporary inventory list

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/dashboard")
def dashboard():
    if 'email' in session:
        return render_template("dashboard.html", email=session['email'])
    else:
        flash('Please log in to view the dashboard.', 'warning')
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Email and password are required.', 'danger')
            return redirect(url_for('login'))

        user = users_collection.find_one({"email": email})

        if user and checkpw(password.encode('utf-8'), user['password']):
            session['email'] = email
            flash('Login Successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials, please try again.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Email and password are required.', 'danger')
            return redirect(url_for('register'))

        if users_collection.find_one({"email": email}):
            flash('Email already registered!', 'warning')
        else:
            hashed_password = hashpw(password.encode('utf-8'), gensalt())
            user = {"email": email, "password": hashed_password}
            users_collection.insert_one(user)
            session['email'] = email
            flash('Registration successful! Welcome 🎉', 'success')
            return redirect(url_for('dashboard'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('email', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/profile", methods=['GET', 'POST'])
def profile():
    if 'email' not in session:
        flash('Please log in first', 'warning')
        return redirect(url_for('login'))

    email = session['email']
    profile = profiles_collection.find_one({"email": email}) or {}

    if request.method == 'POST':
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        country = request.form.get("country")

        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and allowed_file(file.filename):
                filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
                blob_client = blob_service_client.get_blob_client(container=container_name, blob=filename)
                blob_client.upload_blob(file, overwrite=True)
                profile_pic_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{filename}"
            else:
                profile_pic_url = profile.get('profile_pic', f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/default-profile.jpg")
        else:
            profile_pic_url = profile.get('profile_pic', f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/default-profile.jpg")

        profiles_collection.update_one(
            {"email": email},
            {"$set": {
                "first_name": first_name,
                "last_name": last_name,
                "country": country,
                "profile_pic": profile_pic_url
            }},
            upsert=True
        )

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template("profile.html", profile=profile)

@app.route("/suggestion")
def suggestion():
    recipes = session.get('recipe_suggestions', [])
    return render_template("suggestion.html", recipes=recipes)

@app.route("/analyze", methods=["POST"])
def analyze():
    image_url = "https://media.istockphoto.com/id/842160124/photo-refrigerator-with-fruits-and-vegetables.jpg"
    analysis_result = analyze_image_with_openai(image_url)
    session['recipe_suggestions'] = analysis_result.get('recipes', [])
    return redirect(url_for('suggestion'))

@app.route("/inventory")
def inventory_page():
    return render_template("inventory.html")

@app.route("/recipe_details", methods=["POST"])
def recipe_details():
    recipe_name = request.json.get("recipe_name")
    recipes = session.get('recipe_suggestions', [])
    recipe = next((r for r in recipes if r['name'] == recipe_name), None)
    if recipe:
        return jsonify(recipe)
    else:
        return jsonify({"error": "Recipe not found"}), 404

def analyze_image_with_openai(image_url):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    prompt = f"Given the image of a fridge here: {image_url}, list the top 3 recipes I can make from the ingredients."
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }
            ],
            max_tokens=300
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print("OpenAI error:", e)
        return {"error": str(e)}

if __name__ == "__main__":
    app.run(debug=True)
