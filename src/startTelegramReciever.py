import os
import signal
import subprocess
from telebot import TeleBot
print("Starting telegram reciever")
p=None
def start():
    global p
    p = subprocess.Popen([r'C:\Users\shash\Downloads\CoWin_Auto_Booking-master\autobook\Scripts\python.exe' ,r'C:\Users\shash\Downloads\covid-vaccine-booking-main\src\covidvaccineslotbooking.py'])
    print(f"Started process: {p.pid}") # the pid

TOKEN = "1632564482:AAFMJgCcHuD9AlLXRiTQ7G6ZqwpanUMEU6M"
SELFID = "1830115947"
app = TeleBot(__name__)

@app.route('/Bot +(Start$|Stop$|Restart$)')
def BotStart(message, cmd):
    chat_dest = message['chat']['id']
    if str(chat_dest) == (SELFID):
        msg = "Bot Recieved: {}".format(cmd)
        app.send_message(chat_dest, msg)
        if cmd == "Start":
            start()
        elif cmd == "Stop":
            p.kill()
        elif cmd == "Restart":
            p.kill()
            start()
    else:
        msg = "Bot Recieved: {} from {}".format(cmd, chat_dest)
        app.send_message("1830115947", msg)


if __name__ == '__main__':
    app.config['api_key'] = TOKEN
    app.poll(debug=True)





