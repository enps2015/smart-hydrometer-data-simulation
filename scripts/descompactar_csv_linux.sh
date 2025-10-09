#!/usr/bin/env bash
# Descompacta os arquivos .csv.gz mantidos em datasets_hidrometros_v2/separados_mensais_csv_gz.
# Uso:
#   bash scripts/descompactar_csv_linux.sh
#   ./scripts/descompactar_csv_linux.sh --source /caminho/personalizado
#
# Pré-requisitos: bash, gunzip (ou gzip) disponíveis no PATH.

set -euo pipefail

SOURCE_DIR="datasets_hidrometros_v2/separados_mensais_csv_gz"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source)
      shift
      SOURCE_DIR="${1:-}"
      if [[ -z "$SOURCE_DIR" ]]; then
        echo "Erro: informe um diretório após --source" >&2
        exit 1
      fi
      shift
      ;;
    -h|--help)
      sed -n '1,40p' "$0"
      exit 0
      ;;
    *)
      echo "Parâmetro desconhecido: $1" >&2
      exit 1
      ;;
  esac
done

if [[ ! -d "$SOURCE_DIR" ]]; then
  echo "Diretório não encontrado: $SOURCE_DIR" >&2
  exit 1
fi

mapfile -t FILES < <(find "$SOURCE_DIR" -type f -name "*.csv.gz" | sort)

if [[ ${#FILES[@]} -eq 0 ]]; then
  echo "Nenhum arquivo .csv.gz encontrado em $SOURCE_DIR"
  exit 0
fi

PROCESSED=0
SKIPPED=0

for file in "${FILES[@]}"; do
  target="${file%.gz}"
  if [[ -f "$target" ]]; then
    echo "⏭  Já existe: $target"
    ((SKIPPED++))
    continue
  fi

  echo "🔓 Extraindo $file..."
  gunzip -c "$file" > "$target"
  ((PROCESSED++))
  echo "✅ Criado: $target"
done

echo
echo "Processo concluído:"
echo "  Extraídos : $PROCESSED"
echo "  Ignorados : $SKIPPED (já existiam)"
