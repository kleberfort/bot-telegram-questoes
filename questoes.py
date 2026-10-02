from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup
)


async def exibir_questao(mensagem, context):
    questoes = context.user_data.get("questoes", [])
    indice = context.user_data.get("indice_questao", 0)

    if indice >= len(questoes):
        await mensagem.reply_text(
            "🎉 Você chegou ao final das questões!"
        )
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

    # Verifica se a questão já foi respondida
    if context.user_data.get("respondida"):
        await consulta.answer(
            "Você já respondeu está questão.",
            show_alert=True
        )
        return

    # Confirma o clique ao Telegram 
    await consulta.answer()

    # Recupera a alternativa escolhida 
    alternativa = consulta.data.split(":")[1] 

    # Recupera as questões e o índice atual 
    questoes = context.user_data.get("questoes", []) 
    indice = context.user_data.get("indice_questao", 0)

    # Verifica se existe uma questão 
    if indice >= len(questoes): 
        await consulta.message.reply_text( 
            "Questão não encontrada. Digite /start." 
        ) 
        return
# Recupera os dados da questão
    questao = questoes[indice]
    gabarito = questao.get("resposta", "").upper()
    comentario = questao.get("comentario", "")

# Marca a questão como respondida 
    context.user_data["respondida"] = True

# Verifica a resposta 
    if alternativa == gabarito: 
        resultado = "✅ CORRETO!" 
    else: 
        resultado = "❌ INCORRETO!"

# Monta a mensagem 
    texto = ( 
        f"{resultado}\n\n" 
        f"Você marcou: {alternativa}\n" 
        f"Gabarito: {gabarito}\n\n" 
        f"📖 COMENTÁRIO\n\n{comentario}" 
    )


# Cria os botões 
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


# Envia o resultado 
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