#!/usr/bin/env bash
set -e

APP_NAME="erlandi-security"
SERVICE_NAME="erlandi-security"
PYTHON_BIN="python3"
ENV_FILE="/etc/${SERVICE_NAME}.env"

echo "🛡️ Erlandi Security - Auto Installer"
echo "====================================="

# Auto detect current repo location
REPO_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
APP_DIR="/opt/${APP_NAME}"

echo "==> Installing dependencies..."
sudo apt update -y
sudo apt install -y git ${PYTHON_BIN} ${PYTHON_BIN}-venv ${PYTHON_BIN}-pip

echo "==> Preparing application directory..."
sudo mkdir -p "${APP_DIR}"
sudo chown -R "$USER":"$USER" "${APP_DIR}"

echo "==> Copying project files..."
rsync -a --delete "${REPO_DIR}/" "${APP_DIR}/"

cd "${APP_DIR}"

echo "==> Setting up virtual environment..."
${PYTHON_BIN} -m venv venv
source venv/bin/activate

echo "==> Installing python requirements..."
pip install -U pip
pip install -r requirements.txt

echo "==> Creating data folder..."
mkdir -p data
touch data/fban.txt

echo ""
echo "Masukkan BOT_TOKEN dari @BotFather"
echo "(Input tidak akan terlihat demi keamanan)"
read -r -s -p "BOT_TOKEN: " BOT_TOKEN
echo ""

if [ -z "$BOT_TOKEN" ]; then
  echo "ERROR: BOT_TOKEN kosong!"
  exit 1
fi

echo "==> Saving token securely..."
sudo bash -c "cat > '${ENV_FILE}'" <<EOF
BOT_TOKEN=${BOT_TOKEN}
EOF
sudo chmod 600 "${ENV_FILE}"

echo "==> Installing systemd service..."
sudo cp "${APP_DIR}/scripts/${SERVICE_NAME}.service" "/etc/systemd/system/${SERVICE_NAME}.service"
sudo sed -i "s|__APP_DIR__|${APP_DIR}|g" "/etc/systemd/system/${SERVICE_NAME}.service"
sudo sed -i "s|__USER__|${USER}|g" "/etc/systemd/system/${SERVICE_NAME}.service"

echo "==> Starting service..."
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}
sudo systemctl restart ${SERVICE_NAME}

echo ""
echo "✅ INSTALLATION COMPLETE!"
echo "Bot sekarang berjalan sebagai service."
echo ""
echo "Cek status:"
echo "  sudo systemctl status ${SERVICE_NAME}"
echo ""
echo "Lihat log:"
echo "  sudo journalctl -u ${SERVICE_NAME} -f"
