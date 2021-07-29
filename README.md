# COWIN VACCINATION SLOT AUTO BOOKING
## _(Bot with captcha solving & alerting capabilities. Never miss the vaccine slot.)_

_July-29-2021/ 1220 hrs_: **230 successfully booked -- PAN INDIA** <br>

![Cowin-AutoBot](https://user-images.githubusercontent.com/54980800/120240129-7552e700-c27d-11eb-8edc-de83dc6a991b.jpg)

## HOW IT WORKS
-  Your computer will act as a server to update messages & recieve messages from telegram bot.
-  This automation script, gathers the recieved messages from the user & checks the details on COWIN portal.
-  Your phone (Telegram app) will act as a client to recieve messages sent from the computer.
-  If your computer stops or your script stops on computer, you will not see any updates on telegram, neither it will search for any slots.
-  You need to constantly respond if you recieve any alerts on telegram as notification.

<br>
<br>
<img src="https://user-images.githubusercontent.com/54980800/120373493-0ab1b200-c336-11eb-9e63-9c2a0bbf5a4a.png" align="left" width="200px"/>
<p>
   <q>Personally, we have used this & we (me, Srishti) got vaccinated, hope it helps you as well.</q>
</p>
<br>
<br>
<blockquote>
This automation subscribes to the telegram bot. Once registered mobile number is entered, it gets the cowin-session using otp provided by the user.
While maintaining the valid user session, it tries to find a vaccination slot for the selected user & selected calendar.
It checks for preferences such as vaccine type, state, pincode, district, paid/free & whether to auto-book the slot or not.
Once slot is found, it tries booking it by randomly selecting the slot & resolving the captcha.
</blockquote>
<br clear="left"/>
<br clear="right"/>


## Pre-requisites:
1) **Computer/Laptop/CPU** - capable of running <a href="https://www.python.org/ftp/python/3.9.5/" >python</a> & having access to internet.
2) **Internet connection** - Only with **_Indian_** ISP providers.
3) **Smart phone** - with telegram app
4) **Registered on COWIN-portal** -  Add all the non-vaccinated members in <a href="https://selfregistration.cowin.gov.in/" >here</a>.

 ## Create BOT (in Telegram)
 This is a one time activity. If you already have a bot & its token, you can proceed to Installation step.
 - On **Mobile/Phone** open telegram app:
   <img src="https://user-images.githubusercontent.com/54980800/120314845-48441a00-c2f9-11eb-998f-f5115d93b8fd.png" align="left" width="300px"/> 
   - Search for **@BotFather** userbot.
      - type `/newbot`
      - Enter any desired name for the bot
      - Enter the unique username for the bot
      - if username is valid, confirmation message from @BotFather with token should come. If not, keep on trying different usernames until you get the token message.
      Please see the image for clarification.
   - **Once it is created, say hi to your bot**.         
<br clear="left"/>

 ## Installation
 This is a one time activity.
   1)  Download the source code from the following link-
      -  https://github.com/shashankbafna/cowin-vaccination-book-slot/archive/refs/heads/main.zip
   2)   Unzip & Extract the zip downloaded.
   
   - if you are on windows 10 & have adminitrator rights:
      - right click on setup.ps1 & Run with PowerShell
      - Installation completed, you can skip all the below steps. Proceed to Startup, 2nd step.
   - else if you do not have windows 10 or Admin rights, continue following the below steps.
      1)   Go inside the Extracted folder ->src
      2)   Install latest python if not already present from the link mentioned in **Pre-requisites**
         -  Do not forget to check Add Python 3.7 to Path/Environment variable while installing (**MANDATORY**)
      3)   Go inside the Extracted folder ->src
      4)   In the The Address bar, which is located at the top of File Explorer as shown below, displays the path of the currently selected folder, type "cmd"
         -  ![image](https://user-images.githubusercontent.com/54980800/120198763-1f138300-c240-11eb-8198-aca2ff40178f.png)
      5)   This will open the command prompt with the location of script src.
      6)   Type the following command in command prompt (just opened in above step) to install the dependent packages to run this script.
         -  `pip install -r ../requirements.txt`
         -  Optional if you want to run above command to install above dependencies in a virtual env ->Only for advanced python users.
         -  ![image](https://user-images.githubusercontent.com/54980800/120200115-98f83c00-c241-11eb-86f2-39f5b9386b65.png)
  
 ## STARTUP Script (on computer):
   If installation is done manually, proceed with step 1 else contine from step 2.
   1) Type below command in command prompt (already opened during installation)
      `python ./Booking.py`
      -  Follow the on screen instructions after starting the script.
   ![image](https://user-images.githubusercontent.com/54980800/121158296-e12de480-c867-11eb-90b6-201618d6369b.png)
   
   2) Goto Mobile telegram app:   
       <img src="https://user-images.githubusercontent.com/54980800/121158721-34a03280-c868-11eb-8d59-39d8e451009b.png" align="left" width="300px"/>
      -  Make sure, you have said hi to your newly created bot.
      -  Search for user @CowinAutoBot & click or type /start. -> click SubscribeID link.
      -  After that it should ask for bot token message, which you have recieved from @BotFather bot
     Check this screenshot for further clarification.
     <br>
     <br>
   **MANDATORY (after startup)**
-  **MAKE SURE THAT SCRIPT Keeps RUNNING ON LAPTOP, else you will not see updates on telegram. You need to follow steps for "Startup" if script exits.**
-  **__ALSO MAKE SURE TO ENTER OTP as asked in the telegram bot, else session will not continue, you may need to follow steps for "Startup" again.__** 
      <br>   
   <p>Now respond to your bot in telegram.</p>
   <br clear="left"/>

## SELECTION & FEATURES:
   -  Inputs:
      -  In Telegram, your messages act as input to the script.
      **Mind the caps/digits/case of characters while entering.**
      -  Index numbers are mentioned in front of the selections like in front of your name, in front of states, in front of districts etc.
      -  Mostly, _**the inputs are one time effort, as once entered, this will be saved in a file**_ for future run.
      -  If timeout happens, i.e. user doesnot respond within 100 sec from the time when bot's message arrives.
         -  Manual input can be given from keyboard but only on computer.
      - Below are the list of Inputs gathered for the first run.
         -  Enter the phone number
         -  Enter OTP
         -  Enter comma seperated index numbers of beneficiares
         -  Search using pincode or State/District
            -  Enter pincodes/ Index number of State, followed by Index number of Districts.
         -  How frequent the request should be sent to COWIN portal to find out the slot availability from APIs.
         -  Search for a week from when? today, tomorrow or date?
         -  Fee preferences? Free or Paid?
         -  Auto booking? **yes-please** or no

## Share and Feedback
-  Please let me know if this automation helped you, by giving a vote of thanks in my linked profile: https://www.linkedin.com/in/bafnashashank/
-  Also I would like to hear from you guys about the feedback, suggestions, comments
-  Feel free to ping me
   -  Instagram: https://www.instagram.com/shashankbafna/
   -  Facebook: https://www.facebook.com/shashbafna
   -  or leave out comments in here to get any help.
## _I will not mind sharing a cup of ~~coffee~~ **TEA**_

**Must Read - 1st Para**: https://apisetu.gov.in/public/marketplace/api/cowin/cowin-public-v2

## Futurescope:
1) As I had an ios phone, It was not possible to automate otps, however, it is possible to automate otp transmission via android.
   -  This results in entering the otp every 15 mins, to continue the session for searching the slots.
   -  This requires constant response from the user when notified either via computer beep or telegram notification.
2) Inputs & outputs on telegram can be beautified, right now, I have just pushed them from console.
3) Exception handling for inputs & url requests.

Special thanks to:
1) **pallupz**: For sourcing the raw python code. : https://github.com/pallupz/covid-vaccine-booking/
2) **COWIN**: For providing open APIs. : https://www.cowin.gov.in/
3) **Telegram**: For providing open APIs. : https://web.telegram.org/
4) **Python**: Life without you is not possible. : https://www.python.org/
5) Lastly my wife: **Srishti** (**@ournotesfromtheroads**): For being my guinea pig :(https://www.instagram.com/ournotesfromtheroads/)

**DISCLAIMER: 
USE IT AT YOUR OWN RISK.**
-  This is a make-shift automation for booking the slot which was not possible manually due to the significant ratio for availability of vaccines & People in our country.
-  I am not a developer but an engineer/ Script writer. Consider this before making any comments or giving any advices.
-  Feel free to give suggestions, Also, please copy & enhance the code if you want.
   -  Make sure to let me know, hopefully, I can also help.

Lastly, goes without saying:
**once you get your shot, please do help out any underprivileged people around you who may not have a laptop or the know-how.
For instance any sort of domestic help, or the staff in your local grocery store, or literally the thousands of people who don't have the knowledge or luxury we do.**

## SCREENSHOTS:

<img src="https://user-images.githubusercontent.com/54980800/120204156-22aa0880-c246-11eb-94d5-1f0f7865c99c.png" float="left" width="190px"/><img src="https://user-images.githubusercontent.com/54980800/120204294-4705e500-c246-11eb-8752-64bfae605fd8.png" float="left" width="190px"/><img src="https://user-images.githubusercontent.com/54980800/120204373-5be27880-c246-11eb-9ed2-a57c3ce71396.png" float="left" width="190px"/><img src="https://user-images.githubusercontent.com/54980800/120204494-82081880-c246-11eb-9418-f99db43525ac.png" float="left" width="190px"/><img src="https://user-images.githubusercontent.com/54980800/120204610-a4019b00-c246-11eb-89d0-c142e88d02dc.png" float="left" width="190px"/>

