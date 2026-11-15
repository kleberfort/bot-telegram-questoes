
from pymongo import MongoClient
from config import MONGODB_URI

# ============================================================
# CONEXÃO COM MONGODB
# ============================================================

if not MONGODB_URI:
    raise ValueError("MONGODB_URI não foi configurada.")

cliente = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=30000,
    connectTimeoutMS=20000
)

# ============================================================
# BANCO DE DADOS
# ============================================================

banco = cliente["questoes_concurso"]

# ============================================================
# COLEÇÕES
# ============================================================

# Coleção das questões
colecao = banco["questoes"]

# Coleção dos usuários
colecao_usuarios = banco["usuarios"]

# Comentários personalizados dos usuários
colecao_comentarios = banco["comentarios_usuarios"]

# Vínculos entre usuários e questões
colecao_questoes_usuarios = banco["questoes_usuarios"]

# Histórico de desempenho
colecao_desempenho = banco["desempenho_usuarios"]

# Nova coleção: cronogramas semanais
colecao_cronogramas = banco["cronogramas_usuarios"]


# ============================================================
# ÍNDICE DO DESEMPENHO
# ============================================================

colecao_desempenho.create_index(
    [
        ("login_user", 1),
        ("tentativa_id", 1)
    ],
    unique=True
)


# ============================================================
# ÍNDICE DOS CRONOGRAMAS
# ============================================================

colecao_cronogramas.create_index(
    [
        ("login_user", 1),
        ("semana_inicio", 1)
    ],
    unique=True
)


# ============================================================
# TESTAR CONEXÃO
# ============================================================

def testar_conexao():

    try:
        cliente.admin.command("ping")

        print("Conexão com MongoDB estabelecida!")

        return True

    except Exception as erro:

        print(f"Erro ao conectar ao MongoDB: {erro}")

        return False
