from pymongo import MongoClient
import urllib.parse


username = urllib.parse.quote_plus("jwang259")  
password = urllib.parse.quote_plus("kHyGJCSdNQnkwtP3")


uri = f"mongodb+srv://{username}:{password}@grocerygeniecluster.zucwq.mongodb.net/?retryWrites=true&w=majority&authSource=admin"

try:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    print("✅ MongoDB connected successfully!")
except Exception as e:
    print("❌ MongoDB connection failed:")
    print(e)
