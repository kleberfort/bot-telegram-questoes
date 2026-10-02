import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
MONGODB_URI = os.getenv("MONGODB_URI")

if not TOKEN:
    raise ValueError("TOKEN não configurado.")

if not MONGODB_URI:
    raise ValueError("MONGODB_URI não configurada.")