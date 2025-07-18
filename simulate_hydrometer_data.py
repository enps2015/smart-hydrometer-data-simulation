
import pandas as pd
import numpy as np
import random
import os
from datetime import datetime, timedelta
from bairros_por_cidade import BAIRROS_POR_CIDADE

# --- Configurações da Simulação ---
NUM_HIDROMETROS = 500  # Número total de hidrômetros
MESES_SIMULACAO = 12    # Duração da simulação em meses
DATA_INICIO = datetime(2024, 1, 1) # Data de início da simulação

# Cidades e regiões do Brasil
CIDADES = {
    'Norte': ['Belém', 'Manaus'],
    'Nordeste': ['Recife', 'Salvador'],
    'Sudeste': ['São Paulo', 'Rio de Janeiro'],
    'Sul': ['Porto Alegre', 'Curitiba']
}

PERFIS_SOCIOECONOMICOS = ['Alta', 'Média', 'Baixa']

# --- Geração de Dados Base ---
def gerar_dados_base(num_hidrometros, data_inicio, meses_simulacao):
    hidrometros = []
    for i in range(num_hidrometros):
        id_hidrometro = f'HID_{i:05d}'
        regiao = random.choice(list(CIDADES.keys()))
        cidade = random.choice([c for c in CIDADES[regiao] if c in BAIRROS_POR_CIDADE])
        perfil = random.choice(PERFIS_SOCIOECONOMICOS)
        bairro = random.choice(BAIRROS_POR_CIDADE[cidade][perfil])

        hidrometros.append({
            'id_hidrometro': id_hidrometro,
            'regiao_brasil': regiao,
            'nome_cidade': cidade,
            'bairro': bairro,
            'perfil_socioeconomico': perfil
        })
    
    df_hidrometros = pd.DataFrame(hidrometros)

    # Geração de timestamps (horário)
    # Ajuste para garantir 12 meses completos, considerando dias em cada mês
    total_hours = 0
    current_date = data_inicio
    for _ in range(meses_simulacao):
        days_in_month = (current_date.replace(month=current_date.month%12+1, day=1) - timedelta(days=1)).day
        total_hours += days_in_month * 24
        current_date = current_date.replace(month=current_date.month%12+1, day=1)

    datas = [data_inicio + timedelta(hours=h) for h in range(total_hours)]
    
    dados = []
    for _, row in df_hidrometros.iterrows():
        for data in datas:
            dados.append({
                'id_hidrometro': row['id_hidrometro'],
                'timestamp': data,
                'regiao_brasil': row['regiao_brasil'],
                'nome_cidade': row['nome_cidade'],
                'bairro': row['bairro'],
                'perfil_socioeconomico': row['perfil_socioeconomico'],
                'status_hidrometro': 'OK',
                'alerta_vazamento': False,
                'alerta_fraude': False
            })
            
    df = pd.DataFrame(dados)
    return df

def simular_consumo(df):
    # Consumo base por perfil socioeconômico (m³/hora)
    consumo_base = {
        'Alta': 0.15,  # Maior consumo
        'Média': 0.10,
        'Baixa': 0.05   # Menor consumo
    }

    # Variação diária (picos de manhã e noite)
    def variacao_diaria(hour):
        if 6 <= hour < 9: return 1.5 # Manhã
        if 18 <= hour < 22: return 1.8 # Noite
        if 0 <= hour < 5: return 0.2 # Madrugada
        return 1.0 # Resto do dia

    # Variação sazonal (ex: verão maior consumo)
    def variacao_sazonal(month):
        if 12 <= month or month <= 2: return 1.2 # Verão
        if 6 <= month <= 8: return 0.8 # Inverno
        return 1.0 # Outras estações

    df['consumo_m3'] = df.apply(lambda row:
        consumo_base[row['perfil_socioeconomico']] *
        variacao_diaria(row['timestamp'].hour) *
        variacao_sazonal(row['timestamp'].month) +
        np.random.normal(0, 0.01), axis=1 # Adiciona ruído
    )
    df['consumo_m3'] = df['consumo_m3'].apply(lambda x: max(0, x)) # Garante consumo não negativo

    # Vazão instantânea (simplificada como consumo_m3 * fator)
    df['vazao_instantanea_m3h'] = df['consumo_m3'] * 10 # Fator arbitrário para simular vazão
    
    # Temperatura local (simulação simples baseada no mês)
    df['temperatura_local_c'] = df['timestamp'].apply(lambda x: 25 + 5 * np.sin(x.month * (2 * np.pi / 12)) + np.random.normal(0, 2))
    
    # Pressão da rede (simulação com ruído)
    df['pressao_rede_bar'] = 3.0 + np.random.normal(0, 0.5)

    return df

# --- Injeção de Falhas e Anomalias ---
def injetar_falhas(df):
    # Falhas de Comunicação (dados nulos)
    num_falhas_comunicacao = int(len(df) * 0.001) # 0.1% dos dados
    indices_falha_comunicacao = np.random.choice(df.index, num_falhas_comunicacao, replace=False)
    df.loc[indices_falha_comunicacao, ['consumo_m3', 'vazao_instantanea_m3h', 'temperatura_local_c', 'pressao_rede_bar']] = np.nan
    df.loc[indices_falha_comunicacao, 'status_hidrometro'] = 'FALHA_COMUNICACAO'

    # Leituras Incorretas (valores absurdos)
    num_leituras_incorretas = int(len(df) * 0.0005) # 0.05% dos dados
    indices_leituras_incorretas = np.random.choice(df.index, num_leituras_incorretas, replace=False)
    df.loc[indices_leituras_incorretas, 'consumo_m3'] = np.random.uniform(100, 500) # Valores muito altos
    df.loc[indices_leituras_incorretas, 'vazao_instantanea_m3h'] = np.random.uniform(1000, 5000)
    df.loc[indices_leituras_incorretas, 'status_hidrometro'] = 'LEITURA_INCORRETA'

    # Bateria Fraca (afeta um hidrômetro por um período)
    num_hidrometros_bateria_fraca = int(NUM_HIDROMETROS * 0.02) # 2% dos hidrômetros
    hidrometros_bateria_fraca = np.random.choice(df['id_hidrometro'].unique(), num_hidrometros_bateria_fraca, replace=False)
    for hid in hidrometros_bateria_fraca:
        hid_df = df[df['id_hidrometro'] == hid]
        if not hid_df.empty:
            start_idx = random.randint(0, len(hid_df) - 24*7) # Pelo menos 1 semana de dados
            end_idx = start_idx + random.randint(24*3, 24*7) # 3 a 7 dias de bateria fraca
            df.loc[hid_df.index[start_idx:end_idx], 'status_hidrometro'] = 'BATERIA_FRACA'
            # Simula que o consumo pode ser zero ou inconsistente quando a bateria está fraca
            df.loc[hid_df.index[start_idx:end_idx], 'consumo_m3'] = 0
            df.loc[hid_df.index[start_idx:end_idx], 'vazao_instantanea_m3h'] = 0

    # Vazamentos Lentos (consumo contínuo em horas de baixo uso)
    # Identifica hidrômetros aleatoriamente para ter vazamento
    num_hidrometros_vazamento = int(NUM_HIDROMETROS * 0.05) # 5% dos hidrômetros
    hidrometros_vazamento = np.random.choice(df['id_hidrometro'].unique(), num_hidrometros_vazamento, replace=False)
    for hid in hidrometros_vazamento:
        # Aplica um pequeno consumo constante durante a madrugada
        df.loc[(df['id_hidrometro'] == hid) & (df['timestamp'].dt.hour.isin([0, 1, 2, 3, 4])),
               'consumo_m3'] += np.random.uniform(0.01, 0.05) # Pequeno vazamento
        df.loc[(df['id_hidrometro'] == hid) & (df['timestamp'].dt.hour.isin([0, 1, 2, 3, 4])),
               'alerta_vazamento'] = True

    # Fraudes (consumo zerado por um longo período em hidrômetros ativos)
    num_hidrometros_fraude = int(NUM_HIDROMETROS * 0.03) # 3% dos hidrômetros
    hidrometros_fraude = np.random.choice(df['id_hidrometro'].unique(), num_hidrometros_fraude, replace=False)
    for hid in hidrometros_fraude:
        hid_df = df[df['id_hidrometro'] == hid]
        if not hid_df.empty:
            # Escolhe um período de fraude (ex: 1 a 3 meses)
            start_idx = random.randint(0, len(hid_df) - 24*30*3) # Pelo menos 3 meses de dados
            end_idx = start_idx + random.randint(24*30, 24*30*3) # 1 a 3 meses de fraude
            df.loc[hid_df.index[start_idx:end_idx], 'consumo_m3'] = 0
            df.loc[hid_df.index[start_idx:end_idx], 'vazao_instantanea_m3h'] = 0
            df.loc[hid_df.index[start_idx:end_idx], 'alerta_fraude'] = True
            df.loc[hid_df.index[start_idx:end_idx], 'status_hidrometro'] = 'SUSPEITA_FRAUDE'

    return df

# --- Execução da Simulação ---
if __name__ == '__main__':
    print('Gerando dados base...')
    df_simulacao = gerar_dados_base(NUM_HIDROMETROS, DATA_INICIO, MESES_SIMULACAO)
    print('Simulando consumo...')
    df_simulacao = simular_consumo(df_simulacao)
    print('Injetando falhas e anomalias...')
    df_simulacao = injetar_falhas(df_simulacao)

    # Reordenar colunas para corresponder ao schema definido
    colunas_ordenadas = [
        'id_hidrometro', 'timestamp', 'consumo_m3', 'vazao_instantanea_m3h',
        'status_hidrometro', 'alerta_vazamento', 'alerta_fraude',
        'temperatura_local_c', 'pressao_rede_bar', 'nome_cidade',
        'regiao_brasil', 'bairro', 'perfil_socioeconomico'
    ]
    df_simulacao = df_simulacao[colunas_ordenadas]

    # Converter timestamp para datetime para facilitar a filtragem
    df_simulacao['timestamp'] = pd.to_datetime(df_simulacao['timestamp'])

    print('Salvando dados por mês e cidade...')
    output_dir = 'simulacao_hidrometros_por_mes_cidade'
    os.makedirs(output_dir, exist_ok=True)

    for month in range(1, MESES_SIMULACAO + 1):
        df_mes = df_simulacao[df_simulacao['timestamp'].dt.month == month]
        for cidade in df_mes['nome_cidade'].unique():
            df_final = df_mes[df_mes['nome_cidade'] == cidade].copy()
            
            # Gerar nome do arquivo
            month_name = datetime(2024, month, 1).strftime('%B').lower() # Nome do mês
            file_name_base = f'hidrometros_{cidade.replace(" ", "_").lower()}_{month_name}'
            
            # Salvar para CSV
            csv_path = os.path.join(output_dir, f'{file_name_base}.csv')
            df_final.to_csv(csv_path, index=False)
            
            # Salvar para Parquet
            parquet_path = os.path.join(output_dir, f'{file_name_base}.parquet')
            df_final.to_parquet(parquet_path, index=False)
            print(f'Salvo: {file_name_base}.csv e .parquet')

    print('Simulação concluída! Arquivos gerados na pasta simulacao_hidrometros_por_mes_cidade.')


