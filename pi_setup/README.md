## 🍓 Setting Up the Raspberry Pi 4B

1. Use the [Raspberry PI Imager](https://www.raspberrypi.com/documentation/computers/getting-started.html#raspberry-pi-imager) to format the micro SD card and install the Raspberry Pi OS Lite (64-bit) operating system.

- Choose to "Edit Settings" to enter OS customizations
   - Under the "General" tab set the "hostname" to "rpi-spatial-ai", the "Username" to "frc4607" and "password" to "frc4607"
   - Under the "Services" table enable SSH and "Use password authentication"

2. Disable service by running the "disable_services.bash" script on the Raspberry Pi.
