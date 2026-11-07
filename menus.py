
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from datetime import datetime
import math

import repositorio
import questoes
import usuarios


# ============================================================
# ESTADOS DO LOGIN
# ============================================================

SOLICITAR_LOGIN, SOLICITAR_SENHA = range(2)


# ============================================================
# MONTAR TECLADO PADRÃO
# ============================================================

def montar_teclado(opcoes, prefixo):

    botoes = []

    # Duas opções por linha
    for i in range(0, len(opcoes), 2):

        linha = [
            InlineKeyboardButton(
                opcoes[i],
                callback_data=f"{prefixo}:{i}"
            )
        ]

        if i + 1 < len(opcoes):

            linha.append(
                InlineKeyboardButton(
                    opcoes[i + 1],
                    callback_data=f"{prefixo}:{i + 1}"
                )
            )

        botoes.append(linha)

    botoes.append([
        InlineKeyboardButton(
            "⬅️ Voltar ao início",
            callback_data="inicio"
        )
    ])

    return InlineKeyboardMarkup(botoes)


# ============================================================
# MENU PRINCIPAL
# ============================================================

def montar_teclado_areas(disciplinas):

    teclado = montar_teclado(
        disciplinas,
        "disciplina"
    )

    botoes = list(teclado.inline_keyboard)

    # Mapeamento de questões
    botoes.insert(
        -1,
        [
            InlineKeyboardButton(
                "📋 Mapeamento de Questões",
                callback_data="grade_questoes"
            )
        ]
    )

    # Novo botão: Painel de Desempenho
    botoes.insert(
        -1,
        [
            InlineKeyboardButton(
                "📊 Meu Painel de Desempenho",
                callback_data="painel_desempenho"
            )
        ]
    )

    return InlineKeyboardMarkup(botoes)


# ============================================================
# FORMATAR GRADE COMPLETA DE QUESTÕES
# ============================================================

def formatar_grade_questoes(grade):

    from html import escape

    linhas = []

    linhas.append(
        "📋 <b>MEU ACERVO DE QUESTÕES</b>"
    )

    linhas.append(
        f"📊 Total: {grade['total']} questões cadastradas"
    )

    disciplinas = grade["disciplinas"]

    for disciplina, dados in disciplinas.items():

        linhas.append("")
        linhas.append("━━━━━━━━━━━━━━━━━━━━")
        linhas.append("")

        linhas.append(
            f"📚 <b>{escape(disciplina.upper())}</b> "
            f"({dados['total']})"
        )

        linhas.append("")
        linhas.append("━━━━━━━━━━━━━━━━━━━━")

        for topico, dados_topico in dados["topicos"].items():

            linhas.append("")

            linhas.append(
                f"📁 <b>{escape(topico)}</b> "
                f"({dados_topico['total']})"
            )

            for assunto, quantidade in dados_topico["assuntos"].items():

                linhas.append(
                    f"🔹 {escape(assunto)}: "
                    f"[<code>{quantidade}</code>]"
                )

    linhas.append("")
    linhas.append("━━━━━━━━━━━━━━━━━━━━")
    linhas.append("")

    linhas.append("<b>ℹ️ LEGENDA</b>")
    linhas.append("📚 Área principal")
    linhas.append("📁 Disciplina")
    linhas.append("🔹 Assunto específico")
    linhas.append("[<code>40</code>] Quantidade de questões")

    return "\n".join(linhas)


# ============================================================
# DIVIDIR MENSAGEM
# ============================================================

def dividir_mensagem(texto, limite=3500):

    linhas = texto.split("\n")

    mensagens = []
    mensagem_atual = ""

    for linha in linhas:

        nova_mensagem = (
            mensagem_atual + "\n" + linha
            if mensagem_atual
            else linha
        )

        if len(nova_mensagem) > limite:

            if mensagem_atual:
                mensagens.append(mensagem_atual)

            mensagem_atual = linha

        else:
            mensagem_atual = nova_mensagem

    if mensagem_atual:
        mensagens.append(mensagem_atual)

    return mensagens


# ============================================================
# /START
# ============================================================

async def iniciar(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_type = update.effective_chat.type

    # ========================================================
    # ACESSO PELO GRUPO
    # ========================================================

    if chat_type in ["group", "supergroup"]:

        username_bot = context.bot.username

        link_privado = (
            f"https://t.me/{username_bot}?start=grupo"
        )

        teclado = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🤖 Acessar bot no privado",
                    url=link_privado
                )
            ]
        ])

        await update.message.reply_text(
            "🔐 <b>QG Concurso</b>\n\n"
            "Para utilizar o sistema de questões, "
            "a interação com o bot deve ser feita "
            "em uma conversa privada.\n\n"
            "👇 Clique no botão abaixo para continuar:",
            reply_markup=teclado,
            parse_mode="HTML"
        )

        return ConversationHandler.END

    # ========================================================
    # ACESSO PRIVADO
    # ========================================================

    user_id = update.effective_user.id

    usuario_logado = usuarios.buscar_por_telegram(
        user_id
    )

    # ========================================================
    # USUÁRIO JÁ VINCULADO
    # ========================================================

    if usuario_logado:

        limpar_dados_sessao(context)

        context.user_data["usuario"] = usuario_logado

        login_user = usuario_logado.get("login")

        disciplinas = repositorio.listar_disciplinas(
            login_user
        )

        context.user_data["opcoes"] = disciplinas

        nome = usuario_logado.get("nome", "usuário")

        await update.message.reply_text(
            f"👋 Olá, {nome}! Seja bem-vindo de volta.\n\n"
            "📚 Escolha a área para ESTUDAR:",
            reply_markup=montar_teclado_areas(
                disciplinas
            )
        )

        return ConversationHandler.END

    # ========================================================
    # USUÁRIO NÃO VINCULADO
    # ========================================================

    await update.message.reply_text(
        "🔒 Este Telegram ainda não está vinculado "
        "a uma conta do sistema.\n\n"
        "Por favor, digite o seu login:"
    )

    return SOLICITAR_LOGIN


# ============================================================
# /LOGIN
# ============================================================

async def iniciar_login(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_type = update.effective_chat.type

    if chat_type in ["group", "supergroup"]:

        await update.message.reply_text(
            "🔐 Para fazer login, abra uma conversa "
            "privada com o bot e digite /login."
        )

        return ConversationHandler.END

    user_id = update.effective_user.id

    usuario_logado = usuarios.buscar_por_telegram(
        user_id
    )

    if usuario_logado:

        await update.message.reply_text(
            f"🔐 Você já está logado como "
            f"{usuario_logado.get('nome', 'usuário')}.\n\n"
            "Para sair da conta atual, digite /logout."
        )

        return ConversationHandler.END

    context.user_data.pop("temp_login", None)

    await update.message.reply_text(
        "🔐 Vamos fazer seu login.\n\n"
        "Digite o seu login:"
    )

    return SOLICITAR_LOGIN


# ============================================================
# /LOGOUT
# ============================================================

async def logout(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_type = update.effective_chat.type

    if chat_type in ["group", "supergroup"]:

        await update.message.reply_text(
            "🔐 O logout deve ser feito na conversa "
            "privada com o bot."
        )

        return ConversationHandler.END

    user_id = update.effective_user.id

    usuario = usuarios.buscar_por_telegram(
        user_id
    )

    if usuario is None:

        context.user_data.clear()

        await update.message.reply_text(
            "ℹ️ Você não está conectado a nenhuma conta."
        )

        return ConversationHandler.END

    usuarios.desvincular_telegram(user_id)

    context.user_data.clear()

    await update.message.reply_text(
        f"👋 Até logo, {usuario.get('nome', 'usuário')}!\n\n"
        "Você saiu da sua conta com sucesso.\n\n"
        "Para entrar novamente, digite /login."
    )

    return ConversationHandler.END


# ============================================================
# RECEBER LOGIN
# ============================================================

async def receber_login(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["temp_login"] = (
        update.message.text.strip()
    )

    await update.message.reply_text(
        "🔑 Agora, digite a sua senha:"
    )

    return SOLICITAR_SENHA


# ============================================================
# RECEBER SENHA
# ============================================================

async def receber_senha(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    login = context.user_data.get("temp_login")

    senha = update.message.text.strip()

    user_id = update.effective_user.id

    usuario = usuarios.autenticar(
        login,
        senha
    )

    if usuario is None:

        await update.message.reply_text(
            "❌ Login ou senha incorretos "
            "(ou conta inativa).\n\n"
            "Tente novamente digitando /start."
        )

        context.user_data.pop(
            "temp_login",
            None
        )

        return ConversationHandler.END

    usuarios.vincular_telegram(
        login,
        user_id
    )

    context.user_data["usuario"] = usuario

    context.user_data.pop(
        "temp_login",
        None
    )

    disciplinas = repositorio.listar_disciplinas(
        login
    )

    context.user_data["opcoes"] = disciplinas

    await update.message.reply_text(
        "✅ Autenticação realizada com sucesso!\n\n"
        f"Bem-vindo, {usuario['nome']}."
    )

    await update.message.reply_text(
        "📚 Escolha a área para ESTUDAR:",
        reply_markup=montar_teclado_areas(
            disciplinas
        )
    )

    return ConversationHandler.END


# ============================================================
# LIMPAR DADOS DA SESSÃO
# ============================================================

def limpar_dados_sessao(context):

    chaves = [
        "questoes",
        "indice_questao",
        "respondida",
        "desempenho",
        "assunto",
        "disciplina",
        "topico",
        "todas_questoes",
        "inicio_bloco",
        "total_questoes_assunto",
        "bloco_atual",
        "tentativa_id",
        "aguardando_salvamento",
        "disciplinas_painel"
    ]

    for chave in chaves:

        context.user_data.pop(
            chave,
            None
        )


# ============================================================
# SELECIONAR DISCIPLINA
# ============================================================

async def selecionar_disciplina(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    consulta = update.callback_query

    await consulta.answer()

    try:
        indice = int(
            consulta.data.split(":")[1]
        )

    except (ValueError, IndexError):
        await consulta.answer(
            "Opção inválida.",
            show_alert=True
        )
        return

    disciplinas = context.user_data.get(
        "opcoes",
        []
    )

    if indice < 0 or indice >= len(disciplinas):

        await consulta.message.reply_text(
            "Opção inválida. Digite /start."
        )

        return

    disciplina = disciplinas[indice]

    context.user_data["disciplina"] = disciplina

    usuario = context.user_data.get("usuario", {})

    login_user = usuario.get("login")

    topicos = repositorio.listar_topicos(
        login_user,
        disciplina
    )

    if not topicos:

        await consulta.message.reply_text(
            "Não há tópicos cadastrados nessa área."
        )

        return

    context.user_data["opcoes"] = topicos

    await consulta.message.reply_text(
        f"📚 {disciplina}\n\n"
        "Escolha um tópico:",
        reply_markup=montar_teclado(
            topicos,
            "topico"
        )
    )


# ============================================================
# SELECIONAR TÓPICO
# ============================================================

async def selecionar_topico(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    consulta = update.callback_query

    await consulta.answer()

    try:
        indice = int(
            consulta.data.split(":")[1]
        )

    except (ValueError, IndexError):
        await consulta.answer(
            "Opção inválida.",
            show_alert=True
        )
        return

    topicos = context.user_data.get(
        "opcoes",
        []
    )

    if indice < 0 or indice >= len(topicos):

        await consulta.message.reply_text(
            "Opção inválida. Digite /start."
        )

        return

    topico = topicos[indice]

    disciplina = context.user_data["disciplina"]

    context.user_data["topico"] = topico

    usuario = context.user_data.get("usuario", {})

    login_user = usuario.get("login")

    assuntos = repositorio.listar_assuntos(
        login_user,
        disciplina,
        topico
    )

    if not assuntos:

        await consulta.message.reply_text(
            "Nenhum assunto cadastrado."
        )

        return

    context.user_data["opcoes"] = assuntos

    await consulta.message.reply_text(
        f"📘 {topico}\n\n"
        "Escolha o assunto:",
        reply_markup=montar_teclado(
            assuntos,
            "assunto"
        )
    )


# ============================================================
# SELECIONAR ASSUNTO
# ============================================================

async def selecionar_assunto(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    consulta = update.callback_query

    await consulta.answer()

    try:
        indice = int(
            consulta.data.split(":")[1]
        )

    except (ValueError, IndexError):
        await consulta.answer(
            "Opção inválida.",
            show_alert=True
        )
        return

    assuntos = context.user_data.get(
        "opcoes",
        []
    )

    if indice < 0 or indice >= len(assuntos):

        await consulta.message.reply_text(
            "Opção inválida. Digite /start."
        )

        return

    assunto = assuntos[indice]

    disciplina = context.user_data["disciplina"]

    topico = context.user_data["topico"]

    usuario = context.user_data.get("usuario", {})

    login_user = usuario.get("login")

    questoes_encontradas = repositorio.listar_questoes(
        login_user,
        disciplina,
        topico,
        assunto
    )

    if not questoes_encontradas:

        await consulta.message.reply_text(
            "Não existem questões cadastradas "
            "para esse assunto."
        )

        return

    context.user_data["todas_questoes"] = (
        questoes_encontradas
    )

    context.user_data["assunto"] = assunto

    total = len(questoes_encontradas)

    tamanho_bloco = 10

    quantidade_blocos = math.ceil(
        total / tamanho_bloco
    )

    botoes = []

    for bloco in range(1, quantidade_blocos + 1):

        inicio = (bloco - 1) * tamanho_bloco + 1

        fim = min(
            bloco * tamanho_bloco,
            total
        )

        botoes.append([
            InlineKeyboardButton(
                f"Bloco {bloco} — Questões {inicio} a {fim}",
                callback_data=f"bloco:{bloco}"
            )
        ])

    botoes.append([
        InlineKeyboardButton(
            "⬅️ Voltar ao início",
            callback_data="inicio"
        )
    ])

    await consulta.message.reply_text(
        f"📚 {assunto}\n\n"
        f"📝 Total de questões: {total}\n\n"
        "Escolha o bloco que deseja resolver:",
        reply_markup=InlineKeyboardMarkup(botoes)
    )


# ============================================================
# SELECIONAR BLOCO
# ============================================================

async def selecionar_bloco(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    consulta = update.callback_query

    await consulta.answer()

    try:
        bloco = int(
            consulta.data.split(":")[1]
        )

    except (ValueError, IndexError):
        await consulta.answer(
            "Bloco inválido.",
            show_alert=True
        )
        return

    todas_questoes = context.user_data.get(
        "todas_questoes",
        []
    )

    if not todas_questoes:

        await consulta.message.reply_text(
            "Questões não encontradas. Digite /start."
        )

        return

    tamanho_bloco = 10

    inicio = (bloco - 1) * tamanho_bloco

    fim = inicio + tamanho_bloco

    questoes_bloco = todas_questoes[inicio:fim]

    if not questoes_bloco:

        await consulta.message.reply_text(
            "Bloco não encontrado."
        )

        return

    # Guarda o número do bloco para o histórico.
    context.user_data["bloco_atual"] = bloco

    # Limpa identificador de tentativa anterior.
    context.user_data.pop(
        "tentativa_id",
        None
    )

    context.user_data.pop(
        "aguardando_salvamento",
        None
    )

    context.user_data["questoes"] = questoes_bloco

    context.user_data["indice_questao"] = 0

    context.user_data["inicio_bloco"] = inicio

    context.user_data["total_questoes_assunto"] = (
        len(todas_questoes)
    )

    context.user_data["respondida"] = False

    questoes.iniciar_desempenho(context)

    await consulta.message.reply_text(
        f"📖 Iniciando o bloco {bloco} "
        f"(questões {inicio + 1} a "
        f"{min(fim, len(todas_questoes))})"
    )

    await questoes.exibir_questao(
        consulta.message,
        context
    )


# ============================================================
# VOLTAR AO INÍCIO
# ============================================================

async def voltar_inicio(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    consulta = update.callback_query

    await consulta.answer()

    usuario = context.user_data.get("usuario")

    limpar_dados_sessao(context)

    context.user_data["usuario"] = usuario

    login_user = (
        usuario.get("login")
        if usuario
        else None
    )

    disciplinas = repositorio.listar_disciplinas(
        login_user
    )

    if not disciplinas:

        await consulta.message.reply_text(
            "Nenhuma área foi cadastrada para este usuário."
        )

        return

    context.user_data["opcoes"] = disciplinas

    nome = (
        usuario.get("nome", "usuário")
        if usuario
        else "usuário"
    )

    await consulta.edit_message_text(
        f"👋 Olá, {nome}! Seja bem-vindo de volta.\n\n"
        "📚 Escolha a área para ESTUDAR:",
        reply_markup=montar_teclado_areas(
            disciplinas
        )
    )


# ============================================================
# VISUALIZAR GRADE DE QUESTÕES
# ============================================================

async def visualizar_grade_questoes(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    consulta = update.callback_query

    await consulta.answer()

    usuario = context.user_data.get("usuario", {})

    login_user = usuario.get("login")

    if not login_user:

        await consulta.message.reply_text(
            "⚠️ Não foi possível identificar "
            "seu usuário. Faça login novamente."
        )

        return

    grade = repositorio.obter_grade_questoes(
        login_user
    )

    if not grade:

        await consulta.message.reply_text(
            "📋 Sua grade ainda não possui "
            "questões disponíveis.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "⬅️ Voltar ao início",
                        callback_data="inicio"
                    )
                ]
            ])
        )

        return

    texto = formatar_grade_questoes(grade)

    mensagens = dividir_mensagem(texto)

    teclado = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "⬅️ Voltar ao início",
                callback_data="inicio"
            )
        ]
    ])

    for indice, mensagem in enumerate(mensagens):

        await consulta.message.reply_text(
            mensagem,
            parse_mode="HTML",
            reply_markup=(
                teclado
                if indice == len(mensagens) - 1
                else None
            )
        )


# ============================================================
# PAINEL DE DESEMPENHO — TECLADO
# ============================================================

def montar_teclado_painel(disciplinas):

    botoes = []

    for i in range(0, len(disciplinas), 2):

        linha = [
            InlineKeyboardButton(
                f"📘 {disciplinas[i]}",
                callback_data=f"painel_disciplina:{i}"
            )
        ]

        if i + 1 < len(disciplinas):

            linha.append(
                InlineKeyboardButton(
                    f"📘 {disciplinas[i + 1]}",
                    callback_data=f"painel_disciplina:{i + 1}"
                )
            )

        botoes.append(linha)

    botoes.append([
        InlineKeyboardButton(
            "⬅️ Voltar ao Início",
            callback_data="inicio"
        )
    ])

    return InlineKeyboardMarkup(botoes)


# ============================================================
# ABRIR PAINEL DE DESEMPENHO
# ============================================================

async def abrir_painel_desempenho(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    consulta = update.callback_query

    await consulta.answer()

    usuario = context.user_data.get("usuario")

    if not usuario:

        await consulta.edit_message_text(
            "🔒 Sua sessão expirou. Digite /start."
        )

        return

    login_user = usuario.get("login")

    disciplinas = repositorio.listar_disciplinas_desempenho(
        login_user
    )

    if not disciplinas:

        await consulta.edit_message_text(
            "📊 PAINEL DE DESEMPENHO\n\n"
            "Você ainda não possui blocos salvos.\n\n"
            "Ao finalizar um questionário, "
            "escolha a opção de salvar o desempenho.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "⬅️ Voltar ao Início",
                        callback_data="inicio"
                    )
                ]
            ])
        )

        return

    context.user_data["disciplinas_painel"] = disciplinas

    await consulta.edit_message_text(
        "📊 PAINEL DE DESEMPENHO\n\n"
        "Escolha qual disciplina deseja analisar:",
        reply_markup=montar_teclado_painel(
            disciplinas
        )
    )


# ============================================================
# FORMATAR DATA DO DESEMPENHO
# ============================================================

def formatar_data_desempenho(data):

    if not data:
        return "Data não informada"

    if isinstance(data, datetime):
        return data.strftime("%d/%m/%Y")

    if isinstance(data, str):

        try:
            data = datetime.fromisoformat(
                data.replace("Z", "+00:00")
            )

            return data.strftime("%d/%m/%Y")

        except ValueError:
            return data

    return "Data não informada"


# ============================================================
# OBTER DATA PARA ORDENAÇÃO
# ============================================================

def chave_data_desempenho(registro):

    data = registro.get("data_conclusao")

    if isinstance(data, datetime):

        try:
            return data.timestamp()
        except (ValueError, OSError):
            return 0

    if isinstance(data, str):

        try:
            return datetime.fromisoformat(
                data.replace("Z", "+00:00")
            ).timestamp()

        except ValueError:
            return 0

    return 0


# ============================================================
# GERAR RELATÓRIO DA DISCIPLINA
# ============================================================

def gerar_relatorio_disciplina(
    disciplina,
    grade_disciplina,
    registros
):

    linhas = []

    # Agrupa os registros por tópico, assunto e bloco.
    agrupados = {}

    for registro in registros:

        try:
            bloco = int(registro.get("bloco", 0))
        except (TypeError, ValueError):
            continue

        chave = (
            registro.get("topico"),
            registro.get("assunto"),
            bloco
        )

        agrupados.setdefault(chave, []).append(
            registro
        )

    total_blocos_previstos = 0
    total_blocos_concluidos = 0

    total_questoes = 0
    total_acertos = 0

    linhas.append(
        f"📊 MEU DESEMPENHO — {disciplina.upper()}"
    )

    linhas.append("")

    topicos = grade_disciplina.get(
        "topicos",
        {}
    )

    for topico, dados_topico in topicos.items():

        linhas.append("━━━━━━━━━━━━━━━━━━━━")

        linhas.append(
            f"🧠 TÓPICO: {topico}"
        )

        assuntos = dados_topico.get(
            "assuntos",
            {}
        )

        for assunto, quantidade in assuntos.items():

            quantidade = int(quantidade)

            blocos_previstos = math.ceil(
                quantidade / 10
            )

            total_blocos_previstos += blocos_previstos

            linhas.append("")

            linhas.append(
                f"📁 Assunto: {assunto}"
            )

            for bloco in range(
                1,
                blocos_previstos + 1
            ):

                chave = (
                    topico,
                    assunto,
                    bloco
                )

                tentativas = agrupados.get(
                    chave,
                    []
                )

                if not tentativas:

                    linhas.append(
                        f"• Bloco {bloco}: ⏳ Pendente"
                    )

                    continue

                # Última tentativa salva.
                ultima = max(
                    tentativas,
                    key=chave_data_desempenho
                )

                total = int(
                    ultima.get("total", 0)
                )

                acertos = int(
                    ultima.get("acertos", 0)
                )

                erros = int(
                    ultima.get("erros", 0)
                )

                aproveitamento = float(
                    ultima.get(
                        "aproveitamento",
                        (acertos / total * 100)
                        if total else 0
                    )
                )

                data = formatar_data_desempenho(
                    ultima.get("data_conclusao")
                )

                linhas.append(
                    f"• Bloco {bloco}: "
                    f"✅ {aproveitamento:.2f}% acertos"
                )

                linhas.append(
                    f"  ({data}) | "
                    f"{acertos} acertos | "
                    f"{erros} erros"
                )

                if len(tentativas) > 1:

                    linhas.append(
                        f"  🔄 {len(tentativas)} tentativas registradas"
                    )

                total_blocos_concluidos += 1

                total_questoes += total

                total_acertos += acertos

    # ========================================================
    # RESUMO DA DISCIPLINA
    # ========================================================

    blocos_faltando = max(
        0,
        total_blocos_previstos - total_blocos_concluidos
    )

    media = (
        total_acertos / total_questoes * 100
        if total_questoes else 0
    )

    linhas.append("")
    linhas.append("━━━━━━━━━━━━━━━━━━━━")
    linhas.append("")

    linhas.append("📊 RESUMO DA DISCIPLINA")

    linhas.append(
        f"• Média geral de acertos: {media:.2f}%"
    )

    linhas.append(
        f"• Questões respondidas: {total_questoes}"
    )

    linhas.append(
        f"• Blocos concluídos: {total_blocos_concluidos}"
    )

    linhas.append(
        f"• Total de blocos faltando: {blocos_faltando}"
    )

    return "\n".join(linhas)


# ============================================================
# VISUALIZAR DESEMPENHO DA DISCIPLINA
# ============================================================

async def selecionar_disciplina_desempenho(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    consulta = update.callback_query

    await consulta.answer()

    usuario = context.user_data.get("usuario")

    if not usuario:

        await consulta.edit_message_text(
            "🔒 Sessão expirada. Digite /start."
        )

        return

    try:
        indice = int(
            consulta.data.split(":")[1]
        )

    except (ValueError, IndexError):

        await consulta.answer(
            "Opção inválida.",
            show_alert=True
        )

        return

    disciplinas = context.user_data.get(
        "disciplinas_painel",
        []
    )

    if indice < 0 or indice >= len(disciplinas):

        await consulta.answer(
            "Disciplina inválida.",
            show_alert=True
        )

        return

    disciplina = disciplinas[indice]
    context.user_data["disciplina_painel_atual"] = disciplina
    login_user = usuario.get("login")

    grade = repositorio.obter_grade_questoes(
        login_user
    )

    registros = repositorio.obter_desempenho_disciplina(
        login_user,
        disciplina
    )

    grade_disciplina = (
        grade.get("disciplinas", {}).get(
            disciplina,
            {}
        )
        if grade else {}
    )

    texto = gerar_relatorio_disciplina(
        disciplina,
        grade_disciplina,
        registros
    )

    teclado = InlineKeyboardMarkup([
    [
        InlineKeyboardButton(
            "🗑️ Gerenciar histórico",
            callback_data="painel_exclusao_menu"
        )
    ],
    [
        InlineKeyboardButton(
            "⬅️ Voltar para Disciplinas",
            callback_data="painel_voltar_disciplinas"
        )
    ],
    [
        InlineKeyboardButton(
            "🏠 Início",
            callback_data="inicio"
        )
    ]
])

    partes = dividir_mensagem(texto)

    # A primeira parte substitui a tela anterior.
    await consulta.edit_message_text(
        partes[0]
    )

    # Demais partes são enviadas em novas mensagens.
    for indice_parte, parte in enumerate(partes[1:]):

        await consulta.message.reply_text(
            parte,
            reply_markup=(
                teclado
                if indice_parte == len(partes[1:]) - 1
                else None
            )
        )

    # Se o relatório couber em uma mensagem,
    # os botões ficam na própria mensagem editada.
    if len(partes) == 1:

        await consulta.edit_message_reply_markup(
            reply_markup=teclado
        )


# ============================================================
# VOLTAR À SELEÇÃO DE DISCIPLINAS DO PAINEL
# ============================================================

async def voltar_disciplinas_painel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    consulta = update.callback_query

    await consulta.answer()

    usuario = context.user_data.get("usuario")

    if not usuario:

        await consulta.edit_message_text(
            "🔒 Sessão expirada. Digite /start."
        )

        return

    disciplinas = repositorio.listar_disciplinas_desempenho(
        usuario.get("login")
    )

    if not disciplinas:

        await consulta.edit_message_text(
            "Você ainda não possui desempenhos salvos.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🏠 Início",
                        callback_data="inicio"
                    )
                ]
            ])
        )

        return

    context.user_data["disciplinas_painel"] = disciplinas

    await consulta.edit_message_text(
        "📊 PAINEL DE DESEMPENHO\n\n"
        "Escolha qual disciplina deseja analisar:",
        reply_markup=montar_teclado_painel(
            disciplinas
        )
    )

# ============================================================
# MENU DE GERENCIAMENTO DO HISTÓRICO
# ============================================================

async def abrir_menu_exclusao_historico(update, context):

    consulta = update.callback_query
    await consulta.answer()

    usuario = context.user_data.get("usuario", {})
    login_user = usuario.get("login")
    disciplina = context.user_data.get("disciplina_painel_atual")

    if not login_user or not disciplina:
        await consulta.answer(
            "Sessão ou disciplina não identificada.",
            show_alert=True
        )
        return

    quantidade = repositorio.contar_historico_desempenho(
        login_user,
        disciplina
    )

    if quantidade == 0:
        await consulta.edit_message_text(
            "🗑️ GERENCIAR HISTÓRICO\n\n"
            "Não existem registros de desempenho "
            "para excluir nesta disciplina.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "⬅️ Voltar ao relatório",
                        callback_data="painel_exclusao_cancelar"
                    )
                ]
            ])
        )
        return

    teclado = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🗑️ Excluir disciplina inteira",
                callback_data="excluir_hist:disciplina"
            )
        ],
        [
            InlineKeyboardButton(
                "📁 Excluir um tópico",
                callback_data="excluir_hist:topico"
            )
        ],
        [
            InlineKeyboardButton(
                "📄 Excluir um assunto",
                callback_data="excluir_hist:assunto"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Voltar ao relatório",
                callback_data="painel_exclusao_cancelar"
            )
        ]
    ])

    await consulta.edit_message_text(
        "🗑️ GERENCIAR HISTÓRICO\n\n"
        f"📚 Disciplina: {disciplina}\n"
        f"📊 Registros encontrados: {quantidade}\n\n"
        "Escolha o nível de exclusão:\n\n"
        "• Disciplina: exclui todos os tópicos e assuntos.\n"
        "• Tópico: exclui todos os assuntos daquele tópico.\n"
        "• Assunto: exclui somente os blocos daquele assunto.",
        reply_markup=teclado
    )


# ============================================================
# SELECIONAR NÍVEL DE EXCLUSÃO
# ============================================================

async def selecionar_nivel_exclusao(update, context):

    consulta = update.callback_query
    await consulta.answer()

    usuario = context.user_data.get("usuario", {})
    login_user = usuario.get("login")
    disciplina = context.user_data.get("disciplina_painel_atual")

    if not login_user or not disciplina:
        await consulta.answer(
            "Sessão não identificada.",
            show_alert=True
        )
        return

    nivel = consulta.data.split(":")[1]

    # --------------------------------------------------------
    # EXCLUSÃO DA DISCIPLINA
    # --------------------------------------------------------

    if nivel == "disciplina":

        quantidade = repositorio.contar_historico_desempenho(
            login_user,
            disciplina
        )

        if quantidade == 0:
            await consulta.edit_message_text(
                "Não existe histórico nesta disciplina."
            )
            return

        context.user_data["exclusao_desempenho"] = {
            "nivel": "disciplina",
            "disciplina": disciplina,
            "topico": None,
            "assunto": None,
            "quantidade": quantidade
        }

        await mostrar_confirmacao_exclusao(
            consulta.message,
            context
        )

        return

    # --------------------------------------------------------
    # SELEÇÃO DE TÓPICO
    # --------------------------------------------------------

    if nivel == "topico":

        topicos = repositorio.listar_topicos_desempenho(
            login_user,
            disciplina
        )

        if not topicos:
            await consulta.edit_message_text(
                "Não existem tópicos com histórico registrado."
            )
            return

        context.user_data["opcoes_exclusao"] = topicos

        botoes = []

        for i, topico in enumerate(topicos):
            botoes.append([
                InlineKeyboardButton(
                    f"📁 {topico}",
                    callback_data=f"excluir_topico:{i}"
                )
            ])

        botoes.append([
            InlineKeyboardButton(
                "⬅️ Voltar",
                callback_data="painel_exclusao_menu"
            )
        ])

        await consulta.edit_message_text(
            "🗑️ EXCLUIR HISTÓRICO POR TÓPICO\n\n"
            "Escolha o tópico:",
            reply_markup=InlineKeyboardMarkup(botoes)
        )

        return

    # --------------------------------------------------------
    # SELEÇÃO DE ASSUNTO
    # --------------------------------------------------------

    if nivel == "assunto":

        topicos = repositorio.listar_topicos_desempenho(
            login_user,
            disciplina
        )

        if not topicos:
            await consulta.edit_message_text(
                "Não existem tópicos com histórico registrado."
            )
            return

        context.user_data["opcoes_exclusao"] = topicos

        botoes = []

        for i, topico in enumerate(topicos):
            botoes.append([
                InlineKeyboardButton(
                    f"📁 {topico}",
                    callback_data=f"excluir_assunto_topico:{i}"
                )
            ])

        botoes.append([
            InlineKeyboardButton(
                "⬅️ Voltar",
                callback_data="painel_exclusao_menu"
            )
        ])

        await consulta.edit_message_text(
            "🗑️ EXCLUIR HISTÓRICO POR ASSUNTO\n\n"
            "Primeiro, escolha o tópico:",
            reply_markup=InlineKeyboardMarkup(botoes)
        )


# ============================================================
# SELECIONAR TÓPICO PARA EXCLUSÃO
# ============================================================

async def selecionar_topico_exclusao(update, context):

    consulta = update.callback_query
    await consulta.answer()

    usuario = context.user_data.get("usuario", {})
    login_user = usuario.get("login")
    disciplina = context.user_data.get("disciplina_painel_atual")

    try:
        indice = int(consulta.data.split(":")[1])
        topicos = context.user_data.get("opcoes_exclusao", [])
        topico = topicos[indice]
    except (ValueError, IndexError):
        await consulta.answer("Tópico inválido.", show_alert=True)
        return

    quantidade = repositorio.contar_historico_desempenho(
        login_user,
        disciplina,
        topico
    )

    if quantidade == 0:
        await consulta.edit_message_text(
            "Este tópico não possui histórico registrado."
        )
        return

    context.user_data["exclusao_desempenho"] = {
        "nivel": "topico",
        "disciplina": disciplina,
        "topico": topico,
        "assunto": None,
        "quantidade": quantidade
    }

    await mostrar_confirmacao_exclusao(
        consulta.message,
        context
    )


# ============================================================
# SELECIONAR TÓPICO PARA LISTAR ASSUNTOS
# ============================================================

async def selecionar_topico_assunto_exclusao(update, context):

    consulta = update.callback_query
    await consulta.answer()

    usuario = context.user_data.get("usuario", {})
    login_user = usuario.get("login")
    disciplina = context.user_data.get("disciplina_painel_atual")

    try:
        indice = int(consulta.data.split(":")[1])
        topicos = context.user_data.get("opcoes_exclusao", [])
        topico = topicos[indice]
    except (ValueError, IndexError):
        await consulta.answer("Tópico inválido.", show_alert=True)
        return

    assuntos = repositorio.listar_assuntos_desempenho(
        login_user,
        disciplina,
        topico
    )

    if not assuntos:
        await consulta.edit_message_text(
            "Não existem assuntos com histórico neste tópico."
        )
        return

    context.user_data["topico_exclusao_atual"] = topico
    context.user_data["opcoes_exclusao"] = assuntos

    botoes = []

    for i, assunto in enumerate(assuntos):
        botoes.append([
            InlineKeyboardButton(
                f"📄 {assunto}",
                callback_data=f"excluir_assunto:{i}"
            )
        ])

    botoes.append([
        InlineKeyboardButton(
            "⬅️ Voltar aos tópicos",
            callback_data="excluir_hist:assunto"
        )
    ])

    await consulta.edit_message_text(
        f"🗑️ EXCLUIR HISTÓRICO POR ASSUNTO\n\n"
        f"📁 Tópico: {topico}\n\n"
        "Escolha o assunto:",
        reply_markup=InlineKeyboardMarkup(botoes)
    )


# ============================================================
# SELECIONAR ASSUNTO PARA EXCLUSÃO
# ============================================================

async def selecionar_assunto_exclusao(update, context):

    consulta = update.callback_query
    await consulta.answer()

    usuario = context.user_data.get("usuario", {})
    login_user = usuario.get("login")
    disciplina = context.user_data.get("disciplina_painel_atual")
    topico = context.user_data.get("topico_exclusao_atual")

    try:
        indice = int(consulta.data.split(":")[1])
        assuntos = context.user_data.get("opcoes_exclusao", [])
        assunto = assuntos[indice]
    except (ValueError, IndexError):
        await consulta.answer("Assunto inválido.", show_alert=True)
        return

    quantidade = repositorio.contar_historico_desempenho(
        login_user,
        disciplina,
        topico,
        assunto
    )

    if quantidade == 0:
        await consulta.edit_message_text(
            "Este assunto não possui histórico registrado."
        )
        return

    context.user_data["exclusao_desempenho"] = {
        "nivel": "assunto",
        "disciplina": disciplina,
        "topico": topico,
        "assunto": assunto,
        "quantidade": quantidade
    }

    await mostrar_confirmacao_exclusao(
        consulta.message,
        context
    )


# ============================================================
# CONFIRMAR EXCLUSÃO
# ============================================================

async def mostrar_confirmacao_exclusao(mensagem, context):

    dados = context.user_data.get(
        "exclusao_desempenho"
    )

    if not dados:
        await mensagem.reply_text(
            "Não foi possível identificar a exclusão solicitada."
        )
        return

    nivel = dados["nivel"]

    if nivel == "disciplina":
        descricao = f"Disciplina: {dados['disciplina']}"

    elif nivel == "topico":
        descricao = (
            f"Disciplina: {dados['disciplina']}\n"
            f"Tópico: {dados['topico']}"
        )

    else:
        descricao = (
            f"Disciplina: {dados['disciplina']}\n"
            f"Tópico: {dados['topico']}\n"
            f"Assunto: {dados['assunto']}"
        )

    teclado = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🗑️ SIM, EXCLUIR",
                callback_data="confirmar_exclusao_desempenho"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ NÃO, CANCELAR",
                callback_data="painel_exclusao_cancelar"
            )
        ]
    ])

    await mensagem.reply_text(
        "⚠️ CONFIRMAR EXCLUSÃO DO HISTÓRICO\n\n"
        f"{descricao}\n\n"
        f"📊 Registros que serão excluídos: {dados['quantidade']}\n\n"
        "Esta ação é permanente e não poderá ser desfeita.\n\n"
        "Deseja realmente continuar?",
        reply_markup=teclado
    )


# ============================================================
# EXECUTAR EXCLUSÃO CONFIRMADA
# ============================================================

async def confirmar_exclusao_desempenho(update, context):

    consulta = update.callback_query
    await consulta.answer()

    usuario = context.user_data.get("usuario", {})
    login_user = usuario.get("login")

    dados = context.user_data.get(
        "exclusao_desempenho"
    )

    if not login_user or not dados:
        await consulta.edit_message_text(
            "Não foi possível identificar a operação. "
            "Abra novamente o Painel de Desempenho."
        )
        return

    disciplina = dados["disciplina"]
    nivel = dados["nivel"]

    try:

        # A quantidade é conferida novamente no banco.
        if nivel == "disciplina":

            excluidos = repositorio.excluir_historico_disciplina(
                login_user,
                disciplina
            )

        elif nivel == "topico":

            excluidos = repositorio.excluir_historico_topico(
                login_user,
                disciplina,
                dados["topico"]
            )

        elif nivel == "assunto":

            excluidos = repositorio.excluir_historico_assunto(
                login_user,
                disciplina,
                dados["topico"],
                dados["assunto"]
            )

        else:
            excluidos = 0

    except Exception:
        import logging
        logging.exception("Erro ao excluir histórico de desempenho")

        await consulta.edit_message_text(
            "❌ Ocorreu um erro ao excluir o histórico. "
            "Tente novamente mais tarde."
        )
        return

    context.user_data.pop(
        "exclusao_desempenho",
        None
    )

    if excluidos == 0:
        await consulta.edit_message_text(
            "ℹ️ Nenhum registro foi excluído. "
            "O histórico pode já ter sido removido."
        )
        return

    await consulta.edit_message_text(
        "✅ HISTÓRICO EXCLUÍDO COM SUCESSO!\n\n"
        f"📊 Registros excluídos: {excluidos}\n\n"
        "O painel será atualizado."
    )

    # Atualiza a lista de disciplinas que ainda possuem histórico.
    disciplinas = repositorio.listar_disciplinas_desempenho(
        login_user
    )

    context.user_data["disciplinas_painel"] = disciplinas

    if disciplina in disciplinas:

        registros = repositorio.obter_desempenho_disciplina(
            login_user,
            disciplina
        )

        grade = repositorio.obter_grade_questoes(
            login_user
        )

        grade_disciplina = (
            grade.get("disciplinas", {}).get(disciplina, {})
            if grade else {}
        )

        texto = gerar_relatorio_disciplina(
            disciplina,
            grade_disciplina,
            registros
        )

        teclado = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🗑️ Gerenciar histórico",
                    callback_data="painel_exclusao_menu"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Voltar para Disciplinas",
                    callback_data="painel_voltar_disciplinas"
                )
            ],
            [
                InlineKeyboardButton(
                    "🏠 Início",
                    callback_data="inicio"
                )
            ]
        ])

        for parte in dividir_mensagem(texto):
            await consulta.message.reply_text(
                parte,
                reply_markup=(
                    teclado
                    if parte == dividir_mensagem(texto)[-1]
                    else None
                )
            )

    else:

        await consulta.message.reply_text(
            "📊 Não existem mais registros nesta disciplina.",
            reply_markup=montar_teclado_painel(disciplinas)
            if disciplinas else InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🏠 Voltar ao Início",
                        callback_data="inicio"
                    )
                ]
            ])
        )


# ============================================================
# CANCELAR EXCLUSÃO
# ============================================================

async def cancelar_exclusao_desempenho(update, context):

    consulta = update.callback_query
    await consulta.answer()

    context.user_data.pop(
        "exclusao_desempenho",
        None
    )

    disciplina = context.user_data.get(
        "disciplina_painel_atual"
    )

    usuario = context.user_data.get("usuario", {})
    login_user = usuario.get("login")

    if not disciplina or not login_user:
        await consulta.edit_message_text(
            "Operação cancelada.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🏠 Início",
                        callback_data="inicio"
                    )
                ]
            ])
        )
        return

    registros = repositorio.obter_desempenho_disciplina(
        login_user,
        disciplina
    )

    grade = repositorio.obter_grade_questoes(login_user)

    grade_disciplina = (
        grade.get("disciplinas", {}).get(disciplina, {})
        if grade else {}
    )

    texto = gerar_relatorio_disciplina(
        disciplina,
        grade_disciplina,
        registros
    )

    teclado = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🗑️ Gerenciar histórico",
                callback_data="painel_exclusao_menu"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Voltar para Disciplinas",
                callback_data="painel_voltar_disciplinas"
            )
        ],
        [
            InlineKeyboardButton(
                "🏠 Início",
                callback_data="inicio"
            )
        ]
    ])

    await consulta.edit_message_text(
        texto,
        reply_markup=teclado
    )