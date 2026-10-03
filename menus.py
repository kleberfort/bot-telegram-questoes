
from opentelemetry import context
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

    # Coloca 2 opções por linha
    for i in range(0, len(opcoes), 2):
        linha = []

        linha.append(
            InlineKeyboardButton(
                opcoes[i],
                callback_data=f"{prefixo}:{i}"
            )
        )

        if i + 1 < len(opcoes):
            linha.append(
                InlineKeyboardButton(
                    opcoes[i + 1],
                    callback_data=f"{prefixo}:{i + 1}"
                )
            )

        botoes.append(linha)

    # Botão voltar
    botoes.append([
        InlineKeyboardButton(
            "⬅️ Voltar ao início",
            callback_data="inicio"
        )
    ])

    return InlineKeyboardMarkup(botoes)


async def iniciar(update, context):
    # Limpa os dados do questionário anterior
    context.user_data.pop("questoes", None)
    context.user_data.pop("indice_questao", None)
    context.user_data.pop("respondida", None)
    context.user_data.pop("desempenho", None)
    context.user_data.pop("assunto", None)
    context.user_data.pop("disciplina", None)
    context.user_data.pop("topico", None)
    context.user_data.pop("todas_questoes", None)
    context.user_data.pop("inicio_bloco", None)
    context.user_data.pop("total_questoes_assunto", None)

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

    if indice < 0 or indice >= len(disciplinas):
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

    if indice < 0 or indice >= len(topicos):
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

    if indice < 0 or indice >= len(assuntos):
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

    # Guarda todas as questões encontradas
    context.user_data["todas_questoes"] = questoes_encontradas
    context.user_data["assunto"] = assunto

    total = len(questoes_encontradas)
    tamanho_bloco = 10
    quantidade_blocos = (total + tamanho_bloco - 1) // tamanho_bloco

    botoes = []

    for bloco in range(1, quantidade_blocos + 1):
        inicio = (bloco - 1) * tamanho_bloco + 1
        fim = min(bloco * tamanho_bloco, total)

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



async def selecionar_bloco(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    consulta = update.callback_query
    await consulta.answer()

    bloco = int(consulta.data.split(":")[1])

    todas_questoes = context.user_data.get(
        "todas_questoes", []
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

    # Prepara o questionário selecionado
    context.user_data["questoes"] = questoes_bloco
    context.user_data["indice_questao"] = 0
    context.user_data["inicio_bloco"] = inicio
    context.user_data["total_questoes_assunto"] = len(
        todas_questoes
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

async def voltar_inicio(update, context):
    consulta = update.callback_query
    await consulta.answer()

    # Limpa os dados da navegação e do questionário
    context.user_data.pop("questoes", None)
    context.user_data.pop("indice_questao", None)
    context.user_data.pop("respondida", None)
    context.user_data.pop("desempenho", None)
    context.user_data.pop("assunto", None)
    context.user_data.pop("disciplina", None)
    context.user_data.pop("topico", None)
    context.user_data.pop("todas_questoes", None)
    context.user_data.pop("inicio_bloco", None)
    context.user_data.pop("total_questoes_assunto", None)

    disciplinas = repositorio.listar_disciplinas()

    if not disciplinas:
        await consulta.message.reply_text(
            "Nenhuma disciplina foi cadastrada."
        )
        return

    context.user_data["opcoes"] = disciplinas

    await consulta.message.reply_text(
        "📚 Escolha a área ou disciplina:",
        reply_markup=montar_teclado(disciplinas, "disciplina")
    )