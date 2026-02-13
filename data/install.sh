#!/usr/bin/env bash
set -e

APP_NAME="erlandi-security"
APP_DIR="/opt/${APP_NAME}"
SERVICE_NAME="erlandi-security"
PYTHON_BIN="python3"
ENV_FILE="/etc/${SERVICE_NAME}.env"

echo "🛡️ Erlandi Security - Auto Installer"

echo "==> Installing dependencies..."
sudo apt update -y
sudo apt install -y git ${PYTHON_BIN} ${PYTHON_BIN}-venv ${PYTHON_BIN}-pip

# --- Repo URL ---
if [ -z "${REPO_URL:-}" ]; then
  echo ""
  read -r -p "Masukkan REPO_URL GitHub (contoh: https://github.com/USER/REPO.git): " REPO_URL
fi

if [ -z "${REPO_URL:-}" ]; then
  echo "ERROR: REPO_URL kosong."
  exit 1
fi

# --- Token input ---
echo ""
echo "Masukkan BOT_TOKEN dari @BotFather."
echo "(Input disembunyikan demi keamanan)"
read -r -s -p "BOT_TOKEN: " BOT_TOKEN
echo ""

if [ -z "${BOT_TOKEN:-}" ]; then
  echo "ERROR: BOT_TOKEN kosong."
  exit 1
fi

echo "==> Creating app directory at ${APP_DIR}..."
sudo mkdir -p "${APP_DIR}"
sudo chown -R "$USER":"$USER" "${APP_DIR}"

if [ -d "${APP_DIR}/.git" ]; then
  echo "==> Repo already exists, pulling latest..."
  cd "${APP_DIR}"
  git pull
else
  echo "==> Cloning repo..."
  git clone "${REPO_URL}" "${APP_DIR}"
  cd "${APP_DIR}"
fi

echo "==> Setting up venv..."
${PYTHON_BIN} -m venv venv
source venv/bin/activate

echo "==> Installing python requirements..."
pip install -U pip
pip install -r requirements.txt

echo "==> Creating data directory and fban file..."
mkdir -p data
touch data/fban.txt

echo "==> Saving token to ${ENV_FILE} (root-only)..."
sudo bash -c "cat > '${ENV_FILE}'" <<EOF
BOT_TOKEN=${BOT_TOKEN}
EOF
sudo chmod 600 "${ENV_FILE}"

echo "==> Installing systemd service..."
sudo cp "scripts/${SERVICE_NAME}.service" "/etc/systemd/system/${SERVICE_NAME}.service"
sudo sed -i "s|__APP_DIR__|${APP_DIR}|g" "/etc/systemd/system/${SERVICE_NAME}.service"
sudo sed -i "s|__USER__|${USER}|g" "/etc/systemd/system/${SERVICE_NAME}.service"

echo "==> Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}"
sudo systemctl restart "${SERVICE_NAME}"

echo ""
echo "✅ Selesai!"
echo "Cek status: sudo systemctl status ${SERVICE_NAME} --no-pager"
echo "Lihat log : sudo journalctl -u ${SERVICE_NAME} -f"
