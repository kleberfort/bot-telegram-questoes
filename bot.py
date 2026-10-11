from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters
)

from config import TOKEN
from database import testar_conexao

import menus
import questoes


def main():

    # Testa a conexão com o MongoDB
    if not testar_conexao():
        print("Não foi possível conectar ao banco de dados.")
        return

    # Cria a aplicação com processamento sequencial
    app = (
        Application.builder()
        .token(TOKEN)
        .concurrent_updates(False)
        .build()
    )

    # ============================================================
    # GERENCIADOR DO FLUXO DE LOGIN
    # ============================================================

    login_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", menus.iniciar),
            CommandHandler("login", menus.iniciar_login),
        ],
        states={
            menus.SOLICITAR_LOGIN: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    menus.receber_login
                )
            ],
            menus.SOLICITAR_SENHA: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    menus.receber_senha
                )
            ],
        },
        fallbacks=[
            CommandHandler("start", menus.iniciar),
            CommandHandler("login", menus.iniciar_login),
            CommandHandler("logout", menus.logout),
        ],
    )

    app.add_handler(login_handler, group=0)

    # ============================================================
    # EDIÇÃO DO COMENTÁRIO PERSONALIZADO
    # ============================================================

    comentario_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                questoes.iniciar_edicao_comentario,
                pattern=r"^editar_comentario$",
            )
        ],
        states={
            questoes.AGUARDANDO_COMENTARIO: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    questoes.receber_comentario_personalizado,
                )
            ]
        },
        fallbacks=[
            CommandHandler(
                "cancelar",
                questoes.cancelar_edicao_comentario,
            ),
            CommandHandler("start", menus.iniciar),
            CommandHandler("logout", menus.logout),
        ],
        per_user=True,
        per_chat=True,
    )

    # Grupo separado para a edição do comentário
    app.add_handler(comentario_handler, group=1)

    # ============================================================
    # LOGOUT
    # ============================================================

    app.add_handler(
        CommandHandler("logout", menus.logout),
        group=0,
    )

    # ============================================================
    # NAVEGAÇÃO PELOS MENUS
    # ============================================================

    app.add_handler(
        CallbackQueryHandler(
            menus.voltar_inicio,
            pattern=r"^inicio$",
        ),
        group=0,
    )

    app.add_handler(
        CallbackQueryHandler(
            menus.selecionar_disciplina,
            pattern=r"^disciplina:",
        ),
        group=0,
    )

    app.add_handler(
        CallbackQueryHandler(
            menus.selecionar_topico,
            pattern=r"^topico:",
        ),
        group=0,
    )

    app.add_handler(
        CallbackQueryHandler(
            menus.selecionar_assunto,
            pattern=r"^assunto:",
        ),
        group=0,
    )

    app.add_handler(
        CallbackQueryHandler(
            menus.selecionar_bloco,
            pattern=r"^bloco:",
        ),
        group=0,
    )

    # ============================================================
    # QUESTÕES
    # ============================================================

    app.add_handler(
        CallbackQueryHandler(
            questoes.responder,
            pattern=r"^responder:",
        ),
        group=0,
    )

    app.add_handler(
        CallbackQueryHandler(
            questoes.proxima,
            pattern=r"^proxima$",
        ),
        group=0,
    )

    print("Bot iniciado com sucesso!")
    app.run_polling()


if __name__ == "__main__":
    main()
