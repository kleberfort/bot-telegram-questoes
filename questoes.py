from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler

from repositorio import (
    salvar_comentario_personalizado,
    obter_comentario_personalizado,
    salvar_desempenho
)

from uuid import uuid4

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

    # Identifica esta execução do bloco para evitar registros duplicados.
    context.user_data["tentativa_id"] = str(uuid4())
    context.user_data["aguardando_salvamento"] = False
    context.user_data["questionario_finalizado"] = False


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






def montar_teclado_voltar_inicio():
    """Cria o botão para retornar ao menu principal do bot."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🏠 Voltar ao Início",
                callback_data="inicio"
            )
        ]
    ])


# ============================================================
# EXIBIR QUESTÃO COM OU SEM IMAGEM
# ============================================================

async def exibir_questao(mensagem, context):
    lista_questoes = context.user_data.get("questoes", [])
    indice = context.user_data.get("indice_questao", 0)

    # --------------------------------------------------------
    # FINALIZAR QUESTIONÁRIO
    # --------------------------------------------------------

    if indice >= len(lista_questoes):
        # Evita exibir a finalização novamente caso um botão antigo seja acionado.
        if context.user_data.get("questionario_finalizado"):
            return

        desempenho = context.user_data.get("desempenho", {})

        total = desempenho.get("total", 0)
        acertos = desempenho.get("acertos", 0)
        erros = desempenho.get("erros", 0)

        porcentagem = acertos / total * 100 if total else 0

        texto = (
            "🎉 QUESTIONÁRIO FINALIZADO!\n\n"
            f"📚 Conteúdo: "
            f"{context.user_data.get('assunto', 'Geral')}\n\n"
            f"📝 Questões respondidas: {total}\n"
            f"✅ Acertos: {acertos}\n"
            f"❌ Erros: {erros}\n"
            f"🎯 Aproveitamento: {porcentagem:.2f}%"
        )

        # Marca a finalização antes de enviar mensagens.
        context.user_data["questionario_finalizado"] = True

        # Apresenta as questões erradas, mantendo o comportamento anterior.
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

                limite = 3500

                for inicio in range(0, len(texto_erro), limite):
                    await mensagem.reply_text(
                        texto_erro[inicio:inicio + limite]
                    )
        else:
            await mensagem.reply_text(
                "🏆 Parabéns! Você não errou nenhuma questão."
            )

        # Só oferece salvamento quando há usuário autenticado.
        usuario = context.user_data.get("usuario", {})
        login_user = usuario.get("login")

        if login_user and total > 0:
            context.user_data["aguardando_salvamento"] = True

            teclado_salvar = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "✅ Sim, salvar desempenho",
                        callback_data="desempenho:salvar"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "❌ Não, obrigado",
                        callback_data="desempenho:nao_salvar"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🏠 Voltar ao Início",
                        callback_data="inicio"
                    )
                ]
            ])

            await mensagem.reply_text(
                texto + "\n\n"
                "📊 Deseja salvar o resultado deste bloco "
                "no seu Painel de Desempenho?",
                reply_markup=teclado_salvar
            )
        else:
            await mensagem.reply_text(
                texto + "\n\n"
                "⚠️ Faça login para salvar seu desempenho no painel."
            )

        return

    # --------------------------------------------------------
    # CARREGAR QUESTÃO
    # --------------------------------------------------------

    questao = lista_questoes[indice]
    alternativas = questao.get("alternativas", {})

    usuario = context.user_data.get("usuario", {})
    login_user = usuario.get("login")

    # Guarda os dados para permitir a edição do comentário.
    context.user_data["questao_atual_id"] = str(questao["_id"])
    context.user_data["questao_login_user"] = login_user

    context.user_data["respondida"] = False

    # --------------------------------------------------------
    # VERIFICAR SE A QUESTÃO POSSUI IMAGEM
    # --------------------------------------------------------

    telegram_config = questao.get("telegram_config", {})

    possui_imagem = telegram_config.get("possui_imagem", False)
    imagem_url = telegram_config.get("imagem_url")

    possui_imagem = bool(possui_imagem and imagem_url)

    # --------------------------------------------------------
    # MONTAR ENUNCIADO
    # --------------------------------------------------------

    orientacao_imagem = ""

    if possui_imagem:
        orientacao_imagem = (
            "📷 Para responder à questão, veja a imagem acima.\n\n"
        )

    texto = (
        f"📚 {questao.get('assunto', context.user_data.get('assunto', ''))}\n\n"
        f"🧠 Questão {indice + 1} de {len(lista_questoes)}\n\n"
        f"{orientacao_imagem}"
        f"{questao.get('enunciado', '')}\n\n"
    )

    # --------------------------------------------------------
    # MONTAR ALTERNATIVAS E BOTÕES
    # --------------------------------------------------------

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

    teclado = InlineKeyboardMarkup(botoes)

    # --------------------------------------------------------
    # ENVIAR IMAGEM, SE EXISTIR
    # --------------------------------------------------------

    if possui_imagem:
        try:
            await mensagem.reply_photo(
                photo=imagem_url
            )

        except Exception:
            import logging

            logging.exception(
                "Não foi possível enviar a imagem da questão %s",
                questao.get("_id")
            )

            await mensagem.reply_text(
                "⚠️ Não foi possível carregar a imagem desta questão. "
                "Confira o enunciado abaixo e responda normalmente."
            )

    # --------------------------------------------------------
    # ENVIAR ENUNCIADO, ALTERNATIVAS E BOTÕES
    # --------------------------------------------------------

    await mensagem.reply_text(
        texto,
        reply_markup=teclado
    )


# ============================================================
# RESPONDER QUESTÃO
# ============================================================


async def responder(update, context):
    consulta = update.callback_query

    # Recupera os dados do usuário antes de utilizá-los.
    usuario = context.user_data.get("usuario", {})
    login_user = usuario.get("login")

    # Diagnóstico do usuário que respondeu à questão.
    print(
        "DIAGNÓSTICO TELEGRAM |",
        "telegram_id:", update.effective_user.id,
        "| chat_id:", update.effective_chat.id,
        "| login:", login_user
    )

    # Impede que a mesma questão seja respondida mais de uma vez.
    if context.user_data.get("respondida"):
        await consulta.answer(
            "Você já respondeu esta questão.",
            show_alert=True
        )
        return

    await consulta.answer()

    # Recupera a lista de questões e o índice da questão atual.
    lista_questoes = context.user_data.get("questoes", [])
    indice = context.user_data.get("indice_questao", 0)

    if indice >= len(lista_questoes):
        await consulta.message.reply_text(
            "Questão não encontrada. Digite /start."
        )
        return

    # Recupera a questão atual.
    questao = lista_questoes[indice]
    alternativa = consulta.data.split(":")[1].upper()
    alternativas = questao.get("alternativas", {})

    # Valida a alternativa selecionada.
    if alternativa not in alternativas:
        await consulta.answer(
            "Alternativa inválida.",
            show_alert=True
        )
        return

    # Recupera o gabarito oficial da questão.
    gabarito = questao.get("resposta", "").upper()

    # Registra o usuário e a questão atual para editar o comentário.
    context.user_data["questao_atual_id"] = str(questao["_id"])
    context.user_data["questao_login_user"] = login_user

    # Remove os botões de alternativas após a resposta.
    await consulta.edit_message_reply_markup(reply_markup=None)

    # Inicializa ou recupera o desempenho do usuário.
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

    # Verifica se a resposta está correta.
    if alternativa == gabarito:
        resultado = "✅ RESPOSTA CORRETA!"
        desempenho["acertos"] += 1

    else:
        resultado = "❌ RESPOSTA INCORRETA!"
        desempenho["erros"] += 1

        # Registra os dados da questão respondida incorretamente.
        desempenho["questoes_erradas"].append({
            "numero": indice + 1,
            "assunto": questao.get("assunto", ""),
            "enunciado": resumir_enunciado(
                questao.get("enunciado", "")
            ),
            "marcada": alternativa,
            "gabarito": gabarito
        })

    # Busca o comentário personalizado deste usuário para a questão.
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

    # Monta o comentário e a explicação da questão.
    comentario_formatado = montar_comentario(
        questao,
        alternativa,
        gabarito,
        comentario_personalizado=comentario_personalizado
    )

    # Monta a mensagem de feedback.
    texto = (
        f"{resultado}\n\n"
        f"📝 Você marcou: {alternativa}\n"
        f"🎯 Gabarito: {gabarito}\n\n"
        f"{comentario_formatado}"
    )

    # Cria os botões de navegação.
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

    # Exibe o resultado e as opções de navegação.
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

    print(
    "DIAGNÓSTICO COMENTÁRIO |",
    "telegram_id:", update.effective_user.id,
    "| chat_id:", update.effective_chat.id,
    "| login:", context.user_data.get("usuario", {}).get("login"),
    "| login da questão:", context.user_data.get("questao_login_user")
)


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
    await update.effective_message.reply_text("Edição do comentário cancelada.")
    return ConversationHandler.END


# ============================================================
# SALVAR OU DESCARTAR O DESEMPENHO DO BLOCO
# ============================================================

async def confirmar_salvamento_desempenho(update, context):
    """Salva no MongoDB o resultado do bloco concluído."""

    consulta = update.callback_query
    await consulta.answer()

    # Impede que o mesmo resultado seja salvo mais de uma vez.
    if not context.user_data.get("aguardando_salvamento"):
        await consulta.answer(
            "Este resultado já foi processado.",
            show_alert=True
        )
        return

    usuario = context.user_data.get("usuario", {})
    login_user = usuario.get("login")

    if not login_user:
        context.user_data["aguardando_salvamento"] = False
        await consulta.message.reply_text(
            "⚠️ Sua sessão não foi identificada. Faça login novamente."
        )
        return

    desempenho = context.user_data.get("desempenho", {})

    try:
        salvo = salvar_desempenho(
            login_user=login_user,
            tentativa_id=context.user_data.get("tentativa_id"),
            disciplina=context.user_data.get("disciplina", "Não informada"),
            topico=context.user_data.get("topico", "Não informado"),
            assunto=context.user_data.get("assunto", "Geral"),
            bloco=context.user_data.get("bloco_atual", 1),
            total=desempenho.get("total", 0),
            acertos=desempenho.get("acertos", 0),
            erros=desempenho.get("erros", 0)
        )

    except Exception:
        import logging
        logging.exception("Erro ao salvar desempenho do bloco")

        await consulta.message.reply_text(
            "❌ Não foi possível salvar seu desempenho agora. "
            "Tente novamente mais tarde."
        )
        return

    if salvo:
        context.user_data["aguardando_salvamento"] = False

        await consulta.edit_message_reply_markup(reply_markup=None)
        await consulta.message.reply_text(
            "✅ DESEMPENHO SALVO COM SUCESSO!\n\n"
            "Seu resultado já está registrado no Painel de Desempenho.",
            reply_markup=montar_teclado_voltar_inicio()
        )
    else:
        await consulta.message.reply_text(
            "⚠️ Não foi possível confirmar o salvamento. "
            "Verifique o banco de dados e tente novamente."
        )


async def descartar_salvamento_desempenho(update, context):
    """Encerra a confirmação sem gravar o resultado no painel."""

    consulta = update.callback_query
    await consulta.answer()

    if not context.user_data.get("aguardando_salvamento"):
        await consulta.answer(
            "Esta confirmação já foi processada.",
            show_alert=True
        )
        return

    context.user_data["aguardando_salvamento"] = False

    await consulta.edit_message_reply_markup(reply_markup=None)
    await consulta.message.reply_text(
        "ℹ️ Resultado não salvo no Painel de Desempenho.\n\n"
        "Você pode continuar seus estudos pelo menu inicial.",
        reply_markup=montar_teclado_voltar_inicio()
    )
