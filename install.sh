#!/bin/bash


echo -e "\e[97m████████╗ ██████╗ ██╗    ██╗ █████╗ ████████╗ ██████╗██╗  ██╗"
echo -e "\e[97m╚══██╔══╝██╔      ██║    ██║██╔══██╗╚══██╔══╝██╔════╝██║  ██║"
echo -e "\e[97m   ██║   ██║ ██║  ██║ █╗ ██║███████║   ██║   ██║     ███████║"
echo -e "\e[97m   ██║   ██║   ██║██║███╗██║██╔══██║   ██║   ██║     ██╔═ ██║"
echo -e "\e[97m   ██║   ╚██████╔╝╚███╔███╔╝██║  ██║   ██║   ╚██████╗██║  ██║"
echo -e "\e[97m   ╚═╝    ╚═════╝  ╚══╝╚══╝ ╚═╝  ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝"

echo "Downloading dependencies..."
sudo apt update -qq > /dev/null 2>&1
sudo apt install -y git python3 python3-pip -qq > /dev/null 2>&1

echo "Cloning repository..."
git clone https://github.com/yarchefis/tgwatch_server > /dev/null 2>&1

echo "Installing libraries..."
pip3 install "flask[async]" telethon > /dev/null 2>&1

echo "Running the application..."
cd tgwatch_server
python3 app.py
