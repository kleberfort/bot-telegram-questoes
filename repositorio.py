from database import colecao


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
    """Salva o comentário personalizado do usuário na questão."""

    from bson import ObjectId

    if len(comentario) > 1200:
        raise ValueError(
            "O comentário não pode ultrapassar 1200 caracteres."
        )

    filtro = {
        "_id": ObjectId(id_questao),
        "quiz_login_user": login_user
    }

    resultado = colecao.update_one(
        filtro,
        {
            "$set": {
                "comentario_personalizado": comentario
            }
        }
    )

    return resultado.matched_count == 1


def obter_comentario_personalizado(
    login_user, id_questao
):
    """Recupera o comentário personalizado do usuário."""

    from bson import ObjectId

    filtro = {
        "_id": ObjectId(id_questao),
        "quiz_login_user": login_user
    }

    questao = colecao.find_one(
        filtro,
        {"comentario_personalizado": 1}
    )

    if questao:
        return questao.get("comentario_personalizado", "")

    return ""

