from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update
)
from telegram.ext import ContextTypes

import repositorio
import questoes


def montar_teclado(opcoes, prefixo):
    botoes = []

    for i, opcao in enumerate(opcoes):
        botoes.append([
            InlineKeyboardButton(
                opcao,
                callback_data=f"{prefixo}:{i}"
            )
        ])

    botoes.append([
        InlineKeyboardButton(
            "⬅️ Voltar ao início",
            callback_data="inicio"
        )
    ])

    return InlineKeyboardMarkup(botoes)


async def iniciar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    disciplinas = repositorio.listar_disciplinas()

    if not disciplinas:
        await update.message.reply_text(
            "Nenhuma disciplina foi cadastrada."
        )
        return

    context.user_data["opcoes"] = disciplinas

    await update.message.reply_text(
        "📚 Escolha a área ou disciplina:",
        reply_markup=montar_teclado(disciplinas, "disciplina")
    )


async def selecionar_disciplina(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    consulta = update.callback_query
    await consulta.answer()

    indice = int(consulta.data.split(":")[1])
    disciplinas = context.user_data.get("opcoes", [])

    if indice >= len(disciplinas):
        await consulta.message.reply_text(
            "Opção inválida. Digite /start."
        )
        return

    disciplina = disciplinas[indice]
    context.user_data["disciplina"] = disciplina

    topicos = repositorio.listar_topicos(disciplina)

    if not topicos:
        await consulta.message.reply_text(
            "Não há disciplinas ou tópicos cadastrados nessa área."
        )
        return

    context.user_data["opcoes"] = topicos

    await consulta.message.reply_text(
        f"📚 {disciplina}\n\nEscolha uma disciplina ou tópico:",
        reply_markup=montar_teclado(topicos, "topico")
    )


async def selecionar_topico(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    consulta = update.callback_query
    await consulta.answer()

    indice = int(consulta.data.split(":")[1])
    topicos = context.user_data.get("opcoes", [])

    if indice >= len(topicos):
        await consulta.message.reply_text(
            "Opção inválida. Digite /start."
        )
        return

    topico = topicos[indice]
    disciplina = context.user_data["disciplina"]

    context.user_data["topico"] = topico

    assuntos = repositorio.listar_assuntos(
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
        f"📘 {topico}\n\nEscolha o assunto:",
        reply_markup=montar_teclado(assuntos, "assunto")
    )


async def selecionar_assunto(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    consulta = update.callback_query
    await consulta.answer()

    indice = int(consulta.data.split(":")[1])
    assuntos = context.user_data.get("opcoes", [])

    if indice >= len(assuntos):
        await consulta.message.reply_text(
            "Opção inválida. Digite /start."
        )
        return

    assunto = assuntos[indice]

    disciplina = context.user_data["disciplina"]
    topico = context.user_data["topico"]

    questoes_encontradas = repositorio.listar_questoes(
        disciplina,
        topico,
        assunto
    )

    if not questoes_encontradas:
        await consulta.message.reply_text(
            "Não existem questões cadastradas para esse assunto."
        )
        return

    context.user_data["questoes"] = questoes_encontradas
    context.user_data["indice_questao"] = 0

    await questoes.exibir_questao(
        consulta.message,
        context
    )


async def voltar_inicio(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    consulta = update.callback_query
    await consulta.answer()

    disciplinas = repositorio.listar_disciplinas()
    context.user_data["opcoes"] = disciplinas

    await consulta.message.reply_text(
        "📚 Escolha a área ou disciplina:",
        reply_markup=montar_teclado(disciplinas, "disciplina")
    )