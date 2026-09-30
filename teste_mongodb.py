import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

uri = os.getenv("MONGODB_URI")

try:
    cliente = MongoClient(uri)

    # Testa a conexão
    cliente.admin.command("ping")

    print("✅ Conectado ao MongoDB Atlas!")

    # Lista os bancos
    bancos = cliente.list_database_names()

    print("\n📚 Bancos disponíveis:")
    for banco in bancos:
        print(f" - {banco}")

except Exception as erro:
    print("❌ Erro:")
    print(erro)