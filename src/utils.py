import json
from hashlib import sha256
from inputimeout import inputimeout, TimeoutOccurred
import tabulate, copy, time, datetime, requests, sys, os, random
from captcha import captcha_builder
from bs4 import BeautifulSoup
import base64
import re
import configparser as cfg

import platform
is_windows = any(platform.win32_ver())

from telegramBot import telegram_chatbot, read_runtime_config, write_to_config
bot = telegram_chatbot(r"config.cfg")


BOOKING_URL = "https://cdn-api.co-vin.in/api/v2/appointment/schedule"
BENEFICIARIES_URL = "https://cdn-api.co-vin.in/api/v2/appointment/beneficiaries"
CALENDAR_URL_DISTRICT = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/calendarByDistrict?district_id={0}&date={1}"
CALENDAR_URL_PINCODE = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/calendarByPin?pincode={0}&date={1}"
CAPTCHA_URL = "https://cdn-api.co-vin.in/api/v2/auth/getRecaptcha"
OTP_PUBLIC_URL = 'https://cdn-api.co-vin.in/api/v2/auth/public/generateOTP'
OTP_PRO_URL = 'https://cdn-api.co-vin.in/api/v2/auth/generateMobileOTP'
CANCEL_URL = 'https://cdn-api.co-vin.in/api/v2/appointment/cancel'

WARNING_BEEP_DURATION = (1000, 2000)
try:
    if is_windows:
        import winsound
        def beep(freq, duration): 
            winsound.Beep(freq, duration)
    else:
        import os
        def beep(freq,duration):
            #apt-get install beep
            os.system('beep -f %s -l %s' % (freq,duration))
except:
    if is_windows:
        print("Unable to import winsound on windows, try 'pip install winsound' in command prompt. Alerting on this PC won't work.")
    else:
        print("Unable to find beep package on linux, try re-running after 'apt-get install beep'. Alerting on this PC won't work.")
    

def viable_options(resp, minimum_slots, min_age_booking, fee_type, dose):
    options = []
    if len(resp['centers']) >= 0:
        for center in resp['centers']:
            #print (center)
            for session in center['sessions']:
                # availability = session['available_capacity']
                availability = session['available_capacity_dose1'] if dose == 1 else session['available_capacity_dose2']
                #print(f"{session['date']} - center: {center['name']} - availability:{availability} - {session['min_age_limit']}")
                if (availability >= minimum_slots) \
                        and (session['min_age_limit'] <= min_age_booking)\
                        and (center['fee_type'] in fee_type):
                    out = {
                        'name': center['name'],
                        'district': center['district_name'],
                        'pincode': center['pincode'],
                        'center_id': center['center_id'],
                        'available': availability,
                        'date': session['date'],
                        'slots': session['slots'],
                        'session_id': session['session_id']
                    }
                    options.append(out)

                else:
                    pass
    else:
        pass

    return options


def display_table(dict_list,ret=False):
    """
    This function
        1. Takes a list of dictionary
        2. Add an Index column, and
        3. Displays the data in tabular format
    """
    header = ['IDX'] + list(dict_list[0].keys())
    rows = [[idx + 1] + list(x.values()) for idx, x in enumerate(dict_list)]
    #genTable=tabulate.tabulate(rows, header, tablefmt='presto')
    genTable=tabulate.tabulate(rows, tablefmt='presto')
    print(genTable)
    if ret:
        return genTable
        

def display_info_dict(details,ret=False):
    genPrint="\n"
    for key, value in details.items():
        if isinstance(value, list):
            if all(isinstance(item, dict) for item in value):
                genPrint+=f"\n\t{key}:"
                print(f"\t{key}:\n")
                genPrint+=display_table(value,True)
            else:
                genPrint+=f"\n\t{key}\t: {value}"
                print(f"\t{key}\t: {value}")
        else:
            genPrint+=f"\n\t{key}\t: {value}"
            print(f"\t{key}\t: {value}")
    print(genPrint)
    if ret:
        genPrint+="\n"
        return genPrint

def confirm_and_proceed(collected_details):
    replyMsg="\n======= Confirm Info ========\n"
    print("\n================================= Confirm Info =================================\n")
    replyMsg+=display_info_dict(collected_details,True)
    replyMsg+="\nProceed with above info (y/n Default y) : "
    bot.send_message(msg=replyMsg)
    confirm=bot.recieveFromBot()
    if confirm is None or len(confirm) == 0:
        confirm = 'y'
        bot.send_message(msg=f"_No input recieved, setting default as *{confirm}*_",parse_mode='markdown')
        #confirm = input("\nProceed with above info (y/n Default y) : ")
    confirm = confirm if confirm else 'y'
    if confirm != 'y':
        bot.send_message("Details not confirmed. Exiting process.")
        print("Details not confirmed. Exiting process.")
        os.system("pause")
        sys.exit()


def save_user_info(filename, details):
    print("\n================================= Save Info =================================\n")
    #save_info = input("Would you like to save this as a JSON file for easy use next time?: (y/n Default y): ")
    save_info='y'
    save_info = save_info if save_info else 'y'
    if save_info == 'y':
        with open(filename, 'w') as f:
            json.dump(details, f)

        print(f"Info saved to {filename} in {os.getcwd()}")


def get_saved_user_info(filename):
    with open(filename, 'r') as f:
        data = json.load(f)

    return data


def collect_user_details(request_header):
    # Get Beneficiaries
    bot.send_message("Fetching registered beneficiaries..")
    print("Fetching registered beneficiaries.. ")
    beneficiary_dtls = get_beneficiaries(request_header)

    if len(beneficiary_dtls) == 0:
        bot.send_message("Did you register this number in COWIN Portal?..If yes, Please add members to get vaccinated. Exiting Application.")
        print("There should be at least one beneficiary. Exiting.")
        os.system("pause")
        sys.exit(1)

    # Make sure all beneficiaries have the same type of vaccine
    vaccine_types = [beneficiary['vaccine'] for beneficiary in beneficiary_dtls]
    statuses = [beneficiary['status'] for beneficiary in beneficiary_dtls]

    if len(set(statuses)) > 1:
        replyMsg="\n======= Important =======\n"
        replyMsg+=f"All beneficiaries in one attempt should be of same vaccination status (same dose).\nFound {statuses}"
        replyMsg+="\nExiting Script."
        bot.send_message(replyMsg)
        print("\n================================= Important =================================\n")
        print(f"All beneficiaries in one attempt should be of same vaccination status (same dose). Found {statuses}")
        os.system("pause")
        sys.exit(1)

    vaccines = set(vaccine_types)
    if len(vaccines) > 1 and ('' in vaccines):
        vaccines.remove('')
        vaccine_types.remove('')
        replyMsg="\n======= Important =======\n"
        replyMsg+=f"Some of the beneficiaries have a set vaccine preference ({vaccines}) and some do not."
        replyMsg+="Results will be filtered to show only the set vaccine preference."
        replyMsg+="\nExiting Script."
        bot.send_message(replyMsg)
        print("\n================================= Important =================================\n")
        print(f"Some of the beneficiaries have a set vaccine preference ({vaccines}) and some do not.")
        print("Results will be filtered to show only the set vaccine preference.")
        os.system("pause")

    if len(vaccines) != 1:
        replyMsg="\n======= Important =======\n"
        replyMsg+=f"All beneficiaries in one attempt should have the same vaccine type. Found {len(vaccines)}"
        replyMsg+="\nExiting Script."
        bot.send_message(replyMsg)
        print("\n================================= Important =================================\n")
        print(f"All beneficiaries in one attempt should have the same vaccine type. Found {len(vaccines)}")
        os.system("pause")
        sys.exit(1)

    vaccine_type = vaccine_types[0]
    if not vaccine_type:
        replyMsg="\n======= Vaccine Info =======\n"
        bot.send_message(replyMsg)
        print("\n================================= Vaccine Info =================================\n")
        vaccine_type = get_vaccine_preference()

    replyMsg="\n======= Location Info =======\n"
    print("\n================================= Location Info =================================\n")
    # get search method to use
    replyMsg+="Search by Pincode? Or by State/District? \nEnter 1 for Pincode or 2 for State/District. (Default 2) : "
    bot.send_message(replyMsg)
    search_option = bot.recieveFromBot()
    if search_option is None or len(search_option) == 0:
        search_option = 2
        bot.send_message(msg=f"_No input recieved, setting default as *{search_option}*_",parse_mode='markdown')
        #search_option = input(
        #"""Search by Pincode? Or by State/District? \nEnter 1 for Pincode or 2 for State/District. (Default 2) : """)

    if not search_option or int(search_option) not in [1, 2]:
        search_option = 2
    else:
        search_option = int(search_option)

    if search_option == 2:
        # Collect vaccination center preferance
        location_dtls = get_districts(request_header)

    else:
        # Collect vaccination center preferance
        location_dtls = get_pincodes()

    replyMsg="\n ===== Additional Info ===== \n"
    print("\n================================= Additional Info =================================\n")
    replyMsg+=f'Filter out centers with availability less than ? Minimum {len(beneficiary_dtls)} : '
    # Set filter condition
    bot.send_message(replyMsg)
    minimum_slots = bot.recieveFromBot()
    if minimum_slots is None or len(minimum_slots) == 0:
        minimum_slots = input(f'Filter out centers with availability less than ? Minimum {len(beneficiary_dtls)} : ')
    minimum_slots = int(minimum_slots)
    if minimum_slots:
        minimum_slots = int(minimum_slots) if int(minimum_slots) >= len(beneficiary_dtls) else len(beneficiary_dtls)
    else:
        minimum_slots = len(beneficiary_dtls)


    # Get refresh frequency
    replyMsg='How often do you want to refresh the calendar (in seconds)? Default 15. Minimum 5. : '
    bot.send_message(replyMsg)
    refresh_freq = bot.recieveFromBot()
    if refresh_freq is None or len(refresh_freq) == 0:
        refresh_freq = 15
        bot.send_message(msg=f"_No input recieved, setting default as *{refresh_freq}*_",parse_mode='markdown')
        #refresh_freq = input('How often do you want to refresh the calendar (in seconds)? Default 15. Minimum 5. : ')
    refresh_freq = int(refresh_freq) if refresh_freq and int(refresh_freq) >= 5 else 15

    # Get search start date
    replyMsg='\nSearch for next seven day starting from when?\nUse 1 for today, 2 for tomorrow, or provide a date in the format DD-MM-YYYY. Default 2: '
    bot.send_message(replyMsg)
    start_date = bot.recieveFromBot()
    if start_date is None or len(start_date) == 0:
        start_date = '2'
        bot.send_message(msg=f"_No input recieved, setting default as *{start_date}*_",parse_mode='markdown')
        #start_date = input(
        #'\nSearch for next seven day starting from when?\nUse 1 for today, 2 for tomorrow, or provide a date in the format DD-MM-YYYY. Default 2: ')
    if not start_date:
        start_date = 2
    elif start_date in ['1', '2']:
        start_date = int(start_date)
    else:
        try:
            datetime.datetime.strptime(start_date, '%d-%m-%Y')
        except ValueError:
            replyMsg='Invalid Date! Proceeding with tomorrow.'
            bot.send_message(replyMsg)
            print('Invalid Date! Proceeding with tomorrow.')
            start_date = 2

    # Get preference of Free/Paid option
    fee_type = get_fee_type_preference()
    replyMsg='\n=========== CAUTION! CAUTION! ===========\n'
    replyMsg+="===== BE CAREFUL WITH THIS OPTION! AUTO-BOOKING WILL BOOK THE FIRST AVAILABLE CENTRE, DATE, AND A RANDOM SLOT! ====="
    replyMsg+="Do you want to enable auto-booking? (yes-please or no) Default no: "
    bot.send_message(replyMsg)
    print("\n=========== CAUTION! =========== CAUTION! CAUTION! =============== CAUTION! =======\n")
    print("===== BE CAREFUL WITH THIS OPTION! AUTO-BOOKING WILL BOOK THE FIRST AVAILABLE CENTRE, DATE, AND A RANDOM SLOT! =====")
    auto_book = bot.recieveFromBot()
    if auto_book is None or len(auto_book) == 0:
        auto_book = 'no'
        bot.send_message(msg=f"_No input recieved, setting default as *{auto_book}*_",parse_mode='markdown')
        #auto_book = input("Do you want to enable auto-booking? (yes-please or no) Default no: ")
    auto_book = 'no' if not auto_book else auto_book

    collected_details = {
        'beneficiary_dtls': beneficiary_dtls,
        'location_dtls': location_dtls,
        'search_option': search_option,
        'minimum_slots': minimum_slots,
        'refresh_freq': refresh_freq,
        'auto_book': auto_book,
        'start_date': start_date,
        'vaccine_type': vaccine_type,
        'fee_type': fee_type
    }

    return collected_details


def check_calendar_by_district(request_header, vaccine_type, location_dtls, start_date, minimum_slots, min_age_booking, fee_type, dose):
    """
    This function
        1. Takes details required to check vaccination calendar
        2. Filters result by minimum number of slots available
        3. Returns False if token is invalid
        4. Returns list of vaccination centers & slots if available
    """
    try:
        print('===================================================================================')
        today = datetime.datetime.today()
        base_url = CALENDAR_URL_DISTRICT

        if vaccine_type:
            base_url += f"&vaccine={vaccine_type}"

        options = []
        for location in location_dtls:
            resp = requests.get(base_url.format(location['district_id'], start_date), headers=request_header)

            if resp.status_code == 401:
                print('TOKEN INVALID')
                return False

            elif resp.status_code == 200:
                resp = resp.json()
                if 'centers' in resp:
                    print(f"Centers available in {location['district_name']} from {start_date} as of {today.strftime('%Y-%m-%d %H:%M:%S')}: {len(resp['centers'])}")
                    options += viable_options(resp, minimum_slots, min_age_booking, fee_type, dose)

            else:
                pass

        for location in location_dtls:
            if location['district_name'] in [option['district'] for option in options]:
                for _ in range(2):
                    beep(location['alert_freq'], 550)
        #print(options)
        return options

    except Exception as e:
        print(str(e))
        beep(WARNING_BEEP_DURATION[0], WARNING_BEEP_DURATION[1])

def test_Token(request_header):
    resp = requests.get(CALENDAR_URL_PINCODE.format('560103', 1), headers=request_header)
    if resp.status_code == 401:
        print('TOKEN INVALID')
        return False
    elif resp.status_code == 200:
        print('TOKEN Still VALID')
        return True

def check_calendar_by_pincode(request_header, vaccine_type, location_dtls, start_date, minimum_slots, min_age_booking, fee_type, dose):
    """
    This function
        1. Takes details required to check vaccination calendar
        2. Filters result by minimum number of slots available
        3. Returns False if token is invalid
        4. Returns list of vaccination centers & slots if available
    """
    try:
        print('===================================================================================')
        today = datetime.datetime.today()
        base_url = CALENDAR_URL_PINCODE

        if vaccine_type:
            base_url += f"&vaccine={vaccine_type}"

        options = []
        for location in location_dtls:
            resp = requests.get(base_url.format(location['pincode'], start_date), headers=request_header)

            if resp.status_code == 401:
                print('TOKEN INVALID')
                return False

            elif resp.status_code == 200:
                resp = resp.json()
                if 'centers' in resp:
                    print(f"Centers available in {location['pincode']} from {start_date} for {vaccine_type} as of {today.strftime('%Y-%m-%d %H:%M:%S')}: {len(resp['centers'])}")
                    options += viable_options(resp, minimum_slots, min_age_booking, fee_type, dose)

            else:
                pass

        for location in location_dtls:
            if int(location['pincode']) in [option['pincode'] for option in options]:
                for _ in range(2):
                    beep(location['alert_freq'], 550)

        return options

    except Exception as e:
        print(str(e))
        beep(WARNING_BEEP_DURATION[0], WARNING_BEEP_DURATION[1])

def solve_captcha(resp):
    
    model = "eyJNTExRTExRTExRTExMUUxMUUxMUVpNTExRTExRTExRTExRTExRTExRTExRWk1MTFFMTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRWk1MTFFMTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRWk1MTFFMTExRTExRWk1MTFFMTFFMTFFMTFFaIjogIjAiLCAiTUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUVpNTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTFoiOiAiMSIsICJNTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExMUUxMUUxMUUxMUUxMUUxMUUxMUVpNTExRTExMUUxMUUxMUUxMUUxMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTExRTExRTExRTExRTExRTExMUUxMTFFMTFFaIjogIjIiLCAiTUxMUUxMUUxMUUxMUUxMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRWk1MTFFMTFFMTFFMTFFMTFFMTExMUUxMUUxMUUxMUUxMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTExMUUxMUUxMUUxMUUxMUUxMUUxMTExRTExRTExRTExRTExRTExRTExMTExMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUVoiOiAiMyIsICJNTExRTExRTExRTExRWk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTExRTExRTExRTExRWk1MTFFMTExRTExRTExRTExRTExRTExRTExMUUxMTFFMTExRTExRTExRTExRTExRTExRTExRTExMUUxMUUxMUUxMUVpNTExRTExRTExRTExRTExRWiI6ICI0IiwgIk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFMTExMUUxMUUxMUUxMUUxMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFaTUxMUUxMUUxMUUxMUUxMTExMUUxMTFFMTExRTExRTExRTExMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMTExRTExRTExRTExRTExRWiI6ICI1IiwgIk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFaTUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUVpNTExRTExRTExRTExRTExRTExRTExRTExMTFFMTFFMTFFMTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRWk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFaIjogIjYiLCAiTUxMUUxMUUxMTFFMTFFMTFFMTFFMTFFMTExRTExRTExMUUxMUUxMUUxMTFFMTFFMTFFMTFFMTFFaTUxMTFFMTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExMTExRTExRTExRTExRTExRTExMUUxMTFFMTFFMTFFMTExRWiI6ICI3IiwgIk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFaTUxMUUxMUUxMUUxMUUxMUUxMUUxMUVpNTExMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUVpNTExMUUxMUUxMUUxMUUxMTExMUUxMUUxMUUxMUUxMTExRTExMUUxMUUxMUUxMUUxMUUxMUUxMUUxMTFFMTFFMTFFMTFFMTFFaTUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUVpNTExRTExMUUxMUUxMUUxMUUxMUUxMUVoiOiAiOCIsICJNTExMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUVpNTExMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUVpNTExRTExRTExRTExMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMTFFMTFFMTFFMTFFMTExRWk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFaIjogIjkiLCAiTUxMUUxMUUxMUUxMUUxMUVpNTExRTExRTExRTExRTExRTExRTExRTExMUUxMUUxMUUxMUVpNTExMUUxMUUxMUUxMUUxMUUxMTFFMTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRWk1MTFFMTExRWiI6ICJBIiwgIk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFaTUxMUUxMUUxMUUxMUUxMUUxMUVpNTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRWk1MTFFMTFFMTFFMTFFMTFFMTExRTExRTExRTExRTExRTExRTExRTExRTExRTExMUUxMUUxMUVpNTExRTExRTExRTExRTExMUUxMUUxMUUxMUVpNTExMUUxMTExMUUxMTFFMTFFMTFFMTFFMTFFMTFFaIjogIkIiLCAiTUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUVpNTExRTExRTExRTExMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUVoiOiAiQyIsICJNTExRTExRTExRTExRTExRTExRTExRTExRWk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFaTUxMUUxMUUxMUUxMTFFMTFFMTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRWk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFaIjogIkQiLCAiTUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMTFFMTFFMTFFMTFFMTFFMTExRTExRTExRTExRWk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTExRTExRTExRTExMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFaIjogIkUiLCAiTUxMUUxMUUxMUUxMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTExRTExRTExRWk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTExRTExRTExRTExRTExMUUxMUUxMUUxMUUxMUUxMUVoiOiAiRiIsICJNTExRTExRTExRTExMUUxMUUxMUUxMUUxMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTExRTExRTExRWk1MTFFMTFFMTFFMTFFMTExRTExRTExRTExRTExRTExRTExRTExMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTExRTExRTExRTExRTExRTExRTExRTExRTExMUUxMWiI6ICJHIiwgIk1MTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRWk1MTFFMTFFMTFFMTFFMTFFMTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRWiI6ICJIIiwgIk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFaTUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUVoiOiAibCIsICJNTExMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUVpNTExMTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRWiI6ICJKIiwgIk1MTFFMTFFMTFFMTExRTExRTExRTExRTExRTExRTExMUUxMUUxMUUxMTExMUVpNTExRTExRTExRTExMUUxMUUxMTFFMTFFMTFFMTFFMTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRWiI6ICJLIiwgIk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFaTUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUVoiOiAiTCIsICJNTExRTExMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUVpNTExRTExRTExRTExRTExRTExMUUxMUUxMUUxMUUxMUUxMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTExRTExRTExRTExRTExRWiI6ICJNIiwgIk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMWk1MTFFMTExRTExRTExRTExRTExRTExRTExRTExRTExMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUVoiOiAiTiIsICJNTExRTExRTExRTExRTExRTExRTExRTExRTExRWk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFaTUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUVpNTExRTExRTExRTExRTExRTExRTExRTExRWiI6ICJPIiwgIk1MTFFMTFFMTExRTExRTExRTExRWk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFaTUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMTFFMTFFMTFFMTFFMTFFaTUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMTFFaIjogIlAiLCAiTUxMUUxMUUxMUUxMUUxMUUxMUUxMTFFMTFFMTFFMTExRTExMUUxMUUxMUUxMUUxMUVpNTExRTExMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUVpNTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExMTFFMTFFMTFFMTFFMTFFMTFFMTFFaTUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMTFFMTFFMTExMTFFMTFFMTFFaIjogIlEiLCAiTUxMUUxMUUxMUUxMUUxMUUxMUVpNTExRTExRTExRTExRTExRTExRTExRTExMUUxMUUxMTFFMTFFMTFFaTUxMTExRTExRTExRTExMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMTFFMTFFMTFFaTUxMUUxMTFFMTFFMTFFMTFFMTFFMTFFMTFFaIjogIlIiLCAiTUxMUUxMUUxMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFaTUxMUUxMUUxMUUxMUUxMUUxMUUxMTFFMTExMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMTExMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUVoiOiAiUyIsICJNTExRTExRTExRTExRTExMUUxMUUxMUUxMUUxMUUxMUUxMUVpNTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRWiI6ICJUIiwgIk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTExRTExRTExRTExRWk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFaIjogIlUiLCAiTUxMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFaTUxMUUxMUUxMUUxMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFaIjogIlYiLCAiTUxMUUxMUUxMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTExRTExMUUxMUUxMUUxMUUxMUUxMUUxMTFFaTUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMTFFMTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExMUUxMUUxMUUxMUUxMUUxMUUxMUVoiOiAiVyIsICJNTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRWk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTExMUUxMUUxMUUxMUUxMUUxMUUxMTFFMTFFMTFFMTFFaIjogIlgiLCAiTUxMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFaTUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMTFFMTFFMTFFMTFFMTFoiOiAiWSIsICJNTExRTExRTExRTExRTExRTExRTExRTExRTExMUUxMTFFMTFFMTFFMTExRTExRTExRTExRWk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTExRWiI6ICJaIiwgIk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFaTUxMUUxMTFFMTFFMTFFMTFFMTFFMTExRTExRTExRTExRTExRTExRTExRTExRWk1MTExRTExRTExRTExRTExRTExRTExMUUxMUUxMUUxMUUxMTFFMTFFMTFFMTFFMTFFMTExRTExRWk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFaIjogImEiLCAiTUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUVpNTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRWk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTExRWk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFMTExRWiI6ICJiIiwgIk1MTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExMUUxMUUxMUUxMUUxMUUxMUUxMTFFMTFFMTFFaTUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTExMUUxMUUxMUVoiOiAiYyIsICJNTExRTExRTExRTExRTExRTExRTExRTExRWk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFaTUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMTFFMTFFMTFFMTFFaTUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUVoiOiAiZCIsICJNTExRTExRTExRTExRTExRTExRWk1MTFFMTFFMTFFMTFFMTFFMTFFMTExRTExRTExRTExRTExRTExMUUxMUUxMUUxMUUxMUVpNTExRTExRTExRTExRTExRTExRTExRTExMUUxMUUxMUUxMUUxMTFFMTFFMTFFMTFFMTFFMTFFMTExRWk1MTFFMTFFMTFFMTFFMTFFaTUxMUUxMTExRTExRTExRWiI6ICJlIiwgIk1MTFFMTExRTExRTExRTExMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMTFFMTFFaTUxMUUxMUUxMTFFMTFFMTFFMTFFMTFFMTExRTExRTExMUUxMTExRTExRTExMUUxMUUxMUUxMUUxMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFaIjogImYiLCAiTUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUVpNTExRTExRTExRTExRTExRTExRTExRTExMUUxMUUxMUUxMUUxMUUxMUUxMUUxMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFaTUxMUUxMUUxMUUxMUUxMUUxMTFFMTExRTExRTExRTExMUUxMUUxMUUxMUUxMTExRTExRTExRTExRTExRTExMUUxMTFFMTFFMTExRTExMUVpNTExRTExRTExRTExRTExRTExRTExRTExRWiI6ICJnIiwgIk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFaTUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTExRTExRTExRTExRTExRTExMUUxMUVoiOiAiaCIsICJNTExRTExMUUxMUUxMUUxMUVpNTExRTExRTExRTExRTFpNTExRTExRTExRTExRTExRTExRTExMUUxMUUxMUUxMUVpNTExMTFFMTFFMTFFMTFFMTFFMTFFMTFFaIjogImkiLCAiTUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMTFFMTFFMTFFMTFFMTFFMTFFaTUxMUUxMUUxMWk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFMTExRTExRTExMUUxMUUxMUUxMUUxMUUxMTFFMTExMUUxMUVpNTExMUUxMUUxMUUxMUUxMUUxMUUxMUVoiOiAiaiIsICJNTExRTExRTExRTExRTExRTExRTExRTExRTExRTExMUUxMUUxMUUxMUVpNTExRTExRTExRTExRTExMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUVoiOiAiayIsICJNTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUVpNTExRTExRTExRTExRTExRTExRTExRTExMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMTFFMTFFMTFFMTFFMTFFMTExRTExRTExMUUxMUUxMUUxMUUxMUUxMUUxMTFFMTFFMTFFMTFFMTExRTExRWk1MTExaIjogIm0iLCAiTUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUVpNTExRTExMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUVoiOiAibiIsICJNTExRTExRTExRTExRTExRTExRTExRWk1MTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRWk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTExRTExRTExMUUxMUUxMUUxMUUxMUUxMUUxMTFFMTFFaTUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUVoiOiAibyIsICJNTExRTExRTExRTExRTExRTExRTExRTExRWk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFMTExRTExRTExRTExMUUxMTFFMTFFMTFFMTFFMTFFaTUxMUUxMUUxMUUxMUUxMTExMUUxMTFFMTFFMTExRTExRTExRTExMUUxMUUxMUUxMUUxMUUxaTUxMUUxMUUxMUUxMUUxMTFFMTExRTExMUUxMUVoiOiAicCIsICJNTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRWk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFaTUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMTFFMTFFMTFFaTUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUVoiOiAicSIsICJNTExRTExRTExRTExRTExRTExRTExRTExRTExMUUxMUUxMUUxMUVpNTExRTExRTExRTExRTExRTExRTExMTFFMTFFMTFFMTFFMTFFMTFFMTExRTExRTExRTExRTExaTUxMTFoiOiAiciIsICJNTExMUUxMUUxMUUxMUUxMUUxMUUxMTFFMTFFMTFFMTFFMTFFMTExRTExRTExRTExRTExRTExRTExRTExRTExRWk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTExMTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExMUUxMUUxMTExRTExRTExRTExMUUxMUVoiOiAicyIsICJNTExRTExRTExRTExRTExMUUxMUUxMUUxMTFFMTFFMTFFMTFFMTFFaTUxMUUxMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTExMUUxMUUxMUUxMUUxMUUxMUUxMUUxMTFFMTExRTExRTExRWiI6ICJ0IiwgIk1MTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTExRTExRTExRTExRTExRTExMUUxMUUxMUVpNTExRTExRTExRTExRTExRTExRTExRTExMUUxMUUxMUUxMTExMUUxMUUxMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFaIjogInUiLCAiTUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUVpNTExRTExMUUxMUUxMUUxMUUxMUUxMUUxMTFFMTFFMTFFMTFFMTExRTExMUVoiOiAidiIsICJNTExRTExMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMTFFMTFFMTFFMTFFMTFFMTExRWk1MTFFMTFFMTFFMTFFMTFFMTExRTExRTExRTExRTExMUUxMTFFMTFFMTFFMTExRTExRTExRTExRTExRTExRTExMUUxMUUxMUUxMUUxMWiI6ICJ3IiwgIk1MTFFMTFFMTFFMTExRTExRTExRTExRTExRTExRTExRTExRTExRWk1MTFFMTFFMTFFMTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExMUUxMUUxMUUxMUUxMUUxMTFFaIjogIngiLCAiTUxMUUxMUUxMUUxMUUxMUUxMUUxMUUxMTFFMTFFaTUxMUUxMTFFMTFFMTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExMUUxMUVoiOiAieSIsICJNTExRTExRTExRTExRTExRTExRTExRTExMUUxMUUxMUUxMUUxMUUxMUVpNTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExRTExMUUxMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFMTFFaIjogInoifQ=="
    
    svg_data = resp.json()['captcha']
    soup = BeautifulSoup(svg_data,'html.parser')

    model = json.loads(base64.b64decode(model.encode('ascii')))
    CAPTCHA = {}

    for path in soup.find_all('path',{'fill' : re.compile("#")}):

        ENCODED_STRING = path.get('d').upper()
        INDEX = re.findall('M(\d+)',ENCODED_STRING)[0]

        ENCODED_STRING = re.findall("([A-Z])", ENCODED_STRING)
        ENCODED_STRING = "".join(ENCODED_STRING)

        CAPTCHA[int(INDEX)] =  model.get(ENCODED_STRING)

    CAPTCHA = sorted(CAPTCHA.items())
    CAPTCHA_STRING = ''

    for char in CAPTCHA:
        CAPTCHA_STRING += char[1]
    #print(f'Solved captcha: {CAPTCHA_STRING}, Proceeding.')
    captcha_builder(resp.json(),disp=True)
    #bot.sendImage(img_loc=r"captcha.png",caption=f'CAPTCHA Resolved:{CAPTCHA_STRING}')
    return CAPTCHA_STRING

def generate_captcha(request_header):
    print('================================= GETTING CAPTCHA ==================================================')
    resp = requests.post(CAPTCHA_URL, headers=request_header)
    #print(f'Captcha Response Code: {resp.status_code}')
    
    if resp.status_code == 200:
        #return captcha_builder(resp.json())
        return solve_captcha(resp)


def book_appointment(request_header, details):
    """
    This function
        1. Takes details in json format
        2. Attempts to book an appointment using the details
        3. Returns True or False depending on Token Validity
    """
    try:
        valid_captcha = True
        while valid_captcha:
            captcha = generate_captcha(request_header)
            details['captcha'] = captcha

            print('================================= ATTEMPTING BOOKING ==================================================')
            msg="\n====== ATTEMPTING BOOKING ========\n"
            resp = requests.post(BOOKING_URL, headers=request_header, json=details)
            print(f'Booking Response Code: {resp.status_code}')
            print(f'Booking Response : {resp.text}')
            msg+=f'Booking Response : {resp.text}'
            bot.send_message(msg)
            if resp.status_code == 401:
                print('TOKEN INVALID')
                return False

            elif resp.status_code == 200:
                beep(WARNING_BEEP_DURATION[0], WARNING_BEEP_DURATION[1])
                msg="=====    BOOKED!  =====\n"
                msg+="Hey! It's your lucky day!\n"
                msg+=f"{resp.text}\n"
                msg+="\n\nPlease take a screenshot, share your feedback & experience on instagram, make sure to tag (@ournotesfromtheroads & @shashankbafna).\n"
                msg+="This will help many others & motivates us even more.\n"
                msg+="Also make sure to star mark this effort.\n"
                msg+="https://github.com/shashankbafna/cowin-vaccination-book-slot\n"
                bot.send_message(msg)
                bot.send_message("Booked for "+f"{bot.Name}",chat_id=bot.defaultid)
                print('##############    BOOKED!  ############################    BOOKED!  ##############')
                print("                        Hey, Hey, Hey! It's your lucky day!                       ")
                print('\nPress any key thrice to exit program.')
                os.system("pause")
                os.system("pause")
                os.system("pause")
                sys.exit()

            elif resp.status_code == 400:
                print(f'Response: {resp.status_code} : {resp.text}')
                pass

            else:
                print(f'Response: {resp.status_code} : {resp.text}')
                return True

    except Exception as e:
        print(str(e))
        beep(WARNING_BEEP_DURATION[0], WARNING_BEEP_DURATION[1])


def check_and_book(request_header, beneficiary_dtls, location_dtls, search_option, **kwargs):
    """
    This function
        1. Checks the vaccination calendar for available slots,
        2. Lists all viable options,
        3. Takes user's choice of vaccination center and slot,
        4. Calls function to book appointment, and
        5. Returns True or False depending on Token Validity
    """
    try:
        min_age_booking = get_min_age(beneficiary_dtls)

        minimum_slots = kwargs['min_slots']
        refresh_freq = kwargs['ref_freq']
        auto_book = kwargs['auto_book']
        start_date = kwargs['start_date']
        vaccine_type = kwargs['vaccine_type']
        fee_type = kwargs['fee_type']
        dose = 2 if [beneficiary['status'] for beneficiary in beneficiary_dtls][0] == 'Partially Vaccinated' else 1

        if isinstance(start_date, int) and start_date == 2:
            start_date = (datetime.datetime.today() + datetime.timedelta(days=1)).strftime("%d-%m-%Y")
        elif isinstance(start_date, int) and start_date == 1:
            start_date = datetime.datetime.today().strftime("%d-%m-%Y")
        else:
            pass

        if search_option == 2:
            options = check_calendar_by_district(request_header, vaccine_type, location_dtls, start_date,
                                                 minimum_slots, min_age_booking, fee_type, dose)
        else:
            options = check_calendar_by_pincode(request_header, vaccine_type, location_dtls, start_date,
                                                minimum_slots, min_age_booking, fee_type, dose)

        if isinstance(options, bool):
            return False

        options = sorted(options,
                         key=lambda k: (k['district'].lower(), k['pincode'],
                                        k['name'].lower(),
                                        datetime.datetime.strptime(k['date'], "%d-%m-%Y"))
                         )

        tmp_options = copy.deepcopy(options)
        if len(tmp_options) > 0:
            cleaned_options_for_display = []
            for item in tmp_options:
                item.pop('session_id', None)
                item.pop('center_id', None)
                cleaned_options_for_display.append(item)

            display_table(cleaned_options_for_display)
            if auto_book == 'yes-please':
                print("AUTO-BOOKING IS ENABLED. PROCEEDING WITH FIRST CENTRE, DATE, and RANDOM SLOT.")
                option = options[0]
                random_slot = random.randint(1, len(option['slots']))
                choice = f'1.{random_slot}'
            else:
                replyMsg="----------> Wait 20 seconds for updated options OR \n----------> Enter a choice e.g: 1.4 for (1st center 4th slot): "
                bot.send_message(replyMsg)
                choice = bot.recieveFromBot()
                if choice is None or len(choice) == 0:
                    choice = '.'
                    bot.send_message(msg=f"_No input recieved, setting default as *{choice}*_",parse_mode='markdown')
                #choice = inputimeout(
                   #prompt='----------> Wait 20 seconds for updated options OR \n----------> Enter a choice e.g: 1.4 for (1st center 4th slot): ',
                    #timeout=20)

        else:
            try:
                for i in range(refresh_freq*4, 0, -1):
                    msg = f"No viable options. Next update in {i} seconds. OR press 'Ctrl + C' to refresh now."
                    print(msg, end="\r", flush=True)
                    sys.stdout.flush()
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            choice = '.'

    except TimeoutOccurred:
        time.sleep(1)
        return True

    else:
        if choice == '.':
            return True
        else:
            try:
                choice = choice.split('.')
                choice = [int(item) for item in choice]
                print(f'============> Got Choice: Center #{choice[0]}, Slot #{choice[1]}')

                new_req = {
                    'beneficiaries': [beneficiary['bref_id'] for beneficiary in beneficiary_dtls],
                    'dose': 2 if [beneficiary['status'] for beneficiary in beneficiary_dtls][0] == 'Partially Vaccinated' else 1,
                    'center_id' : options[choice[0] - 1]['center_id'],
                    'session_id': options[choice[0] - 1]['session_id'],
                    'slot'      : options[choice[0] - 1]['slots'][choice[1] - 1]
                }

                print(f'Booking with info: {new_req}')
                bot.send_message(msg=f'Booking with info:\n{new_req}')
                return book_appointment(request_header, new_req)

            except IndexError:
                replyMsg="============> Invalid Option! Exiting"
                bot.send_message(replyMsg)
                print("============> Invalid Option!")
                os.system("pause")
                pass


def get_vaccine_preference():
    
    print("It seems you're trying to find a slot for your first dose. Do you have a vaccine preference?")
    replyMsg="\nIt seems you're trying to find a slot for your first dose. Do you have a vaccine preference?\n"
    replyMsg+="\nEnter 0 for No Preference, 1 for COVISHIELD, 2 for COVAXIN, or 3 for SPUTNIK V. Default 0 :"
    bot.send_message(replyMsg)
    preference = bot.recieveFromBot()
    if preference is None or len(preference) == 0:
        preference = 0
        bot.send_message(msg=f"_No input recieved, setting default as *{preference}*_",parse_mode='markdown')
        #preference = input("Enter 0 for No Preference, 1 for COVISHIELD, 2 for COVAXIN, or 3 for SPUTNIK V. Default 0 : ")
    preference = int(preference) if preference and int(preference) in [0, 1, 2, 3] else 0

    if preference == 1:
        return 'COVISHIELD'
    elif preference == 2:
        return 'COVAXIN'
    elif preference == 3:
        return 'SPUTNIK V'
    else:
        return None


def get_fee_type_preference():
    print("\nDo you have a fee type preference?")
    replyMsg="\nDo you have a fee type preference?\n"
    replyMsg+="\nEnter 0 for No Preference, 1 for Free Only, or 2 for Paid Only. Default 0 : "
    bot.send_message(replyMsg)
    preference = bot.recieveFromBot()
    if preference is None or len(preference) == 0:
        preference = 0
        bot.send_message(msg=f"_No input recieved, setting default as *{preference}*_",parse_mode='markdown')
        #preference = input("Enter 0 for No Preference, 1 for Free Only, or 2 for Paid Only. Default 0 : ")
    preference = int(preference) if preference and int(preference) in [0, 1, 2] else 0

    if preference == 1:
        return ['Free']
    elif preference == 2:
        return ['Paid']
    else:
        return ['Free', 'Paid']


def get_pincodes():
    locations = []
    replyMsg="\nEnter comma separated pincodes to monitor: \n"
    bot.send_message(replyMsg)
    pincodes = bot.recieveFromBot()
    if pincodes is None or len(pincodes) == 0:
        pincodes = input("Enter comma separated pincodes to monitor: ")
    for idx, pincode in enumerate(pincodes.split(',')):
        pincode = {
            'pincode': pincode,
            'alert_freq': 440 + ((2 * idx) * 110)
        }
        locations.append(pincode)
    return locations


def get_districts(request_header):
    """
    This function
        1. Lists all states, prompts to select one,
        2. Lists all districts in that state, prompts to select required ones, and
        3. Returns the list of districts as list(dict)
    """
    states = requests.get('https://cdn-api.co-vin.in/api/v2/admin/location/states', headers=request_header)

    if states.status_code == 200:
        states = states.json()['states']

        refined_states = []
        for state in states:
            tmp = {'state': state['state_name']}
            refined_states.append(tmp)

        replyMsg=display_table(refined_states,True)
        replyMsg+="\nEnter State index: "
        bot.send_message(replyMsg)
        state = int(bot.recieveFromBot())
        if state is None or state <= 0:
            state = int(input('\nEnter State index: '))
        state_id = states[state - 1]['state_id']

        districts = requests.get(f'https://cdn-api.co-vin.in/api/v2/admin/location/districts/{state_id}', headers=request_header)

        if districts.status_code == 200:
            districts = districts.json()['districts']

            refined_districts = []
            for district in districts:
                tmp = {'district': district['district_name']}
                refined_districts.append(tmp)

            replyMsg=display_table(refined_districts,True)
            replyMsg+="\nEnter comma separated index numbers of districts to monitor : "
            bot.send_message(replyMsg)
            reqd_districts = bot.recieveFromBot()
            if reqd_districts is None or len(reqd_districts) == 0:
                reqd_districts = input('\nEnter comma separated index numbers of districts to monitor : ')
            districts_idx = [int(idx) - 1 for idx in reqd_districts.split(',')]
            reqd_districts = [{
                'district_id': item['district_id'],
                'district_name': item['district_name'],
                'alert_freq': 440 + ((2 * idx) * 110)
            } for idx, item in enumerate(districts) if idx in districts_idx]

            print(f'Selected districts: ')
            replyMsg=f'Selected districts: '
            replyMsg+=display_table(reqd_districts,True)
            bot.send_message(replyMsg)
            return reqd_districts

        else:
            replyMsg='Unable to fetch districts'
            replyMsg+=districts.text
            replyMsg+="\n Exiting.."
            bot.send_message(replyMsg)
            print('Unable to fetch districts')
            print(districts.status_code)
            print(districts.text)
            os.system("pause")
            sys.exit(1)

    else:
        replyMsg='Unable to fetch states'
        replyMsg+=states.text
        replyMsg+="\n Exiting.."
        bot.send_message(replyMsg)
        print('Unable to fetch states')
        print(states.status_code)
        print(states.text)
        os.system("pause")
        sys.exit(1)


def get_beneficiaries(request_header):
    """
    This function
        1. Fetches all beneficiaries registered under the mobile number,
        2. Prompts user to select the applicable beneficiaries, and
        3. Returns the list of beneficiaries as list(dict)
    """
    beneficiaries = requests.get(BENEFICIARIES_URL, headers=request_header)

    if beneficiaries.status_code == 200:
        beneficiaries = beneficiaries.json()['beneficiaries']

        refined_beneficiaries = []
        for beneficiary in beneficiaries:
            beneficiary['age'] = datetime.datetime.today().year - int(beneficiary['birth_year'])

            tmp = {
                'bref_id': beneficiary['beneficiary_reference_id'],
                'name': beneficiary['name'],
                'vaccine': beneficiary['vaccine'],
                'age': beneficiary['age'],
                'status': beneficiary['vaccination_status']
            }
            refined_beneficiaries.append(tmp)

        replyMsg=display_table(refined_beneficiaries,True)
        bot.send_message(replyMsg)
        print("""
        ################# IMPORTANT NOTES #################
        # 1. While selecting beneficiaries, make sure that selected beneficiaries are all taking the same dose: either first OR second.
        #    Please do no try to club together booking for first dose for one beneficiary and second dose for another beneficiary.
        #
        # 2. While selecting beneficiaries, also make sure that beneficiaries selected for second dose are all taking the same vaccine: COVISHIELD OR COVAXIN.
        #    Please do no try to club together booking for beneficiary taking COVISHIELD with beneficiary taking COVAXIN.
        #
        # 3. If you're selecting multiple beneficiaries, make sure all are of the same age group (45+ or 18+) as defined by the govt.
        #    Please do not try to club together booking for younger and older beneficiaries.
        ###################################################
        """)
        Msg="\n===== IMP DETAILS =====\n"
        Msg+="==>While selecting beneficiaries, make sure that selected beneficiaries are all taking the same dose: either 1st or 2nd.\n"
        Msg+="==>While selecting beneficiaries, also make sure that beneficiaries selected for second dose are all taking the same vaccine: COVISHIELD OR COVAXIN.\n"
        Msg+="==>If you're selecting multiple beneficiaries, make sure all are of the same age group (45+ or 18+).\n"
        Msg+="\nEnter comma separated index numbers of beneficiaries to book for : "
        print(Msg)
        bot.send_message(Msg)
        reqd_beneficiaries = bot.recieveFromBot()
        if reqd_beneficiaries is None or len(reqd_beneficiaries) == 0:
            reqd_beneficiaries = input('Enter comma separated index numbers of beneficiaries to book for : ')
        beneficiary_idx = [int(idx) - 1 for idx in reqd_beneficiaries.split(',')]
        reqd_beneficiaries = [{
            'bref_id': item['beneficiary_reference_id'],
            'name': item['name'],
            'vaccine': item['vaccine'],
            'age': item['age'],
            'status': item['vaccination_status']
        } for idx, item in enumerate(beneficiaries) if idx in beneficiary_idx]

        print(f'Selected beneficiaries: ')
        replyMsg='Selected beneficiaries: '
        replyMsg+=display_table(reqd_beneficiaries,True)
        bot.send_message(replyMsg)
        return reqd_beneficiaries

    else:
        print('Unable to fetch beneficiaries')
        print(beneficiaries.status_code)
        print(beneficiaries.text)
        replyMsg='Unable to fetch beneficiaries\n'
        replyMsg+=beneficiaries.text
        replyMsg+=" EXITING...."
        bot.send_message(replyMsg)
        os.system("pause")
        return []


def get_min_age(beneficiary_dtls):
    """
    This function returns a min age argument, based on age of all beneficiaries
    :param beneficiary_dtls:
    :return: min_age:int
    """
    age_list = [item['age'] for item in beneficiary_dtls]
    min_age = min(age_list)
    return min_age

def generate_token_OTP(mobile, request_header):
    """
    This function generate OTP and returns a new token
    """

    if not mobile:
        print("Mobile number cannot be empty")
        os.system('pause')
        sys.exit()

    valid_token = False
    i=1
    while not valid_token:
        try:
            data = {"mobile": mobile,
                    "secret": "U2FsdGVkX1+z/4Nr9nta+2DrVJSv7KS6VoQUSQ1ZXYDx/CJUkWxFYG6P3iM/VW+6jLQ9RDQVzp/RcZ8kbT41xw=="
            }
            txnId = requests.post(url=OTP_PRO_URL, json=data, headers=request_header)

            if txnId.status_code == 200:
                print(f"Successfully requested OTP for mobile number {mobile} at {datetime.datetime.today()}..")
                txnId = txnId.json()['txnId']
                replyMsg=f"Enter OTP for {mobile} received in SMS (If this takes more than 2 minutes, press retry):"
                bot.send_message(replyMsg)
                tryOTP = bot.recieveFromBot()
                if tryOTP is None or len(tryOTP) == 0:
                    bot.send_message(msg=f"*BOT SCRIPT*: {i}. _Waiting for you to enter OTP recieved in SMS_",parse_mode='markdown')
                    tryOTP = bot.recieveFromBot()
                    if i > 4:
                        bot.send_message(msg=f"*BOT SCRIPT stopped on computer because no OTP was entered for a long time.*",parse_mode='markdown')
                        bot.send_message(msg=f"*Telegram communication lost.*\nPlease re-run '_python ./Booking.py_' on computer.",parse_mode='markdown')
                        #OTP = input("Enter OTP (If this takes more than 2 minutes, press Enter to retry): ")
                        sys.exit()
                    i+=1
                OTP = tryOTP
                if OTP:
                    data = {"otp": sha256(str(OTP).encode('utf-8')).hexdigest(), "txnId": txnId}
                    print(f"Validating OTP..")

                    token = requests.post(url='https://cdn-api.co-vin.in/api/v2/auth/validateMobileOtp', json=data,
                                          headers=request_header)
                    if token.status_code == 200:
                        token = token.json()['token']
                        bot.send_message("Token Generated, OTP validated.")
                        
                        dictdata={
                                'mobile':mobile,
                                'token':token,
                                'Name':bot.Name,
                                'username': bot.username
                                 }
                        write_to_config(dictdata)

                        i=1
                        valid_token = True
                        return token

                    else:
                        print('Unable to Validate OTP')
                        print(f"Response: {token.text}")
                        bot.send_message(f"Unable to Validate OTP.\nResponse: {token.text}\n")
                        if i < 4:
                            bot.send_message(f"Retry with {mobile} ? (y/n Default y): ")
                            retry = bot.recieveFromBot()
                            if retry is None or len(retry) == 0:
                                retry = 'y'
                                bot.send_message(msg=f"_No input recieved, setting default as *{retry}*_",parse_mode='markdown')
                                i+=1
                                #retry = input(f"Retry with {mobile} ? (y/n Default y): ")
                            retry = retry if retry else 'y'
                            if retry == 'y':
                                pass
                            else:
                                bot.send_message(msg=f"*BOT SCRIPT stopped on computer because invalid OTP was entered again.*",parse_mode='markdown')
                                bot.send_message(msg=f"*Telegram communication lost.*\nPlease re-run '_python ./Booking.py_' on computer.",parse_mode='markdown')
                                sys.exit()
                        else:
                            bot.send_message(msg=f"*BOT SCRIPT stopped on computer because invalid OTP was generated for a long time.*",parse_mode='markdown')
                            bot.send_message(msg=f"*Telegram communication lost.*\nPlease re-run '_python ./Booking.py_' on computer.",parse_mode='markdown')
                            sys.exit()

            else:
                bot.send_message("Unable to Generate OTP.")
                print('Unable to Generate OTP')
                print(txnId.status_code, txnId.text)
                bot.send_message(f"Unable to Generate OTP.\nResponse: {txnId.text}\n\nRetry with {mobile} ? (y/n Default y): ")
                retry = bot.recieveFromBot()
                if retry is None or len(retry) == 0:
                    bot.send_message(f"Retry with {mobile} ? (y/n Default y): ")
                    retry = bot.recieveFromBot()
                    if retry is None or len(retry) == 0:
                        if i < 4:
                            retry = 'y'
                            bot.send_message(msg=f"_No input recieved, setting default as *{retry}*_",parse_mode='markdown')
                            #retry = input(f"Retry with {mobile} ? (y/n Default y): ")
                            i+=1
                        else:
                            bot.send_message(msg=f"*BOT SCRIPT stopped on computer because no valid Mobile number was entered for a long time.*",parse_mode='markdown')
                            bot.send_message(msg=f"*Telegram communication lost.*\nPlease re-run '_python ./Booking.py_' on computer.",parse_mode='markdown')
                            sys.exit()
                retry = retry if retry else 'y'
                if retry == 'y':
                    pass
                else:
                    sys.exit()

        except Exception as e:
            print(str(e))
