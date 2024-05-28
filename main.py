import json
import os
import socket
import threading

import paramiko
import requests
import telebot

token_tg = os.environ['token_tg']
token_ow = os.environ['token_ow']
token_wa = os.environ['token_wa']
token_accu = os.environ['token_accu']

bot = telebot.TeleBot(token_tg)
# Словарь для хранения SSH сессий по id пользователя
ssh_sessions = {}

# приветственный текст
start_txt = ('Привет! Это бот с разными инструментами. \n\n'
             'Отправьте боту название города, чтобы узнать погоду.\n'
             'Команды:\n'
             '/start - Показать приветственное сообщение\n'
             '/help - Показать возможности бота\n'
             '/weather или /pogoda - Узнать погоду\n'
             '/testport - Сканировать порты\n'
             '/ssh - Подключиться к серверу по SSH')

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(message.chat.id, start_txt)

# Обработчик команды /weather и /pogoda
@bot.message_handler(commands=['weather', 'pogoda'])
def ask_city(message):
    msg = bot.send_message(message.chat.id, "Введите название города для получения погоды:")
    bot.register_next_step_handler(msg, get_weather)

def get_weather(message):
    city = message.text

    # Погода с OpenWeatherMap
    url_ow = f'https://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&lang=ru&appid={token_ow}'
    weather_data = requests.get(url_ow).json()
    if weather_data.get('main'):
        temperature = round(weather_data['main']['temp'])
        temperature_feels = round(weather_data['main']['feels_like'])
        bot.send_message(message.chat.id,
                         f"Погода с openweathermap.com \n{city}\nТекущая температура: {temperature} °C,\n"
                         f"Ощущается как {temperature_feels} °C.")
    else:
        bot.send_message(message.chat.id, "Не удается получить информацию от openweathermap.com.")

    # Погода с WeatherAPI
    url_wa = f'http://api.weatherapi.com/v1/current.json?key={token_wa}&q={city}&aqi=no'
    response = requests.get(url_wa)
    if response.status_code == 200:
        data = response.json()['current']
        temp = round(data['temp_c'])
        feels = round(data['feelslike_c'])
        bot.send_message(message.chat.id,
                         f"Погода с weatherapi.com \n{city}\nТекущая температура: {temp} °C,\n"
                         f"Ощущается как {feels} °C.")
    else:
        bot.send_message(message.chat.id, "Не удается получить информацию от weatherapi.com.")

    # Погода с AccuWeather
    url_location_key = (f'http://dataservice.accuweather.com/locations/v1/cities/search?'
                        f'apikey={token_accu}&q={city}&language=ru-ru')
    resp = requests.get(url_location_key)
    if resp.status_code == 200:
        json_data = resp.json()
        if json_data:
            code = json_data[0]['Key']
            url_accu = (f'http://dataservice.accuweather.com/forecasts/v1/hourly/12hour/{code}'
                        f'?apikey={token_accu}&language=ru-ru&details=true&metric=true')
            response = requests.get(url_accu)
            if response.status_code == 200:
                json_accu_data = json.loads(response.text)
                temp_now = round(json_accu_data[0]['Temperature']['Value'])
                temp_feel = round(json_accu_data[0]['RealFeelTemperature']['Value'])
                bot.send_message(message.chat.id,
                                 f"Погода с Accuweather.com \n{city}\nТекущая температура: {temp_now} °C,\n"
                                 f"Ощущается как {temp_feel} °C,\nНа небе {json_accu_data[0]['IconPhrase']}.")
            else:
                bot.send_message(message.chat.id, "Не удается получить информацию от accuweather.com/forecasts.")
        else:
            bot.send_message(message.chat.id, "Не удается получить информацию от accuweather.com/locations.")
    else:
        bot.send_message(message.chat.id, "Не удается получить информацию от accuweather.com/locations.")

# Обработчик команды /testport
@bot.message_handler(commands=['testport'])
def ask_ip_and_ports(message):
    msg = bot.send_message(message.chat.id, "Введите IP-адрес, начальный порт и конечный порт через пробел:")
    bot.register_next_step_handler(msg, start_port_scan)

def start_port_scan(message):
    data = message.text.split()
    if len(data) != 3:
        bot.send_message(message.chat.id, "Неверный формат. Пожалуйста, введите IP-адрес, "
                                          "начальный порт и конечный порт через пробел.")
        return

    ip = data[0]
    start_port = int(data[1])
    end_port = int(data[2])

    bot.send_message(message.chat.id, f"Начинаю сканирование портов на {ip} "
                                      f"в диапазоне {start_port}-{end_port}...")
    thread = threading.Thread(target=scan_ports, args=(message, ip, start_port, end_port))
    thread.start()

def scan_ports(message, ip, start_port, end_port):
    open_ports = []
    for port in range(start_port, end_port + 1):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((ip, port))
        if result == 0:
            open_ports.append(port)
        sock.close()

    if open_ports:
        bot.send_message(message.chat.id, f"Открытые порты на {ip}: {', '.join(map(str, open_ports))}")
    else:
        bot.send_message(message.chat.id, f"Нет открытых портов на {ip} в диапазоне {start_port}-{end_port}.")


# Обработчик команды /ssh
@bot.message_handler(commands=['ssh'])
def ask_ssh_credentials(message):
    msg = bot.send_message(message.chat.id, "Введите IP-адрес, порт, логин и пароль через пробел:")
    bot.register_next_step_handler(msg, start_ssh_connection)

def start_ssh_connection(message):
    data = message.text.split()
    if len(data) != 4:
        bot.send_message(message.chat.id, "Неверный формат. Пожалуйста, введите IP-адрес, порт, логин и пароль через пробел.")
        return

    ip, port, username, password = data[0], int(data[1]), data[2], data[3]

    bot.send_message(message.chat.id, f"Подключаюсь к {ip} по SSH на порт {port}...")
    thread = threading.Thread(target=ssh_connect, args=(message.chat.id, ip, port, username, password))
    thread.start()

def ssh_connect(chat_id, ip, port, username, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, port=port, username=username, password=password)
        ssh_sessions[chat_id] = {'client': client, 'cwd': '~'}
        bot.send_message(chat_id,
                         f"Успешно подключено к {ip} на порт {port}.\n"
                         f"Введите команды для выполнения на сервере.\nТекущая директория: ~")
        listen_ssh_commands(chat_id, client)
    except Exception as e:
        bot.send_message(chat_id, f"Не удалось подключиться к {ip} по SSH на порт {port}.\nОшибка: {str(e)}")

def listen_ssh_commands(chat_id, client):
    @bot.message_handler(func=lambda message: message.chat.id == chat_id)
    def handle_ssh_command(message):
        command = message.text
        session = ssh_sessions.get(chat_id)
        if not session:
            bot.send_message(chat_id, "Ошибка: сессия SSH не найдена.")
            return

        client = session['client']
        cwd = session['cwd']
        full_command = f'cd {cwd} && {command} && echo "__WORKING_DIR__" && pwd'
        try:
            stdin, stdout, stderr = client.exec_command(full_command)
            output = stdout.read().decode().strip()
            errors = stderr.read().decode().strip()

            if '__WORKING_DIR__' in output:
                output, new_cwd = output.split('__WORKING_DIR__')
                session['cwd'] = new_cwd.strip()

            response = f"Текущая директория: {session['cwd']}\n"

            if output:
                # Анализируем вывод команды ls и добавляем метки к папкам и файлам
                entries = output.split('\n')
                marked_entries = []
                for entry in entries:
                    if entry.endswith('directory'):
                        marked_entries.append(f'{{Папка}} {entry[:-9]}')
                    elif entry.endswith('file'):
                        marked_entries.append(f'[Файл] {entry[:-4]}')
                    else:
                        marked_entries.append(entry)
                response += f"Результат выполнения команды:\n {'\n'.join(marked_entries)}"
            elif errors:
                response += f"Ошибка выполнения команды:\n{errors}"
            else:
                response += "Ожидание команды..."

            bot.send_message(chat_id, response)
        except Exception as e:
            bot.send_message(chat_id, f"Ошибка выполнения команды: {str(e)}")


if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True, interval=0)
        except Exception as e:
            print('❌❌❌ Сработало исключение! ❌❌❌', e)
