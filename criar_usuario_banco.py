import random
import string
import database
import usuarios

def gerar_credenciais_seguras(nome_completo):
    # Pega apenas o primeiro nome, remove espaços e coloca em minúsculo
    primeiro_nome = nome_completo.strip().split()[0].lower()
    tamanho_nome = len(primeiro_nome)
    
    # 1. GERAR LOGIN DE EXATAMENTE 15 CARACTERES
    if tamanho_nome >= 15:
        login_gerado = primeiro_nome[:15]
    else:
        caracteres_restantes = 15 - tamanho_nome
        numeros_aleatorios = "".join(random.choices(string.digits, k=caracteres_restantes))
        login_gerado = f"{primeiro_nome}{numeros_aleatorios}"
        
    # 2. GERAR SENHA DE EXATAMENTE 10 CARACTERES (Letras e Números)
    caracteres_senha = string.ascii_letters + string.digits
    
    # Loop garante que a senha NUNCA será igual ao login
    while True:
        senha_gerada = "".join(random.choices(caracteres_senha, k=10)) # Mudado para 10
        if senha_gerada != login_gerado:
            break
            
    return login_gerado, senha_gerada

def gerar_usuario_teste():
    print("Conectando ao banco de dados...")
    if not database.testar_conexao():
        print("Erro: Não foi possível conectar ao banco.")
        return

    # ============================================================
    # ALTERE APENAS O NOME DO ALUNO ABAIXO MANUALMENTE
    # ============================================================
    nome_teste = "cavalcante"

    # Gera o login (15 car.) e a senha (10 car.) seguindo as suas regras
    login_teste, senha_teste = gerar_credenciais_seguras(nome_teste)

    # 3. VERIFICAÇÃO NO BANCO: Garante que o login gerado já não existe
    usuario_existente = usuarios.buscar_por_login(login_teste)
    if usuario_existente:
        print(f"\n⚠️ O login gerado '{login_teste}' já existe por coincidência no banco. Execute novamente para gerar outro.")
        return

    # Cria o usuário usando a sua função do usuarios.py (que gera o hash correto)
    resultado_id = usuarios.criar_usuario(login_teste, senha_teste, nome_teste)

    if resultado_id:
        print("\n============================================================")
        print("✅ NOVO USUÁRIO GERADO COM SUCESSO!")
        print(f"👤 Nome do Aluno:  {nome_teste}")
        print(f"🔑 Login (15 car.): {login_teste}")
        print(f"🔒 Senha (10 car.): {senha_teste}")
        print("============================================================")
        print("As credenciais foram salvas criptografadas de forma segura.")
    else:
        print("\n❌ Erro ao criar o usuário.")

if __name__ == "__main__":
    gerar_usuario_teste()
