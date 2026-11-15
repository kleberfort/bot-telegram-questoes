from database import (
    colecao,
    colecao_comentarios,
    colecao_questoes_usuarios,
    colecao_desempenho,
    colecao_cronogramas
)

from bson import ObjectId

from datetime import datetime, timezone
from uuid import uuid4
from copy import deepcopy


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



# ============================================================
# CRONOGRAMA SEMANAL DOS USUÁRIOS
# ============================================================

DIAS_SEMANA = [
    "segunda",
    "terca",
    "quarta",
    "quinta",
    "sexta",
    "sabado",
    "domingo"
]

MAX_ATIVIDADES_DIA = 6

METAS_QUESTOES = [10, 20, 30, 40, 50]


# ============================================================
# CRIAR ESTRUTURA VAZIA DA SEMANA
# ============================================================

def criar_dias_cronograma():

    return {
        dia: {
            "atividades": []
        }
        for dia in DIAS_SEMANA
    }


# ============================================================
# VALIDAR DATA DA SEMANA
# ============================================================

def validar_semana_inicio(semana_inicio):

    try:
        datetime.strptime(
            semana_inicio,
            "%Y-%m-%d"
        )

        return True

    except (TypeError, ValueError):

        return False


# ============================================================
# OBTER CRONOGRAMA SEMANAL
# ============================================================

def obter_cronograma(login_user, semana_inicio):

    if not login_user or not validar_semana_inicio(semana_inicio):
        return None

    cronograma = colecao_cronogramas.find_one({
        "login_user": login_user,
        "semana_inicio": semana_inicio
    })

    if not cronograma:

        return {
            "login_user": login_user,
            "semana_inicio": semana_inicio,
            "dias": criar_dias_cronograma()
        }

    # Garante que todos os sete dias estejam disponíveis.
    dias_existentes = cronograma.get("dias", {})

    for dia in DIAS_SEMANA:

        dias_existentes.setdefault(
            dia,
            {"atividades": []}
        )

    cronograma["dias"] = dias_existentes

    return cronograma


# ============================================================
# VALIDAR ATIVIDADE DO CRONOGRAMA
# ============================================================

def validar_atividade_cronograma(atividade):

    if not isinstance(atividade, dict):
        raise ValueError("Atividade inválida.")

    tipo = atividade.get("tipo")

    if tipo not in ["questoes", "pausa"]:
        raise ValueError("Tipo de atividade inválido.")

    horario = atividade.get("horario_inicio")

    try:
        datetime.strptime(horario, "%H:%M")

    except (TypeError, ValueError):
        raise ValueError("Horário inválido. Utilize HH:MM.")

    try:
        duracao = int(atividade.get("duracao_minutos", 0))

    except (TypeError, ValueError):
        raise ValueError("Duração inválida.")

    if duracao <= 0:
        raise ValueError("A duração deve ser maior que zero.")

    if tipo == "questoes":

        if not all([
            atividade.get("disciplina"),
            atividade.get("topico"),
            atividade.get("assunto")
        ]):
            raise ValueError(
                "Disciplina, tópico e assunto são obrigatórios."
            )

        meta_tipo = atividade.get("meta_tipo")

        if meta_tipo == "questoes":

            try:
                quantidade = int(
                    atividade.get("quantidade_questoes", 0)
                )

            except (TypeError, ValueError):
                raise ValueError("Meta de questões inválida.")

            if quantidade not in METAS_QUESTOES:
                raise ValueError(
                    "A meta deve ser 10, 20, 30, 40 ou 50 questões."
                )

        elif meta_tipo == "tempo":

            try:
                meta_tempo = int(
                    atividade.get("meta_tempo_minutos", 0)
                )

            except (TypeError, ValueError):
                raise ValueError("Meta de tempo inválida.")

            if meta_tempo <= 0:
                raise ValueError(
                    "A meta de tempo deve ser maior que zero."
                )

        else:
            raise ValueError("Tipo de meta inválido.")

    elif tipo == "pausa":

        if not atividade.get("descricao"):
            atividade["descricao"] = "Descanso"

    return True


# ============================================================
# VERIFICAR CONFLITO DE HORÁRIOS
# ============================================================

def verificar_conflito_horario(
    atividades,
    nova_atividade,
    atividade_id=None
):
    inicio_novo = datetime.strptime(
        nova_atividade["horario_inicio"],
        "%H:%M"
    )

    inicio_novo_minutos = (
        inicio_novo.hour * 60
        + inicio_novo.minute
    )

    fim_novo = (
        inicio_novo_minutos
        + int(nova_atividade["duracao_minutos"])
    )

    if fim_novo > 24 * 60:
        raise ValueError(
            "A atividade ultrapassa o horário de 23:59."
        )

    def formatar_horario(minutos):
        horas = minutos // 60
        minutos_restantes = minutos % 60
        return f"{horas:02d}:{minutos_restantes:02d}"

    def identificar_atividade(atividade):
        if atividade.get("tipo") == "pausa":
            return atividade.get("descricao", "Pausa")

        return (
            atividade.get("assunto")
            or atividade.get("disciplina")
            or "Atividade de questões"
        )

    for atividade in atividades:

        # Durante a edição, ignora a própria atividade.
        if (
            atividade_id
            and atividade.get("atividade_id") == atividade_id
        ):
            continue

        inicio_existente = datetime.strptime(
            atividade["horario_inicio"],
            "%H:%M"
        )

        inicio_existente_minutos = (
            inicio_existente.hour * 60
            + inicio_existente.minute
        )

        fim_existente = (
            inicio_existente_minutos
            + int(atividade["duracao_minutos"])
        )

        existe_sobreposicao = (
            inicio_novo_minutos < fim_existente
            and fim_novo > inicio_existente_minutos
        )

        if existe_sobreposicao:
            nome = identificar_atividade(atividade)

            horario_existente = (
                f"{formatar_horario(inicio_existente_minutos)} "
                f"às {formatar_horario(fim_existente)}"
            )

            horario_novo = (
                f"{formatar_horario(inicio_novo_minutos)} "
                f"às {formatar_horario(fim_novo)}"
            )

            raise ValueError(
                "⚠️ CONFLITO DE HORÁRIO!\n\n"
                f"A atividade que você está tentando cadastrar "
                f"ocupa o horário das {horario_novo}.\n\n"
                f"Esse intervalo coincide com:\n"
                f"📌 {nome}\n"
                f"🕒 {horario_existente}\n\n"
                "Escolha outro horário ou ajuste a duração."
            )

    return True


# ============================================================
# GARANTIR QUE O DOCUMENTO DA SEMANA EXISTA
# ============================================================

def garantir_cronograma(login_user, semana_inicio):

    if not login_user or not validar_semana_inicio(semana_inicio):
        raise ValueError("Usuário ou semana inválida.")

    colecao_cronogramas.update_one(
        {
            "login_user": login_user,
            "semana_inicio": semana_inicio
        },
        {
            "$setOnInsert": {
                "login_user": login_user,
                "semana_inicio": semana_inicio,
                "dias": criar_dias_cronograma(),
                "data_criacao": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )


# ============================================================
# COPIAR CRONOGRAMA DA SEMANA ANTERIOR
# ============================================================

def copiar_cronograma_semana_anterior(
    login_user,
    semana_destino,
    semana_origem
):

    if not login_user:
        raise ValueError("Usuário inválido.")

    if not validar_semana_inicio(semana_destino):
        raise ValueError("Data da semana de destino inválida.")

    if not validar_semana_inicio(semana_origem):
        raise ValueError("Data da semana de origem inválida.")

    # Verifica se a semana de destino já existe.
    destino_existente = colecao_cronogramas.find_one({
        "login_user": login_user,
        "semana_inicio": semana_destino
    })

    if destino_existente:
        return {
            "criado": False,
            "ja_existia": True,
            "mensagem": "A semana de destino já possui um cronograma."
        }

    # Busca o cronograma da semana anterior.
    origem = colecao_cronogramas.find_one({
        "login_user": login_user,
        "semana_inicio": semana_origem
    })

    # Se não existir cronograma anterior, cria uma semana vazia.
    if origem:
        dias = deepcopy(
            origem.get("dias", criar_dias_cronograma())
        )
    else:
        dias = criar_dias_cronograma()

    # Garante que os sete dias estejam disponíveis.
    for dia in DIAS_SEMANA:

        if dia not in dias:
            dias[dia] = {"atividades": []}

        dias[dia].setdefault("atividades", [])

        # Gera novos identificadores para as atividades.
        for atividade in dias[dia]["atividades"]:
            atividade["atividade_id"] = str(uuid4())

    # Monta o novo documento.
    novo_cronograma = {
        "login_user": login_user,
        "semana_inicio": semana_destino,
        "dias": dias,
        "data_criacao": datetime.now(timezone.utc),
        "data_atualizacao": datetime.now(timezone.utc),
        "copiado_de": semana_origem
    }

    # Insere somente se a semana ainda não existir.
    resultado = colecao_cronogramas.update_one(
        {
            "login_user": login_user,
            "semana_inicio": semana_destino
        },
        {
            "$setOnInsert": novo_cronograma
        },
        upsert=True
    )

    if resultado.upserted_id:

        return {
            "criado": True,
            "ja_existia": False,
            "mensagem": "Cronograma copiado com sucesso."
        }

    return {
        "criado": False,
        "ja_existia": True,
        "mensagem": "A semana de destino já possui um cronograma."
    }


# ============================================================
# SUBSTITUIR SEMANA PELO CRONOGRAMA DA SEMANA ANTERIOR
# ============================================================

def substituir_cronograma_por_semana_anterior(
    login_user,
    semana_destino,
    semana_origem
):

    if not login_user:
        raise ValueError("Usuário inválido.")

    if not validar_semana_inicio(semana_destino):
        raise ValueError("Data da semana de destino inválida.")

    if not validar_semana_inicio(semana_origem):
        raise ValueError("Data da semana de origem inválida.")

    if semana_destino == semana_origem:
        raise ValueError("As semanas de origem e destino devem ser diferentes.")

    # Busca o cronograma da semana anterior.
    origem = colecao_cronogramas.find_one({
        "login_user": login_user,
        "semana_inicio": semana_origem
    })

    # Se não houver semana anterior, utiliza uma semana vazia.
    if origem:
        dias = deepcopy(
            origem.get("dias", criar_dias_cronograma())
        )
    else:
        dias = criar_dias_cronograma()

    # Garante os sete dias e gera novos IDs.
    for dia in DIAS_SEMANA:

        if dia not in dias:
            dias[dia] = {"atividades": []}

        dias[dia].setdefault("atividades", [])

        for atividade in dias[dia]["atividades"]:
            atividade["atividade_id"] = str(uuid4())

    agora = datetime.now(timezone.utc)

    # Substitui as atividades da semana de destino.
    resultado = colecao_cronogramas.update_one(
        {
            "login_user": login_user,
            "semana_inicio": semana_destino
        },
        {
            "$set": {
                "dias": dias,
                "copiado_de": semana_origem,
                "data_atualizacao": agora
            },
            "$setOnInsert": {
                "login_user": login_user,
                "semana_inicio": semana_destino,
                "data_criacao": agora
            }
        },
        upsert=True
    )

    return {
        "sucesso": True,
        "mensagem": "Cronograma substituído com sucesso."
    }


# ============================================================
# ADICIONAR ATIVIDADE AO CRONOGRAMA
# ============================================================

def salvar_atividade_cronograma(
    login_user,
    semana_inicio,
    dia,
    atividade
):

    if dia not in DIAS_SEMANA:
        raise ValueError("Dia da semana inválido.")

    validar_atividade_cronograma(atividade)

    garantir_cronograma(
        login_user,
        semana_inicio
    )

    cronograma = obter_cronograma(
        login_user,
        semana_inicio
    )

    atividades = cronograma["dias"][dia]["atividades"]

    # Limite de seis atividades de questões.
    if atividade["tipo"] == "questoes":

        quantidade_questoes = sum(
            1
            for item in atividades
            if item.get("tipo") == "questoes"
        )

        if quantidade_questoes >= MAX_ATIVIDADES_DIA:
            raise ValueError(
                "Este dia já possui seis atividades de questões."
            )

    # Impede conflitos entre atividades e pausas.
    verificar_conflito_horario(
        atividades,
        atividade
    )

    nova_atividade = atividade.copy()

    nova_atividade["atividade_id"] = str(uuid4())

    resultado = colecao_cronogramas.update_one(
        {
            "login_user": login_user,
            "semana_inicio": semana_inicio
        },
        {
            "$push": {
                f"dias.{dia}.atividades": nova_atividade
            },
            "$set": {
                "data_atualizacao": datetime.now(timezone.utc)
            }
        }
    )

    return resultado.modified_count > 0


# ============================================================
# EDITAR ATIVIDADE DO CRONOGRAMA
# ============================================================

def editar_atividade_cronograma(
    login_user,
    semana_inicio,
    dia,
    atividade_id,
    novos_dados
):

    if dia not in DIAS_SEMANA:
        raise ValueError("Dia da semana inválido.")

    validar_atividade_cronograma(novos_dados)

    cronograma = obter_cronograma(
        login_user,
        semana_inicio
    )

    if not cronograma:
        return False

    atividades = cronograma["dias"][dia]["atividades"]

    atividade_existente = next(
        (
            item for item in atividades
            if item.get("atividade_id") == atividade_id
        ),
        None
    )

    if not atividade_existente:
        return False

    # Preserva o identificador original.
    atividade_atualizada = novos_dados.copy()

    atividade_atualizada["atividade_id"] = atividade_id

    # Verifica o limite de seis atividades de questões.
    quantidade_questoes = sum(
        1
        for item in atividades
        if (
            item.get("tipo") == "questoes"
            and item.get("atividade_id") != atividade_id
        )
    )

    if (
        atividade_atualizada["tipo"] == "questoes"
        and quantidade_questoes >= MAX_ATIVIDADES_DIA
    ):
        raise ValueError(
            "Este dia já possui seis atividades de questões."
        )

    # Verifica conflitos, ignorando a atividade editada.
    verificar_conflito_horario(
        atividades,
        atividade_atualizada,
        atividade_id
    )

    resultado = colecao_cronogramas.update_one(
        {
            "login_user": login_user,
            "semana_inicio": semana_inicio
        },
        {
            "$set": {
                f"dias.{dia}.atividades.$[atividade]":
                    atividade_atualizada,

                "data_atualizacao": datetime.now(timezone.utc)
            }
        },
        array_filters=[
            {
                "atividade.atividade_id": atividade_id
            }
        ]
    )

    return resultado.modified_count > 0


# ============================================================
# EXCLUIR ATIVIDADE DO CRONOGRAMA
# ============================================================

def excluir_atividade_cronograma(
    login_user,
    semana_inicio,
    dia,
    atividade_id
):

    if dia not in DIAS_SEMANA:
        return False

    resultado = colecao_cronogramas.update_one(
        {
            "login_user": login_user,
            "semana_inicio": semana_inicio
        },
        {
            "$pull": {
                f"dias.{dia}.atividades": {
                    "atividade_id": atividade_id
                }
            },
            "$set": {
                "data_atualizacao": datetime.now(timezone.utc)
            }
        }
    )

    return resultado.modified_count > 0


# ============================================================
# EXCLUIR CRONOGRAMA DE UMA SEMANA
# ============================================================

def excluir_cronograma_semana(
    login_user,
    semana_inicio
):

    if not login_user or not validar_semana_inicio(semana_inicio):
        return False

    resultado = colecao_cronogramas.delete_one({
        "login_user": login_user,
        "semana_inicio": semana_inicio
    })

    return resultado.deleted_count > 0


# ============================================================
# LISTAR SEMANAS COM CRONOGRAMA CADASTRADO
# ============================================================

def listar_semanas_cronograma(login_user):

    if not login_user:
        return []

    semanas = colecao_cronogramas.find(
        {
            "login_user": login_user
        },
        {
            "_id": 0,
            "semana_inicio": 1
        }
    ).sort(
        "semana_inicio",
        -1
    )

    return [
        item["semana_inicio"]
        for item in semanas
        if item.get("semana_inicio")
    ]
