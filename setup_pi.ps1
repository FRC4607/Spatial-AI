param (
    [string]$User = "ejmccalla",
    [string]$Email = "ejmccalla@gmail.com",
    [string]$Repo = "https://github.com/FRC4607/Spatial-AI.git"
)

# === Constants ===
$LocalFolderPath = ".\pi_setup"
$PiHost = "frc4607"
$RemotePath = "/home/${User}/pi_setup"

# === Check folder existence ===
$ResolvedPath = Resolve-Path $LocalFolderPath
if (-Not (Test-Path $ResolvedPath)) {
    Write-Error "Folder '$LocalFolderPath' does not exist."
    exit 1
}

# === Build destination string ===
$Destination = "${User}@${PiHost}:$RemotePath"

# === Copy folder ===
Write-Host "Copying folder '$ResolvedPath' to $Destination ..."
scp -r "$ResolvedPath" $Destination
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to copy folder to Pi."
    exit 1
}

# === SSH in and make .sh files executable ===
$SetExecutableCommand = "chmod +x $RemotePath/*.sh"
Write-Host "Setting execute permissions on scripts in $RemotePath ..."
ssh "$User@$PiHost" $SetExecutableCommand
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to set script permissions."
    exit 1
}

# === Run the setup.sh script remotely with arguments ===
$RunCommand = "cd $RemotePath && ./setup.sh $User $Email $Repo"
Write-Host "Running remote script: $RunCommand"
ssh "$User@$PiHost" $RunCommand
if ($LASTEXITCODE -eq 0) {
    Write-Host "Setup completed successfully!"
} else {
    Write-Error "Setup failed!"
}
