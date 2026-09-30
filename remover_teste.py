import os
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId

load_dotenv()

uri = os.getenv("MONGODB_URI")

cliente = MongoClient(uri)

db = cliente["questoes_concurso"]
colecao = db["questoes"]

resultado = colecao.delete_one({
    "_id": ObjectId("6abd14c5bd46c47a14dcc6eb")
})

if resultado.deleted_count == 1:
    print("✅ Questão de teste removida com sucesso!")
else:
    print("⚠️ Questão não encontrada.")