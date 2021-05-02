#!/usr/bin/python3
import re
import os
import argparse
import sys

CONFIG_FILE = "/etc/modprobe.d/tuxedo_keyboard.conf"
BRIGHTNESS_FILE = "/sys/devices/platform/tuxedo_keyboard/uw_kbd_bl_color/brightness"
COLOR_STRING_FILE = "/sys/devices/platform/tuxedo_keyboard/uw_kbd_bl_color/color_string"
SUPPORTED_COLORS = ["BLACK", "RED", "GREEN", "BLUE", "YELLOW", "MAGENTA", "CYAN", "WHITE"]

def getCurrentBrightness():
    with open(BRIGHTNESS_FILE, "r") as f:
        return f.read().strip()

def getCurrentColor():
    # Using regex to get the current color
    with open(CONFIG_FILE) as f:
        return re.search('color=([^\s]+)', f.read()).group(1).strip()

def setParameter(color=None, brightness=None):
    if color is None:
        color = getCurrentColor()
    else:
        # Change current color by writing to sys. Does not survive a reboot  
        with open(COLOR_STRING_FILE, "w") as f:
            f.write(color.upper())

    if brightness is None:
        brightness = getCurrentBrightness()
    else:
        # Change current brightness by writing to sys. Does not survive a reboot
        with open(BRIGHTNESS_FILE, "w") as f:
            f.write(brightness)

    with open(CONFIG_FILE, "w") as f:
        # Write current options to config file, to survive reboot 
        f.write("options tuxedo_keyboard brightness=%s color=%s\n" % (brightness, color.upper()))


def configIsValid():
    # check if config file is valid to use with Polaris or XMG Core
    missing_parameter = False
    file_created = False

    if not os.path.exists(CONFIG_FILE):
        os.mknod(CONFIG_FILE)
        file_created = True

    with open(CONFIG_FILE) as f:
        color = re.search('color=([^\s]+)', f.read())
        if not color:
            # Color parameter not present, setting a default color
            set_color = "WHITE"
            missing_parameter = True
        else:
            set_color = color.group(1)
        
    with open(CONFIG_FILE) as f:
        brightness = re.search('brightness=([^\s]+)', f.read())
        if not brightness:
            # Brightness parameter not present, setting a default brightness
            set_brightness = "60"
            missing_parameter = True
        else:
            set_brightness = brightness.group(1)

    if missing_parameter:
        # A config file was already, rename original file
        if not file_created:
            os.rename(CONFIG_FILE, CONFIG_FILE + ".old")

        # Create new config parameters
        with open(CONFIG_FILE, "w") as f:
            f.write("options tuxedo_keyboard brightness=%s color=%s\n" % (set_brightness, set_color))
        return False
    return True

skip_check = False

parser = argparse.ArgumentParser(description='Set color for Tuxedo Polaris and XMG Core E21 (XMG Core needs a customized version of tuxedo-keyboard with added DMI_BOARD_NAME of the used XMG Core)')
parser.add_argument('--set_color', help="Supported Colors: BLACK, RED, GREEN, BLUE, YELLOW, MAGENTA, CYAN, WHITE")
parser.add_argument('--set_brightness', help="Any integer between 0-200.")
parser.add_argument('--get_color', action="store_true", help="Returns current color.")
parser.add_argument('--get_brightness', action="store_true", help="Returns current brightness.")
parser.add_argument('--skip_config_check', action="store_true", help="Skip config file check.")
args = parser.parse_args()

if args.skip_config_check:
    skip_check = True

if not skip_check:
    if not configIsValid():
        print("Missing config file or missing parameter")
        print('New config file "%s" created' % CONFIG_FILE)


if args.set_color:
    if os.getuid() != 0:
        print("set_color needs root permission. Change to root or use sudo.")
        sys.exit()

    if args.set_color.upper() in SUPPORTED_COLORS: 
        setParameter(color=args.set_color)
    else:
        print('Color "%s" is not supported.' % args.set_color)
        print("Supported Colors: BLACK, RED, GREEN, BLUE, YELLOW, MAGENTA, CYAN, WHITE")
        sys.exit()

if args.set_brightness:
    if os.getuid() != 0:
        print("set_brightness needs root permission. Change to root or use sudo.")
        sys.exit()
    try:
        brightness = int(args.set_brightness)
    except ValueError:
        print('Can not set brightness. "%s" is not an integer.' % args.set_brightness)
        sys.exit()
    if brightness in range(0, 201):
        setParameter(brightness=args.set_brightness)
    else:
        print("Brightness need to be between 0-200")
        sys.exit()

if args.get_color:
    print(getCurrentColor())

if args.get_brightness:
    print(getCurrentBrightness())

if len(sys.argv) == 1:
    parser.print_help()
