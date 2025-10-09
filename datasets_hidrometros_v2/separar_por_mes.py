# Script para separar dados de hidrômetros por cidade e mês em modo streaming
# Autor: Prof. Ezra M. Kael
# Data: 08/10/2025 (atualizado para processamento otimizado em 24/02/2026)

import csv
import os
from datetime import datetime
from typing import Dict, Tuple, TextIO

# Caminhos base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ORIG_DIR = BASE_DIR
OUT_DIR = os.path.join(BASE_DIR, 'separados_mensais')

# Detecta automaticamente os arquivos de interesse
CSV_FILES = sorted(
    file_name
    for file_name in os.listdir(ORIG_DIR)
    if file_name.startswith('dataset_hidrometros_') and file_name.endswith('.csv')
)


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def parse_timestamp(ts_value: str) -> datetime:
    """Converte o timestamp do CSV em objeto datetime, garantindo robustez com diferentes formatos."""
    if ts_value is None:
        raise ValueError("Registro sem coluna 'timestamp' identificada.")

    ts_value = ts_value.strip()
    try:
        return datetime.fromisoformat(ts_value)
    except ValueError as exc:
        try:
            return datetime.strptime(ts_value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            raise ValueError(f"Formato de timestamp não suportado: {ts_value}") from exc


def writer_for(out_path: str, fieldnames: Tuple[str, ...], cache: Dict[str, Tuple[TextIO, csv.DictWriter]]) -> csv.DictWriter:
    """Obtém (ou cria) um writer para o arquivo de destino correspondente ao mês."""
    if out_path in cache:
        return cache[out_path][1]

    ensure_dir(os.path.dirname(out_path))
    file_obj = open(out_path, 'w', newline='', encoding='utf-8')
    writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
    writer.writeheader()
    cache[out_path] = (file_obj, writer)
    return writer


def close_writers(cache: Dict[str, Tuple[TextIO, csv.DictWriter]]) -> None:
    """Fecha todos os arquivos abertos para gravação."""
    for file_obj, _ in cache.values():
        file_obj.close()


def process_file(csv_file: str) -> None:
    city_slug = csv_file.replace('dataset_hidrometros_', '').replace('.csv', '')
    source_path = os.path.join(ORIG_DIR, csv_file)

    print(f'Processando {csv_file} -> cidade {city_slug}')
    writers_cache: Dict[str, Tuple[TextIO, csv.DictWriter]] = {}
    total_linhas = 0

    with open(source_path, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        if reader.fieldnames is None:
            raise ValueError(f'Arquivo {csv_file} sem cabeçalho detectado.')

        for row in reader:
            total_linhas += 1
            timestamp = parse_timestamp(row.get('timestamp'))
            ano = timestamp.year
            mes = timestamp.month

            out_dir = os.path.join(OUT_DIR, city_slug, str(ano))
            out_path = os.path.join(out_dir, f'{ano}-{mes:02d}.csv')
            writer = writer_for(out_path, tuple(reader.fieldnames), writers_cache)
            writer.writerow(row)

            if total_linhas % 500_000 == 0:
                print(f'  {total_linhas:,} linhas processadas...')

    close_writers(writers_cache)
    print(f'  Arquivo finalizado com {total_linhas:,} linhas.')


def main() -> None:
    ensure_dir(OUT_DIR)
    if not CSV_FILES:
        print('Nenhum arquivo dataset_hidrometros_*.csv encontrado para processar.')
        return

    for csv_file in CSV_FILES:
        process_file(csv_file)

    print(f'Processamento concluído. Arquivos mensais disponíveis em {OUT_DIR}')


if __name__ == '__main__':
    main()
