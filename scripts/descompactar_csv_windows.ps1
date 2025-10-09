<#
.SYNOPSIS
Descompacta os arquivos .csv.gz gerados nos particionamentos mensais.

.DESCRIPTION
Percorre a pasta datasets_hidrometros_v2\separados_mensais_csv_gz (ou outra informada)
e gera os arquivos .csv correspondentes na mesma estrutura de diretórios.
Os arquivos .gz originais são preservados.

.PARAMETER Source
Diretório base contendo os arquivos .csv.gz. Valor padrão:
datasets_hidrometros_v2\separados_mensais_csv_gz

.EXAMPLE
PS> pwsh -ExecutionPolicy Bypass -File scripts/descompactar_csv_windows.ps1

.EXAMPLE
PS> powershell -ExecutionPolicy Bypass -File scripts/descompactar_csv_windows.ps1 -Source "D:\dados\hidrometros"
#>

param(
    [string]$Source = "datasets_hidrometros_v2\separados_mensais_csv_gz"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

try {
    $resolvedSource = Resolve-Path -Path $Source
} catch {
    Write-Error "Diretório '$Source' não encontrado. Informe o caminho correto via -Source."
    exit 1
}

$files = Get-ChildItem -Path $resolvedSource -Recurse -Filter "*.csv.gz"

if (-not $files) {
    Write-Warning "Nenhum arquivo .csv.gz encontrado em $resolvedSource"
    exit 0
}

Add-Type -AssemblyName System.IO.Compression.FileSystem

$bufferSize = 1024 * 64
$buffer = New-Object byte[] $bufferSize
$processed = 0
$skipped = 0

foreach ($file in $files) {
    $targetPath = $file.FullName.Substring(0, $file.FullName.Length - 3) # remove .gz

    if (Test-Path -LiteralPath $targetPath) {
        Write-Host "⏭  Já existe: $targetPath" -ForegroundColor Yellow
        $skipped++
        continue
    }

    Write-Host "🔓 Extraindo $($file.FullName)..."

    $inputStream = [System.IO.File]::OpenRead($file.FullName)
    $gzipStream = New-Object System.IO.Compression.GzipStream($inputStream, [System.IO.Compression.CompressionMode]::Decompress)
    $outputStream = [System.IO.File]::Open($targetPath, [System.IO.FileMode]::CreateNew)

    try {
        while (($read = $gzipStream.Read($buffer, 0, $buffer.Length)) -gt 0) {
            $outputStream.Write($buffer, 0, $read)
        }
        $processed++
        Write-Host "✅ Criado: $targetPath" -ForegroundColor Green
    } finally {
        $gzipStream.Dispose()
        $inputStream.Dispose()
        $outputStream.Dispose()
    }
}

Write-Host ""
Write-Host "Processo concluído:" -ForegroundColor Cyan
Write-Host "  Extraídos : $processed"
Write-Host "  Ignorados : $skipped (já existiam)"
