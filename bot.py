
import os
import logging
from dotenv import load_dotenv
from pymongo import MongoClient
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# ============================================================
# CONFIGURAÇÕES
# ============================================================

load_dotenv()

TOKEN = os.getenv("TOKEN")
MONGODB_URI = os.getenv("MONGODB_URI")

if not TOKEN:
    raise ValueError("TOKEN não encontrado no arquivo .env")

if not MONGODB_URI:
    raise ValueError("MONGODB_URI não encontrada no arquivo .env")

cliente = MongoClient(MONGODB_URI)
db = cliente["questoes_concurso"]
colecao = db["questoes"]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def criar_teclado(opcoes, prefixo):
    botoes = []

    for i, opcao in enumerate(opcoes):
        botoes.append([
            InlineKeyboardButton(
                opcao,
                callback_data=f"{prefixo}:{i}"
            )
        ])

    return InlineKeyboardMarkup(botoes)


def obter_lista_distinta(campo, filtro=None):
    filtro = filtro or {}

    valores = colecao.distinct(campo, filtro)

    return sorted(
        [valor for valor in valores if valor],
        key=str.casefold
    )


async def mostrar_menu(
    consulta,
    context,
    titulo,
    opcoes,
    tipo
):
    if not opcoes:
        await consulta.message.reply_text(
            "Não há opções cadastradas nesta etapa."
        )
        return

    # Guarda as opções para recuperar pelo índice do botão
    context.user_data[f"opcoes_{tipo}"] = opcoes

    teclado = criar_teclado(opcoes, tipo)

    await consulta.message.reply_text(
        titulo,
        reply_markup=teclado
    )


# ============================================================
# MENU PRINCIPAL
# ============================================================

async def iniciar(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    disciplinas = obter_lista_distinta("disciplina")

    botoes = []

    for i, disciplina in enumerate(disciplinas):
        botoes.append([
            InlineKeyboardButton(
                disciplina,
                callback_data=f"disc:{i}"
            )
        ])

    if not botoes:
        await update.message.reply_text(
            "Ainda não existem disciplinas cadastradas."
        )
        return

    context.user_data["opcoes_disc"] = disciplinas

    await update.message.reply_text(
        "📚 QUESTÕES CONCURSO\n\n"
        "Escolha uma disciplina:",
        reply_markup=InlineKeyboardMarkup(botoes)
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

    indice = int(consulta.data.split(":")[1])
    disciplinas = context.user_data.get("opcoes_disc", [])

    if indice >= len(disciplinas):
        await consulta.message.reply_text(
            "Menu desatualizado. Digite /start."
        )
        return

    disciplina = disciplinas[indice]
    context.user_data["disciplina"] = disciplina

    topicos = obter_lista_distinta(
        "topico",
        {"disciplina": disciplina}
    )

    await mostrar_menu(
        consulta,
        context,
        f"📚 {disciplina}\n\nEscolha um tópico:",
        topicos,
        "top"
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

    indice = int(consulta.data.split(":")[1])
    topicos = context.user_data.get("opcoes_top", [])

    if indice >= len(topicos):
        await consulta.message.reply_text(
            "Menu desatualizado. Digite /start."
        )
        return

    topico = topicos[indice]
    disciplina = context.user_data["disciplina"]

    context.user_data["topico"] = topico

    assuntos = obter_lista_distinta(
        "assunto",
        {
            "disciplina": disciplina,
            "topico": topico
        }
    )

    await mostrar_menu(
        consulta,
        context,
        f"🧠 {topico}\n\nEscolha um assunto:",
        assuntos,
        "ass"
    )


# ============================================================
# SELECIONAR ASSUNTO E CARREGAR QUESTÕES
# ============================================================

async def selecionar_assunto(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    consulta = update.callback_query
    await consulta.answer()

    indice = int(consulta.data.split(":")[1])
    assuntos = context.user_data.get("opcoes_ass", [])

    if indice >= len(assuntos):
        await consulta.message.reply_text(
            "Menu desatualizado. Digite /start."
        )
        return

    assunto = assuntos[indice]

    filtro = {
        "disciplina": context.user_data["disciplina"],
        "topico": context.user_data["topico"],
        "assunto": assunto
    }

    questoes = list(colecao.find(filtro))

    if not questoes:
        await consulta.message.reply_text(
            "Não há questões cadastradas para esse assunto."
        )
        return

    context.user_data["questoes"] = questoes
    context.user_data["indice_questao"] = 0
    context.user_data["assunto"] = assunto

    await enviar_questao(consulta.message, context)


# ============================================================
# ENVIAR QUESTÃO
# ============================================================

async def enviar_questao(mensagem, context):
    questoes = context.user_data.get("questoes", [])
    indice = context.user_data.get("indice_questao", 0)

    if indice >= len(questoes):
        await mensagem.reply_text(
            "🎉 Você chegou ao final das questões!"
        )
        return

    questao = questoes[indice]

    alternativas = questao.get("alternativas", {})
    letras = list(alternativas.keys())

    texto = (
        f"🧠 QUESTÃO {indice + 1}\n\n"
        f"{questao.get('enunciado', 'Enunciado não informado')}\n\n"
    )

    for letra in letras:
        texto += f"{letra}) {alternativas[letra]}\n\n"

    texto += "👇 Escolha uma alternativa:"

    botoes = []

    for letra in letras:
        botoes.append(
            InlineKeyboardButton(
                letra,
                callback_data=f"resp:{letra}"
            )
        )

    linhas = [
        botoes[i:i + 2]
        for i in range(0, len(botoes), 2)
    ]

    await mensagem.reply_text(
        texto,
        reply_markup=InlineKeyboardMarkup(linhas)
    )


# ============================================================
# CORRIGIR RESPOSTA
# ============================================================

async def resposta(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    consulta = update.callback_query
    await consulta.answer()

    letra = consulta.data.split(":")[1]

    questoes = context.user_data.get("questoes", [])
    indice = context.user_data.get("indice_questao", 0)

    if indice >= len(questoes):
        await consulta.message.reply_text(
            "Questão não encontrada. Digite /start."
        )
        return

    questao = questoes[indice]
    gabarito = questao.get("resposta", "").upper()
    comentario = questao.get("comentario", "")

    if letra == gabarito:
        resultado = "✅ CORRETO!"
    else:
        resultado = "❌ INCORRETO!"

    texto = (
        f"{resultado}\n\n"
        f"Você marcou: {letra}\n"
        f"🎯 Gabarito: {gabarito}\n\n"
        f"📖 EXPLICAÇÃO\n{comentario}"
    )

    teclado = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "➡️ PRÓXIMA QUESTÃO",
                callback_data="prox"
            )
        ],
        [
            InlineKeyboardButton(
                "📚 Voltar ao início",
                callback_data="inicio"
            )
        ]
    ])

    await consulta.message.reply_text(
        texto,
        reply_markup=teclado
    )


# ============================================================
# PRÓXIMA QUESTÃO
# ============================================================

async def proxima_questao(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    consulta = update.callback_query
    await consulta.answer()

    context.user_data["indice_questao"] = (
        context.user_data.get("indice_questao", 0) + 1
    )

    await enviar_questao(consulta.message, context)


# ============================================================
# VOLTAR AO MENU PRINCIPAL
# ============================================================

async def voltar_inicio(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    consulta = update.callback_query
    await consulta.answer()

    disciplinas = obter_lista_distinta("disciplina")
    context.user_data["opcoes_disc"] = disciplinas

    botoes = [
        [
            InlineKeyboardButton(
                disciplina,
                callback_data=f"disc:{i}"
            )
        ]
        for i, disciplina in enumerate(disciplinas)
    ]

    await consulta.message.reply_text(
        "📚 QUESTÕES CONCURSO\n\n"
        "Escolha uma disciplina:",
        reply_markup=InlineKeyboardMarkup(botoes)
    )


# ============================================================
# INICIAR APLICAÇÃO
# ============================================================

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", iniciar))

    app.add_handler(
        CallbackQueryHandler(
            selecionar_disciplina,
            pattern=r"^disc:\d+$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            selecionar_topico,
            pattern=r"^top:\d+$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            selecionar_assunto,
            pattern=r"^ass:\d+$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            resposta,
            pattern=r"^resp:[A-E]$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            proxima_questao,
            pattern=r"^prox$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            voltar_inicio,
            pattern=r"^inicio$"
        )
    )

    print("🤖 Bot iniciado e conectado ao MongoDB!")
    app.run_polling()


if __name__ == "__main__":
    main()