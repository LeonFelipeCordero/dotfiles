#!/bin/bash

set -euo pipefail

setup_docker() {
  echo "manual_deps: setting up docker user"
  sudo groupadd docker
  sudo usermod -aG docker $USER
  newgrp docker
  sudo systemctl enable docker.service
  sudo systemctl enable containerd.service
}

if [[ "$(uname)" == "Darwin" ]]; then

  echo "manual_deps: Found MacOS System"
  if ! command -v brew >/dev/null 2>&1; then
    echo "manual_deps: No brew found, installing it"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  fi
  brew install git zsh xclip gh

elif [[ -f /etc/arch-release ]]; then

  echo "manual_deps: Found Arch linux System"
  sudo pacman -Sy --noconfirm git zsh xclip docker github-cli

  setup_docker

  curl -L -o devpod "https://github.com/loft-sh/devpod/releases/latest/download/devpod-linux-amd64" && sudo install -c -m 0755 devpod /usr/local/bin && rm -f devpod

elif [[ -f /etc/debian_version ]]; then

  echo "manual_deps: Found Debian/Ubuntu base system"
  sudo apt-get update
  sudo apt-get install -y git zsh xclip gh

  if ! command -v docker >/dev/null; then
    echo "manual_deps: Installing docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh ./get-docker.sh --dry-run
    setup_docker
  fi

  curl -L -o devpod "https://github.com/loft-sh/devpod/releases/latest/download/devpod-linux-amd64" && sudo install -c -m 0755 devpod /usr/local/bin && rm -f devpod

else
  echo "manual_deps: Unsupported OS"
  exit 1
fi

curl -s "https://get.sdkman.io" | bash

echo "manual_deps: finish to install dependencies"
