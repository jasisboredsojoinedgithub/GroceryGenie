import os

# ONLY load .env locally — skip it in CI
if os.getenv("GITHUB_ACTIONS") != "true":
    from dotenv import load_dotenv
    from pathlib import Path
    env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)

# Use environment variables
SECRET_KEY = os.getenv("SECRET_KEY")
MONGO_URI = os.getenv("MONGO_URI")
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_STORAGE_CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER_NAME")
AZURE_STORAGE_CONTAINER_GROCERY = os.getenv("AZURE_STORAGE_CONTAINER_GROCERY")
#this changes is for deployment 
