#!/bin/bash

# Define the virtual environment directory and the main python script
VENV_DIR="venv"
REQUIREMENTS_FILE="requirements.txt"
MAIN_SCRIPT="main.py"
ENV_FILE="bot_app/.env"

# Function to create a virtual environment and install requirements
# create_venv() {
#     echo "Creating virtual environment..."
#     python3 -m venv $VENV_DIR

#     echo "Activating virtual environment..."
#     source $VENV_DIR/bin/activate

#     echo "Installing requirements..."
#     pip install -r $REQUIREMENTS_FILE

#     echo "Virtual environment is ready."
# }

# Function to update the .env file
update_env_file() {
    # Check if the .env file exists; if not, create an empty one
    if [ ! -f $ENV_FILE ]; then
        echo "Creating .env file..."
        touch $ENV_FILE
    fi

    read -p "Enter TOKEN value: " TOKEN_VALUE
    read -p "Enter CHANNEL_ID value: " CHANNEL_ID_VALUE

    echo "Updating .env file..."
    echo "TOKEN='$TOKEN_VALUE'" > $ENV_FILE
    echo "CHANNEL_ID='$CHANNEL_ID_VALUE'" >> $ENV_FILE
    echo ".env file has been updated."
}

build_exe() {
    pyinstaller --distpath output/ -D -n parser_bot --contents-directory . main.py

    echo "Copying selenium-stealth files..."
    cp -r venv/Lib/site-packages/selenium_stealth output/parser_bot/selenium_stealth

    echo "Build completed."
}

# Check if an argument is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <command>"
    echo "Commands:"
    echo "  install - Create virtual environment and install dependencies"
    echo "  run     - Run the main script"
    echo "  set-env - Set TOKEN and CHANNEL_ID in the .env file"
    exit 1
fi

# Process the command-line argument
case "$1" in
    run)       
        # Run the main script
        echo "Running $MAIN_SCRIPT..."
        python $MAIN_SCRIPT
        ;;
    set-env)
        update_env_file
        ;;
    build_exe)
        build_exe
        ;;
    *)
        echo "Invalid command: $1"
        echo "Usage: $0 <command>"
        echo "Commands:"
        echo "  run     - Run the main script"
        echo "  set-env - Set TOKEN and CHANNEL_ID in the .env file"
        echo "  build_exe - build .exe package"
        exit 1
        ;;
esac
