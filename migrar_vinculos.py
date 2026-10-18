
from database import colecao, colecao_questoes_usuarios

migrados = 0
ignorados = 0

for questao in colecao.find({}):
    login_user = questao.get("quiz_login_user")

    if not login_user:
        ignorados += 1
        continue

    vinculo = {
        "login_user": login_user,
        "questao_id": questao["_id"],
        "disciplina": questao.get("disciplina", ""),
        "topico": questao.get("topico", ""),
        "assunto": questao.get("assunto", "")
    }

    colecao_questoes_usuarios.update_one(
        {
            "login_user": login_user,
            "questao_id": questao["_id"]
        },
        {"$set": vinculo},
        upsert=True
    )

    migrados += 1

print(f"Vínculos processados: {migrados}")
print(f"Questões ignoradas por falta de login: {ignorados}")
print(
    "Total de vínculos na nova coleção:",
    colecao_questoes_usuarios.count_documents({})
)
