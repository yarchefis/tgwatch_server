#!/bin/bash


echo -e "\e[97m████████╗ ██████╗ ██╗    ██╗ █████╗ ████████╗ ██████╗██╗  ██╗"
echo -e "\e[97m╚══██╔══╝██╔      ██║    ██║██╔══██╗╚══██╔══╝██╔════╝██║  ██║"
echo -e "\e[97m   ██║   ██║ ██║  ██║ █╗ ██║███████║   ██║   ██║     ███████║"
echo -e "\e[97m   ██║   ██║   ██║██║███╗██║██╔══██║   ██║   ██║     ██╔═ ██║"
echo -e "\e[97m   ██║   ╚██████╔╝╚███╔███╔╝██║  ██║   ██║   ╚██████╗██║  ██║"
echo -e "\e[97m   ╚═╝    ╚═════╝  ╚══╝╚══╝ ╚═╝  ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝"

# Prompt the user for api_id and api_hash
echo "Please enter your api_id:"
read api_id
echo "Please enter your api_hash:"
read api_hash

# Downloading dependencies
echo "Downloading dependencies..."
sudo apt update -qq > /dev/null 2>&1
sudo apt install -y git python3 python3-pip -qq > /dev/null 2>&1

# Cloning repository
echo "Cloning repository..."
git clone https://github.com/yarchefis/tgwatch_server > /dev/null 2>&1

# Installing libraries
echo "Installing libraries..."
pip3 install "flask[async]" telethon > /dev/null 2>&1

# Navigate to the repository
cd tgwatch_server

# Check if config.ini exists and create it if not
if [ ! -f config.ini ]; then
  echo "Creating configuration file..."
  cat <<EOL > config.ini
[settings]
api_id = 
api_hash = 
chats_per_page = 10
max_msg = 10
key = sas

[watch]
isactivate = 0
lastactivatecode = null
EOL
else
  echo "Configuration file already exists. Updating it..."
fi

# Update config.ini with api_id and api_hash
echo "Updating configuration file..."
sed -i "s/^api_id =.*/api_id = $api_id/" config.ini
sed -i "s/^api_hash =.*/api_hash = $api_hash/" config.ini

# Running the application
echo "Running the application..."
python3 app.py
