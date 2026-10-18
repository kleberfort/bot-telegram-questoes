
from database import (
    colecao,
    colecao_comentarios,
    colecao_questoes_usuarios
)

from bson import ObjectId


# ============================================================
# LISTAR DISCIPLINAS DO USUÁRIO
# ============================================================

def listar_disciplinas(login_user):
    if not login_user:
        return []

    disciplinas = colecao_questoes_usuarios.distinct(
        "disciplina",
        {"login_user": login_user}
    )

    return sorted(d for d in disciplinas if d)


# ============================================================
# LISTAR TÓPICOS DA DISCIPLINA
# ============================================================

def listar_topicos(login_user, disciplina):
    if not login_user or not disciplina:
        return []

    filtro = {
        "login_user": login_user,
        "disciplina": disciplina
    }

    topicos = colecao_questoes_usuarios.distinct(
        "topico",
        filtro
    )

    return sorted(t for t in topicos if t)


# ============================================================
# LISTAR ASSUNTOS DO TÓPICO
# ============================================================

def listar_assuntos(login_user, disciplina, topico):
    if not login_user or not disciplina or not topico:
        return []

    filtro = {
        "login_user": login_user,
        "disciplina": disciplina,
        "topico": topico
    }

    assuntos = colecao_questoes_usuarios.distinct(
        "assunto",
        filtro
    )

    return sorted(a for a in assuntos if a)


# ============================================================
# LISTAR QUESTÕES GLOBAIS VINCULADAS AO USUÁRIO
# ============================================================

def listar_questoes(login_user, disciplina, topico, assunto):
    if not all([login_user, disciplina, topico, assunto]):
        return []

    # 1. Busca os vínculos do usuário com a classificação escolhida.
    filtro = {
        "login_user": login_user,
        "disciplina": disciplina,
        "topico": topico,
        "assunto": assunto
    }

    vinculos = list(
        colecao_questoes_usuarios.find(filtro).sort(
            "questao_id", 1
        )
    )

    if not vinculos:
        return []

    # 2. Extrai os IDs das questões globais.
    questao_ids = list(dict.fromkeys(
        vinculo["questao_id"]
        for vinculo in vinculos
        if vinculo.get("questao_id") is not None
    ))

    if not questao_ids:
        return []

    # 3. Busca as questões na coleção global.
    questoes_globais = colecao.find({
        "_id": {"$in": questao_ids}
    })

    # Cria um mapa para recuperar cada questão pelo ObjectId.
    mapa_questoes = {
        questao["_id"]: questao
        for questao in questoes_globais
    }

    # 4. Monta a lista respeitando a ordem dos vínculos.
    resultado = []
    ids_adicionados = set()

    for vinculo in vinculos:
        questao_id = vinculo.get("questao_id")

        if questao_id in ids_adicionados:
            continue

        questao = mapa_questoes.get(questao_id)

        # Ignora vínculos cuja questão global não existe.
        if questao is None:
            continue

        # Preserva a classificação específica do usuário.
        questao["disciplina"] = vinculo.get(
            "disciplina",
            questao.get("disciplina_base", "")
        )

        questao["topico"] = vinculo.get(
            "topico",
            questao.get("topico_base", "")
        )

        questao["assunto"] = vinculo.get(
            "assunto",
            questao.get("assunto_base", "")
        )

        resultado.append(questao)
        ids_adicionados.add(questao_id)

    return resultado


# ============================================================
# SALVAR COMENTÁRIO PERSONALIZADO
# ============================================================

def salvar_comentario_personalizado(
    login_user, id_questao, comentario
):
    if len(comentario) > 1200:
        raise ValueError(
            "O comentário não pode ultrapassar 1200 caracteres."
        )

    questao_id = ObjectId(id_questao)

    # Confirma que a questão existe na coleção global.
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


# ============================================================
# OBTER COMENTÁRIO PERSONALIZADO
# ============================================================

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
