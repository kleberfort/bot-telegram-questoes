
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

    # Cria a aplicação do Telegram
    app = Application.builder().token(TOKEN).build()

    # ============================================================
    # GERENCIADOR DO FLUXO DE LOGIN
    # ============================================================

    login_handler = ConversationHandler(

        # ========================================================
        # COMANDOS QUE INICIAM O FLUXO
        # ========================================================

        entry_points=[
            CommandHandler("start", menus.iniciar),
            CommandHandler("login", menus.iniciar_login),
        ],

        # ========================================================
        # ESTADOS DO LOGIN
        # ========================================================

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

        # ========================================================
        # COMANDOS DURANTE O FLUXO
        # ========================================================

        fallbacks=[
            CommandHandler("start", menus.iniciar),
            CommandHandler("login", menus.iniciar_login),
            CommandHandler("logout", menus.logout),
        ]
    )

    # Adiciona o gerenciador de login
    app.add_handler(login_handler)

    # ============================================================
    # LOGOUT FORA DO FLUXO DE LOGIN
    # ============================================================

    app.add_handler(
        CommandHandler("logout", menus.logout)
    )

    # ============================================================
    # NAVEGAÇÃO PELOS MENUS
    # ============================================================

    app.add_handler(
        CallbackQueryHandler(
            menus.voltar_inicio,
            pattern="^inicio$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            menus.selecionar_disciplina,
            pattern="^disciplina:"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            menus.selecionar_topico,
            pattern="^topico:"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            menus.selecionar_assunto,
            pattern="^assunto:"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            menus.selecionar_bloco,
            pattern="^bloco:"
        )
    )

    # ============================================================
    # QUESTÕES
    # ============================================================

    app.add_handler(
        CallbackQueryHandler(
            questoes.responder,
            pattern="^responder:"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            questoes.proxima,
            pattern="^proxima$"
        )
    )

    print("Bot iniciado com sucesso!")

    app.run_polling()


if __name__ == "__main__":
    main()
