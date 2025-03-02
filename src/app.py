from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import openai
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'  

# In-memory storage for grocery items
inventory = []

@app.route("/")
def main():
    return render_template("dashborad.html")

@app.route("/suggestion")
def suggestion():
    recipes = session.get('recipe_suggestions', [])
    return render_template("suggestion.html", recipes=recipes)

@app.route("/analyze", methods=["POST"])
def analyze():
    image_url = "https://media.istockphoto.com/id/842160124/photo/refrigerator-with-fruits-and-vegetables.jpg?s=1024x1024&w=is&k=20&c=EyLsx0KNKvsVYSK0_7dkTmjtTwJVFfpQXqU1cs1MgsQ="
    analysis_result = analyze_image_with_openai(image_url)
    session['recipe_suggestions'] = analysis_result['recipes']
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
    objects = [{"name": items[i].strip(), "quantity": items[i + 1].strip() if (i + 1) < len(items) and items[i + 1].strip().isdigit() else "1"} for i in range(0, len(items), 2)]


    inventory.extend(objects)

    return jsonify(objects), 201


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

def analyze_image_with_openai(image_url):
    logging.debug(f"Analyzing image: {image_url}")
    
    # Prompt now explicitly asks for extracting food items
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
        # Use OpenAI API to analyze the image content
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI assistant skilled in detecting food items and suggesting recipes."},
                {"role": "user", "content": prompt}
            ]
        )

        # Process the response
        full_response = response.choices[0].message.content
        
        # Split the response into food items and recipes parts
        items_part, recipes_part = full_response.split('|')
        
        # Process food items
        items = items_part.split(',')
        objects = [{"name": items[i].strip(), "expiration_date": items[i + 1].strip() if (i + 1) < len(items) else "null"} for i in range(0, len(items), 2)]
        
        # Process recipes
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




