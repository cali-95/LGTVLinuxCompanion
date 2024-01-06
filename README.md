# LG TV Linux Companion

## Description

Minimal replica of https://github.com/JPersson77/LGTVCompanion in python to run on linux

## Features

- multi plattform including linux
- can e.g. turn on/off the screnn, turn off the system
- can check if the HDMI input is used and only than turn the screen off
- sends only the screen off command if the screen if on and the other way around
- easy expandable

## Usage

### Manually

- create a dir, which normal users can read and write, I will use ~/lg-companion: `mkdir ~/lg-companion`
- `cd ~/lg-companion`
- `git clone https://github.com/cali-95/LGTVLinuxCompanion.git`
- `python -m venv my_venv`
- `source my_venv/bin/activate`
- `pip install -r requirements.txt`
- run `python lg_tv_linux_companion.py -c turnOffScreen -k wrong_key -t <ip>` with your ip and conform the popup on your tv.
- take note of the client key in the log file ~/lg-companion/log.txt
- run the same commend with the right client-key, your lg tv should go black, active it again by pressing some button on the remote
- find other options with `python lg_tv_linux_companion.py -h`

### Automatic (use triggers)

thanks @fulalas for the suggestion

perform the steps unter manually and then the following ones

- install acpid and enable it `sudo systemctl enable acpid`
- create a file called client-key with your client key: `echo -n "to_be_replaced" > client_key`
- `echo -n "to_be_replaced" > ip`
- `sed -e "s#the_user#$(whoami)#g" -e "s#the_dir#$(pwd)#g" monitor_on.dist > monitor_on`
- `sed -e "s#the_user#$(whoami)#g" -e "s#the_dir#$(pwd)#g" monitor_off.dist > monitor_off`
- `chmod +x monitor_on && chmod +x monitor_off`
- `sudo mv monitor_{on,off} /etc/acpi/events/`
- `chmod +x run_in_venv.sh`
- reboot
- enjoy

## Troubleshooting

### the trigger is not triggered
run `acpi_listen` to find the right acpi event and change it in the monitor_(on|off) files

### change to the monitor_(on|off) files are not activ
a reboot is required

## Disclaimer

use the software at your own risk