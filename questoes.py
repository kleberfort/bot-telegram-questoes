from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler

from repositorio import (
    salvar_comentario_personalizado,
    obter_comentario_personalizado
)

AGUARDANDO_COMENTARIO = 1

# ============================================================
# RESUMIR ENUNCIADO
# ============================================================

def resumir_enunciado(enunciado, limite=400):
    """
    Retorna o início do enunciado para o resumo de erros.
    """

    if not enunciado:
        return ""

    resumo = enunciado.strip().split("\n\n")[0].strip()

    if len(resumo) > limite:
        resumo = resumo[:limite].rsplit(" ", 1)[0] + "..."

    return resumo


# ============================================================
# INICIAR DESEMPENHO
# ============================================================

def iniciar_desempenho(context):
    """Reinicia os dados de desempenho do questionário."""

    context.user_data["desempenho"] = {
        "total": 0,
        "acertos": 0,
        "erros": 0,
        "questoes_erradas": []
    }


# ============================================================
# MONTAR COMENTÁRIO DA QUESTÃO
# ============================================================



def montar_comentario(
    questao,
    alternativa_marcada,
    gabarito,
    comentario_personalizado=None
):
    partes = []

    analise = questao.get("analise_alternativas", {})
    comentario_original = questao.get("comentario", "")
    fixacao = questao.get("fixacao", "")

    # O comentário personalizado substitui somente o comentário principal.
    comentario = (
        comentario_personalizado
        if comentario_personalizado
        else comentario_original
    )

    if isinstance(analise, dict) and analise:
        if alternativa_marcada == gabarito:
            partes.append("💡 COMENTÁRIO DA QUESTÃO")
        else:
            partes.append(
                f"🎯 POR QUE A ALTERNATIVA {gabarito} "
                f"ESTÁ CORRETA?"
            )

        partes.append(
            comentario
            or "Não há comentário cadastrado para esta questão."
        )

        partes.append("📚 ANÁLISE DAS ALTERNATIVAS")

        alternativas = questao.get("alternativas", {})

        for letra, texto_alternativa in alternativas.items():
            dados = analise.get(letra, {})

            if letra == gabarito:
                simbolo, status = "🟢", "Correta"
            else:
                simbolo, status = "🔴", "Incorreta"

            explicacao = ""

            if isinstance(dados, dict):
                explicacao = dados.get("comentario", "")

            partes.append(
                f"{simbolo} {letra}) {status}\n"
                f"{explicacao or texto_alternativa}"
            )

        if fixacao:
            partes.append(
                f"🧠 FIXAÇÃO PARA A PROVA\n{fixacao}"
            )

        return "\n\n".join(partes)

    # Formato para questões sem análise individual das alternativas.
    partes.append("📖 COMENTÁRIO")

    partes.append(
        comentario
        or "Não há comentário cadastrado para esta questão."
    )

    if fixacao:
        partes.append(
            f"🧠 FIXAÇÃO PARA A PROVA\n{fixacao}"
        )

    return "\n\n".join(partes)



# ============================================================
# EXIBIR QUESTÃO
# ============================================================

async def exibir_questao(mensagem, context):
    lista_questoes = context.user_data.get("questoes", [])
    indice = context.user_data.get("indice_questao", 0)

    # Finaliza o questionário quando todas as questões do bloco
    # tiverem sido respondidas.
    if indice >= len(lista_questoes):
        desempenho = context.user_data.get("desempenho", {})

        total = desempenho.get("total", 0)
        acertos = desempenho.get("acertos", 0)
        erros = desempenho.get("erros", 0)
        porcentagem = acertos / total * 100 if total else 0

        texto = (
            "🎉 QUESTIONÁRIO FINALIZADO!\n\n"
            f"📚 Conteúdo: {context.user_data.get('assunto', 'Geral')}\n\n"
            f"📝 Questões respondidas: {total}\n"
            f"✅ Acertos: {acertos}\n"
            f"❌ Erros: {erros}\n"
            f"🎯 Aproveitamento: {porcentagem:.2f}%"
        )

        await mensagem.reply_text(texto)

        questoes_erradas = desempenho.get("questoes_erradas", [])

        if questoes_erradas:
            await mensagem.reply_text("❌ QUESTÕES QUE VOCÊ ERROU:")

            for item in questoes_erradas:
                texto_erro = (
                    f"Questão {item['numero']}\n\n"
                    f"{item['enunciado']}\n\n"
                    f"Você marcou: {item['marcada']}\n"
                    f"Gabarito: {item['gabarito']}"
                )

                # Evita mensagens muito longas no Telegram.
                limite = 3500
                for inicio in range(0, len(texto_erro), limite):
                    await mensagem.reply_text(
                        texto_erro[inicio:inicio + limite]
                    )
        else:
            await mensagem.reply_text(
                "🏆 Parabéns! Você não errou nenhuma questão."
            )

        return

    questao = lista_questoes[indice]
    alternativas = questao.get("alternativas", {})

    # Registra a questão e o usuário para a edição personalizada.
    usuario = context.user_data.get("usuario", {})
    login_user = usuario.get("login")

    context.user_data["questao_atual_id"] = str(questao["_id"])
    context.user_data["questao_login_user"] = login_user

    # O número é relativo ao bloco atual.
    texto = (
        f"📚 {questao.get('assunto', context.user_data.get('assunto', ''))}\n\n"
        f"🧠 Questão {indice + 1} de {len(lista_questoes)}\n\n"
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

    texto += "👇 Escolha uma alternativa:"

    await mensagem.reply_text(
        texto,
        reply_markup=InlineKeyboardMarkup(botoes)
    )


# ============================================================
# RESPONDER QUESTÃO
# ============================================================

async def responder(update, context):
    consulta = update.callback_query

    # Impede que a mesma questão seja respondida mais de uma vez.
    if context.user_data.get("respondida"):
        await consulta.answer(
            "Você já respondeu esta questão.",
            show_alert=True
        )
        return

    await consulta.answer()

    lista_questoes = context.user_data.get("questoes", [])
    indice = context.user_data.get("indice_questao", 0)

    if indice >= len(lista_questoes):
        await consulta.message.reply_text(
            "Questão não encontrada. Digite /start."
        )
        return

    questao = lista_questoes[indice]
    alternativa = consulta.data.split(":")[1].upper()
    alternativas = questao.get("alternativas", {})

    if alternativa not in alternativas:
        await consulta.answer(
            "Alternativa inválida.",
            show_alert=True
        )
        return

    gabarito = questao.get("resposta", "").upper()

    # Registra o usuário e a questão atual para a edição do comentário.
    usuario = context.user_data.get("usuario", {})
    login_user = usuario.get("login")

    context.user_data["questao_atual_id"] = str(questao["_id"])
    context.user_data["questao_login_user"] = login_user

    await consulta.edit_message_reply_markup(reply_markup=None)

    desempenho = context.user_data.setdefault(
        "desempenho",
        {
            "total": 0,
            "acertos": 0,
            "erros": 0,
            "questoes_erradas": []
        }
    )

    context.user_data["respondida"] = True
    desempenho["total"] += 1

    if alternativa == gabarito:
        resultado = "✅ RESPOSTA CORRETA!"
        desempenho["acertos"] += 1
    else:
        resultado = "❌ RESPOSTA INCORRETA!"
        desempenho["erros"] += 1

        desempenho["questoes_erradas"].append({
            "numero": indice + 1,
            "assunto": questao.get("assunto", ""),
            "enunciado": resumir_enunciado(
                questao.get("enunciado", "")
            ),
            "marcada": alternativa,
            "gabarito": gabarito
        })

    # Busca o comentário personalizado deste usuário para esta questão.
    comentario_personalizado = ""

    if login_user:
        try:
            comentario_personalizado = obter_comentario_personalizado(
                login_user,
                str(questao["_id"])
            )
        except Exception:
            import logging
            logging.exception(
                "Erro ao buscar comentário personalizado"
            )

    # O comentário personalizado altera somente o comentário principal.
    # A análise das alternativas e a fixação continuam sendo exibidas.
    comentario_formatado = montar_comentario(
        questao,
        alternativa,
        gabarito,
        comentario_personalizado=comentario_personalizado
    )

    texto = (
        f"{resultado}\n\n"
        f"📝 Você marcou: {alternativa}\n"
        f"🎯 Gabarito: {gabarito}\n\n"
        f"{comentario_formatado}"
    )

    botoes = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✏️ Editar meu comentário",
                callback_data="editar_comentario"
            )
        ],
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


# ============================================================
# PRÓXIMA QUESTÃO
# ============================================================

async def proxima(update, context):

    consulta = update.callback_query

    indice = context.user_data.get(
        "indice_questao", 0
    )

    questoes = context.user_data.get("questoes", [])

    respondida = context.user_data.get(
        "respondida", False
    )

    # Exige resposta antes de avançar
    if indice < len(questoes) and not respondida:

        await consulta.answer(
            "Responda à questão antes de avançar.",
            show_alert=True
        )

        return

    await consulta.answer()

    if indice < len(questoes) and respondida:

        context.user_data["indice_questao"] += 1

        context.user_data["respondida"] = False

    await exibir_questao(consulta.message, context)




async def iniciar_edicao_comentario(update, context):
    consulta = update.callback_query
    await consulta.answer()

    # Confirma que existe uma questão selecionada
    if not context.user_data.get("questao_atual_id"):
        await consulta.message.reply_text(
            "Não foi possível identificar a questão. "
            "Responda à questão novamente e tente editar o comentário."
        )
        return ConversationHandler.END

    # Confirma que o usuário está identificado
    usuario = context.user_data.get("usuario", {})
    login_user = usuario.get("login")

    if not login_user:
        await consulta.message.reply_text(
            "Sua sessão não foi identificada. "
            "Faça login novamente para editar seu comentário."
        )
        return ConversationHandler.END

    context.user_data["aguardando_comentario_personalizado"] = True

    await consulta.message.reply_text(
        "✏️ EDITAR MEU COMENTÁRIO\n\n"
        "Digite seu comentário personalizado "
        "(máximo de 1200 caracteres).\n\n"
        "Ele será salvo somente para sua conta e não substituirá "
        "o comentário original da questão.\n\n"
        "Para cancelar, envie /cancelar."
    )

    return AGUARDANDO_COMENTARIO



async def receber_comentario_personalizado(update, context):
    mensagem = update.message

    if not mensagem or not mensagem.text:
        await update.effective_message.reply_text(
            "Envie o comentário como texto, com até 1200 caracteres."
        )
        return AGUARDANDO_COMENTARIO

    comentario = mensagem.text.strip()

    if not comentario:
        await mensagem.reply_text(
            "O comentário não pode ficar vazio. Digite novamente."
        )
        return AGUARDANDO_COMENTARIO

    if len(comentario) > 1200:
        await mensagem.reply_text(
            f"Seu comentário tem {len(comentario)} caracteres. "
            "O limite é de 1200. Envie uma versão menor."
        )
        return AGUARDANDO_COMENTARIO

    login_user = context.user_data.get("questao_login_user")
    id_questao = context.user_data.get("questao_atual_id")

    if not login_user or not id_questao:
        context.user_data["aguardando_comentario_personalizado"] = False
        await mensagem.reply_text(
            "Não foi possível identificar o usuário ou a questão. "
            "Abra a questão novamente e tente outra vez."
        )
        return ConversationHandler.END

    try:
        salvo = salvar_comentario_personalizado(
            login_user,
            id_questao,
            comentario
        )
    except Exception:
        # Registra o erro no log do Render para facilitar o diagnóstico
        import logging
        logging.exception("Erro ao salvar comentário personalizado")

        await mensagem.reply_text(
            "Ocorreu um erro ao salvar o comentário. "
            "Tente novamente mais tarde."
        )
        return AGUARDANDO_COMENTARIO

    if salvo:
        context.user_data["aguardando_comentario_personalizado"] = False
        await mensagem.reply_text(
            "✅ Comentário personalizado salvo no MongoDB!\n\n"
            "Ele será utilizado na correção desta questão para sua conta."
        )
        return ConversationHandler.END

    await mensagem.reply_text(
        "Não foi possível encontrar a questão para salvar o comentário. "
        "Confira se ela pertence à sua conta e tente novamente."
    )
    return AGUARDANDO_COMENTARIO


async def cancelar_edicao_comentario(update, context):
    context.user_data["aguardando_comentario_personalizado"] = False

    await update.effective_message.reply_text(
        "Edição do comentário cancelada."
    )

    return ConversationHandler.END
