#!/usr/bin/env bash
# Prepara una EC2 con Amazon Linux 2023 para correr SaludYa:
#   Docker, Docker Compose, Buildx, Git y 1 GB de swap.
# Uso (dentro de la EC2):  bash scripts/ec2-setup.sh
set -euo pipefail

echo "==> Instalando Docker y Git"
sudo dnf install -y docker git

echo "==> Iniciando Docker y habilitándolo al arrancar"
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"

PLUGINS=/usr/local/lib/docker/cli-plugins
sudo mkdir -p "$PLUGINS"

echo "==> Instalando Docker Compose"
sudo curl -fsSL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m)" \
  -o "$PLUGINS/docker-compose"
sudo chmod +x "$PLUGINS/docker-compose"

echo "==> Instalando Docker Buildx (lo necesita 'docker compose build')"
BUILDX_VERSION=$(curl -fsSL https://api.github.com/repos/docker/buildx/releases/latest | grep '"tag_name"' | cut -d'"' -f4)
case "$(uname -m)" in
  x86_64) ARCH=amd64 ;;
  aarch64) ARCH=arm64 ;;
  *) echo "Arquitectura no soportada: $(uname -m)"; exit 1 ;;
esac
sudo curl -fsSL "https://github.com/docker/buildx/releases/download/${BUILDX_VERSION}/buildx-${BUILDX_VERSION}.linux-${ARCH}" \
  -o "$PLUGINS/docker-buildx"
sudo chmod +x "$PLUGINS/docker-buildx"

if [ ! -f /swapfile ]; then
  echo "==> Creando 1 GB de swap (la t2.micro tiene solo 1 GB de RAM)"
  sudo dd if=/dev/zero of=/swapfile bs=1M count=1024
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab
fi

echo
docker --version
docker compose version
docker buildx version
free -h
echo
echo "Listo. Cierra la sesión SSH (exit) y vuelve a conectarte para usar docker sin sudo."
