Write-Host "Setting up SAOS development environment..."
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env"
}
if (-not (Test-Path "frontend/.env")) {
    Copy-Item "frontend/.env.example" "frontend/.env"
    Write-Host "Created frontend/.env"
}
Write-Host "Installing backend dependencies..."
pip install -r backend/requirements.txt
Write-Host "Installing frontend dependencies..."
cd frontend
npm install
cd ..
Write-Host "Ready to develop"
