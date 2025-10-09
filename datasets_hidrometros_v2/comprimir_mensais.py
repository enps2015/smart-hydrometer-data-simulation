"""Compacta os CSVs mensais em versões .csv.gz para distribuição no repositório.

Os arquivos originais em datasets_hidrometros_v2/separados_mensais permanecem intactos.
As cópias comprimidas são salvas em datasets_hidrometros_v2/separados_mensais_csv_gz,
mantendo a mesma hierarquia (cidade/ano/arquivo.csv.gz).
"""

import gzip
import os
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SOURCE_DIR = BASE_DIR / "separados_mensais"
TARGET_DIR = BASE_DIR / "separados_mensais_csv_gz"


def compress_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as f_in, gzip.open(target, "wb", compresslevel=6) as f_out:
        shutil.copyfileobj(f_in, f_out)


def main() -> None:
    if not SOURCE_DIR.exists():
        raise FileNotFoundError(
            f"Pasta de origem {SOURCE_DIR} não encontrada. Execute separar_por_mes.py antes."
        )

    total = 0
    for csv_path in SOURCE_DIR.rglob("*.csv"):
        rel = csv_path.relative_to(SOURCE_DIR)
        target_path = TARGET_DIR / rel.with_suffix(rel.suffix + ".gz")
        if target_path.exists() and target_path.stat().st_mtime >= csv_path.stat().st_mtime:
            continue
        compress_file(csv_path, target_path)
        total += 1
        if total % 10 == 0:
            print(f"{total} arquivos comprimidos...")

    print(f"Compressão concluída. {total} arquivos atualizados.")


if __name__ == "__main__":
    main()
