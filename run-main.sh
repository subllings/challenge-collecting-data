#!/bin/bash

# === run-main.sh ===
# Make this file executable: chmod +x run-main.sh
# Run it with: ./run-main.sh
# Both commands: chmod +x run-main.sh &&  ./run-main.sh 

clear

# === Define color codes ===
BLUE_BG="\033[44m"
GREEN_BG="\033[42m"
RED_BG="\033[41m"
WHITE_TEXT="\033[97m"
RESET="\033[0m"

# === Print helpers ===
print_info() {
    echo ""
    echo -e "${BLUE_BG}${WHITE_TEXT}>>> $1${RESET}"
    echo ""
}

print_success() {
    echo ""
    echo -e "${GREEN_BG}${WHITE_TEXT}>>> $1${RESET}"
    echo ""
}

print_error() {
    echo ""
    echo -e "${RED_BG}${WHITE_TEXT}>>> ERROR: $1${RESET}"
    echo ""
    exit 1
}

# === Clear screen ===
clear

# === Activate virtual environment ===
if [ -d ".venv" ]; then
    print_info "Activating virtual environment..."
    source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate 2>/dev/null || print_error "Failed to activate virtual environment."
else
    print_error "Virtual environment (.venv) not found."
fi

# === Launch the main script ===
print_info "Launching scraper..."
PYTHONPATH=src python -m src.main || print_error "Execution failed."


print_success "Program executed successfully."
