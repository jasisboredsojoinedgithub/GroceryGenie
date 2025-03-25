from pymongo import MongoClient
import urllib.parse

# 你当前的用户名和密码
username = urllib.parse.quote_plus("jwang259@admin")  # 注意：@ 需要转义为 %40
password = urllib.parse.quote_plus("J5XccGcw1UVB7Fqc")

# 构建连接 URI
uri = f"mongodb+srv://{username}:{password}@grocerygeniecluster.zucwq.mongodb.net/?retryWrites=true&w=majority&authSource=admin"

try:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    print("✅ MongoDB connected successfully!")
except Exception as e:
    print("❌ MongoDB connection failed:")
    print(e)
