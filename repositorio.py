from database import (
    colecao,
    colecao_comentarios,
    colecao_questoes_usuarios,
    colecao_desempenho
)

from bson import ObjectId

from datetime import datetime, timezone


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

def listar_questoes(
    login_user,
    disciplina,
    topico,
    assunto
):

    if not all([
        login_user,
        disciplina,
        topico,
        assunto
    ]):
        return []

    # 1. Busca os vínculos do usuário.
    filtro = {
        "login_user": login_user,
        "disciplina": disciplina,
        "topico": topico,
        "assunto": assunto
    }

    vinculos = list(
        colecao_questoes_usuarios.find(
            filtro
        ).sort(
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

    # Cria um mapa para recuperar cada questão.
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

        if questao is None:
            continue

        # Preserva a classificação do usuário.
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
    login_user,
    id_questao,
    comentario
):

    if len(comentario) > 1200:
        raise ValueError(
            "O comentário não pode ultrapassar 1200 caracteres."
        )

    questao_id = ObjectId(id_questao)

    # Confirma que a questão existe.
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
    login_user,
    id_questao
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


# ============================================================
# GRADE QUANTITATIVA DE QUESTÕES DO USUÁRIO
# ============================================================

def obter_grade_questoes(login_user):

    if not login_user:
        return None

    # 1. Busca os vínculos pertencentes ao usuário.
    vinculos = list(
        colecao_questoes_usuarios.find(
            {"login_user": login_user},
            {
                "_id": 0,
                "questao_id": 1,
                "disciplina": 1,
                "topico": 1,
                "assunto": 1
            }
        )
    )

    if not vinculos:
        return None

    # 2. Recupera os IDs distintos.
    ids = list({
        v["questao_id"]
        for v in vinculos
        if v.get("questao_id") is not None
    })

    if not ids:
        return None

    # 3. Confirma quais questões realmente existem.
    ids_validos = set(
        colecao.distinct(
            "_id",
            {"_id": {"$in": ids}}
        )
    )

    # 4. Monta a estrutura hierárquica.
    grade = {}

    total_geral = set()

    for vinculo in vinculos:

        questao_id = vinculo.get("questao_id")

        if questao_id not in ids_validos:
            continue

        disciplina = vinculo.get("disciplina")
        topico = vinculo.get("topico")
        assunto = vinculo.get("assunto")

        if not all([
            disciplina,
            topico,
            assunto
        ]):
            continue

        total_geral.add(questao_id)

        grade.setdefault(disciplina, {})
        grade[disciplina].setdefault(topico, {})
        grade[disciplina][topico].setdefault(
            assunto,
            set()
        )

        grade[disciplina][topico][assunto].add(
            questao_id
        )

    if not total_geral:
        return None

    # 5. Converte conjuntos em quantidades.
    resultado = {
        "total": len(total_geral),
        "disciplinas": {}
    }

    for disciplina in sorted(grade):

        total_disciplina = 0
        topicos_resultado = {}

        for topico in sorted(grade[disciplina]):

            total_topico = 0
            assuntos_resultado = {}

            for assunto in sorted(
                grade[disciplina][topico]
            ):

                quantidade = len(
                    grade[disciplina][topico][assunto]
                )

                assuntos_resultado[assunto] = quantidade

                total_topico += quantidade

            topicos_resultado[topico] = {
                "total": total_topico,
                "assuntos": assuntos_resultado
            }

            total_disciplina += total_topico

        resultado["disciplinas"][disciplina] = {
            "total": total_disciplina,
            "topicos": topicos_resultado
        }

    return resultado


# ============================================================
# SALVAR DESEMPENHO DO BLOCO
# ============================================================

def salvar_desempenho(
    login_user,
    tentativa_id,
    disciplina,
    topico,
    assunto,
    bloco,
    total,
    acertos,
    erros
):

    # 1. Valida os dados obrigatórios.
    if not all([
        login_user,
        tentativa_id,
        disciplina,
        topico,
        assunto
    ]):
        raise ValueError(
            "Existem dados obrigatórios ausentes."
        )

    total = int(total)
    acertos = int(acertos)
    erros = int(erros)
    bloco = int(bloco)

    if total <= 0 or bloco <= 0:
        raise ValueError(
            "Quantidade de questões ou bloco inválido."
        )

    if acertos < 0 or erros < 0:
        raise ValueError(
            "Acertos e erros não podem ser negativos."
        )

    if acertos + erros != total:
        raise ValueError(
            "A soma de acertos e erros deve ser igual ao total."
        )

    # 2. Calcula o aproveitamento.
    aproveitamento = round(
        (acertos / total) * 100,
        2
    )

    # 3. Monta o documento.
    documento = {
        "tentativa_id": str(tentativa_id),
        "login_user": login_user,

        "disciplina": disciplina,
        "topico": topico,
        "assunto": assunto,

        "bloco": bloco,

        "total": total,
        "acertos": acertos,
        "erros": erros,

        "aproveitamento": aproveitamento,

        "data_conclusao": datetime.now(
            timezone.utc
        )
    }

    # 4. Insere somente uma vez por tentativa.
    resultado = colecao_desempenho.update_one(
        {
            "login_user": login_user,
            "tentativa_id": str(tentativa_id)
        },
        {
            "$setOnInsert": documento
        },
        upsert=True
    )

    return {
        "salvo": True,
        "novo_registro": resultado.upserted_id is not None,
        "aproveitamento": aproveitamento
    }


# ============================================================
# LISTAR DISCIPLINAS COM DESEMPENHO SALVO
# ============================================================

def listar_disciplinas_desempenho(login_user):

    if not login_user:
        return []

    disciplinas = colecao_desempenho.distinct(
        "disciplina",
        {
            "login_user": login_user
        }
    )

    return sorted(
        d for d in disciplinas if d
    )


# ============================================================
# OBTER DESEMPENHO DE UMA DISCIPLINA
# ============================================================

def obter_desempenho_disciplina(
    login_user,
    disciplina
):

    if not login_user or not disciplina:
        return []

    filtro = {
        "login_user": login_user,
        "disciplina": disciplina
    }

    registros = list(
        colecao_desempenho.find(
            filtro,
            {
                "_id": 0
            }
        ).sort([
            ("data_conclusao", -1)
        ])
    )

    return registros


# ============================================================
# OBTER RESUMO GERAL DO DESEMPENHO
# ============================================================

def obter_resumo_desempenho(login_user):

    if not login_user:
        return None

    registros = list(
        colecao_desempenho.find({
            "login_user": login_user
        })
    )

    if not registros:
        return {
            "total_blocos": 0,
            "total_questoes": 0,
            "acertos": 0,
            "erros": 0,
            "aproveitamento": 0
        }

    # Agrupa pelo assunto e bloco.
    # Considera somente a tentativa mais recente.
    ultimas_tentativas = {}

    for registro in registros:

        chave = (
            registro.get("disciplina"),
            registro.get("topico"),
            registro.get("assunto"),
            registro.get("bloco")
        )

        data = registro.get("data_conclusao")

        atual = ultimas_tentativas.get(chave)

        if atual is None:

            ultimas_tentativas[chave] = registro

        elif (
            data is not None
            and (
                atual.get("data_conclusao") is None
                or data > atual.get("data_conclusao")
            )
        ):

            ultimas_tentativas[chave] = registro

    total_questoes = sum(
        int(r.get("total", 0))
        for r in ultimas_tentativas.values()
    )

    acertos = sum(
        int(r.get("acertos", 0))
        for r in ultimas_tentativas.values()
    )

    erros = sum(
        int(r.get("erros", 0))
        for r in ultimas_tentativas.values()
    )

    aproveitamento = (
        round(acertos / total_questoes * 100, 2)
        if total_questoes else 0
    )

    return {
        "total_blocos": len(ultimas_tentativas),
        "total_questoes": total_questoes,
        "acertos": acertos,
        "erros": erros,
        "aproveitamento": aproveitamento
    }

# ============================================================
# GERENCIAMENTO E EXCLUSÃO DO HISTÓRICO DE DESEMPENHO
# ============================================================

def listar_topicos_desempenho(login_user, disciplina):

    if not login_user or not disciplina:
        return []

    topicos = colecao_desempenho.distinct(
        "topico",
        {
            "login_user": login_user,
            "disciplina": disciplina
        }
    )

    return sorted(t for t in topicos if t)


def listar_assuntos_desempenho(
    login_user,
    disciplina,
    topico
):

    if not all([login_user, disciplina, topico]):
        return []

    assuntos = colecao_desempenho.distinct(
        "assunto",
        {
            "login_user": login_user,
            "disciplina": disciplina,
            "topico": topico
        }
    )

    return sorted(a for a in assuntos if a)


def contar_historico_desempenho(
    login_user,
    disciplina,
    topico=None,
    assunto=None
):

    if not login_user or not disciplina:
        return 0

    filtro = {
        "login_user": login_user,
        "disciplina": disciplina
    }

    if topico is not None:
        filtro["topico"] = topico

    if assunto is not None:
        filtro["assunto"] = assunto

    return colecao_desempenho.count_documents(filtro)


def excluir_historico_disciplina(
    login_user,
    disciplina
):

    if not login_user or not disciplina:
        return 0

    filtro = {
        "login_user": login_user,
        "disciplina": disciplina
    }

    # Confirma que existe histórico antes de excluir.
    if colecao_desempenho.count_documents(filtro) == 0:
        return 0

    resultado = colecao_desempenho.delete_many(filtro)

    return resultado.deleted_count


def excluir_historico_topico(
    login_user,
    disciplina,
    topico
):

    if not all([login_user, disciplina, topico]):
        return 0

    filtro = {
        "login_user": login_user,
        "disciplina": disciplina,
        "topico": topico
    }

    if colecao_desempenho.count_documents(filtro) == 0:
        return 0

    resultado = colecao_desempenho.delete_many(filtro)

    return resultado.deleted_count


def excluir_historico_assunto(
    login_user,
    disciplina,
    topico,
    assunto
):

    if not all([login_user, disciplina, topico, assunto]):
        return 0

    filtro = {
        "login_user": login_user,
        "disciplina": disciplina,
        "topico": topico,
        "assunto": assunto
    }

    if colecao_desempenho.count_documents(filtro) == 0:
        return 0

    resultado = colecao_desempenho.delete_many(filtro)

    return resultado.deleted_count