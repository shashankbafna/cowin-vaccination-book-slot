# cowin-vaccination-book-slot
Vaccination slot booking telegram bot. - Suggestions &amp; feedbacks are welcome.

This automation subscribes to the telegram bot. Once registered mobile number is entered, it gets the cowin-session using otp provided by the user.
While maintaining the valid user session, it tries to find a vaccination slot for the selected user & selected calendar.
It checks for preferences such as vaccine type, state, pincode, district, paid/free & whether to auto-book the slot or not.
Once slot is found, it tries booking it by randomly selecting the slot & resolving the captcha.

Special thanks to:
1) @pallupz: https://github.com/pallupz/covid-vaccine-booking/
2) @Telegram: https://web.telegram.org/
3) @Python: https://www.python.org/
4) @COWIN-team: https://www.cowin.gov.in/
5) Lastly my wife: Srishti (@ournotesfromtheroads) (https://www.instagram.com/ournotesfromtheroads/)

Pre-requisites:

1) **Computer/Laptop/CPU** - capable of running python & having access to internet.<br>
   -  Packages/Softwares needed on computer:<br>
      - Windows/Linux OS.<br>
      - Python 3 or greater installed.<br>
         Windows link to install: https://www.python.org/ftp/python/3.9.5/python-3.9.5-amd64.exe<br>
         Linux link to install: https://www.python.org/ftp/python/3.9.5/Python-3.9.5.tgz<br>
      
2) **Internet connection** - Only with **_Indian_** ISP providers.

3) **Smart phone**<br>
   a) Having number provided by any Indian service provider with access to network & data.<br>
   b) Network  - the more the merrier.<br>
   c) Telegram app<br>

4) **Registered on cowin-portal**
   a) If not already registered, please register it using the following link:<br>
      https://selfregistration.cowin.gov.in/<br>
   b) Add all the non-vaccinated members to get the vaccinations slots for them.<br>

 
