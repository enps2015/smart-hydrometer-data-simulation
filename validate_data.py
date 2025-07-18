
import pandas as pd
import os

output_dir = 'simulacao_hidrometros_por_mes_cidade'

# Encontrar um arquivo de exemplo para validação
example_file = None
for root, dirs, files in os.walk(output_dir):
    for file in files:
        if file.endswith('.csv'):
            example_file = os.path.join(root, file)
            break
    if example_file: # Se encontrou, para o loop externo
        break

if example_file:
    print(f"Carregando o arquivo CSV de exemplo para validação: {example_file}")
    df = pd.read_csv(example_file)

    print("\nVerificando as primeiras linhas do DataFrame:")
    print(df.head())

    print("\nVerificando informações gerais do DataFrame (tipos de dados, valores nulos):")
    print(df.info())

    print("\nVerificando a contagem de valores únicos para 'status_hidrometro':")
    print(df["status_hidrometro"].value_counts())

    print("\nVerificando a contagem de alertas de vazamento:")
    print(df["alerta_vazamento"].value_counts())

    print("\nVerificando a contagem de alertas de fraude:")
    print(df["alerta_fraude"].value_counts())

    print("\nVerificando a presença de valores nulos no consumo_m3 (falhas de comunicação):")
    print(df["consumo_m3"].isnull().sum())

    print("\nValidação básica concluída para o arquivo de exemplo. Verifique os resultados acima.")
else:
    print(f"Nenhum arquivo CSV encontrado na pasta {output_dir} para validação.")


