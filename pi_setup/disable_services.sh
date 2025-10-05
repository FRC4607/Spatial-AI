#!/bin/bash
systemctl disable bluetooth.service 2>/dev/null || true
systemctl disable hciuart.service 2>/dev/null || true
systemctl disable triggerhappy.service 2>/dev/null || true
systemctl disable avahi-daemon.service 2>/dev/null || true
systemctl disable avahi-daemon.socket 2>/dev/null || true
systemctl disable wpa_supplicant.service 2>/dev/null || true
systemctl disable rsyslog.service 2>/dev/null || true
systemctl disable logrotate.service 2>/dev/null || true
systemctl disable logrotate.timer 2>/dev/null || true
systemctl disable cron.service 2>/dev/null || true
systemctl disable keyboard-setup.service 2>/dev/null || true
systemctl disable alsa-utils.service 2>/dev/null || true
systemctl disable apt-daily.timer 2>/dev/null || true
systemctl disable apt-daily-upgrade.timer 2>/dev/null || true

echo "Done disabling unnecessary services."