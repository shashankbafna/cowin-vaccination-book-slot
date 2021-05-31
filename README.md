# cowin-vaccination-book-slot
Vaccination slot booking telegram bot. - Suggestions &amp; feedbacks are welcome.

This automation subscribes to the telegram bot. Once registered mobile number is entered, it gets the cowin-session using otp provided by the user.
While maintaining the valid user session, it tries to find a vaccination slot for the selected user & selected calendar.
It checks for preferences such as vaccine type, state, pincode, district, paid/free & whether to auto-book the slot or not.
Once slot is found, it tries booking it by randomly selecting the slot & resolving the captcha.

**DISCLAIMER: 
USE IT AT YOUR OWN RISK.**
-  This is a make-shift automation for booking the slot which was not possible due the availability of vaccines vs count of people ratio.
-  I am not a developer but an engineer/ Script writer. Consider this before making any comments or giving any advices.
-  Feel free to give suggestions & copy & enhance the code.

Lastly, goes without saying:
**once you get your shot, please do help out any underprivileged people around you who may not have a laptop or the know-how.
For instance any sort of domestic help, or the staff in your local grocery store, or literally the thousands of people who don't have the knowledge or luxury we do.**

Special thanks to:
1) pallupz: https://github.com/pallupz/covid-vaccine-booking/
2) Telegram: https://web.telegram.org/
3) Python: https://www.python.org/
4) COWIN: https://www.cowin.gov.in/
5) Lastly my wife: Srishti (@ournotesfromtheroads) (https://www.instagram.com/ournotesfromtheroads/)

## Pre-requisites:

1) **Computer/Laptop/CPU** - capable of running python & having access to internet.
   -  Packages/Softwares needed on computer:
      - Windows/Linux OS.
      - Python 3 or greater installed.
         Windows link to install: https://www.python.org/ftp/python/3.9.5/python-3.9.5-amd64.exe
         Linux link to install: https://www.python.org/ftp/python/3.9.5/Python-3.9.5.tgz
      
2) **Internet connection** - Only with **_Indian_** ISP providers.

3) **Smart phone**<br>
   - Having number provided by any Indian service provider with access to network & data.
   - Network  - the more the merrier.<br>
   - Telegram app<br>

4) **Registered on cowin-portal**
   -  If not already registered, please register it using the following link:
      https://selfregistration.cowin.gov.in/
   -  Add all the non-vaccinated members to get the vaccinations slots for them.

 ## Installation:
 This is a one time activity.
 1)   Install latest python if not already present from the link mentioned in **Pre-requisites**
      -  Add Python 3.7 to Path while installing (**MANDATORY**)
 3)   Download the source code from the following link-
      -  https://github.com/shashankbafna/cowin-vaccination-book-slot/archive/refs/heads/main.zip
 4)   Unzip & Extract the zip downloaded.
 5)   Go inside the Extracted folder ->src
      -  ![image](https://user-images.githubusercontent.com/54980800/120198763-1f138300-c240-11eb-8198-aca2ff40178f.png)

 5)   In the The Address bar, which is located at the top of File Explorer as shown above, displays the path of the currently selected folder, type "cmd"
 6)   This will open the command prompt with the location of script src.
 7)   Type the following command to install the dependent packages to run this script.
      -  `pip install -r ../requirements.txt`
      -  ![image](https://user-images.githubusercontent.com/54980800/120200115-98f83c00-c241-11eb-86f2-39f5b9386b65.png)

 
 ## STARTING & SUBSCRIBING:
   - Subscribing:
      If you are running this for the first time, you will need to subscribe to telegram bot(**CowinAuto**).
      -  Open telegram app on mobile.
      -  Search for userbot Name:CowinAuto (UserName@CowinAutoBot) in the telegram app.
      -  Click START or Say hi to the bot - *BOT WILL NOT RESPOND AT THIS MOMENT, keep on following the instructions.*
      -  Send the message to the userbot- displayed for the first time after starting the script.
   -  Startup:
      If all the above steps are done, we are good to fire the script.
      - `python ./cowinVaccinationSlotAutoBooking.py`
      - Follow the on screen instructions after starting the script.
   ![image](https://user-images.githubusercontent.com/54980800/120200314-d2c94280-c241-11eb-98d3-84ae76b6a23f.png)
   After posting the Subscribe message on telegram,
   ![image](https://user-images.githubusercontent.com/54980800/120201561-37d16800-c243-11eb-96e1-1ccbb84ac9ba.png)
   
   After this, just read the updates & inputs required in telegram.

## SELECTION & FEATURES:
   -  Inputs:
      -  In Telegram, your messages act as input to the script.
      -  Mostly, the inputs are one time effort, as once entered, this will be saved in a file for future run.
      -  If timeout happens, i.e. user doesnot respond within 100 sec from the time when bot's message arrives.
         -  Manual input can be given from keyboard but only on computer.
      - Below are the list of Inputs gathered for the first run.
         -  Enter the phone number
         -  Enter OTP
         -  Enter comma seperated index numbers of beneficiares
         -  Search using pincode or State/District
            -  Enter pincodes/ Index number of State, followed by Index number of Districts.
         -  Minimum Availability required
         -  How frequent the request should be sent to COWIN portal to find out the slot availability from APIs.
         -  Search for a week from when? today, tomorrow or date?
         -  Fee preferences? Free or Paid?
         -  Auto booking? **yes-please** or no
      -  Mind the caps/digits/case of characters while entering.

## SCREENSHOTS:


