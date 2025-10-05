#!/bin/bash
sudo systemctl disable bluetooth
sudo systemctl disable hciuart
sudo systemctl disable triggerhappy
sudo systemctl disable avahi-daemon
sudo systemctl disable wpa_supplicant
sudo systemctl disable rsyslog
sudo systemctl disable logrotate
sudo systemctl disable cron
sudo systemctl disable keyboard-setup
sudo systemctl disable alsa-utils
sudo systemctl disable apt-daily.timer
sudo systemctl disable apt-daily-upgrade.timer

echo "Done disabling unnecessary services."