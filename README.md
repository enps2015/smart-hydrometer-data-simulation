# Smart Hydrometer Data Simulation

Simulações sintéticas de telemetria hídrica para estudos de IoT, analytics e cidades inteligentes. O repositório agora mantém duas gerações de datasets – a versão original e uma nova coleção com granularidade ampliada e recortes mensais compactados – além dos scripts que geram, particionam e validam os dados.

## 📦 Estrutura de Dados

- `datasets_versao_1/simulacao_hidrometros_por_mes_cidade/`
  - Base histórica do repositório (2024, 500 hidrômetros, leituras horárias).
  - Arquivos `.csv` e `.parquet` já particionados por cidade/mês.
  - Indicada para estudos rápidos e notebooks de prototipagem.
- `datasets_hidrometros_v2/`
  - `dataset_hidrometros_*.csv` *(gigantes – mantidos fora do Git via `.gitignore`)*: geração contínua em intervalos de 15 minutos, com perfis de consumo realistas e eventos culturais.
  - `separados_mensais/` *(uso local)*: recorte puro por cidade/mês, preservando o CSV integral.
  - `separados_mensais_csv_gz/` *(versão distribuída)*: os mesmos recortes em `.csv.gz`, prontos para download no GitHub (todos os arquivos < 100 MB).
  - Scripts utilitários:
    - `gerador_de_dataset_de_hidrômetros_inteligentes_(final_otimizado).py`: geração em streaming.
    - `separar_por_mes.py`: particionamento sem carregar os arquivos completos em memória.
    - `comprimir_mensais.py`: criação das versões compactadas `.csv.gz`.
    - `test_partitioning.py`: validação de integridade (contagem + hash SHA-256 por mês).

## 🚀 Novidades da Versão 2

- **Granularidade de 15 minutos** com 5 perfis de uso (normal, vazamento, fraude, ausência, comercial).
- **Eventos culturais e sazonalidade climática** modulando o consumo.
- **Métricas adicionais** (`pressure_psi`, `temperature_celsius`, `precipitacao_mm`, `anomaly_flag`, `evento_cultural_flag`).
- **Particionamento mensal** pensado para pipelines ETL e cargas incrementais.
- **Distribuição comprimida** para respeitar limites do GitHub sem alterar os dados originais (descompacte com `gzip -d arquivo.csv.gz` ou leitura direta pelo Pandas).

## 🧪 Validação dos Dados e dos Recortes

### 1. Instalar dependências e validar uma amostra

A validação inicial não exige gerar novamente as bases grandes. O script `validate_data.py` procura um CSV na estrutura real do repositório e, por padrão, lê até 10.000 linhas para verificar o esquema, timestamps, consumo, valores ausentes e possíveis valores inválidos.

```bash
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt

# Descobre automaticamente um dataset versionado e valida uma amostra
python validate_data.py

# Escolhe um arquivo e reduz a amostra
python validate_data.py --file "datasets_versao_1/simulacao_hidrometros_por_mes_cidade/csv/belem/hidrometros_belém_january.csv" --sample-rows 5000

# Lê um arquivo CSV/CSV.GZ inteiro (pode demorar e consumir mais memória)
python validate_data.py --file "CAMINHO/arquivo.csv.gz" --full
```

A saída informa o caminho e esquema identificados, tamanho da amostra, campos ausentes e uma prévia opcional. Leituras de consumo ausentes são sinalizadas como possíveis falhas de comunicação; nunca são convertidas silenciosamente em zero. Quando o arquivo completo não é lido, as contagens referem-se apenas à amostra.

### 2. Revalidar a integridade dos recortes mensais

Após gerar/baixar os `.csv` originais da versão 2:

```bash
python3 datasets_hidrometros_v2/separar_por_mes.py
python3 datasets_hidrometros_v2/test_partitioning.py
python3 datasets_hidrometros_v2/comprimir_mensais.py  # opcional para publicar no Git
```

O script `test_partitioning.py` garante que:
- Cabeçalhos coincidam entre original e particionado.
- Contagem de linhas por mês seja idêntica.
- Hash SHA-256 por mês permaneça igual (integridade comprovada).

### 3. Testes automatizados e integração contínua

```bash
python -m pytest -q
```

O GitHub Actions executa os testes de esquema v1/v2, leitura de CSV e CSV.GZ, descoberta de arquivos, validação de valores e execução da CLI. Também perfila uma amostra de um CSV versionado no repositório. As bases originais grandes permanecem fora dos testes automatizados; sua integridade é validada separadamente com os recortes e hashes.


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

[![LinkedIn Badge](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/eric-np-santos/)
[![GitHub Badge](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/enps2015)
[![Instagram Badge](https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white)](https://www.instagram.com/eric.n.pimentel/)
[![Gmail Badge](https://img.shields.io/badge/Gmail-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:enps2006@gmail.com)

---

*✨ Última atualização: 08 de outubro de 2025 ✨*
---

*“A Força está nos Dados, mas o Poder está na Interpretação.”*
