#!/bin/bash

# Переменные
SERVICE_NAME=servsav_tg_bot
SERVICE_FILE=/etc/systemd/system/${SERVICE_NAME}.service
SCRIPT_PATH=$(pwd)
TARGET_PATH=/usr/local/bin
TOKENS_FILE=tokens.txt

# Установка зависимостей
echo "Installing required packages..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip

# Установка Python-библиотек
echo "Installing required Python packages..."
pip3 install paramiko requests pyTelegramBotAPI

# Проверка наличия файла с токенами
if [ ! -f "${SCRIPT_PATH}/${TOKENS_FILE}" ]; then
    echo "Error: File ${TOKENS_FILE} not found!"
    exit 1
fi

# Считывание токенов из файла и экспорт в переменные окружения
echo "Setting up environment variables..."
while IFS='=' read -r key value; do
    if [[ $key == "token_tg" || $key == "token_ow" || $key == "token_wa" || $key == "token_accu" ]]; then
        sudo sed -i "/${key}/d" /etc/environment
        echo "${key}=${value}" | sudo tee -a /etc/environment
    fi
done < "${SCRIPT_PATH}/${TOKENS_FILE}"

# Перезагрузка переменных окружения
source /etc/environment

# Копирование основного скрипта в целевой каталог
echo "Copying main script to target path..."
sudo cp ${SCRIPT_PATH}/main.py ${TARGET_PATH}/main.py

# Создание системного сервиса
echo "Creating systemd service file..."
sudo bash -c "cat > ${SERVICE_FILE}" <<EOL
[Unit]
Description=Service for ${SERVICE_NAME}
After=network.target

[Service]
EnvironmentFile=/etc/environment
ExecStart=/usr/bin/python3 ${TARGET_PATH}/main.py
WorkingDirectory=${TARGET_PATH}
Restart=always
RestartSec=10
User=$(whoami)
Group=$(id -gn)

[Install]
WantedBy=multi-user.target
EOL

# Перезагрузка systemd и запуск сервиса
echo "Reloading systemd and starting the service..."
sudo systemctl daemon-reload
sudo systemctl start ${SERVICE_NAME}.service
sudo systemctl enable ${SERVICE_NAME}.service

echo "Installation completed successfully!"
