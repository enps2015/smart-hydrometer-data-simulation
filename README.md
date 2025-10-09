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

## 🧪 Validação dos Recortes

Após gerar/baixar os `.csv` originais:

```bash
python3 datasets_hidrometros_v2/separar_por_mes.py
python3 datasets_hidrometros_v2/test_partitioning.py
python3 datasets_hidrometros_v2/comprimir_mensais.py  # opcional para publicar no Git
```

O script `test_partitioning.py` garante que:
- Cabeçalhos coincidam entre original e particionado.
- Contagem de linhas por mês seja idêntica.
- Hash SHA-256 por mês permaneça igual (integridade comprovada).

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
