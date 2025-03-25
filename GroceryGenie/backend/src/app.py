import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from pymongo import MongoClient
import openai
from dotenv import load_dotenv  # Load environment variables from .env file

# Load variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='../../frontend/static', template_folder='../../frontend/templates')
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")  # Fallback to default if not set

# Load MongoDB URI from environment variables
MONGO_URI = os.environ.get("MONGO_URI")

# Validate MongoDB URI
if not MONGO_URI:
    raise ValueError("❌ MONGO_URI is not set. Please check your .env file.")

# Initialize MongoDB client and test the connection
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("✅ MongoDB connection successful.")
except Exception as e:
    print("❌ MongoDB connection failed:", e)

# Connect to the database and user collection
db = client.get_database("grocery_genie")
users_collection = db.users

# Temporary in-memory inventory (can be moved to MongoDB)
inventory = []

@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/")
def index():
    if 'username' in session:
        return render_template("dashboard.html", username=session['username'])
    else:
        return render_template("dashboard.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users_collection.find_one({"username": username})
        if user and user.get("password") == password:
            session['username'] = username
            flash('Login Successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid Credentials, Try Again.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if users_collection.find_one({"username": username}):
            flash('Username already exists!', 'warning')
        else:
            user = {"username": username, "password": password}
            users_collection.insert_one(user)
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

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

# Helper function to call OpenAI API with image analysis
def analyze_image_with_openai(image_url):
    openai.api_key = os.environ.get("OPENAI_API_KEY")
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