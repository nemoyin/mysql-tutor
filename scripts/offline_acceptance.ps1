param([Parameter(Mandatory=$true)][string]$Root)
$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path -LiteralPath $Root).Path
$taskRequired = @('MySQL学习工具.exe','runtime/mysql/bin/mysqld.exe','runtime/manifest.json','web/index.html','content/chapters/01.json')
$taskMissing = @($taskRequired | Where-Object { -not (Test-Path -LiteralPath (Join-Path $taskRoot $_)) })
[pscustomobject]@{ Root=$taskRoot; StructurePassed=($taskMissing.Count -eq 0); Missing=$taskMissing; ManualChecks=@('Disconnect external network','Launch without administrator rights','Complete one exercise','Exit and restart; confirm progress','Restore practice data; confirm progress remains','Test on clean Windows 10 and Windows 11') } | ConvertTo-Json -Depth 4
if ($taskMissing.Count -gt 0) { exit 1 }
