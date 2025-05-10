# Get the current directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$batchPath = Join-Path $scriptPath "run_crypto_reporter.bat"

# Get the current user's credentials
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$taskName = "Crypto News Reporter"
$description = "Automated cryptocurrency news and market data reporter"

# Create the task action with working directory and environment variables
$action = New-ScheduledTaskAction `
    -Execute $batchPath `
    -WorkingDirectory $scriptPath

# Create the task trigger (daily at 10 AM)
$trigger = New-ScheduledTaskTrigger -Daily -At 10AM

# Create the task settings with more detailed configuration
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
    -MultipleInstances IgnoreNew

# Create the task principal with highest privileges
$principal = New-ScheduledTaskPrincipal `
    -UserId $currentUser `
    -LogonType S4U `
    -RunLevel Highest

# Remove existing task if it exists
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# Register the task
Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description $description `
    -Force

Write-Host "Task '$taskName' has been created successfully!"
Write-Host "The script will run daily at 10:00 AM"
Write-Host "Log files will be created in: $scriptPath"
Write-Host "`nTo test the task:"
Write-Host "1. Open Task Scheduler"
Write-Host "2. Find '$taskName'"
Write-Host "3. Right-click and select 'Run'"
Write-Host "4. Check the log file in $scriptPath" 