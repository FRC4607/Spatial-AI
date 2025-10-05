param (
    [string]$PiUser = "frc4607",
    [string]$PiHost = "frc4607-spatial-ai"
)

$RemoteFile = "/media/RECORDINGS"
$LocalFolder = ".\recordings"

Write-Host "Copying from Pi (recursive)..." -ForegroundColor Green
scp -r "$PiUser@$PiHost`:$RemoteFile/*" $LocalFolder
if ($LASTEXITCODE -eq 0) {
    Write-Host "Copy completed!" -ForegroundColor Green
} else {
    Write-Host "Copy failed!" -ForegroundColor Red
}