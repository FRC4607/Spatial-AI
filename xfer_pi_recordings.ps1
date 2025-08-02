# Configuration - Edit these values
$PiIP = "frc4607"        # Your Pi's IP address
$PiUser = "ejmccalla"                 # Your Pi username
$RemoteFile = "/media/RECORDINGS"  # File/folder to copy from Pi
$LocalFolder = ".\recordings"      # Where to save on Windows

# Copy recursively (all folders and files)
Write-Host "Copying from Pi (recursive)..." -ForegroundColor Green
scp -r "$PiUser@$PiIP`:$RemoteFile" $LocalFolder

if ($LASTEXITCODE -eq 0) {
    Write-Host "Copy completed!" -ForegroundColor Green
} else {
    Write-Host "Copy failed!" -ForegroundColor Red
}