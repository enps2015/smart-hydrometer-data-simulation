from __future__ import annotations

import gzip
from pathlib import Path

import pandas as pd
import pytest

from validate_data import (
    detect_schema,
    discover_data_file,
    load_dataset,
    main,
    validate_dataframe,
)


def test_detects_version_1_schema():
    assert detect_schema(["timestamp", "id_hidrometro", "consumo_m3"]) == "v1"


def test_detects_version_2_schema():
    assert detect_schema(["timestamp", "meter_id", "consumption_liters"]) == "v2"


@pytest.mark.parametrize(
    "frame,expected_schema",
    [
        (
            pd.DataFrame(
                {
                    "timestamp": ["2024-01-01T00:00:00", "2024-01-01T00:15:00"],
                    "id_hidrometro": ["HID_00001", "HID_00002"],
                    "consumo_m3": [0.12, None],
                    "status_hidrometro": ["OK", "FALHA_COMUNICACAO"],
                }
            ),
            "v1",
        ),
        (
            pd.DataFrame(
                {
                    "timestamp": ["2024-01-01T00:00:00"],
                    "meter_id": ["MTR_001"],
                    "consumption_liters": [120.0],
                    "anomaly_flag": [False],
                }
            ),
            "v2",
        ),
    ],
)
def test_validates_known_schema_and_allows_missing_consumption(frame, expected_schema):
    schema, errors, warnings, metrics = validate_dataframe(frame)

    assert schema == expected_schema
    assert errors == []
    assert metrics["rows"] == len(frame)
    assert metrics["invalid_timestamps"] == 0
    assert metrics["invalid_consumption"] == 0
    if expected_schema == "v1" and frame["consumo_m3"].isna().any():
        assert metrics["missing_consumption"] == 1
        assert any("falha de comunicação" in warning for warning in warnings)


def test_rejects_unknown_schema():
    frame = pd.DataFrame({"date": ["2024-01-01"], "consumption": [1.0]})

    schema, errors, _, _ = validate_dataframe(frame)

    assert schema == "desconhecido"
    assert any("Esquema não reconhecido" in error for error in errors)


def test_invalid_timestamp_non_numeric_and_negative_consumption_are_errors():
    frame = pd.DataFrame(
        {
            "timestamp": ["not-a-date", "2024-01-01T00:15:00", "2024-01-01T00:30:00"],
            "id_hidrometro": ["HID_00001", "HID_00002", "HID_00003"],
            "consumo_m3": ["0.2", "desconhecido", "-0.1"],
        }
    )

    schema, errors, _, metrics = validate_dataframe(frame)

    assert schema == "v1"
    assert metrics["invalid_timestamps"] == 1
    assert metrics["invalid_consumption"] == 1
    assert metrics["negative_consumption"] == 1
    assert len(errors) == 3


def test_empty_dataframe_fails_validation():
    frame = pd.DataFrame(columns=["timestamp", "id_hidrometro", "consumo_m3"])

    _, errors, _, metrics = validate_dataframe(frame)

    assert metrics["rows"] == 0
    assert any("não contém registros" in error for error in errors)


def test_load_dataset_respects_sample_limit(tmp_path):
    path = tmp_path / "sample.csv"
    pd.DataFrame(
        {
            "timestamp": [f"2024-01-01T00:{minute:02d}:00" for minute in range(5)],
            "id_hidrometro": [f"HID_{i:05d}" for i in range(5)],
            "consumo_m3": [0.1, 0.2, 0.3, 0.4, 0.5],
        }
    ).to_csv(path, index=False)

    sample = load_dataset(path, sample_rows=2)

    assert len(sample) == 2


def test_load_dataset_reads_csv_gzip(tmp_path):
    path = tmp_path / "sample.csv.gz"
    csv_text = (
        "timestamp,meter_id,consumption_liters\n"
        "2024-01-01T00:00:00,MTR_001,120.0\n"
        "2024-01-01T00:15:00,MTR_001,130.0\n"
    )
    with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
        handle.write(csv_text)

    frame = load_dataset(path, sample_rows=None)

    assert len(frame) == 2
    assert detect_schema(list(frame.columns)) == "v2"


def test_discovers_realistic_v1_path_and_v2_fallback(tmp_path):
    v1_dir = tmp_path / "datasets_versao_1" / "simulacao_hidrometros_por_mes_cidade" / "csv" / "belem"
    v1_dir.mkdir(parents=True)
    v1_file = v1_dir / "sample.csv"
    v1_file.write_text("timestamp,id_hidrometro,consumo_m3\n2024-01-01T00:00:00,HID_1,0.1\n", encoding="utf-8")

    found_v1 = discover_data_file(tmp_path)
    assert found_v1 == v1_file

    v1_file.unlink()
    v2_dir = tmp_path / "datasets_hidrometros_v2" / "separados_mensais_csv_gz" / "belem" / "2024"
    v2_dir.mkdir(parents=True)
    v2_file = v2_dir / "2024-01.csv.gz"
    v2_file.write_bytes(b"gzip placeholder")

    found_v2 = discover_data_file(tmp_path)
    assert found_v2 == v2_file


def test_cli_reports_success_for_valid_file(tmp_path, capsys):
    path = tmp_path / "sample.csv"
    path.write_text(
        "timestamp,id_hidrometro,consumo_m3,status_hidrometro\n"
        "2024-01-01T00:00:00,HID_00001,0.1,OK\n",
        encoding="utf-8",
    )

    result = main(["--file", str(path), "--full", "--preview-rows", "0"])
    output = capsys.readouterr()

    assert result == 0
    assert "Esquema detectado: v1" in output.out
    assert "Validação concluída sem erros" in output.out
