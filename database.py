from pymongo import MongoClient
from config import MONGODB_URI

cliente = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=30000
)

banco = cliente["questoes_concurso"]
colecao = banco["questoes"]


def testar_conexao():
    cliente.admin.command("ping")
    print("Conexão com MongoDB estabelecida!")