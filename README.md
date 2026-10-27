# Smart Hydrometer Data Simulation

Simulações sintéticas de telemetria hídrica para estudos de IoT, analytics, engenharia de dados e cidades inteligentes. O código e as ferramentas de validação ficam no GitHub; as coleções completas de dados são distribuídas pelo Kaggle.

## 📦 Onde estão os dados?

**Fonte oficial dos datasets completos:** [Dados de Hidrômetros Inteligentes Simulados — Kaggle](https://www.kaggle.com/datasets/ericnarciso/dados-de-hidrmetros-inteligentes-simulados).

O repositório GitHub mantém código, testes, documentação e uma pequena amostra sintética. Os arquivos completos ficam no Kaggle para evitar que clones do repositório precisem transferir gigabytes de dados e todo esse volume permaneça no histórico Git.

### Versão 1 — dados mensais CSV e Parquet

- **192 arquivos**: 96 CSV e 96 Parquet.
- Oito cidades, com arquivos organizados por cidade e mês.
- Tamanho de referência: 805.503.910 bytes (aproximadamente 806 MB).
- Indicada para prototipagem, exploração e exemplos de análise.

### Versão 2 — telemetria de maior granularidade

- **60 arquivos `.csv.gz`**: cinco cidades × doze meses de 2024.
- Leituras simuladas em intervalos de 15 minutos, com perfis de consumo, eventos culturais e variáveis ambientais/operacionais.
- Tamanho compactado de referência: 1.572.595.424 bytes (aproximadamente 1,57 GB).
- Indicada para pipelines ETL, séries temporais, detecção de anomalias e experimentos de IoT/TinyML.

### Baixar os dados em Python

Para usar a versão publicada no Kaggle, instale o KaggleHub e baixe o dataset no seu ambiente. O download acontece no ambiente em que o código é executado; não é necessário manter os dados no clone do GitHub.

```bash
python -m pip install kagglehub
```

```python
import kagglehub

dataset_path = kagglehub.dataset_download(
    "ericnarciso/dados-de-hidrmetros-inteligentes-simulados"
)
print(dataset_path)
```

Se estiver usando um Notebook Kaggle com o dataset anexado como entrada, os arquivos já estarão montados em `/kaggle/input`; não é necessário baixar uma segunda cópia.

### Conteúdo que permanece no GitHub

- Scripts de simulação, particionamento e compressão.
- Validador de dados, testes automatizados e integração contínua.
- Uma amostra sintética pequena para executar os testes sem baixar o dataset completo.

**Não adicione datasets completos ao Git.** Use o Kaggle como local de distribuição e versionamento dos arquivos.

## 🚀 Novidades da Versão 2

- **Granularidade de 15 minutos** com 5 perfis de uso (normal, vazamento, fraude, ausência, comercial).
- **Eventos culturais e sazonalidade climática** modulando o consumo.
- **Métricas adicionais** (`pressure_psi`, `temperature_celsius`, `precipitacao_mm`, `anomaly_flag`, `evento_cultural_flag`).
- **Particionamento mensal** pensado para pipelines ETL e cargas incrementais.
- **Distribuição compactada no Kaggle**, mantendo os dados fora do histórico Git. Os arquivos `.csv.gz` podem ser lidos diretamente pelo Pandas ou descompactados com `gzip -d arquivo.csv.gz`.

## 🧪 Validação dos Dados e dos Recortes

### 1. Instalar dependências e validar uma amostra

A validação de demonstração usa uma amostra sintética pequena incluída no repositório. Quando o dataset completo estiver baixado do Kaggle, você também pode apontar o validador para qualquer arquivo CSV ou CSV.GZ.

```bash
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt

# Descobre automaticamente um dataset versionado e valida uma amostra
python validate_data.py

# Valida a amostra sintética incluída no repositório
python validate_data.py --file "samples/v1_sample.csv" --sample-rows 100

# Valida um arquivo completo baixado do Kaggle
python validate_data.py --file "/caminho/para/hidrometros_belém_january.csv" --sample-rows 5000

# Lê um arquivo CSV/CSV.GZ inteiro (pode demorar e consumir mais memória)
python validate_data.py --file "CAMINHO/arquivo.csv.gz" --full
```

A saída informa o caminho e esquema identificados, tamanho da amostra, campos ausentes e uma prévia opcional. Leituras de consumo ausentes são sinalizadas como possíveis falhas de comunicação; nunca são convertidas silenciosamente em zero. Quando o arquivo completo não é lido, as contagens referem-se apenas à amostra.

### 2. Revalidar a integridade dos recortes mensais

**Atenção:** estes scripts reconstroem e verificam o particionamento a partir dos CSVs brutos (`dataset_hidrometros_*.csv`) que precisam existir localmente em `datasets_hidrometros_v2/`. Esses CSVs agregados não fazem parte da coleção publicada no Kaggle descrita neste README; a distribuição contém os recortes mensais compactados (`.csv.gz`). Sem os CSVs brutos originais, não é possível repetir a comparação de integridade entre a fonte agregada e os recortes.

Quando os CSVs brutos originais estiverem disponíveis nessa pasta, execute:

```bash
python3 datasets_hidrometros_v2/separar_por_mes.py
python3 datasets_hidrometros_v2/test_partitioning.py
python3 datasets_hidrometros_v2/comprimir_mensais.py  # gera .csv.gz localmente
```

O último comando apenas regenera cópias compactadas no computador; ele **não** publica dados no GitHub nem no Kaggle. Não versione os datasets completos no Git. Para distribuir uma nova versão, publique a coleção correspondente no Kaggle.

O script `test_partitioning.py` garante que:
- Cabeçalhos coincidam entre original e particionado.
- Contagem de linhas por mês seja idêntica.
- Hash SHA-256 por mês permaneça igual (integridade comprovada).

### 3. Testes automatizados e integração contínua

```bash
python -m pytest -q
```

O GitHub Actions executa os testes de esquema v1/v2, leitura de CSV e CSV.GZ, descoberta de arquivos, validação de valores e execução da CLI. Também valida a amostra sintética pequena incluída no repositório. Os datasets completos são obtidos no Kaggle e não precisam ser baixados pelo CI.


## 🔓 Como descompactar os `.csv.gz`

### Windows

1. Abra o PowerShell ou Windows Terminal na raiz do projeto.
2. Execute:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/descompactar_csv_windows.ps1
```

- Para uma pasta diferente, use `-Source "D:\meus_dados"`.
- O script cria os `.csv` lado a lado e preserva os `.gz`.
- Alternativa manual: instalar [7-Zip](https://www.7-zip.org/) e usar “Extract Here”.

### Linux / WSL / macOS

```bash
bash scripts/descompactar_csv_linux.sh
```

- Informe outro diretório com `--source /caminho/personalizado`.
- É possível descompactar manualmente com `gunzip -c arquivo.csv.gz > arquivo.csv`.

## 📚 Variáveis da Versão 2

- `timestamp`: marca temporal (15 em 15 minutos).
- `meter_id`: identificador do hidrômetro.
- `city`, `region`: cidade e região do Brasil.
- `neighborhood`, `socioeconomic_class`: bairro e classe socioeconômica.
- `user_type`: perfil de consumo simulado.
- `consumption_liters`: consumo instantâneo.
- `pressure_psi`, `temperature_celsius`, `precipitacao_mm`: contexto operacional.
- `anomaly_flag`: flag para vazamentos/fraudes simuladas.
- `evento_cultural_flag`: indica impacto de evento cultural.

## 🧭 Roadmap Sugerido

1. Versão 1 para prototipagem rápida em notebooks.
2. Versão 2 para análises avançadas, pipelines ETL e experimentos TinyML/IoT.
3. Ajustes adicionais? Abra uma Issue ou envie um Pull Request!

## 💡 Propostas de Projetos

### Iniciante
- Painel interativo no Power BI ou Data Studio mostrando consumo médio diário por bairro em uma única cidade.
- Notebook exploratório em Python comparando padrões de vazamento entre classes socioeconômicas.
- Relatório estatístico básico sobre sazonalidade mensal utilizando `seaborn` ou `ggplot`.
- Mini-api Flask que retorna KPIs (consumo, alertas) filtrados por bairro.
- Classificador simples (árvore de decisão) para detectar leituras suspeitas com base em poucos atributos.

### Intermediário
- Pipeline ETL em Airflow ou Prefect carregando os CSV mensais para um Data Warehouse em camadas bronze/prata/ouro.
- Dashboard IoT em Grafana simulando telemetria em tempo real via MQTT com dados derivados do dataset.
- Análise de correlação entre eventos culturais, temperatura e consumo utilizando causal impact ou ARIMAX.
- Modelo de clustering para segmentar hidrômetros por perfil de uso e riscos operacionais.
- Estudo de benchmarking entre 3 algoritmos de detecção de fraudes (Isolation Forest, LSTM Autoencoder, Prophet residual).

### Avançado
- Arquitetura completa de Data Lakehouse (Delta/Iceberg) em ambiente cloud com ingestion incremental e versionamento de dados.
- TinyML no ESP32 treinando um detector de vazamentos com subset sintetizado e implantando quantização.
- Geminação digital de rede hídrica simulando pressões e vazões com integração a modelos hidráulicos (ex.: EPANET).
- Sistema de recomendação de manutenção preventiva usando grafos de vizinhança (Neo4j/NetworkX).
- Pipeline MLOps ponta a ponta (CI/CD, monitoramento, retraining) focado na predição de consumo futuro e alertas em produção.

## 👨‍🏫 Contato

Projeto guiado por **Eric Pimentel** e entusiastas da Força Analítica.

**Eric Pimentel**

[![LinkedIn Badge](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/ericpimentel-dados/)
[![GitHub Badge](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/enps2015)
[![Instagram Badge](https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white)](https://www.instagram.com/eric.n.pimentel/)
[![Gmail Badge](https://img.shields.io/badge/Gmail-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:enps2006@gmail.com)

---

*✨ Última atualização: 27 de outubro de 2026 ✨*
---

*“A Força está nos Dados, mas o Poder está na Interpretação.”*
