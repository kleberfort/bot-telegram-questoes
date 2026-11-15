
from repositorio import (
    obter_cronograma,
    copiar_cronograma_semana_anterior
)

login_user = "kleberfort89788"

semana_origem = "2026-11-16"
semana_destino = "2026-11-23"

resultado = copiar_cronograma_semana_anterior(
    login_user,
    semana_destino,
    semana_origem
)

print("Resultado da cópia:")
print(resultado)

print("\nCronograma da semana de destino:")

cronograma = obter_cronograma(
    login_user,
    semana_destino
)

for dia, dados in cronograma["dias"].items():

    print(f"\n{dia}:")

    for atividade in dados["atividades"]:
        print(atividade)
