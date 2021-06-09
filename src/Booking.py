#!/usr/bin/env python3

import copy
from types import SimpleNamespace
import requests, sys, argparse, os, datetime
from utils import generate_token_OTP, check_and_book, beep, BENEFICIARIES_URL, WARNING_BEEP_DURATION, \
    display_info_dict, save_user_info, collect_user_details, get_saved_user_info, confirm_and_proceed, bot, write_to_config, read_runtime_config, \
        swapDate

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', help='Pass token directly')
    parser.add_argument('--mobile', help='Pass mobile directly')
    args = parser.parse_args()

    filename = 'vaccine-booking-details.json'
    mobile = None

    print('Begin: Booking.py')
    beep(500, 550)

    try:
        base_request_header = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
            'origin': 'https://selfregistration.cowin.gov.in/',
            'referer': 'https://selfregistration.cowin.gov.in/'
        }

        if args.token:
            token = args.token
        else:
            mobile = ''
            if args.mobile:
                mobile = args.mobile
            else:
                mobile = read_runtime_config('mobile')
                if mobile is None or len(mobile) == 0:
                    replyMsg="Enter the mobile number registered to access COWIN Portal: "
                    mobile = bot.recieveFromBot(msg=replyMsg)
                    if mobile is None or len(mobile) == 0:
                        #mobile = '7875604546'
                        mobile = input("Enter the registered mobile number: ")
            
            token = generate_token_OTP(mobile, base_request_header)
            
        request_header = copy.deepcopy(base_request_header)
        request_header["Authorization"] = f"Bearer {token}"

        if os.path.exists(filename):
            print("\n=================================== Note ===================================\n")
            print(f"Info from perhaps a previous run already exists in {filename} in this directory.")
            print(f"IMPORTANT: If this is your first time running this version of the application, DO NOT USE THE FILE!")
            replyMsg="\n===== Note =====\n"
            replyMsg+=f"Info from perhaps a previous run already exists.\n"
            #replyMsg+=f"IMPORTANT: If this is your first time running this version of the application, DO NOT USE THE FILE!\n"
            #replyMsg+="Would you like to see the details and confirm to proceed? (y/n Default y): "
            bot.send_message(replyMsg)
            #try_file = bot.recieveFromBot(msg=replyMsg,isDefault=True)
            try_file = 'y'
            if try_file is None or len(try_file) == 0:
                try_file = input("Would you like to see the details and confirm to proceed? (y/n Default y): ")
            try_file = try_file if try_file else 'y'

            if try_file == 'y':
                collected_details = get_saved_user_info(filename)
                print("\n================================= Info =================================\n")
                replyMsg="\n======= Info =======\n"
                replyMsg+=display_info_dict(collected_details,True)
                replyMsg+="\nProceed with above info? (y/n Default n): "
                bot.send_message("Info for "+f"{bot.Name}"+"\n\n"+replyMsg,chat_id=bot.defaultid)
                file_acceptable = bot.recieveFromBot(msg=replyMsg,isDefault=True)
                if file_acceptable is None or len(file_acceptable) == 0:
                    file_acceptable = 'n'
                    bot.send_message(msg=f"_No input recieved, setting default as *{file_acceptable}*_",parse_mode='markdown')
                    #file_acceptable = input("\nProceed with above info? (y/n Default n): ")
                file_acceptable = file_acceptable if file_acceptable else 'n'

                if file_acceptable != 'y':
                    collected_details = collect_user_details(request_header)
                    save_user_info(filename, collected_details)

            else:
                collected_details = collect_user_details(request_header)
                save_user_info(filename, collected_details)

        else:
            collected_details = collect_user_details(request_header)
            save_user_info(filename, collected_details)
            confirm_and_proceed(collected_details)
        replyMsg="Starting auto slot booking app with above details."
        bot.send_message(replyMsg)
        
        info = SimpleNamespace(**collected_details)
        
        token_valid = True
        i=1
        while token_valid:
            request_header = copy.deepcopy(base_request_header)
            request_header["Authorization"] = f"Bearer {token}"
            info.start_date=swapDate(info.start_date)
            # call function to check and book slots
            token_valid = check_and_book(request_header, info.beneficiary_dtls, info.location_dtls, info.search_option,
                                         min_slots=info.minimum_slots,
                                         ref_freq=info.refresh_freq,
                                         auto_book=info.auto_book,
                                         start_date=info.start_date,
                                         vaccine_type=info.vaccine_type,
                                         fee_type=info.fee_type,
                                         attemptCount=i)
            
            tempValidity=token_valid
            #check number of attempts made
            if token_valid:
                #print(f"{i}#Attempt: ")
                i+=1
                
            # check if token is still valid
            beneficiaries_list = requests.get(BENEFICIARIES_URL, headers=request_header)
            if beneficiaries_list.status_code == 200:
                token_valid = True

            if (i > 20 and not tempValidity and token_valid) or not token_valid:
                # if token invalid, regenerate OTP and new token
                beep(WARNING_BEEP_DURATION[0], WARNING_BEEP_DURATION[1])
                print('Token is INVALID.')
                token_valid = False
                beep(WARNING_BEEP_DURATION[0], WARNING_BEEP_DURATION[1])
                
                print("Try for a new Token? (y/n Default y)")
                replyMsg="Try for a new Token? (y/n Default y):"
                tryOTP = bot.recieveFromBot(msg=replyMsg,isDefault=True)
                #print("Recieved from telegram: "+str(tryOTP))
                if tryOTP is None or len(tryOTP) == 0:
                    tryOTP = 'y'
                    bot.send_message(msg=f"_No input recieved, setting default as *{tryOTP}*_",parse_mode='markdown')
                    #tryOTP = input('Try for a new Token? (y/n Default y): ')
                if tryOTP.lower() == 'y':
                    if mobile is None or len(mobile) == 0:
                        beep(WARNING_BEEP_DURATION[0], WARNING_BEEP_DURATION[1])
                        mobile = read_runtime_config('mobile')
                        replyMsg=f"Do you want to continue with mobile number: {mobile} (y/n) default y"
                        confirm=bot.recieveFromBot(msg=replyMsg,isDefault=True)
                        if confirm != 'y' or confirm !='Y':
                            replyMsg="Enter the mobile number registered to access COWIN Portal: "
                            mobile = bot.recieveFromBot(msg=replyMsg)
                        if mobile is None or len(mobile) == 0:
                            #mobile = '7875604546'
                            #mobile = input("Enter the registered mobile number: ")
                            bot.send_message(msg=f"*BOT SCRIPT stopped on computer because Mobile number was invalid.*",parse_mode='markdown')
                            bot.send_message(msg=f"*Telegram communication lost.*\nPlease re-run '_python ./Booking.py_' on computer.",parse_mode='markdown')
                    token = generate_token_OTP(mobile, base_request_header)
                    token_valid = True
                    replyMsg="Resuming to find slots.."
                    bot.send_message(replyMsg)
                    i=1
                else:
                    bot.send_message("Denied generation of new Token, Stopping Script..")
                    bot.send_message(msg=f"*Telegram communication ended from your computer.*\nPlease re-run '_python ./Booking.py_' on computer to re-establish.",parse_mode='markdown')
                    print("Exiting")
                    os.system("pause")

    except Exception as e:
        print(str(e))
        print('Exiting Script')
        bot.send_message(f"{str(e)}\nExiting Script..")
        os.system("pause")


if __name__ == '__main__':
    main()

