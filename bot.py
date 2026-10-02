from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import os


from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler
)

from config import TOKEN
import menus
import questoes


def main():
    app = Application.builder().token(TOKEN).build()

    # Comando inicial
    app.add_handler(
        CommandHandler("start", menus.iniciar)
    )

    # Navegação dos menus
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

    # Questões
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

    print("🤖 Bot iniciado!")

    app.run_polling()


if __name__ == "__main__":
    main()