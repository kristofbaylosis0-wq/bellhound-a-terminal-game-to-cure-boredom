$ErrorActionPreference = 'Stop'

$Repo = 'https://github.com/kristofbaylosis0-wq/idk.git'
$InstallDir = Join-Path $HOME '.text-rpg-chatgpt'
$LauncherDir = Join-Path $HOME 'bin'
$Launcher = Join-Path $LauncherDir 'RPG.ps1'

function Step($Text) { Write-Host "  • $Text" }
function Done($Text) { Write-Host "  ✓ $Text" }

Write-Host ''
Write-Host '  A TEXT RPG GAME MADE BY CHATGPT + MANUS' -ForegroundColor Cyan
Write-Host ''

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'Git is required. Install Git for Windows and run this installer again.'
}
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw 'Python 3.10+ is required. Install Python for Windows and run this installer again.'
}

Step 'Preparing installation'
if (Test-Path $InstallDir) {
    git -C $InstallDir fetch --quiet origin
    git -C $InstallDir reset --hard --quiet origin/main
} else {
    New-Item -ItemType Directory -Force -Path (Split-Path $InstallDir) | Out-Null
    git clone --quiet $Repo $InstallDir
}
Done 'Source downloaded'

Step 'Creating Python environment'
python -m venv (Join-Path $InstallDir '.venv')
$Python = Join-Path $InstallDir '.venv\Scripts\python.exe'
& $Python -m pip install --disable-pip-version-check --quiet --upgrade pip
& $Python -m pip install --disable-pip-version-check --quiet -e "$InstallDir[dev]"
Done 'RPG installed'

Step 'Installing RPG command'
New-Item -ItemType Directory -Force -Path $LauncherDir | Out-Null
@"
& '$Python' -m game @args
"@ | Set-Content -Encoding UTF8 $Launcher

$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if (-not (($userPath -split ';') -contains $LauncherDir)) {
    $newPath = if ([string]::IsNullOrWhiteSpace($userPath)) { $LauncherDir } else { "$userPath;$LauncherDir" }
    [Environment]::SetEnvironmentVariable('Path', $newPath, 'User')
}
Done 'RPG command installed'

Write-Host ''
Write-Host '  Installation complete.' -ForegroundColor Green
Write-Host '  Restart PowerShell if needed, then use:'
Write-Host '    RPG game'
Write-Host '    RPG new game'
Write-Host '    RPG Save1'
Write-Host ''

# Launch immediately from this process so the freshly installed command is usable.
& $Python -m game
