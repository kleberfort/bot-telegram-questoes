from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import os

# ============================================================
# TOKEN DO BOT
# ============================================================



TOKEN = os.getenv("TOKEN")

# ============================================================
# BANCO DE QUESTÕES
# ============================================================

QUESTOES = [

    {
        "id": 2,

        "pergunta": """🧠 QUESTÃO 01 — PLN

Qual sequência apresenta corretamente os estágios do fluxo de
Processamento de Linguagem Natural?""",

        "alternativas": {

            "A": "Pré-processamento → Análise léxica → Análise tradutória → Análise intencional → Análise verificadora",

            "B": "Pré-processamento → Análise léxica → Análise sintática → Análise semântica → Análise pragmática",

            "C": "Pré-processamento → Análise tradutória → Análise sintática → Análise verificadora",

            "D": "Pré-processamento → Análise tradutória → Análise pragmática → Análise sintática"
        },

        "gabarito": "B",

        "explicacao": """
📖 EXPLICAÇÃO

O Processamento de Linguagem Natural (PLN) é uma área da
Inteligência Artificial que busca permitir que computadores
processem e compreendam a linguagem humana.

A sequência correta é:

1️⃣ Pré-processamento
2️⃣ Análise léxica
3️⃣ Análise sintática
4️⃣ Análise semântica
5️⃣ Análise pragmática

🔹 Pré-processamento

É a etapa de preparação do texto para as etapas seguintes.

🔹 Análise léxica

Analisa as unidades que formam o texto, como palavras e tokens.

🔹 Análise sintática

Analisa a estrutura da frase e a relação entre seus elementos.

🔹 Análise semântica

Analisa o significado da frase e das relações entre seus elementos.

🔹 Análise pragmática

Considera o contexto em que a mensagem foi utilizada.

🎯 CONCLUSÃO

A alternativa correta é B.
"""
    },


    {
        "id": 1,

        "pergunta": """🧠 QUESTÃO 02

Qual é a finalidade principal da Inteligência Artificial?""",

        "alternativas": {

            "A": "Criar sistemas capazes de realizar tarefas que normalmente exigiriam inteligência humana.",

            "B": "Aumentar exclusivamente a velocidade dos computadores.",

            "C": "Substituir todos os seres humanos.",

            "D": "Criar apenas programas para cálculos matemáticos."
        },

        "gabarito": "A",

        "explicacao": """
📖 EXPLICAÇÃO

A Inteligência Artificial busca desenvolver sistemas capazes
de executar tarefas associadas à inteligência humana.

Entre essas tarefas estão:

• reconhecimento de padrões;
• aprendizagem;
• compreensão de linguagem;
• tomada de decisões;
• resolução de problemas.

🎯 CONCLUSÃO

A alternativa correta é A.
"""
    }

]


# ============================================================
# COMANDO /START
# ============================================================

async def iniciar(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Por enquanto, começa sempre pela primeira questão
    questao = QUESTOES[0]

    botoes = [

        [
            InlineKeyboardButton(
                "A",
                callback_data=f"questao_{questao['id']}_A"
            ),

            InlineKeyboardButton(
                "B",
                callback_data=f"questao_{questao['id']}_B"
            )
        ],

        [
            InlineKeyboardButton(
                "C",
                callback_data=f"questao_{questao['id']}_C"
            ),

            InlineKeyboardButton(
                "D",
                callback_data=f"questao_{questao['id']}_D"
            )
        ]

    ]

    teclado = InlineKeyboardMarkup(botoes)


    texto = f"""
{questao["pergunta"]}

🅰️ {questao["alternativas"]["A"]}

🅱️ {questao["alternativas"]["B"]}

©️ {questao["alternativas"]["C"]}

🅳️ {questao["alternativas"]["D"]}

👇 Escolha uma alternativa:
"""


    await update.message.reply_text(
        texto,
        reply_markup=teclado
    )


# ============================================================
# PROCESSAR RESPOSTA
# ============================================================

async def resposta(update: Update, context: ContextTypes.DEFAULT_TYPE):

    consulta = update.callback_query

    # Confirma ao Telegram que o clique foi recebido
    await consulta.answer()

    # --------------------------------------------------------
    # Recupera o callback enviado pelo botão
    # Exemplo:
    #
    # questao_1_B
    #
    # significa:
    # Questão = 1
    # Resposta = B
    # --------------------------------------------------------

    dados = consulta.data

    print("Callback recebido:", dados)


    # --------------------------------------------------------
    # Verifica se o callback está no formato novo
    # --------------------------------------------------------

    partes = dados.split("_")


    if len(partes) != 3 or partes[0] != "questao":

        await consulta.message.reply_text(
            "⚠️ Esse botão pertence a uma versão antiga da questão.\n\n"
            "Digite /start para receber uma nova questão."
        )

        return


    # --------------------------------------------------------
    # Identifica a questão e a alternativa
    # --------------------------------------------------------

    id_questao = int(partes[1])

    alternativa = partes[2]


    # --------------------------------------------------------
    # Procura a questão dentro da lista QUESTOES
    # --------------------------------------------------------

    questao = next(
        (
            q for q in QUESTOES
            if q["id"] == id_questao
        ),
        None
    )


    # --------------------------------------------------------
    # Verifica se a questão existe
    # --------------------------------------------------------

    if questao is None:

        await consulta.message.reply_text(
            "⚠️ Questão não encontrada."
        )

        return


    # --------------------------------------------------------
    # Recupera gabarito e explicação
    # --------------------------------------------------------

    gabarito = questao["gabarito"]

    explicacao = questao["explicacao"]


    # --------------------------------------------------------
    # Verifica se o usuário acertou
    # --------------------------------------------------------

    if alternativa == gabarito:

        mensagem = f"""
✅ CORRETO!

Você marcou: {alternativa}

🎯 Gabarito: {gabarito}

{explicacao}
"""

    else:

        mensagem = f"""
❌ INCORRETO!

Você marcou: {alternativa}

🎯 Gabarito: {gabarito}

{explicacao}
"""


    # --------------------------------------------------------
    # Envia resultado + explicação
    # --------------------------------------------------------

    await consulta.message.reply_text(mensagem)


# ============================================================
# FUNÇÃO PRINCIPAL
# ============================================================

def main():

    app = Application.builder().token(TOKEN).build()


    # Comando /start
    app.add_handler(
        CommandHandler("start", iniciar)
    )


    # Cliques nos botões A/B/C/D
    app.add_handler(
        CallbackQueryHandler(resposta)
    )


    print("🤖 Bot iniciado!")


    # Mantém o bot funcionando
    app.run_polling()


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    main()
