#!/bin/bash

# Переменные
SERVICE_NAME=servsav_tg_bot
SERVICE_FILE=/etc/systemd/system/${SERVICE_NAME}.service
TARGET_PATH=/usr/local/bin
MAIN_SCRIPT=servsav_tg_bot.py

# Остановка сервиса
echo "Stopping the service..."
sudo systemctl stop ${SERVICE_NAME}.service

# Отключение сервиса
echo "Disabling the service..."
sudo systemctl disable ${SERVICE_NAME}.service

# Удаление сервисного файла
echo "Removing the service file..."
sudo rm ${SERVICE_FILE}

# Перезагрузка systemd
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Удаление основного скрипта
echo "Removing the main script..."
sudo rm ${TARGET_PATH}/${MAIN_SCRIPT}

# Удаление переменных окружения из /etc/environment
echo "Removing environment variables..."
sudo sed -i '/token_tg/d' /etc/environment
sudo sed -i '/token_ow/d' /etc/environment
sudo sed -i '/token_wa/d' /etc/environment
sudo sed -i '/token_accu/d' /etc/environment

# Перезагрузка переменных окружения
source /etc/environment

echo "Uninstallation completed successfully!"
