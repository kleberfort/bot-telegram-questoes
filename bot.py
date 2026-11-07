
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

    # ============================================================
    # TESTAR CONEXÃO COM O MONGODB
    # ============================================================

    if not testar_conexao():
        print("Não foi possível conectar ao banco de dados.")
        return

    # ============================================================
    # CRIAR APLICAÇÃO
    # ============================================================

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
                pattern=r"^editar_comentario$"
            )
        ],

        states={

            questoes.AGUARDANDO_COMENTARIO: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    questoes.receber_comentario_personalizado
                )
            ],
        },

        fallbacks=[
            CommandHandler(
                "cancelar",
                questoes.cancelar_edicao_comentario
            ),

            CommandHandler("start", menus.iniciar),
            CommandHandler("logout", menus.logout),
        ],

        per_user=True,
        per_chat=True,
    )

    app.add_handler(
        comentario_handler,
        group=1
    )

    # ============================================================
    # LOGOUT
    # ============================================================

    app.add_handler(
        CommandHandler(
            "logout",
            menus.logout
        ),
        group=0
    )

    # ============================================================
    # NAVEGAÇÃO PELOS MENUS DE ESTUDO
    # ============================================================

    app.add_handler(
        CallbackQueryHandler(
            menus.voltar_inicio,
            pattern=r"^inicio$"
        ),
        group=0
    )

    app.add_handler(
        CallbackQueryHandler(
            menus.selecionar_disciplina,
            pattern=r"^disciplina:"
        ),
        group=0
    )

    app.add_handler(
        CallbackQueryHandler(
            menus.selecionar_topico,
            pattern=r"^topico:"
        ),
        group=0
    )

    app.add_handler(
        CallbackQueryHandler(
            menus.selecionar_assunto,
            pattern=r"^assunto:"
        ),
        group=0
    )

    app.add_handler(
        CallbackQueryHandler(
            menus.selecionar_bloco,
            pattern=r"^bloco:"
        ),
        group=0
    )

    # ============================================================
    # GRADE DE QUESTÕES
    # ============================================================

    app.add_handler(
        CallbackQueryHandler(
            menus.visualizar_grade_questoes,
            pattern=r"^grade_questoes$"
        ),
        group=0
    )

    # ============================================================
    # PAINEL DE DESEMPENHO
    # ============================================================

    # 1. Abrir o painel de desempenho
    app.add_handler(
        CallbackQueryHandler(
            menus.abrir_painel_desempenho,
            pattern=r"^painel_desempenho$"
        ),
        group=0
    )

    # 2. Selecionar disciplina para consultar desempenho
    app.add_handler(
        CallbackQueryHandler(
            menus.selecionar_disciplina_desempenho,
            pattern=r"^painel_disciplina:"
        ),
        group=0
    )

    # 3. Voltar para seleção de disciplinas do painel
    app.add_handler(
        CallbackQueryHandler(
            menus.voltar_disciplinas_painel,
            pattern=r"^painel_voltar_disciplinas$"
        ),
        group=0
    )

    # Salvar desempenho do bloco
    app.add_handler(
    CallbackQueryHandler(
        questoes.confirmar_salvamento_desempenho,
        pattern=r"^desempenho:salvar$"
    ),
    group=0
)

    # Não salvar desempenho do bloco
    app.add_handler(
    CallbackQueryHandler(
        questoes.descartar_salvamento_desempenho,
        pattern=r"^desempenho:nao_salvar$"
    ),
    group=0
)

    # ============================================================
# GERENCIAMENTO DO HISTÓRICO DE DESEMPENHO
# ============================================================

    app.add_handler(
    CallbackQueryHandler(
        menus.abrir_menu_exclusao_historico,
        pattern=r"^painel_exclusao_menu$"
    ),
    group=0
)

    app.add_handler(
    CallbackQueryHandler(
        menus.selecionar_nivel_exclusao,
        pattern=r"^excluir_hist:"
    ),
    group=0
)

    app.add_handler(
    CallbackQueryHandler(
        menus.selecionar_topico_exclusao,
        pattern=r"^excluir_topico:"
    ),
    group=0
)

    app.add_handler(
    CallbackQueryHandler(
        menus.selecionar_topico_assunto_exclusao,
        pattern=r"^excluir_assunto_topico:"
    ),
    group=0
)

    app.add_handler(
    CallbackQueryHandler(
        menus.selecionar_assunto_exclusao,
        pattern=r"^excluir_assunto:"
    ),
    group=0
)

    app.add_handler(
    CallbackQueryHandler(
        menus.confirmar_exclusao_desempenho,
        pattern=r"^confirmar_exclusao_desempenho$"
    ),
    group=0
)

    app.add_handler(
    CallbackQueryHandler(
        menus.cancelar_exclusao_desempenho,
        pattern=r"^painel_exclusao_cancelar$"
    ),
    group=0
)

    # ============================================================
    # QUESTÕES
    # ============================================================

    app.add_handler(
        CallbackQueryHandler(
            questoes.responder,
            pattern=r"^responder:"
        ),
        group=0
    )

    app.add_handler(
        CallbackQueryHandler(
            questoes.proxima,
            pattern=r"^proxima$"
        ),
        group=0
    )

    # ============================================================
    # INICIAR BOT
    # ============================================================

    print("Bot iniciado com sucesso!")

    app.run_polling()


if __name__ == "__main__":
    main()
