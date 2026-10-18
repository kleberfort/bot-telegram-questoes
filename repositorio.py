from database import colecao, colecao_comentarios 

from bson import ObjectId

def listar_disciplinas(login_user):
    # Filtra as disciplinas únicas que pertencem apenas a este usuário
    return sorted(colecao.distinct("disciplina", {"quiz_login_user": login_user}))

def listar_topicos(login_user, disciplina):
    # Filtra os tópicos daquela disciplina que pertencem apenas a este usuário
    filtro = {"quiz_login_user": login_user, "disciplina": disciplina}
    return sorted(colecao.distinct("topico", filtro))

def listar_assuntos(login_user, disciplina, topico):
    # Filtra os assuntos daquela disciplina/tópico que pertencem apenas a este usuário
    filtro = {
        "quiz_login_user": login_user,
        "disciplina": disciplina,
        "topico": topico
    }
    return sorted(colecao.distinct("assunto", filtro))

def listar_questoes(login_user, disciplina, topico, assunto):
    # Garante que a busca final traga apenas as questões deste usuário específico
    filtro = {
        "quiz_login_user": login_user,
        "disciplina": disciplina,
        "topico": topico,
        "assunto": assunto
    }
    return list(colecao.find(filtro).sort("_id", 1))



def salvar_comentario_personalizado(
    login_user, id_questao, comentario
):
    if len(comentario) > 1200:
        raise ValueError(
            "O comentário não pode ultrapassar 1200 caracteres."
        )

    questao_id = ObjectId(id_questao)

    # Confirma que a questão existe no banco central.
    questao = colecao.find_one(
        {"_id": questao_id},
        {"_id": 1}
    )

    if not questao:
        return False

    # Salva o comentário separado por usuário.
    colecao_comentarios.update_one(
        {
            "login_user": login_user,
            "questao_id": questao_id
        },
        {
            "$set": {
                "comentario": comentario
            }
        },
        upsert=True
    )

    return True






def obter_comentario_personalizado(
    login_user, id_questao
):
    comentario = colecao_comentarios.find_one(
        {
            "login_user": login_user,
            "questao_id": ObjectId(id_questao)
        },
        {
            "_id": 0,
            "comentario": 1
        }
    )

    if comentario:
        return comentario.get("comentario", "")

    return ""


