$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ModelDir = Join-Path $ProjectRoot "models\ollama"
New-Item -ItemType Directory -Force -Path $ModelDir | Out-Null
$env:OLLAMA_MODELS = $ModelDir
Write-Host "Using Ollama model directory: $ModelDir"
Write-Host "If Ollama is already running as a desktop/service process, stop it first."
ollama pull qwen2.5:1.5b
Write-Host "Model stored under $ModelDir"
