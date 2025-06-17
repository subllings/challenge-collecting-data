#!/bin/bash

# Make this file executable: chmod +x merge_temporary_csvs.sh
# Run it with: ./merge_temporary_csvs.sh
# chmod +x merge_temporary_csvs.sh && ./merge_temporary_csvs.sh

clear

# === Define color codes ===
BLUE_BG="\033[44m"
GREEN_BG="\033[42m"
RED_BG="\033[41m"
WHITE_TEXT="\033[97m"
BLACK_TEXT="\033[30m"
RESET="\033[0m"

# === Define print helpers ===
print_blue() {
    echo ""
    echo -e "${BLUE_BG}${WHITE_TEXT}>>> $1${RESET}"
    echo ""
}

print_green() {
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

# === Launch the Python merge script ===
print_blue "Merging all partial CSV files into one final dataset..."

python src/utils/merge_temporary_csvs.py || print_error "Execution failed."

if [ $? -eq 0 ]; then
    print_green "CSV merge complete! File saved at: output/merged_unique_urls.csv"
else
    print_error "CSV merge failed. Please check the Python script for issues."
fi
