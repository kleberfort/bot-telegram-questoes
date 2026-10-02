
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup
)


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
            f"🎯 Aproveitamento: {porcentagem:.2f}%\n"
        )

        questoes_erradas = desempenho.get("questoes_erradas", [])

        if questoes_erradas:
            texto += "\n❌ QUESTÕES QUE VOCÊ ERROU:\n\n"

            for item in questoes_erradas:
                texto += (
                    f"Questão {item['numero']}\n"
                    f"{item['enunciado']}\n"
                    f"Você marcou: {item['marcada']}\n"
                    f"Gabarito: {item['gabarito']}\n\n"
                )
        else:
            texto += "\n🏆 Parabéns! Você não errou nenhuma questão."

        await mensagem.reply_text(texto)
        return

    questao = questoes[indice]
    alternativas = questao.get("alternativas", {})

    texto = (
        f"📚 {questao.get('assunto', '')}\n\n"
        f"🧠 {indice + 1}ª questão\n\n"
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
            "numero": indice + 1,
            "assunto": questao.get("assunto", ""),
            "enunciado": questao.get("enunciado", ""),
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

    if not context.user_data.get("respondida"):
        await consulta.answer(
            "Responda à questão antes de avançar.",
            show_alert=True
        )
        return

    await consulta.answer()

    context.user_data["indice_questao"] += 1
    context.user_data["respondida"] = False

    await exibir_questao(
        consulta.message,
        context
    )