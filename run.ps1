param (
    [ValidateSet(
        "dev-up",
        "dev-up-build",
        "dev-build",
        "dev-stop",
        "dev-down",
        "dev-reset",
        "dev-logs",
        "prod-up",
        "prod-up-build",
        "prod-build",
        "prod-down",
        "makemigrations",
        "migrate",
        "superuser"
    )]
    [string]$Action
)

function Assert-EnvFile {
    param ([string]$Path)
    if (-not (Test-Path -Path $Path)) {
        Write-Host "ERROR: Required environment file '$Path' was not found." -ForegroundColor Red
        Write-Host "Please create '$Path' in the project root before running this command." -ForegroundColor Yellow
        exit 1
    }
}

if ($Action -like "dev-*" -or $Action -in @("makemigrations", "migrate", "superuser")) {
    Assert-EnvFile ".env.dev"
} elseif ($Action -like "prod-*") {
    Assert-EnvFile ".env"
}

switch ($Action) {
    # --- Development --- 
    "dev-down"       { docker compose --env-file .env.dev down }
    "dev-up-build"   { docker compose --env-file .env.dev up -d --build }
    "dev-up"         { docker compose --env-file .env.dev up -d }    

    "dev-stop"       { docker compose --env-file .env.dev stop }
    "dev-reset"      { docker compose --env-file .env.dev down -v }
    "dev-logs"       { docker compose --env-file .env.dev logs -f backend }
    "dev-build"      { docker compose --env-file .env.dev build }


    # --- Production ---
    "prod-up"        { docker compose up -d }
    "prod-up-build"  { docker compose up -d --build }
    "prod-build"     { docker compose build }
    "prod-down"      { docker compose down }


    # --- Django Management ---
    "makemigrations" { docker compose --env-file .env.dev exec backend python manage.py makemigrations }
    "migrate"        { docker compose --env-file .env.dev exec backend python manage.py migrate }
    "superuser"      { docker compose --env-file .env.dev exec backend python manage.py createsuperuser }
}