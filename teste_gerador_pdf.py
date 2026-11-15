
from gerador_pdf import gerar_pdf_erros


# ============================================================
# SIMULAÇÃO DE DESEMPENHO
# 6 QUESTÕES: 2 ACERTOS E 4 ERROS
# ============================================================

questoes_teste = [

    # ========================================================
    # QUESTÃO 1 - FCC
    # ========================================================

    {
        "numero": 1,
        "banca": "FCC",
        "orgao": "MPE SE",
        "cargo": "Manutenção e Suporte de Equipamentos de Informática e Softwares",
        "ano": 2026,

        "enunciado_completo": (
            "Durante o desenvolvimento de um chatbot interno no Ministério Público, "
            "a equipe de TI percebeu que as respostas da IA, embora corretas, eram "
            "genéricas e pouco adaptadas ao contexto jurídico da instituição. "
            "O objetivo passou a ser obter respostas mais detalhadas, com terminologia "
            "adequada e foco nas normas e procedimentos internos. O técnico responsável "
            "foi orientado a revisar a formulação das instruções dadas ao modelo, "
            "ajustando a forma e a estrutura dos comandos textuais.\n\n"
            "Para isso, o técnico deve fazer"
        ),

        "alternativas": {
            "A": "a aplicação de técnicas de prompt-engineering, definindo papéis, contexto e exemplos explícitos na instrução.",
            "B": "uso de mecanismos e filtros de moderação de conteúdo para restringir a saída do modelo a temas jurídicos.",
            "C": "o refinamento de clusters do modelo de linguagem para aumentar a precisão estatística das respostas.",
            "D": "a expansão do conjunto de treinamento com documentos públicos e decisões judiciais disponíveis em bases abertas.",
            "E": "a implementação de um pipeline de aprendizado de esforço com a curadoria de promotores e procuradores."
        },

        "marcada": "B",
        "gabarito": "A",
        "motivo_erro": "Lacuna teórica",

        "comentario": (
            "A resposta correta é A. O enunciado apresenta a necessidade de revisar "
            "a formulação das instruções e ajustar a estrutura dos comandos textuais. "
            "Isso corresponde à engenharia de prompts.\n\n"
            "A técnica utiliza papéis, contexto e exemplos explícitos para orientar "
            "o modelo e melhorar a qualidade das respostas, sem necessidade de "
            "retreinar o modelo."
        )
    },

    # ========================================================
    # QUESTÃO 2 - FGV
    # ========================================================

    {
        "numero": 2,
        "banca": "FGV",
        "orgao": "TCE PE",
        "cargo": "Auditoria de Tecnologia da Informação",
        "ano": 2025,

        "enunciado_completo": (
            "Uma forma de garantir que um modelo de linguagem revise cláusulas "
            "de confidencialidade em contratos com alta precisão é fornecer "
            "exemplos concretos de cláusulas corretas e incorretas, para que "
            "o modelo aprenda o padrão desejado antes de analisar novas cláusulas.\n\n"
            "A técnica de Engenharia de Prompt que descreve corretamente "
            "esse processo é chamada:"
        ),

        "alternativas": {
            "A": "zero-shot prompt.",
            "B": "self-consistency prompt.",
            "C": "chain-of-thought prompt.",
            "D": "soft prompt.",
            "E": "few-shot prompt."
        },

        "marcada": "A",
        "gabarito": "E",
        "motivo_erro": "Falta de atenção",

        "comentario": (
            "A resposta correta é E: few-shot prompt.\n\n"
            "A expressão fornecer exemplos concretos é a principal pista. "
            "No few-shot, são apresentados exemplos dentro do próprio prompt "
            "para orientar o modelo.\n\n"
            "Zero-shot não fornece exemplos. Chain-of-thought apresenta "
            "etapas de raciocínio."
        )
    },

    # ========================================================
    # QUESTÃO 3 - CEBRASPE
    # ACERTO
    # ========================================================

    {
        "numero": 3,
        "banca": "CEBRASPE (CESPE)",
        "orgao": "ANM",
        "cargo": "Tecnologia da Informação / Ciência de Dados",
        "ano": 2025,

        "enunciado_completo": (
            "Um prompt é um conjunto de instruções que o modelo generativo "
            "utiliza para prever a resposta desejada."
        ),

        "alternativas": {
            "A": "Certo.",
            "B": "Errado."
        },

        "marcada": "A",
        "gabarito": "A",
        "motivo_erro": "",

        "comentario": (
            "A afirmativa está CERTA.\n\n"
            "Um prompt é o conjunto de instruções, perguntas ou informações "
            "fornecidas ao modelo generativo para orientar a resposta."
        )
    },

    # ========================================================
    # QUESTÃO 4 - IBFC
    # ========================================================

    {
        "numero": 4,
        "banca": "IBFC",
        "orgao": "TRF 5",
        "cargo": "Apoio Especializado / Análise de Sistemas de Informação",
        "ano": 2024,

        "enunciado_completo": (
            "Assinale a alternativa correta sobre a importância da criação "
            "de prompts detalhados para obter resultados úteis de uma "
            "Inteligência Artificial (IA) generativa."
        ),

        "alternativas": {
            "A": "Prompts detalhados ajudam a IA generativa a prever a melhor saída com base em treinamentos anteriores, gerando resultados mais precisos e relevantes.",
            "B": "Prompts detalhados são importantes para garantir que a IA generativa opere com maior velocidade, reduzindo o tempo de resposta.",
            "C": "Prompts detalhados são necessários para a IA generativa realizar análises estatísticas complexas e otimizar seus modelos de linguagem.",
            "D": "Prompts detalhados são utilizados para atualizar os modelos de machine learning da IA generativa com novos dados de treinamento."
        },

        "marcada": "B",
        "gabarito": "A",
        "motivo_erro": "Interpretação / Pegadinha",

        "comentario": (
            "A resposta correta é A. Prompts detalhados ajudam a IA a "
            "compreender melhor o pedido, produzindo respostas mais precisas "
            "e relevantes.\n\n"
            "Prompts não aceleram diretamente o processamento, não otimizam "
            "o modelo e não atualizam os dados de treinamento."
        )
    },

    # ========================================================
    # QUESTÃO 5 - BFC
    # ========================================================

    {
        "numero": 5,
        "banca": "BFC",
        "orgao": "TRF 5ª Região",
        "cargo": "Análise de Sistemas de Informação",
        "ano": 2024,

        "enunciado_completo": (
            "Assinale a alternativa que apresenta a principal função da "
            "engenharia de prompt no contexto da inteligência artificial "
            "(IA) generativa."
        ),

        "alternativas": {
            "A": "A engenharia de prompt visa desenvolver novos algoritmos de aprendizado de máquina para melhorar a precisão dos modelos de IA generativa.",
            "B": "A engenharia de prompt é responsável por criar instruções detalhadas e formatos específicos que orientam a IA generativa para gerar resultados relevantes e de alta qualidade.",
            "C": "A engenharia de prompt foca em implementar soluções de hardware para melhorar a performance da IA generativa em termos de processamento.",
            "D": "A engenharia de prompt trata da integração de diferentes plataformas de IA generativa para maximizar a eficiência na execução de tarefas."
        },

        "marcada": "A",
        "gabarito": "B",
        "motivo_erro": "Chute",

        "comentario": (
            "A resposta correta é B. A engenharia de prompt refina as "
            "instruções de entrada para orientar a IA e obter resultados "
            "relevantes e de alta qualidade.\n\n"
            "Não desenvolve algoritmos, não implementa hardware e não "
            "realiza integração de plataformas."
        )
    },

    # ========================================================
    # QUESTÃO 6 - IBFC
    # ACERTO
    # ========================================================

    {
        "numero": 6,
        "banca": "IBFC",
        "orgao": "TRF 5",
        "cargo": "Apoio Especializado / Análise de Sistemas de Informação",
        "ano": 2024,

        "enunciado_completo": (
            "Assinale a alternativa que apresenta o papel de um prompt "
            "na interação com a inteligência artificial (IA) generativa."
        ),

        "alternativas": {
            "A": "Um prompt é um conjunto de algoritmos usados para melhorar a precisão dos modelos de IA generativa.",
            "B": "Um prompt é um texto em linguagem natural que orienta a IA generativa a executar uma tarefa específica, gerando novos conteúdos com base em modelos de machine learning pré-treinados.",
            "C": "Um prompt é uma interface de usuário que facilita a comunicação entre humanos e sistemas de IA generativa sem a necessidade de linguagem natural.",
            "D": "Um prompt é um mecanismo de armazenamento de dados que armazena informações geradas por modelos de IA para posterior análise."
        },

        "marcada": "B",
        "gabarito": "B",
        "motivo_erro": "",

        "comentario": (
            "A resposta correta é B. O prompt é uma instrução em linguagem "
            "natural fornecida ao modelo de IA para orientar a execução "
            "de uma tarefa específica."
        )
    }
]


# ============================================================
# CALCULAR RESULTADO DA SIMULAÇÃO
# ============================================================

total = len(questoes_teste)

questoes_corretas = [
    q for q in questoes_teste
    if q["marcada"] == q["gabarito"]
]

questoes_erradas = [
    q for q in questoes_teste
    if q["marcada"] != q["gabarito"]
]

acertos = len(questoes_corretas)
erros = len(questoes_erradas)

percentual = round((acertos / total) * 100, 1)


# ============================================================
# PREPARAR QUESTÕES PARA O GERADOR PDF
# ============================================================

questoes_para_pdf = []

for questao in questoes_erradas:

    questao_pdf = questao.copy()

    # Campos utilizados pelo gerador PDF original.
    questao_pdf["resposta_usuario"] = questao["marcada"]
    questao_pdf["resposta_correta"] = questao["gabarito"]

    # Preservar identificação da banca e do órgão.
    questao_pdf["banca"] = questao["banca"]
    questao_pdf["orgao"] = questao["orgao"]
    questao_pdf["cargo"] = questao["cargo"]
    questao_pdf["ano"] = questao["ano"]

    questoes_para_pdf.append(questao_pdf)


# ============================================================
# MONTAR DADOS DO CADERNO DE ERROS
# ============================================================

dados_teste = {

    "disciplina": "Ciência de Dados",

    "topico": "Processamento de Linguagem Natural",

    "assunto": "Engenharia de Prompts",

    "bloco": "Simulação",

    "desempenho": {
        "total": total,
        "acertos": acertos,
        "erros": erros,
        "percentual": percentual
    },

    "questoes_erradas": questoes_para_pdf
}


# ============================================================
# GERAR PDF
# ============================================================

pdf = gerar_pdf_erros(dados_teste)

nome_arquivo = "caderno_de_erros_engenharia_de_prompts.pdf"

with open(nome_arquivo, "wb") as arquivo:
    arquivo.write(pdf.getvalue())


# ============================================================
# RESULTADO NO TERMINAL
# ============================================================

print("=" * 55)
print("SIMULAÇÃO FINALIZADA")
print("=" * 55)

print(f"Questões respondidas: {total}")
print(f"Acertos: {acertos}")
print(f"Erros: {erros}")
print(f"Aproveitamento: {percentual}%")

print("-" * 55)

print("QUESTÕES ENVIADAS PARA O CADERNO DE ERROS:")

for q in questoes_erradas:
    print(
        f"Questão {q['numero']} - "
        f"{q['banca']} - "
        f"Marcada: {q['marcada']} - "
        f"Gabarito: {q['gabarito']}"
    )

print("-" * 55)
print(f"PDF gerado: {nome_arquivo}")
print("=" * 55)
