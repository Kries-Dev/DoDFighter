# Converts any audio file Windows can play (mp3, wav, m4a ...) into WMA, the only
# music format OpenLF2's bundled FFmpeg decodes (WMA v2 in ASF, like LF2's bgm).
# Uses Windows' own Media Foundation encoder, so nothing needs installing.
#
#   powershell -ExecutionPolicy Bypass -File tools\to_wma.ps1 IN.mp3 OUT.wma
param([Parameter(Mandatory)] [string]$In, [Parameter(Mandatory)] [string]$Out)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTask = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' } | Select-Object -First 1
$asTaskAction = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncActionWithProgress`1' } | Select-Object -First 1
function Await($op, [Type]$type) { $t = $asTask.MakeGenericMethod($type).Invoke($null, @($op)); $t.Wait(-1) | Out-Null; $t.Result }
function AwaitProgress($op, [Type]$progress) { $t = $asTaskAction.MakeGenericMethod($progress).Invoke($null, @($op)); $t.Wait(-1) | Out-Null }

[Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime] | Out-Null
[Windows.Media.Transcoding.MediaTranscoder, Windows.Media.Transcoding, ContentType = WindowsRuntime] | Out-Null
[Windows.Media.MediaProperties.MediaEncodingProfile, Windows.Media.MediaProperties, ContentType = WindowsRuntime] | Out-Null

$inPath = (Resolve-Path $In).Path
$outFull = [System.IO.Path]::GetFullPath($Out)
$outDir = [System.IO.Path]::GetDirectoryName($outFull)
New-Item -ItemType Directory -Force $outDir | Out-Null
$source = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($inPath)) ([Windows.Storage.StorageFile])
$folder = Await ([Windows.Storage.StorageFolder]::GetFolderFromPathAsync($outDir)) ([Windows.Storage.StorageFolder])
$target = Await ($folder.CreateFileAsync([System.IO.Path]::GetFileName($outFull), [Windows.Storage.CreationCollisionOption]::ReplaceExisting)) ([Windows.Storage.StorageFile])

$profile = [Windows.Media.MediaProperties.MediaEncodingProfile]::CreateWma([Windows.Media.MediaProperties.AudioEncodingQuality]::High)
# "High" picks WMA 9 Pro (format tag 0x162), which OpenLF2 cannot decode. WMA 8
# (0x161, FFmpeg's wmav2) is what LF2's own bgm uses.
$profile.Audio.Subtype = 'WMA8'
$profile.Audio.SampleRate = 44100
$profile.Audio.ChannelCount = 2
$profile.Audio.BitsPerSample = 16
$profile.Audio.Bitrate = 192000
$transcoder = New-Object Windows.Media.Transcoding.MediaTranscoder
$prepared = Await ($transcoder.PrepareFileTranscodeAsync($source, $target, $profile)) ([Windows.Media.Transcoding.PrepareTranscodeResult])
if (-not $prepared.CanTranscode) { throw "cannot transcode: $($prepared.FailureReason)" }
AwaitProgress ($prepared.TranscodeAsync()) ([double])
"wrote $outFull ($((Get-Item $outFull).Length) bytes)"
