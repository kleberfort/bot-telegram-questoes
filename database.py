from pymongo import MongoClient
from config import MONGODB_URI

if not MONGODB_URI:
    raise ValueError("MONGODB_URI não foi configurada.")

cliente = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=30000,
    connectTimeoutMS=20000
)

banco = cliente["questoes_concurso"]
colecao = banco["questoes"]


def testar_conexao():
    try:
        cliente.admin.command("ping")
        print("Conexão com MongoDB estabelecida!")
        return True

    except Exception as erro:
        print(f"Erro ao conectar ao MongoDB: {erro}")
        return False


