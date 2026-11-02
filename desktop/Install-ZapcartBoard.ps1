<#
  Zapcart Control Board - desktop app installer
  Puts the board on your Desktop, Start Menu and taskbar with the Zapcart logo.
  Run it once. Nothing is installed system-wide; everything lands in your own
  user folder and can be removed by deleting %LOCALAPPDATA%\Zapcart.
#>

$ErrorActionPreference = 'Stop'
$Url  = 'https://claude.ai/artifact/BzDjpcTEGnMWXwPZfpLxG4'
$Name = 'Zapcart Board'
$Dir  = Join-Path $env:LOCALAPPDATA 'Zapcart'

Write-Host ''
Write-Host '  Zapcart Control Board' -ForegroundColor Cyan
Write-Host '  ---------------------'
Write-Host ''

# --- 1. folder + icon -------------------------------------------------------
New-Item -ItemType Directory -Force -Path $Dir | Out-Null

$IcoSrc  = Join-Path $PSScriptRoot 'ZapcartBoard.ico'
$Ico     = Join-Path $Dir 'ZapcartBoard.ico'
$HaveIco = $false
if (Test-Path $IcoSrc) {
  Copy-Item $IcoSrc $Ico -Force
  $HaveIco = $true
  Write-Host '  Zapcart logo installed'
} elseif (Test-Path $Ico) {
  $HaveIco = $true
  Write-Host '  Using the Zapcart logo already installed'
} else {
  Write-Host '  ZapcartBoard.ico is not in this folder - the shortcut will use' -ForegroundColor Yellow
  Write-Host '  the browser icon for now. Drop ZapcartBoard.ico in beside this'
  Write-Host '  installer and run it again to get the Zapcart logo.'
}

# --- 2. find a Chromium browser so the board opens as its own window --------
$Candidates = @(
  (Join-Path $env:ProgramFiles        'Microsoft\Edge\Application\msedge.exe'),
  (Join-Path ${env:ProgramFiles(x86)} 'Microsoft\Edge\Application\msedge.exe'),
  (Join-Path $env:ProgramFiles        'Google\Chrome\Application\chrome.exe'),
  (Join-Path ${env:ProgramFiles(x86)} 'Google\Chrome\Application\chrome.exe'),
  (Join-Path $env:LOCALAPPDATA        'Google\Chrome\Application\chrome.exe'),
  (Join-Path $env:ProgramFiles        'BraveSoftware\Brave-Browser\Application\brave.exe')
)
$Exe = $Candidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1

# --- 3. build the shortcut --------------------------------------------------
$Shell = New-Object -ComObject WScript.Shell
$Lnk   = Join-Path $Dir "$Name.lnk"
$s     = $Shell.CreateShortcut($Lnk)

if ($Exe) {
  # --app= gives a clean window with no address bar: it looks and behaves
  # like a desktop application rather than a browser tab.
  $s.TargetPath       = $Exe
  $s.Arguments        = "--app=$Url"
  $s.WorkingDirectory = (Split-Path $Exe)
  Write-Host "  Opening with $(Split-Path $Exe -Leaf) in app mode"
} else {
  # No Chromium browser: fall back to the default browser.
  $s.TargetPath = $Url
  Write-Host '  No Edge or Chrome found - will open in your default browser' -ForegroundColor Yellow
}
if ($HaveIco) { $s.IconLocation = "$Ico,0" }
$s.Description  = 'Zapcart Control Board - everything waiting on you, live'
$s.Save()
Write-Host "  Shortcut created"

# --- 4. Desktop and Start Menu ---------------------------------------------
$Desktop = [Environment]::GetFolderPath('Desktop')
Copy-Item $Lnk (Join-Path $Desktop "$Name.lnk") -Force
Write-Host '  Added to Desktop'

$StartMenu = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'
Copy-Item $Lnk (Join-Path $StartMenu "$Name.lnk") -Force
Write-Host '  Added to Start Menu'

# --- 5. taskbar -------------------------------------------------------------
# Windows 11 blocks programmatic pinning, so try it and say so if it refuses.
$Pinned = $false
try {
  $folder = (New-Object -ComObject Shell.Application).Namespace($Dir)
  $item   = $folder.ParseName("$Name.lnk")
  $verb   = $item.Verbs() | Where-Object { $_.Name -replace '&','' -match 'Pin to tas' }
  if ($verb) { $verb.DoIt(); Start-Sleep -Milliseconds 600; $Pinned = $true }
} catch { $Pinned = $false }

Write-Host ''
if ($Pinned) {
  Write-Host '  Pinned to the taskbar.' -ForegroundColor Green
} else {
  Write-Host '  One last step - Windows does not allow pinning from a script:' -ForegroundColor Yellow
  Write-Host '    Open the board from the Desktop icon, then right-click its'
  Write-Host '    taskbar button and choose "Pin to taskbar".'
}
Write-Host ''
Write-Host '  Done. The board updates itself - leave it open all day.' -ForegroundColor Green
Write-Host ''

$open = Read-Host '  Open it now? (Y/n)'
if ($open -ne 'n' -and $open -ne 'N') { Start-Process $Lnk }
