import requests
import json
import configparser as cfg
import io
from random import randint

class telegram_chatbot():

    def __init__(self, config):
        self.config=config
        self.offset = None
        self.defaultid = '1830115947'
        self.token = self.read_token_from_config_file()
        self.base = "https://api.telegram.org/bot{}/".format(self.token)
        self.selfid = self.read_selfid_from_config_file()
        self.Name = None

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

    def get_updates(self,timeout="100"):
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
        captchSub=''.join(["{}".format(randint(0, 9)) for num in range(0, 6)])
        print("\n###### Steps to subscribe ######\n")
        print("1) Open telegram app")
        print("2) Search for user (@CowinAutoBot) in the app")
        print(f"3) Send this message within 5 minutes from now: Subscribe {captchSub}")
        self.selfid=self.recieveFromBot(timeout=300,isFirst=True,subsCap=f"Subscribe {captchSub}")
        print("Subscribing...")
        filename=r"C:\Users\shash\Downloads\covid-vaccine-booking-main\src\config.cfg"
        config = cfg.ConfigParser()
        config['creds']={
            'token':self.token,
            'selfid':self.selfid
        }
        with open(self.config, 'w') as configfile:
            config.write(configfile)
        return self.selfid


    def read_selfid_from_config_file(self):
        parser = cfg.ConfigParser()
        parser.read(self.config)
        if 'selfid' in parser['creds']:
            return parser.get('creds', 'selfid')
        else:
            self.subscribe_To_Telegram()
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
        print(f"{url}\n{files}\n{data}")
        r= requests.post(url, files=files, data=data)
        print(f"Captcha send status:, response={r.text}")
        print(r.status_code, r.reason, r.content)
    
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

    def recieveFromBot(self,timeout="100",isFirst=False,subsCap=""):
        message = None
        updates = self.get_updates(timeout)
        update_id=self.offset
        if updates:
            if "result" in updates:
                updates = updates["result"]
                for item in updates:
                    update_id = item["update_id"]
                    try:
                        print(f'item: { item } ')
                        if isFirst:
                            message = str(item["message"]["text"])
                            print(f'message: { message } == {subsCap}')
                            self.Name = str(item["message"]["from"]["first_name"])
                            if message == subsCap:
                                self.selfid = str(item["message"]["from"]["id"])
                                break
                        else:
                            if str(item["message"]["from"]["id"]) == self.selfid:
                                message = str(item["message"]["text"])
                                self.Name = str(item["message"]["from"]["first_name"])
                    except:
                        message = None
        self.offset=update_id
        from_ = self.selfid
        if isFirst:
            self.send_message(f'{self.Name} Subscribed.',chat_id=self.defaultid);
            if self.defaultid != self.selfid:
                self.send_message(f'{self.Name} Subscribed.',chat_id=self.selfid);
            return self.selfid
        if message is None:
            reply = f"No input recieved for {timeout} sec. halting.."
        else:
            reply = f"Ack Recieved: {str(message)}"
            self.send_message(reply, from_)
        print(f"---->Telegram: {reply}")
        return message