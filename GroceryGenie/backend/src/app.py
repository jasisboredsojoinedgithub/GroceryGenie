from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import openai
import os
import logging

app = Flask(__name__, static_folder='../../frontend/static', template_folder="../../frontend/templates")
app.secret_key = 'supersecretkey'  # Please change the secret key as needed

# In-memory storage for grocery items
inventory = []

# Simulated user database (replace with a real database)
users = {'testuser': 'password123'}

# Root route: displays different pages based on the user's login status
@app.route("/")
def index():
    if 'username' in session:
        return render_template("dashborad.html", username=session['username'])
    else:
        return render_template("dashboard.html")

# User authentication related routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users and users[username] == password:
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

# Other functional routes

@app.route("/profile", methods=['GET', 'POST'])
def profile():
    return render_template("profile.html")

@app.route("/suggestion")
def suggestion():
    recipes = session.get('recipe_suggestions', [])
    return render_template("suggestion.html", recipes=recipes)

@app.route("/analyze", methods=["POST"])
def analyze():
    image_url = "https://media.istockphoto.com/id/842160124/photo-refrigerator-with-fruits-and-vegetables.jpg?s=1024x1024&w=is&k=20&c=EyLsx0KNKvsVYSK0_7dkTmjtTwJVFfpQXqU1cs1MgsQ="
    analysis_result = analyze_image_with_openai(image_url)
    session['recipe_suggestions'] = analysis_result.get('recipes', [])
    return redirect(url_for('suggestion'))

@app.route("/recipe_details", methods=["POST"])
def recipe_details():
    recipe_name = request.json['recipe_name']
    detailed_recipe = get_detailed_recipe(recipe_name)
    return jsonify({"recipe_name": recipe_name, "detailed_recipe": detailed_recipe})

@app.route("/grocery_analyze", methods=["POST"])
def grocery_analyze():
    image_url = ""
    
    prompt = (
        "Extract food items and their quantities from the following grocery receipt image. "
        "Format: item1, quantity1, item2, quantity2, ... If an item does not have a quantity, assume 1.\n\n"
        f"Image URL: {image_url}\n\n"
    )

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an AI assistant skilled in extracting food items and quantities from grocery receipts."},
            {"role": "user", "content": prompt}
        ]
    )

    analysis = response.choices[0].message['content']
    items = analysis.split(',')
    objects = [{"name": items[i].strip(), 
                "quantity": items[i + 1].strip() if (i + 1) < len(items) and items[i + 1].strip().isdigit() else "1"} 
                for i in range(0, len(items), 2)]
    inventory.extend(objects)

    return jsonify(objects), 201

# Inventory management related routes
@app.route("/inventory", methods=["GET"])
def get_inventory():
    return jsonify(inventory)

@app.route("/inventory", methods=["POST"])
def add_item():
    item = request.json
    inventory.append(item)
    return jsonify({"message": "Item added successfully!"}), 201

@app.route("/inventory/<int:item_index>", methods=["PUT"])
def update_item(item_index):
    item = request.json
    if 0 <= item_index < len(inventory):
        inventory[item_index] = item
        return jsonify({"message": "Item updated successfully!"})
    else:
        return jsonify({"message": "Item not found!"}), 404

@app.route("/inventory/<int:item_index>", methods=["DELETE"])
def delete_item(item_index):
    if 0 <= item_index < len(inventory):
        inventory.pop(item_index)
        return jsonify({"message": "Item deleted successfully!"})
    else:
        return jsonify({"message": "Item not found!"}), 404

# Helper functions

def analyze_image_with_openai(image_url):
    logging.debug(f"Analyzing image: {image_url}")
    
    prompt = f"""
    You are an AI assistant skilled in detecting food items from images.
    Analyze the contents of this image: {image_url}. 
    Provide a list of detected food items and their potential expiration dates (if known). 
    If expiration dates are not available, just mention the food items.
    After listing the items, suggest some recipes based on the detected ingredients.
    Provide the response in the following format:
    "Item1, Expiration1, Item2, Expiration2 ... | Recipe1, Recipe2, ..."
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI assistant skilled in detecting food items and suggesting recipes."},
                {"role": "user", "content": prompt}
            ]
        )

        full_response = response.choices[0].message.content
        
        # Split the ingredients and recipes parts
        items_part, recipes_part = full_response.split('|')
        
        items = items_part.split(',')
        objects = [{"name": items[i].strip(), "expiration_date": items[i + 1].strip() if (i + 1) < len(items) else "null"} 
                   for i in range(0, len(items), 2)]
        
        recipes = [recipe.strip() for recipe in recipes_part.split(',')]
        
        return {"objects": objects, "recipes": recipes}

    except Exception as e:
        logging.error(f"Error during API call: {str(e)}")
        return {"error": str(e)}

def suggest_recipes(objects):
    ingredients_list = ", ".join([obj['name'] for obj in objects])
    prompt = f"Based on the following detected objects: {ingredients_list}, suggest some recipes that can be made. Provide each recipe in a separate line as 'Recipe Name'."

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an AI assistant skilled in suggesting recipes based on available ingredients."},
            {"role": "user", "content": prompt}
        ]
    )
    
    recipes = response.choices[0].message['content']
    recipes_cleaned = [recipe.replace('*', '').strip() for recipe in recipes.split('\n')]
    return recipes_cleaned

def get_detailed_recipe(recipe_name):
    prompt = f"Provide the detailed recipe for the following dish: {recipe_name}"

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an AI assistant skilled in providing detailed recipes."},
            {"role": "user", "content": prompt}
        ]
    )
    
    detailed_recipe = response.choices[0].message['content']
    return detailed_recipe

if __name__ == "__main__":
    app.run(debug=True)


