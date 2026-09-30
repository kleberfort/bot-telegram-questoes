import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

uri = os.getenv("MONGODB_URI")

try:
    cliente = MongoClient(uri)

    # Testa conexão
    cliente.admin.command("ping")

    db = cliente["questoes_concurso"]
    colecao = db["questoes"]

    # Insere uma questão de teste
    questao_teste = {
        "disciplina": "Português",
        "assunto": "Interpretação de texto",
        "enunciado": "Esta é uma questão de teste.",
        "alternativas": {
            "A": "Alternativa A",
            "B": "Alternativa B",
            "C": "Alternativa C",
            "D": "Alternativa D",
            "E": "Alternativa E"
        },
        "resposta": "A"
    }

    resultado = colecao.insert_one(questao_teste)

    print("✅ Banco criado!")
    print("✅ Coleção criada!")
    print(f"✅ Questão de teste inserida: {resultado.inserted_id}")

except Exception as erro:
    print("❌ Erro:")
    print(erro)