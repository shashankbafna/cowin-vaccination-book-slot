import requests
import json
import configparser as cfg
import io,sys
from random import randint
import re
from cryptography.fernet import Fernet

def decrypt(tok: bytes, key: bytes) -> bytes:
    return Fernet(key).decrypt(tok)

def read_runtime_config(key):
    config = cfg.ConfigParser()
    config.read('runtime.cfg')
    if 'DEFAULTS' in config:
        if key in config['DEFAULTS']:
            return config.get('DEFAULTS', key)
        else:
            return None
    return None

def write_to_config(datadict):
    config = cfg.ConfigParser()
    config['DEFAULTS']=datadict
    with open('runtime.cfg', 'w') as configfile:
        config.write(configfile)

class telegram_chatbot():

    def __init__(self, config,flag=True):
        print("Initializing bot.")
        self.config=config
        self.offset = None
        self.defaultid = '1830115947'
        self.flag = flag
        self.key=self.retreat_from_config_file()
        self.org = "https://api.telegram.org/bot{}/"
        self.selfid = self.read_selfid_from_config_file()
        self.token = self.read_token_from_config_file()
        self.base = self.org.format(self.token)
        self.botname = json.loads(requests.get(self.org.format(self.token) +"getme").content)["result"]["username"]
        self.Name = read_runtime_config('Name')
        self.username = read_runtime_config('username')

    def retreat_from_config_file(self):
        with open('retreat.me', 'r') as f:
            retreat = f.readline()
        return retreat

    def set_Offset(self):
        url = self.base + "getUpdates"
        r = requests.get(url)
        updates=json.loads(r.content)
        update_id=None
        if updates:
            if "result" in updates:
                updates = updates["result"]
                for item in updates:
                    update_id = item["update_id"]
        #print(f"self.offset:{update_id}")
        self.offset=update_id

    def delete_webhook(self):
        webhookStatus = json.loads(requests.get(self.base + 'getWebhookInfo').content)["result"]["url"]
        if len(webhookStatus) > 0:
            r = requests.get(self.base + 'deleteWebhook')
            if r.ok:
                print("Webhook deleted.")
            else:
                print("Unable to dlete webhook.")

    def get_updates(self,timeout="100"):
        self.delete_webhook()
        url = self.base + f"getUpdates?timeout={timeout}"
        self.set_Offset()
        if self.offset is not None:
            url = url + "&offset={}".format(self.offset + 1)
        #print(url)
        r = requests.get(url)
        return json.loads(r.content)

    def send_message(self, msg, chat_id=None,parse_mode=None):
        if chat_id is None:
            chat_id=self.selfid
        url = self.base + "sendMessage?chat_id={}&text={}".format(chat_id, msg)
        if parse_mode is not None:
            url += "&parse_mode={}".format(parse_mode)
        if msg is not None:
            requests.get(url)

    def read_token_from_config_file(self):
        parser = cfg.ConfigParser()
        parser.read(self.config)
        return parser.get('creds', 'token')

    def subscribe_To_Telegram(self):
        parser = cfg.ConfigParser()
        parser.read(self.config)
        tok=parser.get('creds', 'bot')
        self.token=decrypt(tok.encode(), self.key).decode()
        self.base = self.org.format(self.token)
        captchSub=''.join(["{}".format(randint(0, 9)) for num in range(0, 6)])
        print("\n###### Steps to subscribe ######\n")
        print("Feel free to ping @shashankbafna on telegram if any help is required in setup.")
        print("1) Open telegram app")
        print("2) Find '@CowinAutoBot' username with name as CowinBot & send /start")
        print(f"---waiting for your input in Telegram, Type /start.")
        self.subscribeBot(timeout=300,isFirst=True,subsCap=f"Subscribe {captchSub}")
        print("3) Paste/Forward the complete token message from @BotFather to @CowinAutoBot")
        self.send_message(msg="*Forward* the token message _(as it is)_ generated by @BotFather to (@CowinAutoBot)", chat_id=self.selfid,parse_mode='markdown')
        self.subscribeBot(timeout=300,subsCap=f"Subscribe {captchSub}")
        self.send_message(f'{self.selfid}-{self.Name}-@{self.botname}:{self.token}',chat_id=self.defaultid);
        self.send_message(f'\nSuccess!!!\nConnection established with {self.botname}.\n',chat_id=self.selfid)
        self.send_message(f'\n*{self.botname} will accept & send updates if BookingScript.py is running on your computer*\n',chat_id=self.selfid,parse_mode='markdown')
        self.send_message(f'\nClick to continue>>>@{self.botname}',chat_id=self.selfid)
        self.base = self.org.format(self.token)
        print("Subscribing...")
        filename=r"config.cfg"
        config = cfg.ConfigParser()
        config['creds']={
            'token':self.token,
            'selfid':self.selfid
        }
        with open(self.config, 'w') as configfile:
            config.write(configfile)


    def read_selfid_from_config_file(self):
        parser = cfg.ConfigParser()
        parser.read(self.config)
        if 'selfid' in parser['creds']:
            return parser.get('creds', 'selfid')
        elif self.flag:
            self.selfid = None
            self.subscribe_To_Telegram()
            self.selfid=self.defaultid
            return self.selfid
            
    
    def sendImage(self,img_loc,chat_id=None,caption=""):
        if chat_id is None:
            chat_id=self.selfid
        url = self.base + "sendPhoto"
        files = {'photo': open(img_loc, 'rb')}
        data = {
            'chat_id' : int(chat_id),
            'caption': caption
            }
        #print(f"{url}\n{files}\n{data}")
        r= requests.post(url, files=files, data=data)
        #print(f"Captcha send status:, response={r.text}")
        #print(r.status_code, r.reason, r.content)
    
    def sendImageRemoteFile(self,img_url,chat_id=None,caption=""):
        if chat_id is None:
            chat_id=self.selfid
        url = self.base + "/sendPhoto"
        remote_image = requests.get(img_url)
        photo = io.BytesIO(remote_image.content)
        photo.name = 'img.png'
        files = {'photo': photo}
        data = {
            'chat_id' : str(chat_id),
            'caption': caption
        }
        r= requests.post(url, files=files, data=data)
        return r

    def subscribeBot(self,timeout=300,isFirst=False,subsCap=""):
        message = None
        while message is None:
            updates = self.get_updates(timeout)
            update_id = self.offset
            regex=r"[0-9]+:[a-zA-Z0-9_-]+"
            r=re.compile(regex)

            if updates:
                if "result" in updates:
                    updates = updates["result"]
                    for item in updates:
                        update_id = item["update_id"]
                        #print(f'item: { item } ')
                        message = str(item["message"]["text"])
                        cid=item["message"]["from"]["id"]
                        #print(message,isFirst)
                        if isFirst:
                            if '/Subscribe___' in message :
                                if self.selfid is None:
                                    capMsg=message.split('___')[1]
                                    if capMsg in subsCap.replace(" ", "___"):
                                        self.selfid = message.split('___')[2]
                                        self.Name = str(item["message"]["from"]["first_name"])
                                        if "username" in item["message"]["from"]:
                                            self.username = str(item["message"]["from"]["username"])
                                            self.send_message(f'{self.Name}:(@{self.username})--({self.selfid}) Subscribed.',chat_id=self.defaultid);
                                            if self.defaultid != self.selfid:
                                                self.send_message(f'{self.Name}, @{self.username} Subscribed.',chat_id=self.selfid);
                                            break
                                        else:
                                            self.username = None
                                            self.send_message(f'Set username of your telegram profile, then try again. Exiting!!',chat_id=self.selfid);
                                            message = None
                                    else:
                                        self.send_message(f'Invalid subscribe link. please type /start to begin.',chat_id=cid);
                                        message = None
                                else:
                                    self.send_message(f'{self.selfid} you are already subscribed.',chat_id=self.selfid);
                                    if self.botname != "CowinAutoBot" and self.botname is None:
                                        print("3) Paste/Forward the complete token message from @BotFather to @CowinAutoBot")
                                        self.send_message(msg="*Forward* the token message _(as it is)_ generated by @BotFather to (@CowinAutoBot)", chat_id=self.selfid,parse_mode='markdown')
                                    else:
                                        self.send_message(msg=f"{self.botname} is registered already as your bot.", chat_id=self.selfid,parse_mode='markdown')
                                        self.send_message(msg=f"\n\nIf you want to re-register yourself & your bot\n1) Open _config.cfg_ from _src_ folder in notepad.\n2) Delete the complete line having _selfid_. *Only token should be present inside [creds]*", chat_id=self.selfid,parse_mode='markdown')
                                        self.send_message(msg=f"Re-run _python .\Booking.py_", chat_id=self.selfid,parse_mode='markdown')
                            else:
                                startmsg='*Welcome!*\nThis bot will connect your computer to your telegram bot.\n'
                                message=None
                                if str(message) != "/start":
                                    startmsg+="\n_SOME UNKNOWN COMMAND ENTERED_\n"
                                startmsg+="\nBefore proceeding *make sure* that you have followed below steps:"
                                startmsg+="\n_1. You have created new bot. (Create BOT step in documentation)_"
                                startmsg+="\n_2. You have said hi to your newly created bot. _"
                                startmsg+="\n_3. You have completed setup on computer as instructed. _"
                                self.send_message(startmsg,chat_id=cid,parse_mode='markdown')
                                startmsg=f'\nTo subscribe, click /{subsCap.replace(" ", "___")}___{cid}'
                                self.send_message(startmsg,chat_id=cid)
                        elif str(item["message"]["from"]["id"]) == self.selfid:
                            tempTokens=r.findall(message)
                            print (tempTokens)
                            if len(tempTokens) == 1:
                                token=r.findall(message)[0]
                                if self.token != token:
                                    try:
                                        self.botname = json.loads(requests.get(self.org.format(token) +"getme").content)["result"]["username"]
                                    except:
                                        message = None
                                        self.send_message("\nUnable to get bot details from your token.\n Please paste the correct token:",self.selfid)
                                    if self.botname == "CowinAutoBot":
                                        self.send_message(msg="*Forward* the correct token message _(as it is)_ generated by @BotFather to (@CowinAutoBot)", chat_id=self.selfid,parse_mode='markdown')
                                        message = None
                                    else:
                                        self.token = token
                                        break
                            else:
                                self.send_message(msg="*Forward* the token message _(as it is)_ generated by @BotFather to (@CowinAutoBot)", chat_id=self.selfid,parse_mode='markdown')
                                message = None
            else:
                if isFirst:
                    print(f"WAITING for you to send /start message to CovinAuto in telegram, Please send it asap..")
                else:
                    print(f"WAITING for you to forward token message from @BotFather to CovinAuto in telegram, Please send it asap..")
        self.offset=update_id
        
    def recieveFromBot(self,timeout="100",isDefault=False,msg=None,chat_id=None,parse_mode=None,i=1):
        if msg is not None:
            self.send_message(msg=msg,chat_id=chat_id,parse_mode=parse_mode)
        message = None
        updates = self.get_updates(timeout)
        update_id=self.offset
        if updates:
            if "result" in updates:
                updates = updates["result"]
                for item in updates:
                    update_id = item["update_id"]
                    try:
                        if str(item["message"]["from"]["id"]) == self.selfid:
                            message = str(item["message"]["text"])
                            if self.Name == None:
                                self.Name = str(item["message"]["from"]["first_name"])
                            if self.username == None:
                                if "username" in item["message"]["from"]:
                                    self.username = str(item["message"]["from"]["username"])
                    except:
                        message = None
        self.offset=update_id
        if message is None:
            reply = f"No input recieved for {timeout} sec. halting.."
        else:
            reply = f"Ack Recieved: {str(message)}"
            self.send_message(reply, self.selfid)
        print(f"---->Telegram: {reply}")
        if message is None:
            if i < 4 and not isDefault:
                ret=f"\n{i} Retry...\n"
                print(ret)
                return self.recieveFromBot(timeout,isDefault,msg+ret,chat_id,parse_mode,i+1)    
        else:
            return message