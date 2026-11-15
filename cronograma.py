from datetime import date, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import repositorio


# ============================================================
# CONFIGURAÇÕES
# ============================================================

DIAS = {
    "segunda": "Segunda-feira",
    "terca": "Terça-feira",
    "quarta": "Quarta-feira",
    "quinta": "Quinta-feira",
    "sexta": "Sexta-feira",
    "sabado": "Sábado",
    "domingo": "Domingo"
}

DURACOES = [15, 20, 30, 40, 50, 60, 90]
METAS_QUESTOES = [10, 20, 30, 40, 50]
METAS_TEMPO = [15, 30, 45, 60, 90]


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def obter_login(context):
    usuario = context.user_data.get("usuario") or {}
    return usuario.get("login")


def obter_segunda_atual():
    hoje = date.today()
    segunda = hoje - timedelta(days=hoje.weekday())
    return segunda.isoformat()


def obter_proxima_segunda():
    segunda_atual = date.fromisoformat(obter_segunda_atual())
    proxima = segunda_atual + timedelta(days=7)
    return proxima.isoformat()


def formatar_data(data_iso):
    data = date.fromisoformat(data_iso)
    return data.strftime("%d/%m/%Y")


def obter_periodo_semana(semana_inicio):
    inicio = date.fromisoformat(semana_inicio)
    fim = inicio + timedelta(days=6)

    return (
        f"{inicio.strftime('%d/%m/%Y')} "
        f"a {fim.strftime('%d/%m/%Y')}"
    )


def teclado_voltar_inicio():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🏠 Voltar ao início",
                callback_data="inicio"
            )
        ]
    ])


async def editar_mensagem(consulta, texto, teclado=None):
    await consulta.edit_message_text(
        texto,
        reply_markup=teclado
    )


def obter_cronograma_usuario(context):
    login_user = obter_login(context)
    semana_inicio = context.user_data.get("cronograma_semana")

    if not login_user or not semana_inicio:
        return None

    return repositorio.obter_cronograma(
        login_user,
        semana_inicio
    )


# ============================================================
# ABRIR CRONOGRAMA
# ============================================================

async def abrir_cronograma(update, context):
    consulta = update.callback_query
    await consulta.answer()

    login_user = obter_login(context)

    if not login_user:
        await editar_mensagem(
            consulta,
            "🔒 Sua sessão não foi identificada.\n\n"
            "Digite /start para entrar novamente.",
            teclado_voltar_inicio()
        )
        return

    semana_atual = obter_segunda_atual()
    proxima_semana = obter_proxima_segunda()

    teclado = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📅 Semana atual",
                callback_data=f"crono:semana:{semana_atual}"
            )
        ],
        [
            InlineKeyboardButton(
                "➡️ Próxima semana",
                callback_data=f"crono:semana:{proxima_semana}"
            )
        ],
        [
            InlineKeyboardButton(
                "🏠 Voltar ao início",
                callback_data="inicio"
            )
        ]
    ])

    await editar_mensagem(
        consulta,
        "📅 MEU CRONOGRAMA SEMANAL\n\n"
        "Organize suas atividades de estudo como preferir.\n\n"
        "Você pode escolher os dias, os conteúdos, "
        "os horários, as metas e as pausas.\n\n"
        "Nenhum dia ou horário é obrigatório.\n\n"
        "Escolha a semana que deseja visualizar:",
        teclado
    )


# ============================================================
# EXIBIR SEMANA
# ============================================================

async def mostrar_semana(consulta, context):
    cronograma = obter_cronograma_usuario(context)

    if not cronograma:
        await editar_mensagem(
            consulta,
            "Não foi possível carregar seu cronograma.",
            teclado_voltar_inicio()
        )
        return

    semana_inicio = context.user_data["cronograma_semana"]

    botoes = []

    for dia, nome in DIAS.items():
        atividades = cronograma["dias"][dia]["atividades"]

        quantidade = len(atividades)

        botoes.append([
            InlineKeyboardButton(
                f"📌 {nome} ({quantidade})",
                callback_data=f"crono:dia:{dia}"
            )
        ])

    botoes.append([
        InlineKeyboardButton(
            "✏️ Alterar cronograma",
            callback_data="crono:alterar"
        )
    ])

    botoes.append([
        InlineKeyboardButton(
            "📅 Escolher outra semana",
            callback_data="crono:semanas"
        )
    ])

    botoes.append([
        InlineKeyboardButton(
            "🏠 Voltar ao início",
            callback_data="inicio"
        )
    ])

    texto = (
        "📅 MEU CRONOGRAMA SEMANAL\n\n"
        f"Período: {obter_periodo_semana(semana_inicio)}\n\n"
        "Escolha um dia para visualizar suas atividades.\n\n"
        "Os números entre parênteses representam "
        "a quantidade de atividades cadastradas."
    )

    await editar_mensagem(
        consulta,
        texto,
        InlineKeyboardMarkup(botoes)
    )


# ============================================================
# ESCOLHER DIA PARA ALTERAÇÃO
# ============================================================

async def mostrar_dias_edicao(consulta):
    botoes = []

    for dia, nome in DIAS.items():
        botoes.append([
            InlineKeyboardButton(
                nome,
                callback_data=f"crono:dia:{dia}"
            )
        ])

    botoes.append([
        InlineKeyboardButton(
            "⬅️ Voltar ao cronograma",
            callback_data="crono:voltar_semana"
        )
    ])

    await editar_mensagem(
        consulta,
        "✏️ ALTERAR CRONOGRAMA\n\n"
        "Escolha o dia que deseja modificar:",
        InlineKeyboardMarkup(botoes)
    )


# ============================================================
# EXIBIR ATIVIDADES DE UM DIA
# ============================================================

async def mostrar_dia(consulta, context, dia):
    cronograma = obter_cronograma_usuario(context)

    if not cronograma or dia not in DIAS:
        await editar_mensagem(
            consulta,
            "Não foi possível localizar esse dia.",
            teclado_voltar_inicio()
        )
        return

    atividades = cronograma["dias"][dia]["atividades"]

    atividades = sorted(
        atividades,
        key=lambda item: item.get("horario_inicio", "00:00")
    )

    nome_dia = DIAS[dia]

    linhas = [
        f"📅 {nome_dia.upper()}",
        "",
        f"Período: {obter_periodo_semana(context.user_data['cronograma_semana'])}",
        ""
    ]

    botoes = []

    if not atividades:
        linhas.append("Nenhuma atividade cadastrada neste dia.")
    else:
        linhas.append("📚 ATIVIDADES PROGRAMADAS")
        linhas.append("")

        for indice, atividade in enumerate(atividades, start=1):
            horario = atividade.get("horario_inicio", "")
            duracao = atividade.get("duracao_minutos", 0)

            if atividade.get("tipo") == "pausa":
                descricao = atividade.get("descricao", "Pausa")

                linhas.append(
                    f"☕ {horario} — {descricao} "
                    f"({duracao} minutos)"
                )

                titulo_botao = f"☕ {horario} — {descricao}"

            else:
                disciplina = atividade.get("disciplina", "")
                topico = atividade.get("topico", "")
                assunto = atividade.get("assunto", "")

                linhas.append(
                    f"📚 {horario} — {assunto}\n"
                    f"Disciplina: {disciplina}\n"
                    f"Tópico: {topico}\n"
                    f"Duração: {duracao} minutos"
                )

                if atividade.get("meta_tipo") == "questoes":
                    linhas.append(
                        f"Meta: {atividade.get('quantidade_questoes')} questões"
                    )
                else:
                    linhas.append(
                        "Meta de tempo: "
                        f"{atividade.get('meta_tempo_minutos')} minutos"
                    )

                titulo_botao = f"📚 {horario} — {assunto[:30]}"

            linhas.append("")

            atividade_id = atividade.get("atividade_id")

            botoes.append([
                InlineKeyboardButton(
                    f"✏️ Editar {indice}: {titulo_botao[:45]}",
                    callback_data=f"crono:editar:{dia}:{atividade_id}"
                )
            ])

            botoes.append([
                InlineKeyboardButton(
                    f"🗑 Excluir {indice}",
                    callback_data=f"crono:excluir:{dia}:{atividade_id}"
                )
            ])

    botoes.append([
        InlineKeyboardButton(
            "➕ Adicionar atividade",
            callback_data=f"crono:add:{dia}"
        )
    ])

    botoes.append([
        InlineKeyboardButton(
            "⬅️ Voltar à semana",
            callback_data="crono:voltar_semana"
        )
    ])

    await editar_mensagem(
        consulta,
        "\n".join(linhas),
        InlineKeyboardMarkup(botoes)
    )


# ============================================================
# INICIAR CADASTRO DE ATIVIDADE
# ============================================================

async def iniciar_atividade(consulta, context, dia):
    context.user_data["crono_wizard"] = {
        "dia": dia,
        "semana_inicio": context.user_data.get("cronograma_semana"),
        "atividade_id": None
    }

    teclado = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📚 Atividade de questões",
                callback_data="crono:tipo:questoes"
            )
        ],
        [
            InlineKeyboardButton(
                "☕ Pausa",
                callback_data="crono:tipo:pausa"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Voltar",
                callback_data=f"crono:dia:{dia}"
            )
        ]
    ])

    await editar_mensagem(
        consulta,
        "➕ NOVA ATIVIDADE\n\n"
        "O que deseja adicionar ao seu cronograma?",
        teclado
    )


# ============================================================
# ESCOLHER DISCIPLINA
# ============================================================

async def mostrar_disciplinas(consulta, context):
    login_user = obter_login(context)

    disciplinas = repositorio.listar_disciplinas(login_user)

    if not disciplinas:
        await editar_mensagem(
            consulta,
            "Você ainda não possui disciplinas cadastradas "
            "no seu acervo de questões.",
            teclado_voltar_inicio()
        )
        return

    wizard = context.user_data["crono_wizard"]
    wizard["disciplinas"] = disciplinas

    botoes = []

    for i, disciplina in enumerate(disciplinas):
        botoes.append([
            InlineKeyboardButton(
                disciplina[:60],
                callback_data=f"crono:disciplina:{i}"
            )
        ])

    botoes.append([
        InlineKeyboardButton(
            "⬅️ Cancelar",
            callback_data=f"crono:dia:{wizard['dia']}"
        )
    ])

    await editar_mensagem(
        consulta,
        "📚 ESCOLHA A DISCIPLINA\n\n"
        "Selecione uma disciplina do seu acervo:",
        InlineKeyboardMarkup(botoes)
    )


# ============================================================
# ESCOLHER TÓPICO
# ============================================================

async def mostrar_topicos(consulta, context):
    wizard = context.user_data["crono_wizard"]

    login_user = obter_login(context)
    disciplina = wizard["disciplina"]

    topicos = repositorio.listar_topicos(
        login_user,
        disciplina
    )

    if not topicos:
        await editar_mensagem(
            consulta,
            "Não existem tópicos cadastrados nessa disciplina.",
            teclado_voltar_inicio()
        )
        return

    wizard["topicos"] = topicos

    botoes = []

    for i, topico in enumerate(topicos):
        botoes.append([
            InlineKeyboardButton(
                topico[:60],
                callback_data=f"crono:topico:{i}"
            )
        ])

    botoes.append([
        InlineKeyboardButton(
            "⬅️ Cancelar",
            callback_data=f"crono:dia:{wizard['dia']}"
        )
    ])

    await editar_mensagem(
        consulta,
        f"📁 DISCIPLINA: {disciplina}\n\n"
        "Escolha o tópico:",
        InlineKeyboardMarkup(botoes)
    )


# ============================================================
# ESCOLHER ASSUNTO
# ============================================================

async def mostrar_assuntos(consulta, context):
    wizard = context.user_data["crono_wizard"]

    login_user = obter_login(context)

    assuntos = repositorio.listar_assuntos(
        login_user,
        wizard["disciplina"],
        wizard["topico"]
    )

    if not assuntos:
        await editar_mensagem(
            consulta,
            "Não existem assuntos cadastrados nesse tópico.",
            teclado_voltar_inicio()
        )
        return

    wizard["assuntos"] = assuntos

    botoes = []

    for i, assunto in enumerate(assuntos):
        botoes.append([
            InlineKeyboardButton(
                assunto[:60],
                callback_data=f"crono:assunto:{i}"
            )
        ])

    botoes.append([
        InlineKeyboardButton(
            "⬅️ Cancelar",
            callback_data=f"crono:dia:{wizard['dia']}"
        )
    ])

    await editar_mensagem(
        consulta,
        f"📁 TÓPICO: {wizard['topico']}\n\n"
        "Escolha o assunto que deseja estudar:",
        InlineKeyboardMarkup(botoes)
    )


# ============================================================
# ESCOLHER HORÁRIO
# ============================================================

async def mostrar_horarios(consulta, context):
    botoes = []
    linha = []

    for hora in range(6, 23):
        for minuto in [0, 30]:
            if hora == 22 and minuto == 30:
                continue

            horario = f"{hora:02d}:{minuto:02d}"

            linha.append(
                InlineKeyboardButton(
                    horario,
                    callback_data=f"crono:horario:{hora:02d}{minuto:02d}"
                )
            )

            if len(linha) == 4:
                botoes.append(linha)
                linha = []

    if linha:
        botoes.append(linha)

    botoes.append([
        InlineKeyboardButton(
            "⬅️ Cancelar",
            callback_data=f"crono:dia:{context.user_data['crono_wizard']['dia']}"
        )
    ])

    await editar_mensagem(
        consulta,
        "🕒 ESCOLHA O HORÁRIO DE INÍCIO\n\n"
        "Selecione o horário desejado:",
        InlineKeyboardMarkup(botoes)
    )


# ============================================================
# ESCOLHER DURAÇÃO
# ============================================================

async def mostrar_duracoes(consulta, context):
    botoes = []

    for duracao in DURACOES:
        botoes.append([
            InlineKeyboardButton(
                f"{duracao} minutos",
                callback_data=f"crono:duracao:{duracao}"
            )
        ])

    botoes.append([
        InlineKeyboardButton(
            "⬅️ Cancelar",
            callback_data=f"crono:dia:{context.user_data['crono_wizard']['dia']}"
        )
    ])

    await editar_mensagem(
        consulta,
        "⏱️ ESCOLHA A DURAÇÃO DA ATIVIDADE:",
        InlineKeyboardMarkup(botoes)
    )


# ============================================================
# ESCOLHER TIPO DE META
# ============================================================

async def mostrar_tipos_meta(consulta, context):
    botoes = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📝 Quantidade de questões",
                callback_data="crono:meta:questoes"
            )
        ],
        [
            InlineKeyboardButton(
                "⏱️ Tempo de estudo",
                callback_data="crono:meta:tempo"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Cancelar",
                callback_data=f"crono:dia:{context.user_data['crono_wizard']['dia']}"
            )
        ]
    ])

    await editar_mensagem(
        consulta,
        "🎯 QUAL SERÁ SUA META?\n\n"
        "Você pode definir uma quantidade de questões "
        "ou estabelecer um tempo de estudo.",
        botoes
    )


# ============================================================
# ESCOLHER QUANTIDADE DE QUESTÕES
# ============================================================

async def mostrar_metas_questoes(consulta):
    botoes = []

    for quantidade in METAS_QUESTOES:
        botoes.append([
            InlineKeyboardButton(
                f"{quantidade} questões",
                callback_data=f"crono:qtd:{quantidade}"
            )
        ])

    await editar_mensagem(
        consulta,
        "📝 ESCOLHA SUA META DE QUESTÕES\n\n"
        "As metas seguem os blocos de 10 questões do bot:",
        InlineKeyboardMarkup(botoes)
    )


# ============================================================
# ESCOLHER META DE TEMPO
# ============================================================

async def mostrar_metas_tempo(consulta):
    botoes = []

    for minutos in METAS_TEMPO:
        botoes.append([
            InlineKeyboardButton(
                f"{minutos} minutos",
                callback_data=f"crono:tempo_meta:{minutos}"
            )
        ])

    await editar_mensagem(
        consulta,
        "⏱️ ESCOLHA SUA META DE TEMPO DE ESTUDO:",
        InlineKeyboardMarkup(botoes)
    )


# ============================================================
# SALVAR ATIVIDADE
# ============================================================

async def salvar_atividade(consulta, context):
    wizard = context.user_data.get("crono_wizard")

    if not wizard:
        await consulta.answer(
            "Não foi possível recuperar os dados da atividade.",
            show_alert=True
        )
        return

    atividade = {
        "tipo": wizard["tipo"],
        "horario_inicio": wizard["horario_inicio"],
        "duracao_minutos": wizard["duracao_minutos"]
    }

    if wizard["tipo"] == "questoes":
        atividade.update({
            "disciplina": wizard["disciplina"],
            "topico": wizard["topico"],
            "assunto": wizard["assunto"],
            "meta_tipo": wizard["meta_tipo"]
        })

        if wizard["meta_tipo"] == "questoes":
            atividade["quantidade_questoes"] = (
                wizard["quantidade_questoes"]
            )
        else:
            atividade["meta_tempo_minutos"] = (
                wizard["meta_tempo_minutos"]
            )

    else:
        atividade["descricao"] = "Pausa"

    login_user = obter_login(context)
    semana_inicio = wizard["semana_inicio"]
    dia = wizard["dia"]
    atividade_id = wizard.get("atividade_id")

    try:
        if atividade_id:
            resultado = repositorio.editar_atividade_cronograma(
                login_user,
                semana_inicio,
                dia,
                atividade_id,
                atividade
            )
        else:
            resultado = repositorio.salvar_atividade_cronograma(
                login_user,
                semana_inicio,
                dia,
                atividade
            )

        if not resultado:
            await editar_mensagem(
                consulta,
                "⚠️ Não foi possível salvar a atividade.\n\n"
                "Volte ao dia escolhido e tente novamente.",
                teclado_voltar_inicio()
            )
            return

    except ValueError as erro:
        await consulta.answer(
            str(erro),
            show_alert=True
        )
        return

    except Exception:
        import logging
        logging.exception("Erro ao salvar atividade do cronograma")

        await editar_mensagem(
            consulta,
            "❌ Ocorreu um erro ao salvar sua atividade.\n\n"
            "Tente novamente.",
            teclado_voltar_inicio()
        )
        return

    context.user_data.pop("crono_wizard", None)

    await editar_mensagem(
        consulta,
        "✅ ATIVIDADE SALVA!\n\n"
        "Sua atividade foi registrada no cronograma semanal.",
        InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "📅 Visualizar o dia",
                    callback_data=f"crono:dia:{dia}"
                )
            ],
            [
                InlineKeyboardButton(
                    "📋 Visualizar a semana",
                    callback_data="crono:voltar_semana"
                )
            ],
            [
                InlineKeyboardButton(
                    "🏠 Voltar ao início",
                    callback_data="inicio"
                )
            ]
        ])
    )


# ============================================================
# PROCESSADOR PRINCIPAL DOS BOTÕES DO CRONOGRAMA
# ============================================================

async def processar_callback(update, context):
    consulta = update.callback_query
    await consulta.answer()

    dados = consulta.data.split(":")

    if len(dados) < 2:
        return

    acao = dados[1]

    # --------------------------------------------------------
    # ESCOLHER SEMANA
    # --------------------------------------------------------

    if acao == "semana":
        semana_inicio = dados[2]

        context.user_data["cronograma_semana"] = semana_inicio

        await mostrar_semana(consulta, context)
        return

    if acao == "semanas":
        await abrir_cronograma_sem_callback(consulta, context)
        return

    if acao == "voltar_semana":
        await mostrar_semana(consulta, context)
        return

    # --------------------------------------------------------
    # ALTERAR CRONOGRAMA
    # --------------------------------------------------------

    if acao == "alterar":
        await mostrar_dias_edicao(consulta)
        return

    # --------------------------------------------------------
    # ESCOLHER DIA
    # --------------------------------------------------------

    if acao == "dia":
        dia = dados[2]
        await mostrar_dia(consulta, context, dia)
        return

    # --------------------------------------------------------
    # INICIAR ATIVIDADE
    # --------------------------------------------------------

    if acao == "add":
        dia = dados[2]
        await iniciar_atividade(consulta, context, dia)
        return

    # --------------------------------------------------------
    # ESCOLHER TIPO
    # --------------------------------------------------------

    if acao == "tipo":
        tipo = dados[2]

        wizard = context.user_data.get("crono_wizard")

        if not wizard:
            return

        wizard["tipo"] = tipo

        if tipo == "questoes":
            await mostrar_disciplinas(consulta, context)
        elif tipo == "pausa":
            await mostrar_horarios(consulta, context)

        return

    # --------------------------------------------------------
    # ESCOLHER DISCIPLINA
    # --------------------------------------------------------

    if acao == "disciplina":
        wizard = context.user_data.get("crono_wizard")

        if not wizard:
            return

        indice = int(dados[2])
        disciplinas = wizard.get("disciplinas", [])

        if indice >= len(disciplinas):
            return

        wizard["disciplina"] = disciplinas[indice]

        await mostrar_topicos(consulta, context)
        return

    # --------------------------------------------------------
    # ESCOLHER TÓPICO
    # --------------------------------------------------------

    if acao == "topico":
        wizard = context.user_data.get("crono_wizard")

        if not wizard:
            return

        indice = int(dados[2])
        topicos = wizard.get("topicos", [])

        if indice >= len(topicos):
            return

        wizard["topico"] = topicos[indice]

        await mostrar_assuntos(consulta, context)
        return

    # --------------------------------------------------------
    # ESCOLHER ASSUNTO
    # --------------------------------------------------------

    if acao == "assunto":
        wizard = context.user_data.get("crono_wizard")

        if not wizard:
            return

        indice = int(dados[2])
        assuntos = wizard.get("assuntos", [])

        if indice >= len(assuntos):
            return

        wizard["assunto"] = assuntos[indice]

        await mostrar_horarios(consulta, context)
        return

    # --------------------------------------------------------
    # ESCOLHER HORÁRIO
    # --------------------------------------------------------

    if acao == "horario":
        wizard = context.user_data.get("crono_wizard")

        if not wizard:
            return

        horario_bruto = dados[2]

        wizard["horario_inicio"] = (
            f"{horario_bruto[:2]}:{horario_bruto[2:]}"
        )

        await mostrar_duracoes(consulta, context)
        return

    # --------------------------------------------------------
    # ESCOLHER DURAÇÃO
    # --------------------------------------------------------

    if acao == "duracao":
        wizard = context.user_data.get("crono_wizard")

        if not wizard:
            return

        wizard["duracao_minutos"] = int(dados[2])

        if wizard["tipo"] == "pausa":
            await salvar_atividade(consulta, context)
        else:
            await mostrar_tipos_meta(consulta, context)

        return

    # --------------------------------------------------------
    # ESCOLHER TIPO DE META
    # --------------------------------------------------------

    if acao == "meta":
        wizard = context.user_data.get("crono_wizard")

        if not wizard:
            return

        wizard["meta_tipo"] = dados[2]

        if dados[2] == "questoes":
            await mostrar_metas_questoes(consulta)
        elif dados[2] == "tempo":
            await mostrar_metas_tempo(consulta)

        return

    # --------------------------------------------------------
    # ESCOLHER QUANTIDADE DE QUESTÕES
    # --------------------------------------------------------

    if acao == "qtd":
        wizard = context.user_data.get("crono_wizard")

        if not wizard:
            return

        quantidade = int(dados[2])

        if quantidade not in METAS_QUESTOES:
            return

        wizard["quantidade_questoes"] = quantidade

        await salvar_atividade(consulta, context)
        return

    # --------------------------------------------------------
    # ESCOLHER META DE TEMPO
    # --------------------------------------------------------

    if acao == "tempo_meta":
        wizard = context.user_data.get("crono_wizard")

        if not wizard:
            return

        minutos = int(dados[2])

        if minutos not in METAS_TEMPO:
            return

        wizard["meta_tempo_minutos"] = minutos

        await salvar_atividade(consulta, context)
        return

    # --------------------------------------------------------
    # EDITAR ATIVIDADE
    # --------------------------------------------------------

    if acao == "editar":
        dia = dados[2]
        atividade_id = dados[3]

        cronograma = obter_cronograma_usuario(context)

        if not cronograma:
            return

        atividades = cronograma["dias"][dia]["atividades"]

        atividade = next(
            (
                item for item in atividades
                if item.get("atividade_id") == atividade_id
            ),
            None
        )

        if not atividade:
            await consulta.answer(
                "Essa atividade não foi encontrada.",
                show_alert=True
            )
            return

        context.user_data["crono_wizard"] = {
            "dia": dia,
            "semana_inicio": context.user_data["cronograma_semana"],
            "atividade_id": atividade_id
        }

        teclado = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "📚 Atividade de questões",
                    callback_data="crono:tipo:questoes"
                )
            ],
            [
                InlineKeyboardButton(
                    "☕ Pausa",
                    callback_data="crono:tipo:pausa"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Voltar",
                    callback_data=f"crono:dia:{dia}"
                )
            ]
        ])

        await editar_mensagem(
            consulta,
            "✏️ EDITAR ATIVIDADE\n\n"
            "Você poderá redefinir o tipo, o conteúdo, "
            "o horário, a duração e a meta.\n\n"
            "Escolha o tipo da atividade:",
            teclado
        )
        return

    # --------------------------------------------------------
    # EXCLUIR ATIVIDADE
    # --------------------------------------------------------

    if acao == "excluir":
        dia = dados[2]
        atividade_id = dados[3]

        login_user = obter_login(context)
        semana_inicio = context.user_data.get("cronograma_semana")

        try:
            resultado = repositorio.excluir_atividade_cronograma(
                login_user,
                semana_inicio,
                dia,
                atividade_id
            )

            if resultado:
                await editar_mensagem(
                    consulta,
                    "🗑️ Atividade excluída do cronograma.",
                    InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton(
                                "📅 Voltar ao dia",
                                callback_data=f"crono:dia:{dia}"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "📋 Voltar à semana",
                                callback_data="crono:voltar_semana"
                            )
                        ]
                    ])
                )
            else:
                await consulta.answer(
                    "Não foi possível excluir essa atividade.",
                    show_alert=True
                )

        except Exception:
            import logging
            logging.exception("Erro ao excluir atividade do cronograma")

            await consulta.answer(
                "Ocorreu um erro ao excluir a atividade.",
                show_alert=True
            )

        return


# ============================================================
# ABRIR SELEÇÃO DE SEMANAS A PARTIR DE UM CALLBACK
# ============================================================

async def abrir_cronograma_sem_callback(consulta, context):
    semana_atual = obter_segunda_atual()
    proxima_semana = obter_proxima_segunda()

    teclado = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📅 Semana atual",
                callback_data=f"crono:semana:{semana_atual}"
            )
        ],
        [
            InlineKeyboardButton(
                "➡️ Próxima semana",
                callback_data=f"crono:semana:{proxima_semana}"
            )
        ],
        [
            InlineKeyboardButton(
                "🏠 Voltar ao início",
                callback_data="inicio"
            )
        ]
    ])

    await editar_mensagem(
        consulta,
        "📅 ESCOLHA A SEMANA DO SEU CRONOGRAMA:",
        teclado
    )