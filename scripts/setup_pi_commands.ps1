# ========================================
# setup_pi_commands.ps1
# Raspberry Pi Remote Commands Setup Script
# Overwrites PowerShell profile with working functions
# ========================================

Write-Host "=== Raspberry Pi Remote Commands Setup (Overwrite Profile) ===" -ForegroundColor Cyan

# ===== Configuration =====
$PI_USER  = "frc4607"
$PI_HOST  = "frc4607-spatial-ai.local"
$PI_FULL  = "$PI_USER@$PI_HOST"

# ===== Step 1: Check if SSH key exists =====
$sshKeyPath = "$env:USERPROFILE\.ssh\id_rsa"
if (-not (Test-Path $sshKeyPath)) {
    Write-Host "No SSH key found. Generating new SSH key..." -ForegroundColor Green
    ssh-keygen -t rsa -b 4096 -f $sshKeyPath -N ''
    Write-Host "SSH key generated at $sshKeyPath" -ForegroundColor Green
} else {
    Write-Host "SSH key already exists at $sshKeyPath" -ForegroundColor Green
}

# ===== Step 2: Copy SSH key to Pi =====
Write-Host "Copying SSH key to Raspberry Pi..." -ForegroundColor Yellow
$pubKey = Get-Content "$sshKeyPath.pub"
$command = "mkdir -p ~/.ssh && echo '$pubKey' >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
ssh $PI_FULL $command
Write-Host "SSH key copied successfully!" -ForegroundColor Green

# ===== Step 3: Test SSH connection =====
Write-Host "Testing SSH connection..." -ForegroundColor Yellow
ssh $PI_FULL "echo 'Connection successful!'"
if ($LASTEXITCODE -ne 0) {
    Write-Host "SSH test failed! Ensure key authentication works." -ForegroundColor Red
    exit 1
}

# ===== Step 4: Overwrite PowerShell profile with Pi functions =====
Write-Host "Overwriting PowerShell profile with Pi functions..." -ForegroundColor Yellow

$PROFILE_CONTENT = @'
# ========================================
# Raspberry Pi Remote Commands (frc4607-spatial-ai)
# Corrected for Windows PowerShell
# Includes TTY fix for tail commands
# ========================================

$PI_USER  = 'frc4607'
$PI_HOST  = 'frc4607-spatial-ai.local'
$PI_FULL  = "$PI_USER@$PI_HOST"

# Helper function to run SSH commands safely
function pishell {
    param([string]$cmd)
    ssh $PI_FULL "$cmd"
}

# Helper function to run SSH commands with TTY allocation (for tail, interactive commands)
function pishelltty {
    param([string]$cmd)
    ssh -t $PI_FULL "$cmd"
}

# ===== Service Commands =====
function servicestatus { pishell "sudo systemctl status frc4607-spatial-ai.service" }
function servicestart    { pishell "sudo systemctl start frc4607-spatial-ai.service"; Write-Host "Service started." -ForegroundColor Green }
function servicestop     { pishell "sudo systemctl stop frc4607-spatial-ai.service"; Write-Host "Service stopped." -ForegroundColor Yellow }
function servicerestart  { pishell "sudo systemctl restart frc4607-spatial-ai.service"; Write-Host "Service restarted." -ForegroundColor Green }

# ===== Log Commands =====
function viewlogs        { pishelltty "bash -c 'tail -n 1000 /media/RECORDINGS/frc4607-spatial-ai-error.log'" }
function followlogs      { pishelltty "bash -c 'tail -f /media/RECORDINGS/frc4607-spatial-ai-error.log'" }
function deletelogs      { pishell "sudo rm -f /media/RECORDINGS/*.log"; Write-Host "Logs deleted." -ForegroundColor Yellow }

# ===== Recording Permissions =====
function fixrecordings   { pishell "sudo chown -R frc4607:frc4607 /media/RECORDINGS && sudo chmod -R 775 /media/RECORDINGS"; Write-Host "Permissions fixed for /media/RECORDINGS" -ForegroundColor Green }

# ===== Direct SSH =====
function pissh           { ssh -t $PI_FULL }

# ===== Copy recordings from Pi =====
function copyrecordings {
    param([string]$LocalFolder = ".\recordings")
    $RemoteFile = "/media/RECORDINGS"
    if (-not (Test-Path $LocalFolder)) { New-Item -ItemType Directory -Path $LocalFolder | Out-Null }
    Write-Host "Copying from ${PI_FULL}:$RemoteFile ..." -ForegroundColor Cyan
    scp -r "${PI_FULL}:${RemoteFile}/*" "$LocalFolder"
    if ($LASTEXITCODE -eq 0) { Write-Host "Copy completed!" -ForegroundColor Green } 
    else { Write-Host "Copy failed with exit code $LASTEXITCODE" -ForegroundColor Red }
}

# ===== Virtual Environment Environment Variable Setter =====
function setenv {
    param([string]$VarName, [string]$Value)
    $safeValue = $Value -replace "'", "'\''"
    $cmd = "grep -q '^export $VarName=' ~/Spatial-AI/venv/bin/postactivate && sed -i 's|^export $VarName=.*|export $VarName='\''$safeValue'\''|' ~/Spatial-AI/venv/bin/postactivate || echo 'export $VarName='\''$safeValue'\''' >> ~/Spatial-AI/venv/bin/postactivate"
    pishell $cmd
    Write-Host "$VarName set to $Value in postactivate." -ForegroundColor Green
}

# ===== Convenience wrappers =====
function setcompmode { setenv "SPATIAL_AI_MODE" "comp" }
function setdevmode  { setenv "SPATIAL_AI_MODE" "dev" }
function setreslow   { setenv "RESOLUTION" "low" }
function setresmed   { setenv "RESOLUTION" "med" }
function setreshigh  { setenv "RESOLUTION" "high" }

Write-Host "Raspberry Pi remote commands loaded!" -ForegroundColor Green
Write-Host "Available commands:" -ForegroundColor Cyan
Write-Host "  servicestatus, servicestart, servicestop, servicerestart" -ForegroundColor White
Write-Host "  viewlogs, followlogs, deletelogs" -ForegroundColor White
Write-Host "  fixrecordings, pissh, copyrecordings" -ForegroundColor White
Write-Host "  setcompmode, setdevmode, setreslow, setresmed, setreshigh" -ForegroundColor White
'@

# Ensure profile directory exists
$PROFILE_DIR = Split-Path -Parent $PROFILE
if (-not (Test-Path $PROFILE_DIR)) { New-Item -ItemType Directory -Path $PROFILE_DIR | Out-Null }

# Overwrite profile
Set-Content -Path $PROFILE -Value $PROFILE_CONTENT -Force
Write-Host "PowerShell profile overwritten at $PROFILE" -ForegroundColor Green

# ===== Step 5: Reload profile =====
. $PROFILE
Write-Host "Profile loaded. Remote commands are ready to use!" -ForegroundColor Cyan
