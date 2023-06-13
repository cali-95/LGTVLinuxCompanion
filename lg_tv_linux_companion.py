#!/usr/bin/env python

__author__ = "cali-95"

"""
tested on python 3.11 on linux and with a LG OLED42C21

run python lg_tv_linux_companion.py --help to show all options

to get a client_key run the script with an invaild client_key like 1337 and look at the log file

based on https://github.com/JPersson77/LGTVCompanion
"""

import logging
import os
import argparse

import asyncio
from websockets.sync.client import connect

import ssl

import json

LEVEL = logging.INFO
FORMAT = '%(asctime)s %(message)s'


LG_HANDSHAKE_PAIRED = """{"type":"register","id":"register_42","payload":{"forcePairing":false,"pairingType":"PROMPT","client-key":"<client_key>","manifest":{"manifestVersion":1,"appVersion":"1.1","signed":{"created":"20140509","appId":"com.lge.test","vendorId":"com.lge","localizedAppNames":{"":"LG Remote App","ko-KR":"리모컨 앱","zxx-XX":"ЛГ Rэмotэ AПП"},"localizedVendorNames":{"":"LG Electronics"},"permissions":["TEST_SECURE","CONTROL_INPUT_TEXT","CONTROL_MOUSE_AND_KEYBOARD","READ_INSTALLED_APPS","READ_LGE_SDX","READ_NOTIFICATIONS","SEARCH","WRITE_SETTINGS","WRITE_NOTIFICATION_ALERT","CONTROL_POWER","READ_CURRENT_CHANNEL","READ_RUNNING_APPS","READ_UPDATE_INFO","UPDATE_FROM_REMOTE_APP","READ_LGE_TV_INPUT_EVENTS","READ_TV_CURRENT_TIME"],"serial":"2f930e2d2cfe083771f68e4fe7bb07"},"permissions":["LAUNCH","LAUNCH_WEBAPP","APP_TO_APP","CLOSE","TEST_OPEN","TEST_PROTECTED","CONTROL_AUDIO","CONTROL_DISPLAY","CONTROL_INPUT_JOYSTICK","CONTROL_INPUT_MEDIA_RECORDING","CONTROL_INPUT_MEDIA_PLAYBACK","CONTROL_INPUT_TV","CONTROL_POWER","CONTROL_TV_SCREEN","READ_APP_STATUS","READ_CURRENT_CHANNEL","READ_INPUT_DEVICE_LIST","READ_NETWORK_STATE","READ_RUNNING_APPS","READ_TV_CHANNEL_LIST","WRITE_NOTIFICATION_TOAST","READ_POWER_STATE","READ_COUNTRY_INFO","READ_SETTINGS"],"signatures":[{"signatureVersion":1,"signature":"eyJhbGdvcml0aG0iOiJSU0EtU0hBMjU2Iiwia2V5SWQiOiJ0ZXN0LXNpZ25pbmctY2VydCIsInNpZ25hdHVyZVZlcnNpb24iOjF9.hrVRgjCwXVvE2OOSpDZ58hR+59aFNwYDyjQgKk3auukd7pcegmE2CzPCa0bJ0ZsRAcKkCTJrWo5iDzNhMBWRyaMOv5zWSrthlf7G128qvIlpMT0YNY+n/FaOHE73uLrS/g7swl3/qH/BGFG2Hu4RlL48eb3lLKqTt2xKHdCs6Cd4RMfJPYnzgvI4BNrFUKsjkcu+WD4OO2A27Pq1n50cMchmcaXadJhGrOqH5YmHdOCj5NSHzJYrsW0HPlpuAx/ECMeIZYDh6RMqaFM2DXzdKX9NmmyqzJ3o/0lkk/N97gfVRLW5hA29yeAwaCViZNCP8iC9aO0q9fQojoa7NQnAtw=="}]}}}"""

WEBSOCKET_SSL_PORT = 3001
WEBSOCKET_NON_SSL_PORT = 3000

ws_connection = None

TURN_ON_SCREEN = "turnOnScreen"
TURN_OFF_SCREEN = "turnOffScreen"
GET_POWER_STATE = "getPowerState"

command_mapping = {
    TURN_ON_SCREEN: "com.webos.service.tvpower/power/turnOnScreen",
    TURN_OFF_SCREEN: "com.webos.service.tvpower/power/turnOffScreen",
    "turnOnSystem": "system/turnOff",
    "turnOffSystem": "system/turnOn",
    GET_POWER_STATE: "com.webos.service.tvpower/power/getPowerState"
}

def send_lg_uri(lg_uri):
    cmd_object = {}
    cmd_object["id"] = 42
    cmd_object["type"] = "request"
    cmd_object["uri"] = f"ssap://{lg_uri}"
    to_send = json.dumps(cmd_object)
    return send_string(to_send)

def send_string(to_send):
    ws_connection.send(to_send)

    msg = ws_connection.recv()
    return msg

def init(args):

    working_dir = args.working_dir
    client_key = args.client_key
    target_ip = args.target_ip
    ssl_use = args.ssl_use
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)

    log_file_path = os.path.join(working_dir, "log.txt")

    logging.basicConfig(filename=log_file_path, level=LEVEL, format=FORMAT)

    logging.debug(f"using {working_dir} as the working dir")

    global ws_connection

    ssl_context = None
    connection_string = None
    if ssl_use:        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        connection_string = f"wss://{target_ip}:{WEBSOCKET_SSL_PORT}"

    else:
        ssl_context = None
        connection_string = f"ws://{target_ip}:{WEBSOCKET_NON_SSL_PORT}"
  
    try:
        ws_connection = connect(connection_string, ssl_context=ssl_context)
    except Exception:
        clean_up()
        logging.error("websocket connection failed, check ip and try the other ssl setting")
        raise

    handshake = LG_HANDSHAKE_PAIRED.replace("<client_key>", client_key)
    
    msg = send_string(handshake)
    
    res = json.loads(msg)
    if res["type"] != "registered":
        logging.info("after user approval, the next line should contain the valid client key")
        second_response = ws_connection.recv()
        logging.info(second_response)
        clean_up_and_raise_exception("invalid client_key")

    logging.info("init finished")


def parse_arguments():
    parser = argparse.ArgumentParser(
                    prog='LG TV Linux Companion',
                    description='Script to control a LG OLED TV')

    parser.add_argument("-t", "--target_ip", required=True)
    parser.add_argument("-c", "--command", required=True, choices=list(command_mapping.keys()))
    parser.add_argument("-w", "--working_dir", default=os.path.join(os.path.expanduser('~'), "lg_tv_linux_companion"), help="default is '~/lg_tv_linux_companion'")
    parser.add_argument("-k", "--client_key", required=True)
    parser.add_argument("-s", "--ssl_use", default=True, action=argparse.BooleanOptionalAction)
    
    args = parser.parse_args()
    return args

def is_display_on(lg_uri):
    msg = send_lg_uri(lg_uri)
    msg_object = json.loads(msg)
    logging.debug(msg_object)
    return msg_object["type"] == "response" and msg_object["payload"]["state"] == "Active"

def run_display_off(lg_uri_action, lg_uri_state):
    change_display_state(lg_uri_action, lg_uri_state, True, False)
    
    
def run_display_on(lg_uri_action, lg_uri_state):
    change_display_state(lg_uri_action, lg_uri_state, False, True)
    
    
def change_display_state(lg_uri_action, lg_uri_state, wanted_first_state, wanted_second_state):

    isOn = is_display_on(lg_uri_state)
    
    if isOn == wanted_first_state:
        send_lg_uri(lg_uri_action)
    else:
        clean_up_and_raise_exception("wrong first state")

    isOn = is_display_on(lg_uri_state)
    if isOn == wanted_second_state:
        logging.debug(f"display state change '{lg_uri_action}' was successful")
    else:
        clean_up_and_raise_exception("display state change was not successful")

def run_command(args):
    command = args.command
    logging.info(f"run '{command}' command")


    lg_uri = command_mapping[command]
    if command == TURN_OFF_SCREEN:
        run_display_off(lg_uri, command_mapping[GET_POWER_STATE])

    elif command == TURN_ON_SCREEN:
        run_display_on(lg_uri, command_mapping[GET_POWER_STATE])

    elif lg_uri:
        send_lg_uri(lg_uri)
    else:
        clean_up_and_raise_exception("unknown command")


def clean_up():
    if ws_connection:
        ws_connection.close()
    logging.info("cleanup finished")

def clean_up_and_raise_exception(exception_message):
    clean_up()
    raise Exception(exception_message)

def main():
    args = parse_arguments()
    init(args)
    run_command(args)
    clean_up()


if __name__ == "__main__":
    main()
