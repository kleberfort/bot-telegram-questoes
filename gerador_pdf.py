
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
    LARGURA_PAGINA - MARGEM_ESQUERDA - MARGEM_DIREITA
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
            fontSize=8.5,
            leading=12,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#52647A"),
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
# CABEÇALHO DO CADERNO
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
# DESEMPENHO
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
# IDENTIFICAÇÃO DA BANCA / ÓRGÃO / CARGO / ANO
# ============================================================

def obter_identificacao_questao(questao):

    banca = questao.get("banca", "")
    orgao = (
        questao.get("orgao")
        or questao.get("órgão")
        or questao.get("tribunal")
        or ""
    )

    cargo = questao.get("cargo", "")
    ano = questao.get("ano", "")

    partes = [
        str(valor)
        for valor in [banca, orgao, cargo, ano]
        if valor
    ]

    if not partes:
        return "Identificação não informada"

    return " / ".join(partes)


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

    # Aceita o formato novo e o formato anterior.

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
            Paragraph(texto_marcada, ParagraphStyle(
                "RespostaMarcada",
                fontName="Helvetica-Bold",
                fontSize=9,
                leading=12,
            )),

            Paragraph(texto_gabarito, ParagraphStyle(
                "RespostaCorreta",
                fontName="Helvetica-Bold",
                fontSize=9,
                leading=12,
            )),
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

    # Identifica automaticamente o motivo informado.
    # Os demais ficam disponíveis para marcação manual.

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

    # Outro, caso tenha sido selecionado.

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

    # --------------------------------------------------------
    # EXPLICAÇÃO DO ERRO
    # --------------------------------------------------------

    linhas.append([
        Paragraph(
            "<b>Por que errei / Conceito-chave para memorizar:</b>",
            estilos["normal"],
        )
    ])

    # Linhas para escrita manual.

    for _ in range(3):

        linhas.append([""])

    return linhas


# ============================================================
# ÁREA PARA ANOTAÇÕES
# ============================================================

def adicionar_area_anotacoes(linhas, largura, estilos):

    linhas.append([
        Paragraph(
            "ANOTAÇÕES",
            estilos["anotacao"],
        )
    ])

    area = Table(
        [[""]],
        colWidths=[largura],
        rowHeights=[5 * cm],
    )

    area.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.6, COR_BORDA),
            ("BACKGROUND", (0, 0), (-1, -1), colors.white),

            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
        ])
    )

    linhas.append([area])

    linhas.append([
        Paragraph(
            "[ ] QUESTÃO REVISADA",
            estilos["normal"],
        )
    ])


# ============================================================
# MONTAGEM DA QUESTÃO COM BORDA EXTERNA
# ============================================================

def adicionar_questao(questao, numero, elementos, estilos):

    # Largura interna da moldura.

    largura_interna = LARGURA_UTIL - 0.5 * cm

    linhas = []

    # --------------------------------------------------------
    # 1. IDENTIFICAÇÃO DA QUESTÃO
    # --------------------------------------------------------

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

    linhas.append([cabecalho])

    # --------------------------------------------------------
    # 2. ENUNCIADO
    # --------------------------------------------------------

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
                "<br/>"
            ),
            estilos["questao"],
        )
    ])

    # --------------------------------------------------------
    # 3. IMAGEM
    # --------------------------------------------------------

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

        linhas.append([
            Spacer(1, 5)
        ])

        linhas.append([
            imagem
        ])

        linhas.append([
            Spacer(1, 5)
        ])

    # --------------------------------------------------------
    # 4. ALTERNATIVAS
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # 5. RESPOSTA E GABARITO
    # --------------------------------------------------------

    linhas.append([
        Spacer(1, 5)
    ])

    linhas.append([
        criar_tabela_respostas(
            questao,
            largura_interna,
        )
    ])

    # --------------------------------------------------------
    # 6. COMENTÁRIO / EXPLICAÇÃO
    # --------------------------------------------------------

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
                    "<br/>"
                ),
                estilos["questao"],
            )
        ])

    # --------------------------------------------------------
    # 7. MOTIVO DO ERRO
    # --------------------------------------------------------

    adicionar_motivos_erro(
        questao,
        linhas,
        estilos,
        largura_interna,
    )

    # --------------------------------------------------------
    # 8. ANOTAÇÕES
    # --------------------------------------------------------

    adicionar_area_anotacoes(
        linhas,
        largura_interna,
        estilos,
    )

    # --------------------------------------------------------
    # 9. TABELA EXTERNA COM BORDA
    # --------------------------------------------------------

    tabela_questao = Table(
        linhas,
        colWidths=[LARGURA_UTIL],
        splitByRow=1,
        hAlign="LEFT",
    )

    tabela_questao.setStyle(
        TableStyle([

            # Borda externa envolvendo a questão inteira.

            ("BOX", (0, 0), (-1, -1), 1, COR_BORDA),

            # Fundo do cabeçalho.

            ("BACKGROUND", (0, 0), (-1, 0), COR_CABECALHO),

            # Alinhamento.

            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

            # Espaçamento interno.

            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),

            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),

            # Separação entre cabeçalho e conteúdo.

            ("LINEBELOW", (0, 0), (-1, 0), 0.6, COR_BORDA),

        ])
    )

    elementos.append(
        tabela_questao
    )

    elementos.append(
        Spacer(1, 15)
    )


# ============================================================
# FUNÇÃO PRINCIPAL
# ============================================================

def gerar_pdf_erros(dados):

    """
    Gera o Caderno de Erros em PDF.

    Parâmetro:
        dados: dicionário contendo os dados do bloco.

    Retorno:
        BytesIO: arquivo PDF em memória.
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

    # --------------------------------------------------------
    # CABEÇALHO
    # --------------------------------------------------------

    adicionar_cabecalho(
        dados,
        elementos,
        estilos,
    )

    # --------------------------------------------------------
    # DESEMPENHO
    # --------------------------------------------------------

    adicionar_desempenho(
        dados,
        elementos,
        estilos,
    )

    # --------------------------------------------------------
    # QUESTÕES PARA REVISÃO
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # GERAR CADA QUESTÃO
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # NENHUMA QUESTÃO ERRADA
    # --------------------------------------------------------

    if not questoes_erradas:

        elementos.append(
            Paragraph(
                "Nenhuma questão errada foi registrada neste bloco.",
                estilos["normal"],
            )
        )

    # --------------------------------------------------------
    # CONSTRUIR PDF
    # --------------------------------------------------------

    documento.build(
        elementos,

        onFirstPage=adicionar_numero_pagina,
        onLaterPages=adicionar_numero_pagina,
    )

    arquivo.seek(0)

    return arquivo
