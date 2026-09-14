$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ModelDir = Join-Path $ProjectRoot "models\ollama"

New-Item -ItemType Directory -Force -Path $ModelDir | Out-Null

$env:OLLAMA_MODELS = $ModelDir
$env:OLLAMA_HOST = "0.0.0.0:11434"

Write-Host "Ollama model directory: $ModelDir"
Write-Host "Ollama host: $env:OLLAMA_HOST"
Write-Host "Starting Ollama with project-local model storage..."

& ollama serve