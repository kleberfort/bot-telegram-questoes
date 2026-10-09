
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


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

def montar_comentario(questao, alternativa_marcada, gabarito):
    """
    Monta a correção usando os campos novos do MongoDB.

    Compatibilidade:
    - Questões novas: comentario + analise_alternativas + fixacao.
    - Questões antigas: somente comentario.
    """

    partes = []

    analise = questao.get("analise_alternativas", {})
    comentario = questao.get("comentario", "")
    fixacao = questao.get("fixacao", "")

    # --------------------------------------------------------
    # FORMATO NOVO: COMENTÁRIOS SEPARADOS POR ALTERNATIVA
    # --------------------------------------------------------

    if isinstance(analise, dict) and analise:

        if alternativa_marcada == gabarito:
            partes.append("💡 COMENTÁRIO DA QUESTÃO")
        else:
            partes.append(
                f"🎯 POR QUE A ALTERNATIVA {gabarito} "
                f"ESTÁ CORRETA?"
            )

        if comentario:
            partes.append(comentario)

        partes.append("📚 ANÁLISE DAS ALTERNATIVAS")

        alternativas = questao.get("alternativas", {})

        for letra, texto_alternativa in alternativas.items():

            dados = analise.get(letra, {})

            # A letra do gabarito é a referência principal
            if letra == gabarito:
                simbolo = "🟢"
                status = "Correta"
            else:
                simbolo = "🔴"
                status = "Incorreta"

            # Utiliza o comentário individual, se existir
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

    # --------------------------------------------------------
    # FORMATO ANTIGO: UM ÚNICO CAMPO COMENTARIO
    # --------------------------------------------------------

    partes.append("📖 COMENTÁRIO")

    if comentario:
        partes.append(comentario)
    else:
        partes.append(
            "Não há comentário cadastrado para esta questão."
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

    questoes = context.user_data.get("questoes", [])
    indice = context.user_data.get("indice_questao", 0)

    # --------------------------------------------------------
    # FINALIZAR QUESTIONÁRIO
    # --------------------------------------------------------

    if indice >= len(questoes):

        desempenho = context.user_data.get("desempenho", {})

        total = desempenho.get("total", 0)
        acertos = desempenho.get("acertos", 0)
        erros = desempenho.get("erros", 0)

        porcentagem = (
            acertos / total * 100 if total > 0 else 0
        )

        texto = (
            "🎉 QUESTIONÁRIO FINALIZADO!\n\n"
            f"📚 Conteúdo: "
            f"{context.user_data.get('assunto', 'Geral')}\n\n"
            f"📝 Questões respondidas: {total}\n"
            f"✅ Acertos: {acertos}\n"
            f"❌ Erros: {erros}\n"
            f"🎯 Aproveitamento: {porcentagem:.2f}%"
        )

        await mensagem.reply_text(texto)

        questoes_erradas = desempenho.get(
            "questoes_erradas", []
        )

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

                # Divide o texto para evitar mensagens extensas
                limite = 3500

                for inicio in range(
                    0, len(texto_erro), limite
                ):
                    parte = texto_erro[
                        inicio:inicio + limite
                    ]

                    await mensagem.reply_text(parte)

        else:
            await mensagem.reply_text(
                "🏆 Parabéns! Você não errou nenhuma questão."
            )

        return

    # --------------------------------------------------------
    # PREPARAR QUESTÃO
    # --------------------------------------------------------

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

    # Cria um botão para cada alternativa cadastrada
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

    # Impede responder mais de uma vez
    if context.user_data.get("respondida"):

        await consulta.answer(
            "Você já respondeu esta questão.",
            show_alert=True
        )

        return

    await consulta.answer()

    questoes = context.user_data.get("questoes", [])
    indice = context.user_data.get("indice_questao", 0)

    if indice >= len(questoes):

        await consulta.message.reply_text(
            "Questão não encontrada. Digite /start."
        )

        return

    questao = questoes[indice]

    alternativa = consulta.data.split(":")[1].upper()

    alternativas = questao.get("alternativas", {})

    # Valida a alternativa recebida
    if alternativa not in alternativas:

        await consulta.answer(
            "Alternativa inválida.",
            show_alert=True
        )

        return

    gabarito = questao.get("resposta", "").upper()

    # Remove os botões da questão respondida
    await consulta.edit_message_reply_markup(
        reply_markup=None
    )

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

    # --------------------------------------------------------
    # VERIFICAR RESPOSTA
    # --------------------------------------------------------

    if alternativa == gabarito:

        resultado = "✅ RESPOSTA CORRETA!"

        desempenho["acertos"] += 1

    else:

        resultado = "❌ RESPOSTA INCORRETA!"

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

    # --------------------------------------------------------
    # MONTAR RESPOSTA COMENTADA
    # --------------------------------------------------------

    comentario_formatado = montar_comentario(
        questao,
        alternativa,
        gabarito
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

    # Mantém a navegação atual
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
