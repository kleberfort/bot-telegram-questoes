import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

uri = os.getenv("MONGODB_URI")

cliente = MongoClient(uri)

db = cliente["questoes_concurso"]
colecao = db["questoes"]

questoes = colecao.find()

print("📚 Questões encontradas:\n")

for questao in questoes:
    print(f"ID: {questao['_id']}")
    print(f"Disciplina: {questao['disciplina']}")
    print(f"Assunto: {questao['assunto']}")
    print(f"Enunciado: {questao['enunciado']}")
    print(f"Resposta: {questao['resposta']}")
    print("-" * 50)