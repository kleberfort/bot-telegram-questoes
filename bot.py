from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler
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

    # Comandos
    app.add_handler(CommandHandler("start", menus.iniciar))

    # Navegação pelos menus
    app.add_handler(CallbackQueryHandler(menus.voltar_inicio,pattern="^inicio$"))
    app.add_handler(CallbackQueryHandler(menus.selecionar_disciplina,pattern="^disciplina:"))
    app.add_handler(CallbackQueryHandler(menus.selecionar_topico,pattern="^topico:"))
    app.add_handler(CallbackQueryHandler(menus.selecionar_assunto,pattern="^assunto:"))
    app.add_handler(CallbackQueryHandler(menus.selecionar_bloco,pattern="^bloco:"))

    # Respostas e navegação das questões
    app.add_handler(CallbackQueryHandler(questoes.responder,pattern="^responder:"))
    app.add_handler(CallbackQueryHandler(questoes.proxima,pattern="^proxima$"))

    print("Bot iniciado com sucesso!")

    app.run_polling()

if __name__ == "__main__":
    main()