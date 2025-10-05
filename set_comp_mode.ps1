# === Constants ===
$PiHost = "frc4607-spatial-ai"
$PiUser = "frc4607"
$RemotePath = "/home/frc4607/pi_setup"

# === Run the /pi_setup/setup.sh script remotely with arguments ===
$RunCommand = "cd $RemotePath && ./enable_comp_mode.sh"
Write-Host "Running remote script: $RunCommand"
ssh "$PiUser@$PiHost" $RunCommand
if ($LASTEXITCODE -eq 0) {
    Write-Host "Enable comp mode successfull!"
} else {
    Write-Error "Enable comp mode failed!"
}
