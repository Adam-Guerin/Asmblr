param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

$ErrorActionPreference = "Stop"

$argsString = ""
if ($Args) {
    $argsString = ($Args | ForEach-Object { '"' + $_ + '"' }) -join " "
}

python -m app $argsString
