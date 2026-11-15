
from datetime import date, timedelta

import repositorio


# Login de um usuário que já existe no seu banco.
LOGIN_TESTE = "kleberfort89788"

# Próxima segunda-feira.
hoje = date.today()

dias_ate_segunda = (0 - hoje.weekday()) % 7

if dias_ate_segunda == 0:
    dias_ate_segunda = 7

segunda = hoje + timedelta(days=dias_ate_segunda)

semana_inicio = segunda.isoformat()


# Consultar cronograma.
cronograma = repositorio.obter_cronograma(
    LOGIN_TESTE,
    semana_inicio
)

print("Semana:", semana_inicio)

print("Dias disponíveis:")

for dia, dados in cronograma["dias"].items():
    print(dia, dados["atividades"])


# Testar cadastro de atividade.
atividade = {
    "tipo": "questoes",
    "disciplina": "Ciência de Dados",
    "topico": "Processamento de Linguagem Natural",
    "assunto": "Pré-processamento de Textos",
    "horario_inicio": "07:00",
    "duracao_minutos": 50,
    "meta_tipo": "questoes",
    "quantidade_questoes": 20
}

salvou = repositorio.salvar_atividade_cronograma(
    LOGIN_TESTE,
    semana_inicio,
    "segunda",
    atividade
)

print("Atividade salva:", salvou)


# Consultar novamente.
cronograma = repositorio.obter_cronograma(
    LOGIN_TESTE,
    semana_inicio
)

print("\nAtividades de segunda-feira:")

for item in cronograma["dias"]["segunda"]["atividades"]:
    print(item)
