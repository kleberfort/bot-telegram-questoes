
from io import BytesIO
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from xml.sax.saxutils import escape

import requests

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as ReportLabImage,
)


# ============================================================
# CONFIGURAÇÕES
# ============================================================

LARGURA_PAGINA, ALTURA_PAGINA = A4

MARGEM_ESQUERDA = 1.5 * cm
MARGEM_DIREITA = 1.5 * cm

LARGURA_UTIL = (
    LARGURA_PAGINA
    - MARGEM_ESQUERDA
    - MARGEM_DIREITA
)

COR_BORDA = colors.HexColor("#B8C5D3")
COR_CABECALHO = colors.HexColor("#EFF4F9")
COR_FUNDO = colors.HexColor("#F5F7FA")
COR_TEXTO = colors.HexColor("#263746")
COR_ERRO = colors.HexColor("#DC5555")
COR_ACERTO = colors.HexColor("#25A56A")

MOTIVOS_ERRO = [
    "Lacuna teórica",
    "Falta de atenção",
    "Interpretação / Pegadinha",
    "Chute",
]


# ============================================================
# ESTILOS
# ============================================================

def criar_estilos():

    base = getSampleStyleSheet()

    return {

        "titulo": ParagraphStyle(
            "Titulo",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            alignment=TA_CENTER,
            textColor=colors.black,
            spaceAfter=12,
        ),

        "subtitulo": ParagraphStyle(
            "Subtitulo",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=COR_TEXTO,
            spaceBefore=5,
            spaceAfter=5,
        ),

        "normal": ParagraphStyle(
            "NormalPersonalizado",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=colors.black,
            spaceAfter=3,
        ),

        "questao": ParagraphStyle(
            "EnunciadoQuestao",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=15,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#172B45"),
            spaceAfter=5,
        ),

        "cabecalho_questao": ParagraphStyle(
            "CabecalhoQuestao",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=COR_TEXTO,
        ),

        "identificacao": ParagraphStyle(
            "Identificacao",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=10,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#52647A"),
            wordWrap="CJK",
        ),

        "pequeno": ParagraphStyle(
            "Pequeno",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
        ),

        "motivo": ParagraphStyle(
            "Motivo",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=12,
        ),

        "anotacao": ParagraphStyle(
            "Anotacao",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=COR_TEXTO,
        ),
    }


# ============================================================
# RODAPÉ E NUMERAÇÃO
# ============================================================

def adicionar_numero_pagina(canvas, documento):

    canvas.saveState()

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)

    canvas.drawRightString(
        LARGURA_PAGINA - 1.5 * cm,
        1 * cm,
        f"Página {documento.page}",
    )

    canvas.restoreState()


# ============================================================
# IDENTIFICAÇÃO DA BANCA / ÓRGÃO / CARGO / ANO
# ============================================================

def obter_identificacao_questao(questao):
    """
    Monta a identificação completa da questão.

    Exemplo:
    CEBRASPE (CESPE)/TCE MS/Tecnologia da Informação/2025

    Aceita diferentes nomes de campos para facilitar
    a compatibilidade com os registros existentes.
    """

    # Caso a identificação completa já esteja armazenada
    identificacao_direta = (
        questao.get("identificacao")
        or questao.get("identificacao_questao")
        or questao.get("origem_questao")
    )

    if identificacao_direta:
        return str(identificacao_direta).strip()

    banca = (
        questao.get("banca")
        or questao.get("nome_banca")
        or ""
    )

    orgao = (
        questao.get("orgao")
        or questao.get("órgão")
        or questao.get("tribunal")
        or questao.get("instituicao")
        or questao.get("instituição")
        or ""
    )

    cargo = (
        questao.get("cargo")
        or questao.get("funcao")
        or questao.get("função")
        or ""
    )

    ano = (
        questao.get("ano")
        or questao.get("ano_prova")
        or questao.get("ano_concurso")
        or ""
    )

    partes = []

    for valor in [banca, orgao, cargo, ano]:

        if valor is not None:

            valor = str(valor).strip()

            if valor:
                partes.append(valor)

    if not partes:
        return "Identificação não informada"

    # Formato sem espaços entre as barras
    return "/".join(partes)


# ============================================================
# CABEÇALHO DO CADERNO DE ERROS
# ============================================================

def adicionar_cabecalho(dados, elementos, estilos):

    disciplina = dados.get("disciplina", "Não informada")
    topico = dados.get("topico", "Não informado")
    assunto = dados.get("assunto", "Não informado")
    bloco = dados.get("bloco", "Não informado")

    elementos.append(
        Paragraph(
            "CADERNO DE ERROS",
            estilos["titulo"],
        )
    )

    elementos.append(
        Paragraph(
            f"<b>Disciplina:</b> {escape(str(disciplina))}<br/>"
            f"<b>Tópico:</b> {escape(str(topico))}<br/>"
            f"<b>Assunto:</b> {escape(str(assunto))}<br/>"
            f"<b>Bloco:</b> {escape(str(bloco))}",
            estilos["normal"],
        )
    )

    elementos.append(Spacer(1, 8))


# ============================================================
# CABEÇALHO DO PDF DE RESOLUÇÃO
# ============================================================

def adicionar_cabecalho_resolucao(dados, elementos, estilos):

    disciplina = dados.get("disciplina", "Não informada")
    topico = dados.get("topico", "Não informado")
    assunto = dados.get("assunto", "Não informado")
    bloco = dados.get("bloco", "Não informado")

    elementos.append(
        Paragraph(
            "RESOLUÇÃO DE QUESTÕES",
            estilos["titulo"],
        )
    )

    elementos.append(
        Paragraph(
            f"<b>Disciplina:</b> {escape(str(disciplina))}<br/>"
            f"<b>Tópico:</b> {escape(str(topico))}<br/>"
            f"<b>Assunto:</b> {escape(str(assunto))}<br/>"
            f"<b>Bloco:</b> {escape(str(bloco))}",
            estilos["normal"],
        )
    )

    elementos.append(Spacer(1, 12))


# ============================================================
# DESEMPENHO DO CADERNO DE ERROS
# ============================================================

def adicionar_desempenho(dados, elementos, estilos):

    desempenho = dados.get("desempenho", {})

    total = desempenho.get("total", 0)
    acertos = desempenho.get("acertos", 0)
    erros = desempenho.get("erros", 0)

    percentual = desempenho.get(
        "percentual",
        round((acertos / total) * 100, 1) if total else 0,
    )

    tabela_dados = [
        ["QUESTÕES", "ACERTOS", "ERROS", "APROVEITAMENTO"],
        [
            str(total),
            str(acertos),
            str(erros),
            f"{percentual}%",
        ],
    ]

    tabela = Table(
        tabela_dados,
        colWidths=[
            4 * cm,
            4 * cm,
            4 * cm,
            LARGURA_UTIL - 12 * cm,
        ],
    )

    tabela.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COR_TEXTO),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BACKGROUND", (0, 1), (-1, 1), COR_FUNDO),
            ("TEXTCOLOR", (0, 1), (-1, 1), colors.black),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOX", (0, 0), (-1, -1), 0.6, colors.grey),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )

    elementos.append(tabela)
    elementos.append(Spacer(1, 12))


# ============================================================
# CARREGAMENTO DE IMAGENS
# ============================================================

def preparar_url_imagem(url):

    partes = urlsplit(url)

    parametros = dict(
        parse_qsl(partes.query)
    )

    parametros["dl"] = "1"

    return urlunsplit((
        partes.scheme,
        partes.netloc,
        partes.path,
        urlencode(parametros),
        partes.fragment,
    ))


def carregar_imagem_questao(url, estilos):

    if not url:
        return None

    try:

        resposta = requests.get(
            preparar_url_imagem(url),
            timeout=30,
            headers={
                "User-Agent": "Mozilla/5.0"
            },
        )

        resposta.raise_for_status()

        imagem_bytes = BytesIO(resposta.content)

        leitor = ImageReader(imagem_bytes)

        largura_original, altura_original = leitor.getSize()

        if largura_original <= 0 or altura_original <= 0:
            raise ValueError("Dimensões inválidas.")

        largura_maxima = LARGURA_UTIL - 0.8 * cm
        altura_maxima = 8 * cm

        escala = min(
            largura_maxima / largura_original,
            altura_maxima / altura_original,
            1,
        )

        imagem_bytes.seek(0)

        imagem = ReportLabImage(
            imagem_bytes,
            width=largura_original * escala,
            height=altura_original * escala,
        )

        imagem.hAlign = "CENTER"

        return imagem

    except Exception as erro:

        print(
            f"Erro ao carregar imagem da questão: {erro}"
        )

        return Paragraph(
            "<b>[Imagem da questão não pôde ser carregada.]</b>",
            estilos["pequeno"],
        )


# ============================================================
# RESPOSTA DO USUÁRIO E GABARITO
# ============================================================

def obter_respostas(questao):

    marcada = questao.get(
        "marcada",
        questao.get(
            "resposta_usuario",
            questao.get(
                "resposta_marcada",
                "Não informada",
            ),
        ),
    )

    gabarito = questao.get(
        "gabarito",
        questao.get(
            "resposta_correta",
            questao.get(
                "resposta",
                "Não informada",
            ),
        ),
    )

    return marcada, gabarito


# ============================================================
# TABELA DE RESPOSTAS DO CADERNO DE ERROS
# ============================================================

def criar_tabela_respostas(questao, largura):

    marcada, gabarito = obter_respostas(questao)

    texto_marcada = (
        f"<b>Você marcou:</b> "
        f"<font color='#DC5555'>{escape(str(marcada))}</font>"
    )

    texto_gabarito = (
        f"<b>Gabarito oficial:</b> "
        f"<font color='#25A56A'>{escape(str(gabarito))}</font>"
    )

    tabela = Table(
        [[
            Paragraph(
                texto_marcada,
                ParagraphStyle(
                    "RespostaMarcada",
                    fontName="Helvetica-Bold",
                    fontSize=9,
                    leading=12,
                ),
            ),

            Paragraph(
                texto_gabarito,
                ParagraphStyle(
                    "RespostaCorreta",
                    fontName="Helvetica-Bold",
                    fontSize=9,
                    leading=12,
                ),
            ),
        ]],
        colWidths=[
            largura / 2,
            largura / 2,
        ],
    )

    tabela.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COR_FUNDO),
            ("BOX", (0, 0), (-1, -1), 0.5, COR_BORDA),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )

    return tabela


# ============================================================
# MOTIVOS DO ERRO
# ============================================================

def adicionar_motivos_erro(questao, linhas, estilos, largura):

    motivo_selecionado = questao.get(
        "motivo_erro",
        "",
    )

    motivo_normalizado = str(
        motivo_selecionado
    ).strip().casefold()

    linhas.append([
        Paragraph(
            "<b>Motivo do erro:</b>",
            estilos["subtitulo"],
        )
    ])

    colunas = [
        3.7 * cm,
        3.5 * cm,
        6.2 * cm,
        largura - 13.4 * cm,
    ]

    celulas = []

    for motivo in MOTIVOS_ERRO:

        marcado = (
            motivo.casefold() == motivo_normalizado
        )

        checkbox = "[x]" if marcado else "[ ]"

        celulas.append(
            Paragraph(
                f"{checkbox} {escape(motivo)}",
                estilos["motivo"],
            )
        )

    tabela = Table(
        [celulas],
        colWidths=colunas,
    )

    tabela.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ])
    )

    linhas.append([tabela])

    if motivo_normalizado == "outro":

        linhas.append([
            Paragraph(
                "[x] Outro: ______________________________",
                estilos["motivo"],
            )
        ])

    else:

        linhas.append([
            Paragraph(
                "[ ] Outro: ______________________________",
                estilos["motivo"],
            )
        ])


# ============================================================
# ÁREA ÚNICA DE RESOLUÇÃO / ANOTAÇÕES
# ============================================================

def adicionar_area_resolucao_anotacoes(
    linhas,
    largura,
    estilos,
    altura=5 * cm,
):
    """
    Cria uma única área em branco para resolução e anotações.
    Substitui os espaços separados utilizados anteriormente.
    """

    linhas.append([
        Spacer(1, 8)
    ])

    linhas.append([
        Paragraph(
            "RESOLUÇÃO / ANOTAÇÕES",
            estilos["anotacao"],
        )
    ])

    area = Table(
        [[""]],
        colWidths=[largura],
        rowHeights=[altura],
    )

    area.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.6, COR_BORDA),
            ("BACKGROUND", (0, 0), (-1, -1), colors.white),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ])
    )

    linhas.append([area])


# ============================================================
# CABEÇALHO VISUAL DE CADA QUESTÃO
# ============================================================

def criar_cabecalho_questao(
    questao,
    numero,
    estilos,
    largura_interna,
):

    identificacao = obter_identificacao_questao(
        questao
    )

    cabecalho = Table(
        [[
            Paragraph(
                f"Questão {numero}",
                estilos["cabecalho_questao"],
            ),

            Paragraph(
                f"({escape(identificacao)})",
                estilos["identificacao"],
            ),
        ]],
        colWidths=[
            3.2 * cm,
            largura_interna - 3.2 * cm,
        ],
    )

    cabecalho.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COR_CABECALHO),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ])
    )

    return cabecalho


# ============================================================
# ADICIONAR ENUNCIADO, IMAGEM E ALTERNATIVAS
# ============================================================

def adicionar_conteudo_questao(
    questao,
    linhas,
    estilos,
):
    """
    Adiciona o enunciado, a imagem e as alternativas.
    Utilizado pelos dois modelos de PDF.
    """

    enunciado = questao.get(
        "enunciado_completo",
        questao.get(
            "enunciado",
            "Enunciado não informado.",
        ),
    )

    linhas.append([
        Paragraph(
            escape(str(enunciado)).replace(
                "\n",
                "<br/>",
            ),
            estilos["questao"],
        )
    ])

    telegram_config = questao.get(
        "telegram_config",
        {},
    ) or {}

    imagem_url = (
        questao.get("imagem_url")
        or telegram_config.get("imagem_url")
    )

    imagem = carregar_imagem_questao(
        imagem_url,
        estilos,
    )

    if imagem:

        linhas.append([Spacer(1, 5)])
        linhas.append([imagem])
        linhas.append([Spacer(1, 5)])

    alternativas = questao.get(
        "alternativas",
        {},
    )

    if isinstance(alternativas, dict):

        for letra, texto in alternativas.items():

            linhas.append([
                Paragraph(
                    f"<b>{escape(str(letra))})</b> "
                    f"{escape(str(texto))}",
                    estilos["normal"],
                )
            ])

    elif isinstance(alternativas, list):

        for indice, texto in enumerate(alternativas):

            letra = chr(65 + indice)

            linhas.append([
                Paragraph(
                    f"<b>{letra})</b> "
                    f"{escape(str(texto))}",
                    estilos["normal"],
                )
            ])


# ============================================================
# MONTAGEM DA QUESTÃO DO CADERNO DE ERROS
# ============================================================

def adicionar_questao(questao, numero, elementos, estilos):

    largura_interna = LARGURA_UTIL - 0.5 * cm

    linhas = []

    cabecalho = criar_cabecalho_questao(
        questao,
        numero,
        estilos,
        largura_interna,
    )

    linhas.append([cabecalho])

    adicionar_conteudo_questao(
        questao,
        linhas,
        estilos,
    )

    linhas.append([Spacer(1, 5)])

    linhas.append([
        criar_tabela_respostas(
            questao,
            largura_interna,
        )
    ])

    comentario = questao.get(
        "comentario",
        "",
    )

    if comentario:

        linhas.append([
            Paragraph(
                "COMENTÁRIO / EXPLICAÇÃO",
                estilos["subtitulo"],
            )
        ])

        linhas.append([
            Paragraph(
                escape(str(comentario)).replace(
                    "\n",
                    "<br/>",
                ),
                estilos["questao"],
            )
        ])

    adicionar_motivos_erro(
        questao,
        linhas,
        estilos,
        largura_interna,
    )

    # Uma única área para resolução e anotações
    adicionar_area_resolucao_anotacoes(
        linhas,
        largura_interna,
        estilos,
        altura=5 * cm,
    )

    tabela_questao = Table(
        linhas,
        colWidths=[LARGURA_UTIL],
        splitByRow=1,
        hAlign="LEFT",
    )

    tabela_questao.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, COR_BORDA),
            ("BACKGROUND", (0, 0), (-1, 0), COR_CABECALHO),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LINEBELOW", (0, 0), (-1, 0), 0.6, COR_BORDA),
        ])
    )

    elementos.append(tabela_questao)
    elementos.append(Spacer(1, 15))


# ============================================================
# MONTAGEM DA QUESTÃO PARA RESOLUÇÃO
# ============================================================

def adicionar_questao_resolucao(
    questao,
    numero,
    elementos,
    estilos,
):
    """
    Monta uma questão sem resposta marcada, gabarito,
    comentário, motivo de erro ou desempenho.
    """

    largura_interna = LARGURA_UTIL - 0.5 * cm

    linhas = []

    cabecalho = criar_cabecalho_questao(
        questao,
        numero,
        estilos,
        largura_interna,
    )

    linhas.append([cabecalho])

    adicionar_conteudo_questao(
        questao,
        linhas,
        estilos,
    )

    # Uma única área para resolução e anotações
    adicionar_area_resolucao_anotacoes(
        linhas,
        largura_interna,
        estilos,
        altura=5 * cm,
    )

    tabela_questao = Table(
        linhas,
        colWidths=[LARGURA_UTIL],
        splitByRow=1,
        hAlign="LEFT",
    )

    tabela_questao.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, COR_BORDA),
            ("BACKGROUND", (0, 0), (-1, 0), COR_CABECALHO),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LINEBELOW", (0, 0), (-1, 0), 0.6, COR_BORDA),
        ])
    )

    elementos.append(tabela_questao)
    elementos.append(Spacer(1, 15))


# ============================================================
# FUNÇÃO PRINCIPAL — CADERNO DE ERROS
# ============================================================

def gerar_pdf_erros(dados):
    """
    Gera o Caderno de Erros em PDF.

    Inclui:
    - Identificação da banca, órgão, cargo e ano;
    - Enunciado;
    - Imagem, quando disponível;
    - Alternativas;
    - Resposta marcada;
    - Gabarito oficial;
    - Comentário;
    - Motivo do erro;
    - Área de resolução e anotações;
    - Desempenho do bloco.

    Retorna um arquivo BytesIO.
    """

    arquivo = BytesIO()

    documento = SimpleDocTemplate(
        arquivo,
        pagesize=A4,
        rightMargin=MARGEM_DIREITA,
        leftMargin=MARGEM_ESQUERDA,
        topMargin=1.5 * cm,
        bottomMargin=1.7 * cm,
        title="Caderno de Erros",
        author="Bot de Questões",
    )

    estilos = criar_estilos()
    elementos = []

    adicionar_cabecalho(
        dados,
        elementos,
        estilos,
    )

    adicionar_desempenho(
        dados,
        elementos,
        estilos,
    )

    questoes_erradas = dados.get(
        "questoes_erradas",
        [],
    )

    elementos.append(
        Paragraph(
            f"QUESTÕES PARA REVISÃO: {len(questoes_erradas)}",
            estilos["subtitulo"],
        )
    )

    for numero, questao in enumerate(
        questoes_erradas,
        start=1,
    ):

        adicionar_questao(
            questao,
            numero,
            elementos,
            estilos,
        )

    if not questoes_erradas:

        elementos.append(
            Paragraph(
                "Nenhuma questão errada foi registrada neste bloco.",
                estilos["normal"],
            )
        )

    documento.build(
        elementos,
        onFirstPage=adicionar_numero_pagina,
        onLaterPages=adicionar_numero_pagina,
    )

    arquivo.seek(0)

    return arquivo


# ============================================================
# FUNÇÃO PRINCIPAL — PDF DE RESOLUÇÃO
# ============================================================

def gerar_pdf_resolucao(dados):
    """
    Gera um PDF independente para resolução de questões.

    Inclui:
    - Identificação da banca, órgão, cargo e ano;
    - Enunciado;
    - Imagem, quando disponível;
    - Alternativas;
    - Uma única área de resolução e anotações.

    Não inclui:
    - Resposta marcada;
    - Gabarito;
    - Comentários;
    - Motivos de erro;
    - Desempenho do usuário.

    Retorna um arquivo BytesIO.
    """

    arquivo = BytesIO()

    documento = SimpleDocTemplate(
        arquivo,
        pagesize=A4,
        rightMargin=MARGEM_DIREITA,
        leftMargin=MARGEM_ESQUERDA,
        topMargin=1.5 * cm,
        bottomMargin=1.7 * cm,
        title="Resolução de Questões",
        author="Bot de Questões",
    )

    estilos = criar_estilos()
    elementos = []

    adicionar_cabecalho_resolucao(
        dados,
        elementos,
        estilos,
    )

    questoes = dados.get(
        "questoes",
        [],
    )

    elementos.append(
        Paragraph(
            f"QUESTÕES DO BLOCO: {len(questoes)}",
            estilos["subtitulo"],
        )
    )

    for numero, questao in enumerate(
        questoes,
        start=1,
    ):

        adicionar_questao_resolucao(
            questao,
            numero,
            elementos,
            estilos,
        )

    if not questoes:

        elementos.append(
            Paragraph(
                "Nenhuma questão foi encontrada neste bloco.",
                estilos["normal"],
            )
        )

    documento.build(
        elementos,
        onFirstPage=adicionar_numero_pagina,
        onLaterPages=adicionar_numero_pagina,
    )

    arquivo.seek(0)

    return arquivo
