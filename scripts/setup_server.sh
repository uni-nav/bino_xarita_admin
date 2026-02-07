#!/bin/bash

# Exit on error
set -e

echo "🚀 Serverni sozlash boshlandi..."

# 1. Update system packages
echo "📦 Paketlar yangilanmoqda..."
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg make

# 2. Install Docker
echo "🐳 Docker o'rnatilmoqda..."
if ! command -v docker &> /dev/null; then
    # Add Docker's official GPG key:
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg

    # Add the repository to Apt sources:
    echo \
      "deb [arch=\"$(dpkg --print-architecture)\" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Add current user to docker group (to run without sudo)
    sudo usermod -aG docker $USER
    echo "✅ Docker o'rnatildi!"
else
    echo "⚠️ Docker allaqachon o'rnatilgan."
fi

# 3. Verify installations
echo "🔍 Tekshirilmoqda..."
docker compose version
make --version

echo "🎉 Sozlash tugadi! Iltimos, serverdan chiqib qayta kiring (yoki 'newgrp docker' deb yozing)."
