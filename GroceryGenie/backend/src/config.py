from pymongo import MongoClient

MONGO_URI = "mongodb+srv://dimpal:Dimpal22@grocerygeniecluster.zucwq.mongodb.net/?retryWrites=true&w=majority&appName=GroceryGenieCluster"
client = MongoClient(MONGO_URI)

# Create Database and Collection
db = client["GroceryGenieDB"]
users_collection = db["users"]

# Ensure 'email' is unique
users_collection.create_index("email", unique=True)