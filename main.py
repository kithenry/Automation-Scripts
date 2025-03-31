import os
import subprocess
import serial
import telebot
import threading
import time
import requests
from datetime import datetime, timedelta
import socket

just_started = True
wake_datetime = None
alarm_set = False
reminders = []

CHAT_ID = os.getenv('TG_CHAT_ID')
BOT_TOKEN = os.getenv('TG_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)
dateFormat = "%Y-%m-%d %H:%M:%S"

def send_message(message):
    global CHAT_ID, BOT_TOKEN
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
             'chat_id': CHAT_ID,
             'text': message
            }
    requests.post(url, data=payload)


def run_system_command(cmd):
    output = subprocess.run(cmd.strip(), capture_output=True, text=True, shell=True)
    print(output)
    return output.stdout.split("\n")[0]

command_categories = ['exec','info']
def handle_command(command,category):
    if(category not in command_categories):
        return(f"{category} not supported");
    elif(category == "info"):
        if(command == "battery"):
            cmd = 'upower -d | grep  "percentage"'
            battery_level = run_system_command(cmd)
            battery_level = battery_level.split("percentage:")[1].strip()
            response = f"Battery Level: {battery_level}"
            return response
        elif(command == "ip"):
            # response = requests.get("https://api64.ipify.org?format=text").text (only for public ip's)
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8',1))
            ip = s.getsockname()[0]
            return ip
    else:
        pass
        #process other commands here




@bot.message_handler(commands=["note"])
def note(message):
    try:
        parts = message.text.split(" ")
        if len(parts) < 2:
            raise ValueError("Insufficent args provided")
        note_command = parts[1]
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")
        return
    if(note_command == 'add'):
        note_file = parts[-1].strip()
        note_text = " ".join(parts[2:-1])
        add_note(bot,note_file, note_text,message)
    else:
        bot.reply_to(message, "Uknown cmd")




def add_note(bot,note_file, note_text,message):
    try:
        vault_path = "/home/sentinel/Second Brain Vault/Notes"  # Adjust to your vault path  (env var)
        file_path = os.path.expanduser(f"{vault_path}/{note_file}.md")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"## {timestamp}\n- {note_text}\n"
        
        with open(file_path, "a") as f:
            f.write(entry)
        bot.reply_to(message,f"Added to {note_file}.md: \n'{note_text}'\nTimme added: {timestamp}")
    except Exception as e:
        send_message(f"Error: {str(e)}. Use /note add note_text note_name")



@bot.message_handler(commands=["system"])
def system(message):
    try:
        parts = message.text.split()
        category = parts[1]
        command = parts[2]
        response = handle_command(category=category,command=command)
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"There was an error processing your command\n{e}")


def get_battery_level():
    batteryLevel = int(run_system_command("cat /sys/class/power_supply/BAT0/capacity"))
    return batteryLevel

batteryNotificationSent = False
def safe_charge_mon():
    #monitor battery status, tell me when its full
    #run as daemon, check status every 5 mins
    #when its full , send me a message
    global batteryNotificationSent
    timeSinceLastCheck = datetime.now() #  now-6min is the initial value  time I last run script should be 5 minutes older than now (its in minutes)
    while(((datetime.now()-timeSinceLastCheck)).seconds/60 <= 5 ):
        pass
        #run script after 5 min since last run
    timeSinceLastCheck = datetime.now()
    # its now ready, check battery and if it is full send message
    batteryLevel = get_battery_level();
    if(batteryLevel < 94):
        pass
    else: #mod to check if it is charging
        if(not batteryNotificationSent):
            send_message(f"Battery Sufficiently Charged!\nBattery Level:{batteryLevel}%")
            batteryNotificationSent = True
        safe_charge_mon()

# update user system just got online

if(just_started):
        just_started = False
        send_message(f"SENTINEL IS UP AND RUNNING!\nTIME: {datetime.now().strftime(dateFormat)}") 



threading.Thread(target=safe_charge_mon, daemon=True).start()

bot.polling()
