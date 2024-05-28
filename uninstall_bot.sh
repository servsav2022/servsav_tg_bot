#!/bin/bash

# Переменные
SERVICE_NAME=servsav_tg_bot
SERVICE_FILE=/etc/systemd/system/${SERVICE_NAME}.service
TARGET_PATH=/usr/local/bin
MAIN_SCRIPT=main.py

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

# Очистка переменных окружения
unset token_tg
unset token_ow
unset token_wa
unset token_accu

# Удаление токенов из текущей сессии
sed -i '/token_tg/d' ~/.bashrc
sed -i '/token_ow/d' ~/.bashrc
sed -i '/token_wa/d' ~/.bashrc
sed -i '/token_accu/d' ~/.bashrc

echo "Uninstallation completed successfully!"
