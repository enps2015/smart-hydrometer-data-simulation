"""Validação streaming dos particionamentos mensais dos datasets de hidrômetros.

Executa verificações que evitam carregar os arquivos completos em memória:
1. Checa se cada arquivo mensal possui o mesmo cabeçalho do CSV original.
2. Conta as linhas por mês (YYYY-MM) e compara original vs particionado.
3. Calcula um hash SHA-256 por mês com base no conteúdo de cada linha,
   garantindo que nenhuma alteração ocorreu ao mover os dados.

Uso:
    python3 test_partitioning.py
"""

import csv
import hashlib
import os
from collections import defaultdict
from typing import Dict, Iterable, Tuple

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ORIG_DIR = BASE_DIR
PARTITION_DIR = os.path.join(BASE_DIR, 'separados_mensais')

DATASET_PREFIX = 'dataset_hidrometros_'


def dataset_files() -> Iterable[str]:
    for name in sorted(os.listdir(ORIG_DIR)):
        if name.startswith(DATASET_PREFIX) and name.endswith('.csv'):
            yield name


def ensure_partition_exists() -> None:
    if not os.path.isdir(PARTITION_DIR):
        raise FileNotFoundError(
            f"Pasta de particionamento '{PARTITION_DIR}' não encontrada. "
            "Execute primeiro separar_por_mes.py."
        )


def canonical_line(row: Tuple[str, ...]) -> bytes:
    """Compacta uma linha em representação determinística para hashing."""
    return '\x1f'.join(row).encode('utf-8')


def analyze_original(path: str) -> Tuple[Dict[str, int], Dict[str, str], Tuple[str, ...]]:
    counts: Dict[str, int] = defaultdict(int)
    hashes: Dict[str, hashlib._hashlib.HASH] = {}

    with open(path, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        header = tuple(next(reader))
        timestamp_idx = header.index('timestamp')

        for row in reader:
            month_key = row[timestamp_idx][:7]
            counts[month_key] += 1
            if month_key not in hashes:
                hashes[month_key] = hashlib.sha256()
            hashes[month_key].update(canonical_line(tuple(row)))

    return counts, {k: h.hexdigest() for k, h in hashes.items()}, header


def analyze_partition(city_slug: str, header: Tuple[str, ...]) -> Tuple[Dict[str, int], Dict[str, str]]:
    city_dir = os.path.join(PARTITION_DIR, city_slug)
    if not os.path.isdir(city_dir):
        raise FileNotFoundError(f"Pasta de saída para cidade '{city_slug}' não encontrada em {PARTITION_DIR}.")

    counts: Dict[str, int] = defaultdict(int)
    hashes: Dict[str, hashlib._hashlib.HASH] = {}

    for year in sorted(os.listdir(city_dir)):
        year_dir = os.path.join(city_dir, year)
        if not os.path.isdir(year_dir):
            continue
        for fname in sorted(os.listdir(year_dir)):
            if not fname.endswith('.csv'):
                continue
            month_key = fname.replace('.csv', '')
            full_path = os.path.join(year_dir, fname)

            with open(full_path, 'r', newline='', encoding='utf-8') as infile:
                reader = csv.reader(infile)
                partition_header = tuple(next(reader))
                if partition_header != header:
                    raise ValueError(
                        f'Cabeçalho divergente em {full_path}. Esperado {header} e encontrado {partition_header}.'
                    )

                for row in reader:
                    counts[month_key] += 1
                    if month_key not in hashes:
                        hashes[month_key] = hashlib.sha256()
                    hashes[month_key].update(canonical_line(tuple(row)))

    return counts, {k: h.hexdigest() for k, h in hashes.items()}


def compare_metrics(city_slug: str, orig_counts: Dict[str, int], orig_hashes: Dict[str, str],
                    part_counts: Dict[str, int], part_hashes: Dict[str, str]) -> None:
    months = sorted(set(orig_counts) | set(part_counts))
    errors = []

    for month in months:
        o_count = orig_counts.get(month, 0)
        p_count = part_counts.get(month, 0)
        if o_count != p_count:
            errors.append(f'Contagem divergente para {month}: original={o_count} particionado={p_count}')

        o_hash = orig_hashes.get(month)
        p_hash = part_hashes.get(month)
        if o_hash != p_hash:
            errors.append(f'Hash divergente para {month}: original={o_hash} particionado={p_hash}')

    if errors:
        raise AssertionError(f'Divergências detectadas para {city_slug}:\n' + '\n'.join(errors))

    total = sum(orig_counts.values())
    print(f'✔ {city_slug}: {len(months)} meses validados, {total:,} linhas íntegras.')


def main() -> None:
    ensure_partition_exists()

    for dataset in dataset_files():
        city_slug = dataset.replace(DATASET_PREFIX, '').replace('.csv', '')
        dataset_path = os.path.join(ORIG_DIR, dataset)

        print(f'Validando {dataset}...')
        orig_counts, orig_hashes, header = analyze_original(dataset_path)
        part_counts, part_hashes = analyze_partition(city_slug, header)
        compare_metrics(city_slug, orig_counts, orig_hashes, part_counts, part_hashes)

    print('Todos os datasets foram validados com sucesso.')


if __name__ == '__main__':
    main()
