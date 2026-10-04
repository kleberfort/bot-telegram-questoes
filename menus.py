from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

import repositorio
import questoes
import usuarios


# ============================================================
# ESTADOS DO LOGIN
# ============================================================

SOLICITAR_LOGIN, SOLICITAR_SENHA = range(2)


# ============================================================
# MONTAR TECLADO
# ============================================================

def montar_teclado(opcoes, prefixo):
    botoes = []

    # 2 opções por linha
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

    # Botão voltar ao início
    botoes.append([
        InlineKeyboardButton(
            "⬅️ Voltar ao início",
            callback_data="inicio"
        )
    ])

    return InlineKeyboardMarkup(botoes)


# ============================================================
# /START
# ============================================================

async def iniciar(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id

    # Procura usuário pelo Telegram ID
    usuario_logado = usuarios.buscar_por_telegram(user_id)

    if usuario_logado:

        # Limpa dados anteriores da navegação
        limpar_dados_sessao(context)

        # Mantém o usuário logado
        context.user_data["usuario"] = usuario_logado

        # Recupera o login
        login_user = usuario_logado.get("login")

        # Busca somente as áreas desse usuário
        disciplinas = repositorio.listar_disciplinas(login_user)

        if not disciplinas:
            await update.message.reply_text(
                "Nenhuma área foi cadastrada para este usuário."
            )
            return ConversationHandler.END

        context.user_data["opcoes"] = disciplinas

        await update.message.reply_text(
            f"Olá, {usuario_logado['nome']}! "
            f"Seja bem-vindo de volta. 👋\n\n"
            "📚 Escolha a área:",
            reply_markup=montar_teclado(
                disciplinas,
                "disciplina"
            )
        )

        return ConversationHandler.END

    else:

        await update.message.reply_text(
            "🔒 Este Telegram ainda não está vinculado "
            "a uma conta do sistema.\n\n"
            "Por favor, digite o seu login:"
        )

        return SOLICITAR_LOGIN


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
    user_id = update.message.from_user.id

    # Tenta autenticar
    usuario = usuarios.autenticar(login, senha)

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

    # Vincula Telegram ao usuário
    usuarios.vincular_telegram(
        login,
        user_id
    )

    # Guarda usuário na sessão
    context.user_data["usuario"] = usuario

    context.user_data.pop(
        "temp_login",
        None
    )

    await update.message.reply_text(
        f"✅ Autenticação realizada com sucesso!\n\n"
        f"Bem-vindo, {usuario['nome']}."
    )

    # Busca áreas desse usuário
    disciplinas = repositorio.listar_disciplinas(login)

    if not disciplinas:

        await update.message.reply_text(
            "Nenhuma área foi cadastrada para este usuário."
        )

        return ConversationHandler.END

    context.user_data["opcoes"] = disciplinas

    await update.message.reply_text(
        "📚 Escolha a área:",
        reply_markup=montar_teclado(
            disciplinas,
            "disciplina"
        )
    )

    return ConversationHandler.END


# ============================================================
# LIMPAR SESSÃO
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
        "total_questoes_assunto"
    ]

    for chave in chaves:
        context.user_data.pop(
            chave,
            None
        )


# ============================================================
# SELECIONAR ÁREA
# ============================================================

async def selecionar_disciplina(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    consulta = update.callback_query

    await consulta.answer()

    indice = int(
        consulta.data.split(":")[1]
    )

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

    # Recupera usuário
    usuario = context.user_data.get(
        "usuario",
        {}
    )

    login_user = usuario.get("login")

    # Busca tópicos daquele usuário
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
        "Escolha uma disciplina:",
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

    indice = int(
        consulta.data.split(":")[1]
    )

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

    disciplina = context.user_data[
        "disciplina"
    ]

    context.user_data["topico"] = topico

    # Recupera usuário
    usuario = context.user_data.get(
        "usuario",
        {}
    )

    login_user = usuario.get("login")

    # Busca assuntos
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

    indice = int(
        consulta.data.split(":")[1]
    )

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

    disciplina = context.user_data[
        "disciplina"
    ]

    topico = context.user_data[
        "topico"
    ]

    # Recupera usuário
    usuario = context.user_data.get(
        "usuario",
        {}
    )

    login_user = usuario.get("login")

    # Busca questões somente desse usuário
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

    context.user_data[
        "todas_questoes"
    ] = questoes_encontradas

    context.user_data[
        "assunto"
    ] = assunto

    total = len(
        questoes_encontradas
    )

    tamanho_bloco = 10

    quantidade_blocos = (
        total + tamanho_bloco - 1
    ) // tamanho_bloco

    botoes = []

    for bloco in range(
        1,
        quantidade_blocos + 1
    ):

        inicio = (
            bloco - 1
        ) * tamanho_bloco + 1

        fim = min(
            bloco * tamanho_bloco,
            total
        )

        botoes.append([
            InlineKeyboardButton(
                f"Bloco {bloco} — "
                f"Questões {inicio} a {fim}",
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
        reply_markup=InlineKeyboardMarkup(
            botoes
        )
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

    bloco = int(
        consulta.data.split(":")[1]
    )

    todas_questoes = context.user_data.get(
        "todas_questoes",
        []
    )

    if not todas_questoes:

        await consulta.message.reply_text(
            "Questões não encontradas. "
            "Digite /start."
        )

        return

    tamanho_bloco = 10

    inicio = (
        bloco - 1
    ) * tamanho_bloco

    fim = inicio + tamanho_bloco

    questoes_bloco = todas_questoes[
        inicio:fim
    ]

    if not questoes_bloco:

        await consulta.message.reply_text(
            "Bloco não encontrado."
        )

        return

    context.user_data[
        "questoes"
    ] = questoes_bloco

    context.user_data[
        "indice_questao"
    ] = 0

    context.user_data[
        "inicio_bloco"
    ] = inicio

    context.user_data[
        "total_questoes_assunto"
    ] = len(todas_questoes)

    context.user_data[
        "respondida"
    ] = False

    questoes.iniciar_desempenho(
        context
    )

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

    # ========================================================
    # 1. PRESERVA O USUÁRIO LOGADO
    # ========================================================

    usuario = context.user_data.get(
        "usuario"
    )

    # ========================================================
    # 2. LIMPA A NAVEGAÇÃO
    # ========================================================

    limpar_dados_sessao(
        context
    )

    # Mantém o usuário logado
    context.user_data[
        "usuario"
    ] = usuario

    # ========================================================
    # 3. RECUPERA O LOGIN
    # ========================================================

    login_user = (
        usuario.get("login")
        if usuario
        else None
    )

    # ========================================================
    # 4. BUSCA NOVAMENTE AS ÁREAS
    # ========================================================

    disciplinas = repositorio.listar_disciplinas(
        login_user
    )

    if not disciplinas:

        await consulta.message.reply_text(
            "Nenhuma área foi cadastrada "
            "para este usuário."
        )

        return

    # Guarda as áreas atuais
    context.user_data[
        "opcoes"
    ] = disciplinas

    # ========================================================
    # 5. MOSTRA O MENU INICIAL
    # ========================================================

    nome = (
        usuario.get("nome", "usuário")
        if usuario
        else "usuário"
    )

    await consulta.message.reply_text(
        f"👋 {nome}\n\n"
        "📚 Escolha a área:",
        reply_markup=montar_teclado(
            disciplinas,
            "disciplina"
        )
    )