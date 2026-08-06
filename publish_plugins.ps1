[CmdletBinding()]
param(
    [string[]]$PluginId,
    [string]$SourcePluginsDirectory = "",
    [switch]$NoCopy
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

# Add only the plugins that you want to publish publicly.
# You can also override this list from PowerShell:
#   .\publish_plugins.ps1 -PluginId FUniqueNotifier,FStats
$PublishedPlugins = @(
    "FaaUpdater"
    "FUniqueNotifier"
    "FCaravanNavigator"
    # "FStats"
)

$GitHubOwner = "fascinate78"
$GitHubRepository = "phbot-plugins"
$GitHubBranch = "main"

function Get-AbsolutePath {
    param([Parameter(Mandatory = $true)][string]$Path)

    return [System.IO.Path]::GetFullPath($Path)
}

function Assert-ChildPath {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Candidate
    )

    $rootPath = (Get-AbsolutePath -Path $Root).TrimEnd('\', '/')
    $candidatePath = Get-AbsolutePath -Path $Candidate
    $comparison = [System.StringComparison]::OrdinalIgnoreCase
    if (-not $candidatePath.StartsWith($rootPath + [System.IO.Path]::DirectorySeparatorChar, $comparison)) {
        throw "Path leaves the expected root: $candidatePath"
    }
    return $candidatePath
}

function Read-PluginMetadata {
    param([Parameter(Mandatory = $true)][string]$FilePath)

    $source = [System.IO.File]::ReadAllText($FilePath, [System.Text.Encoding]::UTF8)
    $nameMatch = [regex]::Match(
        $source,
        "(?m)^\s*pName\s*=\s*['`"]([^'`"]+)['`"]"
    )
    $versionMatch = [regex]::Match(
        $source,
        "(?m)^\s*pVersion\s*=\s*['`"]([^'`"]+)['`"]"
    )

    if (-not $nameMatch.Success) {
        throw "pName was not found in $FilePath"
    }
    if (-not $versionMatch.Success) {
        throw "pVersion was not found in $FilePath"
    }

    return [PSCustomObject]@{
        Name = $nameMatch.Groups[1].Value.Trim()
        Version = $versionMatch.Groups[1].Value.Trim()
    }
}

function Convert-VersionParts {
    param([string]$Version)

    $numbers = @([regex]::Matches($Version, "\d+") | ForEach-Object { [int]$_.Value })
    while ($numbers.Count -lt 4) {
        $numbers += 0
    }
    return [version]("{0}.{1}.{2}.{3}" -f $numbers[0], $numbers[1], $numbers[2], $numbers[3])
}

function Find-PluginEntryFile {
    param(
        [Parameter(Mandatory = $true)][string]$PluginDirectory,
        [Parameter(Mandatory = $true)][string]$Id
    )

    $candidates = @(Get-ChildItem -LiteralPath $PluginDirectory -File -Filter "*.py" |
        Where-Object {
            $_.Name -notmatch "(?i)(_working|_backup|_test|\.backup\.py)$"
        })

    if ($candidates.Count -eq 0) {
        throw "No publishable Python file found in $PluginDirectory"
    }
    $versioned = @()
    foreach ($candidate in $candidates) {
        try {
            $metadata = Read-PluginMetadata -FilePath $candidate.FullName
            if ($metadata.Name -match ('(?i)^' + [regex]::Escape($Id) + '(?:\s+V\d+)?$')) {
                $versioned += [PSCustomObject]@{
                    File = $candidate
                    SortVersion = Convert-VersionParts -Version $metadata.Version
                }
            }
        }
        catch {
            # Ignore helper Python files that do not declare plugin metadata.
        }
    }

    if ($versioned.Count -eq 0) {
        throw "Multiple Python files found for $Id; keep an exact $Id.py entry file or publish it manually."
    }

    return ($versioned |
        Sort-Object SortVersion, @{ Expression = { $_.File.Name } } -Descending |
        Select-Object -First 1).File
}

function Copy-PluginDirectory {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination
    )

    if (-not (Test-Path -LiteralPath $Destination)) {
        New-Item -ItemType Directory -Path $Destination | Out-Null
    }

    $excludedDirectories = @("__pycache__", "tests", ".pytest_cache")
    $excludedExtensions = @(".pyc", ".pyo", ".tmp", ".backup", ".bak")

    Get-ChildItem -LiteralPath $Source -Recurse -File | ForEach-Object {
        $relativePath = $_.FullName.Substring($Source.TrimEnd('\').Length).TrimStart('\')
        $segments = $relativePath -split "[\\/]"
        if (@($segments | Where-Object { $excludedDirectories -contains $_ }).Count -gt 0) {
            return
        }
        if ($excludedExtensions -contains $_.Extension.ToLowerInvariant()) {
            return
        }

        $destinationFile = Assert-ChildPath -Root $Destination -Candidate (Join-Path $Destination $relativePath)
        $destinationDirectory = Split-Path -Parent $destinationFile
        if (-not (Test-Path -LiteralPath $destinationDirectory)) {
            New-Item -ItemType Directory -Path $destinationDirectory -Force | Out-Null
        }
        Copy-Item -LiteralPath $_.FullName -Destination $destinationFile -Force
    }
}

$repositoryRoot = Get-AbsolutePath -Path $PSScriptRoot
if (-not $SourcePluginsDirectory) {
    $SourcePluginsDirectory = Join-Path (Split-Path -Parent $repositoryRoot) "phbot-plugins\plugins"
}
$sourceRoot = Get-AbsolutePath -Path $SourcePluginsDirectory
$destinationRoot = Join-Path $repositoryRoot "plugins"
$manifestPath = Join-Path $repositoryRoot "manifest.json"

if (-not (Test-Path -LiteralPath $sourceRoot -PathType Container)) {
    throw "Source plugin directory was not found: $sourceRoot"
}
if (-not (Test-Path -LiteralPath $destinationRoot -PathType Container)) {
    New-Item -ItemType Directory -Path $destinationRoot | Out-Null
}

$selectedPlugins = @(
    if ($PluginId -and @($PluginId).Count -gt 0) {
        $PluginId
    }
    else {
        $PublishedPlugins
    }
)

if ($selectedPlugins.Count -eq 0) {
    throw "The publish list is empty. Add plugin IDs to PublishedPlugins or use -PluginId."
}

$manifestEntries = @{}
if (Test-Path -LiteralPath $manifestPath -PathType Leaf) {
    $existingManifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    if ($existingManifest.schema_version -ne 1) {
        throw "Unsupported existing manifest schema."
    }
    foreach ($entry in @($existingManifest.plugins)) {
        $manifestEntries[[string]$entry.id] = $entry
    }
}

foreach ($id in $selectedPlugins) {
    if ($id -notmatch "^[A-Za-z0-9_-]+$") {
        throw "Invalid plugin ID: $id"
    }

    $sourceDirectory = Assert-ChildPath -Root $sourceRoot -Candidate (Join-Path $sourceRoot $id)
    if (-not (Test-Path -LiteralPath $sourceDirectory -PathType Container)) {
        throw "Plugin source directory was not found: $sourceDirectory"
    }

    $sourceEntry = Find-PluginEntryFile -PluginDirectory $sourceDirectory -Id $id
    $metadata = Read-PluginMetadata -FilePath $sourceEntry.FullName
    if ($metadata.Name -notmatch ('(?i)^' + [regex]::Escape($id) + '(?:\s+V\d+)?$')) {
        throw "Plugin ID $id does not match pName $($metadata.Name) in $($sourceEntry.Name)"
    }

    $destinationDirectory = Assert-ChildPath -Root $destinationRoot -Candidate (Join-Path $destinationRoot $id)
    if (-not $NoCopy) {
        Copy-PluginDirectory -Source $sourceDirectory -Destination $destinationDirectory
    }

    $destinationEntry = Assert-ChildPath -Root $destinationDirectory -Candidate (
        Join-Path $destinationDirectory $sourceEntry.Name
    )
    if (-not (Test-Path -LiteralPath $destinationEntry -PathType Leaf)) {
        throw "Published entry file was not found: $destinationEntry"
    }

    $hash = (Get-FileHash -LiteralPath $destinationEntry -Algorithm SHA256).Hash.ToLowerInvariant()
    $encodedId = [uri]::EscapeDataString($id)
    $encodedFile = [uri]::EscapeDataString($sourceEntry.Name)
    $downloadUrl = "https://raw.githubusercontent.com/$GitHubOwner/$GitHubRepository/$GitHubBranch/plugins/$encodedId/$encodedFile"

    $oldEntry = $manifestEntries[$id]
    $description = "FasscinaTe phBot plugin."
    if ($null -ne $oldEntry -and $oldEntry.description) {
        $description = [string]$oldEntry.description
    }

    $manifestEntries[$id] = [ordered]@{
        id = $id
        name = $metadata.Name
        version = $metadata.Version
        description = $description
        install_path = "$id/$($sourceEntry.Name)"
        download_url = $downloadUrl
        sha256 = $hash
    }

    Write-Host ("Published {0} v{1} ({2})" -f $id, $metadata.Version, $sourceEntry.Name) -ForegroundColor Green
}

$orderedPlugins = @($manifestEntries.Values | Sort-Object { [string]$_.id })
$newManifest = [ordered]@{
    schema_version = 1
    plugins = $orderedPlugins
}

$json = $newManifest | ConvertTo-Json -Depth 8
[System.IO.File]::WriteAllText(
    $manifestPath,
    $json + [Environment]::NewLine,
    (New-Object System.Text.UTF8Encoding($false))
)

Write-Host "Manifest updated: $manifestPath" -ForegroundColor Cyan
Write-Host "Review the files, then run: git add .; git commit; git push" -ForegroundColor Cyan
