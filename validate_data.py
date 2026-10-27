#!/usr/bin/env python3
"""Valida e perfila uma amostra dos datasets de telemetria do Smart Hydrometer.

Por padrão, procura um CSV real na estrutura versionada da versão 1 e lê até
10.000 linhas. Para CSV.gz, Pandas detecta a compressão pela extensão. Use
--full para percorrer o arquivo inteiro, ciente do custo de memória/tempo.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent
DEFAULT_SEARCH_DIRS = (
    ROOT_DIR / "datasets_versao_1" / "simulacao_hidrometros_por_mes_cidade" / "csv",
    ROOT_DIR / "datasets_hidrometros_v2" / "separados_mensais_csv_gz",
)
V1_REQUIRED_COLUMNS = {"timestamp", "id_hidrometro", "consumo_m3"}
V2_REQUIRED_COLUMNS = {"timestamp", "meter_id", "consumption_liters"}


def discover_data_file(root: Path = ROOT_DIR) -> Path:
    """Encontra um arquivo existente na estrutura real do repositório."""
    search_dirs = (
        root / "datasets_versao_1" / "simulacao_hidrometros_por_mes_cidade" / "csv",
        root / "datasets_hidrometros_v2" / "separados_mensais_csv_gz",
    )
    for directory in search_dirs:
        if not directory.is_dir():
            continue
        csv_files = sorted(directory.rglob("*.csv"))
        if csv_files:
            return csv_files[0]
        gz_files = sorted(directory.rglob("*.csv.gz"))
        if gz_files:
            return gz_files[0]
    raise FileNotFoundError(
        "Nenhum CSV encontrado nos diretórios padrão. Informe --file CAMINHO "
        "ou confira se os datasets foram baixados."
    )


def resolve_data_path(raw_path: str, root: Path = ROOT_DIR) -> Path:
    """Resolve caminho absoluto ou relativo ao diretório atual/do projeto."""
    candidate = Path(raw_path).expanduser()
    if candidate.is_file():
        return candidate.resolve()
    project_candidate = root / candidate
    if project_candidate.is_file():
        return project_candidate.resolve()
    raise FileNotFoundError(f"Arquivo de dados não encontrado: {raw_path}")


def load_dataset(path: Path, sample_rows: Optional[int] = 10_000) -> pd.DataFrame:
    """Carrega CSV/CSV.GZ em modo amostra por padrão, ou inteiro se sample_rows=None."""
    if sample_rows is not None and sample_rows < 1:
        raise ValueError("sample_rows deve ser maior que zero ou None.")
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo de dados não encontrado: {path}")
    if not (path.name.lower().endswith(".csv") or path.name.lower().endswith(".csv.gz")):
        raise ValueError("Formato não suportado. Informe um arquivo .csv ou .csv.gz.")
    return pd.read_csv(path, nrows=sample_rows, compression="infer")


def detect_schema(columns: List[str]) -> str:
    """Identifica qual geração do esquema de telemetria está presente."""
    names = set(columns)
    if V1_REQUIRED_COLUMNS.issubset(names):
        return "v1"
    if V2_REQUIRED_COLUMNS.issubset(names):
        return "v2"
    return "desconhecido"


def validate_dataframe(df: pd.DataFrame) -> Tuple[str, List[str], List[str], Dict[str, int]]:
    """Valida o esquema reconhecido e retorna (esquema, erros, avisos, métricas)."""
    errors: List[str] = []
    warnings: List[str] = []
    schema = detect_schema([str(column) for column in df.columns])

    if df.empty:
        errors.append("O arquivo não contém registros na amostra lida.")
    if len(set(df.columns)) != len(df.columns):
        errors.append("Há nomes de coluna duplicados.")
    if schema == "desconhecido":
        errors.append(
            "Esquema não reconhecido. Esperado v1 "
            "(timestamp, id_hidrometro, consumo_m3) ou v2 "
            "(timestamp, meter_id, consumption_liters)."
        )
        return schema, errors, warnings, {
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "missing_cells": int(df.isna().sum().sum()),
        }

    consumption_col = "consumo_m3" if schema == "v1" else "consumption_liters"
    timestamps = pd.to_datetime(df["timestamp"], errors="coerce")
    invalid_timestamps = int(timestamps.isna().sum())
    if invalid_timestamps:
        errors.append(f"{invalid_timestamps} timestamp(s) ausentes ou inválidos na amostra.")

    raw_consumption = df[consumption_col]
    numeric_consumption = pd.to_numeric(raw_consumption, errors="coerce")
    invalid_consumption = int((raw_consumption.notna() & numeric_consumption.isna()).sum())
    if invalid_consumption:
        errors.append(
            f"{invalid_consumption} valor(es) não numéricos em '{consumption_col}'."
        )

    negative_consumption = int((numeric_consumption.dropna() < 0).sum())
    if negative_consumption:
        errors.append(
            f"{negative_consumption} valor(es) negativos em '{consumption_col}'."
        )

    missing_consumption = int(raw_consumption.isna().sum())
    if missing_consumption:
        warnings.append(
            f"{missing_consumption} leitura(s) de consumo ausentes; isso pode representar "
            "falha de comunicação e não é tratado automaticamente como zero."
        )

    status_col = "status_hidrometro" if schema == "v1" else None
    status_count = int(df[status_col].nunique(dropna=True)) if status_col in df.columns else 0
    metrics = {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "missing_cells": int(df.isna().sum().sum()),
        "missing_consumption": missing_consumption,
        "invalid_timestamps": invalid_timestamps,
        "invalid_consumption": invalid_consumption,
        "negative_consumption": negative_consumption,
        "distinct_statuses": status_count,
    }
    return schema, errors, warnings, metrics


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Perfila e valida um dataset CSV/CSV.GZ do Smart Hydrometer."
    )
    parser.add_argument(
        "--file",
        help="Caminho do CSV/CSV.GZ. Se omitido, encontra um arquivo na estrutura do projeto.",
    )
    parser.add_argument(
        "--sample-rows",
        type=int,
        default=10_000,
        help="Número de linhas a ler (padrão: 10000). Ignorado com --full.",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Lê o arquivo inteiro. Pode exigir mais memória e tempo.",
    )
    parser.add_argument(
        "--preview-rows",
        type=int,
        default=5,
        help="Quantidade de registros de exemplo a imprimir (padrão: 5).",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.preview_rows < 0:
        print("ERRO: --preview-rows não pode ser negativo.", file=sys.stderr)
        return 2
    if not args.full and args.sample_rows < 1:
        print("ERRO: --sample-rows deve ser maior que zero.", file=sys.stderr)
        return 2

    try:
        path = resolve_data_path(args.file) if args.file else discover_data_file()
        sample_rows = None if args.full else args.sample_rows
        df = load_dataset(path, sample_rows=sample_rows)
    except (OSError, ValueError, pd.errors.ParserError) as error:
        print(f"ERRO: {error}", file=sys.stderr)
        return 2

    schema, errors, warnings, metrics = validate_dataframe(df)
    mode = "arquivo inteiro" if args.full else f"amostra de até {args.sample_rows:,} linhas"
    print(f"Arquivo: {path.relative_to(ROOT_DIR) if path.is_relative_to(ROOT_DIR) else path}")
    print(f"Modo: {mode}")
    print(f"Esquema detectado: {schema}")
    print(f"Registros analisados: {metrics['rows']:,}")
    print(f"Colunas: {metrics['columns']}")
    print(f"Células ausentes na amostra: {metrics['missing_cells']:,}")

    if schema != "desconhecido":
        print(f"Consumo ausente: {metrics['missing_consumption']:,}")
        if schema == "v1":
            print("\nDistribuição de status_hidrometro:")
            if "status_hidrometro" in df.columns:
                print(df["status_hidrometro"].value_counts(dropna=False).to_string())

    if args.preview_rows:
        print(f"\nPrévia ({min(args.preview_rows, len(df))} linha(s)):")
        print(df.head(args.preview_rows).to_string(index=False))

    for warning in warnings:
        print(f"AVISO: {warning}")
    for error in errors:
        print(f"ERRO DE VALIDAÇÃO: {error}")

    if errors:
        return 1
    print("\nValidação concluída sem erros na amostra analisada.")
    if not args.full:
        print("Nota: os indicadores de qualidade referem-se à amostra lida, não ao arquivo inteiro.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
