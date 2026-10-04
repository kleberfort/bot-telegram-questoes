
from opentelemetry import context
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

import time


def resumir_enunciado(enunciado, limite=400):
    """
    Retorna apenas o início do enunciado,
    evitando exibir o texto completo.
    """
    if not enunciado:
        return ""

    # Mantém somente o primeiro parágrafo
    resumo = enunciado.strip().split("\n\n")[0].strip()

    # Evita resumos muito longos
    if len(resumo) > limite:
        resumo = resumo[:limite].rsplit(" ", 1)[0] + "..."

    return resumo

def iniciar_desempenho(context):
    """Reinicia os dados de desempenho de um novo questionário."""
    context.user_data["desempenho"] = {
        "total": 0,
        "acertos": 0,
        "erros": 0,
        "questoes_erradas": []
    }


async def exibir_questao(mensagem, context):
    questoes = context.user_data.get("questoes", [])
    indice = context.user_data.get("indice_questao", 0)

    if indice >= len(questoes):
        desempenho = context.user_data.get("desempenho", {})

        # Calcula o tempo total do bloco
    inicio_bloco = context.user_data.get("inicio_tempo_bloco")

    if inicio_bloco is not None:
        tempo_total = time.monotonic() - inicio_bloco
    else:
        tempo_total = 0

    minutos = int(tempo_total // 60)
    segundos = int(tempo_total % 60)

    if minutos > 0:
        tempo_bloco = f"{minutos} min e {segundos} s"
    else:
        tempo_bloco = f"{segundos} s"

        total = desempenho.get("total", 0)
        acertos = desempenho.get("acertos", 0)
        erros = desempenho.get("erros", 0)

        porcentagem = (acertos / total * 100) if total > 0 else 0

        texto = (
        "🎉 QUESTIONÁRIO FINALIZADO!\n\n"
        f"📚 Conteúdo: {context.user_data.get('assunto', 'Geral')}\n\n"
        f"📝 Questões respondidas: {total}\n"
        f"✅ Acertos: {acertos}\n"
        f"❌ Erros: {erros}\n"
        f"🎯 Aproveitamento: {porcentagem:.2f}%\n\n"
        f"⏱️ Tempo total do bloco: {tempo_bloco}\n"
)

        # Envia o resumo separadamente
        await mensagem.reply_text(texto)

        questoes_erradas = desempenho.get("questoes_erradas", [])

        if questoes_erradas:
            await mensagem.reply_text(
                "❌ QUESTÕES QUE VOCÊ ERROU:"
            )

            for item in questoes_erradas:
                texto_erro = (
                    f"Questão {item['numero']}\n\n"
                    f"{item['enunciado']}\n\n"
                    f"Você marcou: {item['marcada']}\n"
                    f"Gabarito: {item['gabarito']}"
                )

                # Divide textos muito grandes em blocos
                limite = 3500

                for inicio in range(0, len(texto_erro), limite):
                    parte = texto_erro[inicio:inicio + limite]
                    await mensagem.reply_text(parte)
        else:
            await mensagem.reply_text(
                "🏆 Parabéns! Você não errou nenhuma questão."
            )

        return

    questao = questoes[indice]
    alternativas = questao.get("alternativas", {})

    total_questoes = context.user_data.get(
    "total_questoes_assunto", len(questoes)
    )

    inicio_bloco = context.user_data.get("inicio_bloco", 0)

    numero_atual = inicio_bloco + indice + 1

    texto = (
    f"📚 {questao.get('assunto', '')}\n\n"
    f"🧠 Questão {numero_atual} de {total_questoes}\n\n"
    f"{questao.get('enunciado', '')}\n\n"
    )

    botoes = []

    for letra, alternativa in alternativas.items():
        texto += f"{letra}) {alternativa}\n\n"
        botoes.append([
            InlineKeyboardButton(
                letra,
                callback_data=f"responder:{letra}"
            )
        ])

    texto += "\n👇 Escolha uma alternativa:"

    await mensagem.reply_text(
        texto,
        reply_markup=InlineKeyboardMarkup(botoes)
    )


async def responder(update, context):
    consulta = update.callback_query

    if context.user_data.get("respondida"):
        await consulta.answer(
            "Você já respondeu esta questão.",
            show_alert=True
        )
        return

    await consulta.answer()

    # Remove os botões da questão respondida
    await consulta.edit_message_reply_markup(reply_markup=None)

    alternativa = consulta.data.split(":")[1].upper()
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

    desempenho = context.user_data.setdefault("desempenho", {
        "total": 0,
        "acertos": 0,
        "erros": 0,
        "questoes_erradas": []
    })

    context.user_data["respondida"] = True
    desempenho["total"] += 1

    if alternativa == gabarito:
        resultado = "✅ CORRETO!"
        desempenho["acertos"] += 1
    else:
        resultado = "❌ INCORRETO!"
        desempenho["erros"] += 1

        desempenho["questoes_erradas"].append({
        "numero": (
        context.user_data.get("inicio_bloco", 0)
        + indice + 1
    ),
        "assunto": questao.get("assunto", ""),
        "enunciado": resumir_enunciado(
        questao.get("enunciado", "")
    ),
        "marcada": alternativa,
        "gabarito": gabarito
    })

    texto = (
        f"{resultado}\n\n"
        f"Você marcou: {alternativa}\n"
        f"Gabarito: {gabarito}\n\n"
        f"📖 COMENTÁRIO\n\n{comentario}"
    )

    botoes = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "➡️ Próxima questão",
                callback_data="proxima"
            )
        ],
        [
            InlineKeyboardButton(
                "🏠 Voltar ao início",
                callback_data="inicio"
            )
        ]
    ])

    await consulta.message.reply_text(
        texto,
        reply_markup=botoes
    )

async def proxima(update, context):
    consulta = update.callback_query

    indice = context.user_data.get("indice_questao", 0)
    questoes = context.user_data.get("questoes", [])
    respondida = context.user_data.get("respondida", False)

    # Só exige resposta se ainda houver uma questão para responder
    if indice < len(questoes) and not respondida:
        await consulta.answer(
            "Responda à questão antes de avançar.",
            show_alert=True
        )
        return

    await consulta.answer()

    # Avança apenas se a questão atual foi respondida
    if indice < len(questoes) and respondida:
        context.user_data["indice_questao"] += 1
        context.user_data["respondida"] = False

    # Exibe a próxima questão ou o resumo final
    await exibir_questao(consulta.message, context)