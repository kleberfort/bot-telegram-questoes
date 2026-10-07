from database import colecao_usuarios
import bcrypt


# ============================================================
# CRIAR USUÁRIO
# ============================================================

def criar_usuario(login, senha, nome):

    usuario_existente = colecao_usuarios.find_one({
        "login": login
    })

    if usuario_existente:
        return None

    senha_hash = bcrypt.hashpw(
        senha.encode("utf-8"),
        bcrypt.gensalt()
    )

    usuario = {
        "login": login,
        "senha_hash": senha_hash,
        "nome": nome,
        "ativo": True
    }

    resultado = colecao_usuarios.insert_one(usuario)

    return resultado.inserted_id


# ============================================================
# BUSCAR USUÁRIO PELO LOGIN
# ============================================================

def buscar_por_login(login):

    return colecao_usuarios.find_one({
        "login": login
    })


# ============================================================
# VALIDAR LOGIN E SENHA
# ============================================================

def autenticar(login, senha):

    usuario = buscar_por_login(login)

    if usuario is None:
        return None

    senha_correta = bcrypt.checkpw(
        senha.encode("utf-8"),
        usuario["senha_hash"]
    )

    if not senha_correta:
        return None

    if not usuario.get("ativo", True):
        return None

    return usuario


# ============================================================
# VINCULAR TELEGRAM AO USUÁRIO
# ============================================================

def vincular_telegram(login, telegram_id):

    colecao_usuarios.update_one(
        {
            "login": login
        },
        {
            "$set": {
                "telegram_id": telegram_id
            }
        }
    )


# ============================================================
# BUSCAR USUÁRIO PELO TELEGRAM_ID
# ============================================================

def buscar_por_telegram(telegram_id):

    return colecao_usuarios.find_one({
        "telegram_id": telegram_id,
        "ativo": True
    })

# ============================================================
# DESVINCULAR TELEGRAM DO USUÁRIO
# ============================================================

def desvincular_telegram(telegram_id):

    resultado = colecao_usuarios.update_one(
        {
            "telegram_id": telegram_id
        },
        {
            "$unset": {
                "telegram_id": ""
            }
        }
    )

    return resultado.modified_count > 0