# Build a ready-to-send copy of DoD Fighter: OpenLF2 + the darthnox mod + a
# double-click launcher, zipped.
#
#   powershell -ExecutionPolicy Bypass -File tools\make_package.ps1 [-Game DIR] [-Out DIR]
#
# -Game: the OpenLF2 install to copy (default: %LOCALAPPDATA%\Programs\OpenLF2)
# -Out:  where "DoD Fighter\" and "DoD Fighter.zip" go (default: Downloads)
#
# The mod comes from this repo (mods\darthnox), not from the install. Not copied:
# the uninstaller, Play-DarthNox.bat, other mods. The LF2 installer is not bundled:
# OpenLF2 offers to download it into .\config on the first start.
# Online play needs both players on exactly the same package (mod profile check).
param(
    [string]$Game = "$env:LOCALAPPDATA\Programs\OpenLF2",
    [string]$Out = "$env:USERPROFILE\Downloads"
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$dest = Join-Path $Out 'DoD Fighter'
$zip = Join-Path $Out 'DoD Fighter.zip'

if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
New-Item -ItemType Directory -Force $dest | Out-Null

# the engine: everything but the uninstaller, our old .bat and the mods
Get-ChildItem $Game | Where-Object {
    $_.Name -notlike 'unins000*' -and $_.Name -ne 'Play-DarthNox.bat' -and $_.Name -ne 'mods'
} | ForEach-Object { Copy-Item $_.FullName -Destination $dest -Recurse }

# the mod, from the repo
New-Item -ItemType Directory -Force (Join-Path $dest 'mods') | Out-Null
Copy-Item (Join-Path $repo 'mods\darthnox') -Destination (Join-Path $dest 'mods') -Recurse
New-Item -ItemType Directory -Force (Join-Path $dest 'config') | Out-Null

# the launcher
$csc = "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
& $csc /nologo /target:winexe /optimize "/win32icon:$PSScriptRoot\launcher\dod.ico" `
    "/out:$(Join-Path $dest 'DoD Fighter.exe')" /reference:System.Windows.Forms.dll `
    "$PSScriptRoot\launcher\DoDFighter.cs"
if ($LASTEXITCODE -ne 0) { throw 'launcher build failed' }
Copy-Item "$PSScriptRoot\launcher\READ ME - DoD Fighter.txt" -Destination $dest

if (Test-Path $zip) { Remove-Item -Force $zip }
Compress-Archive -Path $dest -DestinationPath $zip -CompressionLevel Optimal
$size = [math]::Round((Get-Item $zip).Length / 1MB, 1)
Write-Output "Folder: $dest"
Write-Output "Zip:    $zip ($size MB)"
