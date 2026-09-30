import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

uri = os.getenv("MONGODB_URI")

cliente = MongoClient(uri)

db = cliente["questoes_concurso"]
colecao = db["questoes"]

questao = {
    "disciplina": "Aprendizado e Máquinas",

    "assunto": "Aprendizado de Máquina",

    "enunciado": (
        "Em relação à Inteligência Artificial (IA), como é conhecido "
        "o processo de identificação de padrões a partir de dados em "
        "vez do uso de regras predefinidas para fazer previsões ou "
        "tomar decisões?"
    ),

    "alternativas": {
        "A": "Aprendizado de máquina.",
        "B": "Pseudoconhecimento.",
        "C": "Automação tradicional.",
        "D": "Sistema especialista.",
        "E": "Algoritmo determinístico."
    },

    "resposta": "A",

    "comentario": (
        "O aprendizado de máquina (Machine Learning) é conceituado "
        "como a área da inteligência artificial que foca no desenvolvimento "
        "de agentes que aprendem sozinhos a partir de dados. Em vez de "
        "seguirem regras predefinidas (programação clássica), esses sistemas "
        "identificam padrões de forma autônoma para construir modelos que "
        "permitem tomar decisões e resolver problemas."
    )
}

resultado = colecao.insert_one(questao)

print("✅ Questão inserida com sucesso!")
print(f"ID: {resultado.inserted_id}")