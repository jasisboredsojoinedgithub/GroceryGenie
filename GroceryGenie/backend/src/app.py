import os
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from pymongo import MongoClient
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../.env'))
load_dotenv(dotenv_path=env_path, override=True)
print(f"🔍 Looking for .env at: {env_path}")
print(f"📄 .env exists: {os.path.exists(env_path)}")
print("✅ Loaded MONGO_URI from .env:", os.environ.get("MONGO_URI"))

# Initialize Flask app
app = Flask(__name__, static_folder='../../frontend/static', template_folder='../../frontend/templates')
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

# Connect MongoDB
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise ValueError("❌ MONGO_URI is not set.")
try:
    client = MongoClient(MONGO_URI)
    client.admin.command('ping')
    print("MongoDB connection successful.")
except Exception as e:
    print("MongoDB connection failed:", e)

db = client.get_database("grocery_genie")
users_collection = db.users

# In-memory inventory
inventory = []

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
        if user and user.get("password") == password:
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
            user = {"email": email, "password": password}
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

@app.route("/profile", methods=['GET', 'POST'])
def profile():
    if 'email' not in session:
        flash('Please log in first', 'warning')
        return redirect(url_for('login'))
    user = users_collection.find_one({"email": session['email']})
    return render_template("profile.html", user=user)

@app.route("/suggestion")
def suggestion():
    # 从 session 拿到完整的 recipe_suggestions（每个元素是 dict）
    full_recipes = session.get('recipe_suggestions', [])
    # 前端只需要 name 字段来渲染按钮
    recipes = [{'name': r.get('name')} for r in full_recipes]
    return render_template("suggestion.html", recipes=recipes)

@app.route("/analyze", methods=["POST"])
def analyze():
    print("📁 /analyze called with inventory:", inventory)

    if not inventory:
        return jsonify({"error": "Inventory is empty!"}), 400

    ingredient_list = [item["name"] for item in inventory]
    analysis_result = analyze_image_with_openai(ingredient_list, task="recipe")

    if isinstance(analysis_result, dict) and "recipes" in analysis_result:
        session['recipe_suggestions'] = analysis_result["recipes"]
    else:
        session['recipe_suggestions'] = []

    return jsonify({"success": True, "redirect": url_for('suggestion')})

@app.route("/grocery_analyze", methods=["POST"])
def grocery_analyze():
    test_url = "https://www.chowhound.com/img/gallery/follow-these-easy-tips-to-reduce-food-waste/intro-1696446020.webp"
    result = analyze_image_with_openai(test_url, task="grocery")

    try:
        raw_items = result.get("grocery_items")
        print("🧠 Raw OpenAI result:", raw_items)

        # ✅ Remove Markdown ```json wrapping
        if isinstance(raw_items, str):
            raw_items = raw_items.strip()
            if raw_items.startswith("```json"):
                raw_items = raw_items[7:]
            if raw_items.endswith("```"):
                raw_items = raw_items[:-3]
            raw_items = raw_items.strip()

        items = json.loads(raw_items)
        parsed_items = [{"name": item.strip(), "quantity": 1} for item in items]

        # ✅ Add to inventory
        inventory.extend(parsed_items)

        return jsonify(parsed_items)
    except Exception as e:
        print("❌ JSON parsing failed:", e)
        return jsonify({"error": "Invalid response format from OpenAI."}), 500


@app.route("/inventory")
def inventory_page():
    return render_template("inventory.html")

@app.route("/recipe_details", methods=["POST"])
def recipe_details():
    recipe_name = request.json.get("recipe_name")
    full_recipes = session.get('recipe_suggestions', [])

    # 在完整列表中找到匹配 name 的那一项
    recipe = next((r for r in full_recipes if r.get('name') == recipe_name), None)
    if not recipe:
        return jsonify({"error": "Recipe not found"}), 404

    # 返回完整的 recipe dict，前端会读取 ingredients & detailed_recipe
    return jsonify(recipe)

def analyze_image_with_openai(input_data, task="grocery"):
    openai.api_key = os.environ.get("OPENAI_API_KEY")

    if not openai.api_key:
        print("❌ Missing OpenAI API key.")
        return {"error": "Missing OpenAI API key."}

    try:
        if task == "grocery":
            prompt = (
                "You are a helpful grocery assistant. Analyze the image and return a JSON list of grocery item names. "
                "Respond with a plain list like: [\"banana\", \"tomato\", \"milk\"]. "
                "DO NOT include any markdown, code block, or ```json around your response."
            )
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": input_data}},
                    ],
                }
            ]
        else:  # task == "recipe"
            ingredients = ", ".join(input_data)
            prompt = (
                f"I have the following ingredients in my fridge: {ingredients}. "
                "Suggest 3 recipes I can make using these items. "
                "Respond in JSON format like: {\"recipes\": [{\"name\": \"Pasta\", \"ingredients\": [...], \"detailed_recipe\": \"...\"}, ...]}. "
                "DO NOT include any markdown, code block, or ```json around your response."
            )
            print("📤 Prompt used:", prompt)
            messages = [{"role": "user", "content": prompt}]

        # 🔥 Send request
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=1000
        )

        content = response['choices'][0]['message']['content']
        print("🧠 OpenAI response:", content)

        # 🔍 Clean up response if needed
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        # ✅ Handle each task separately
        if task == "grocery":
            return {"grocery_items": content}
        else:  # task == "recipe"
            return json.loads(content)

    except Exception as e:
        print("OpenAI error:", e)
        return {"error": str(e)}


if __name__ == "__main__":
    app.run(debug=True)
