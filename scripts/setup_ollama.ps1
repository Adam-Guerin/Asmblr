param(
  [string]$BaseUrl = $env:OLLAMA_BASE_URL,
  [string]$GeneralModel = $env:GENERAL_MODEL,
  [string]$CodeModel = $env:CODE_MODEL
)

if (-not $BaseUrl) { $BaseUrl = "http://localhost:11434" }
if (-not $GeneralModel) { $GeneralModel = "llama3.1:8b" }
if (-not $CodeModel) { $CodeModel = "qwen2.5-coder:7b" }

$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollama) {
  Write-Host "Ollama not found. Install from https://ollama.com/download"
  exit 1
}

function Test-OllamaService {
  param($Url)
  try {
    Invoke-RestMethod "$Url/api/tags" | Out-Null
    return $true
  } catch {
    return $false
  }
}

if (-not (Test-OllamaService -Url $BaseUrl)) {
  Write-Host "Ollama service unreachable; trying to start..."
  try { Start-Process ollama -ArgumentList "serve --port 11434" -WindowStyle Hidden } catch {}
  Start-Sleep -Seconds 3
}

ollama pull $GeneralModel
ollama pull $CodeModel

if (Test-OllamaService -Url $BaseUrl) {
  Write-Host "Ollama ready"
} else {
  Write-Host "Failed to reach Ollama after pulling models. Check https://ollama.com/docs for logs."
  exit 1
}
