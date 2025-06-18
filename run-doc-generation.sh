#!/bin/bash

# === generate-docs.sh ===
# Make this file executable: chmod +x run-doc-generation.sh
# Run it with: ./run-doc-generation.sh
# Or run both commands: chmod +x run-doc-generation.sh && ./run-doc-generation.sh

# -----------------------------------------------------------------------------
# Purpose: Generate HTML documentation with pdoc and open it automatically
# Compatible: Git Bash on Windows, pdoc ≥ 15
# -----------------------------------------------------------------------------

# Move to the root of the project (where this script is)
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

# Activate the virtual environment (Windows-specific path)
. .venv/Scripts/activate

# === Install pdoc if not installed ===
print_blue "Checking if pdoc is installed..."
if ! pip show pdoc > /dev/null 2>&1; then
    print_blue "'pdoc' is not installed. Attempting to install it..."
    pip install pdoc || print_error "Failed to install 'pdoc'"
    print_green "'pdoc' installed successfully."
fi

# === Move to script directory ===
cd "$(dirname "$0")" || print_error "Failed to navigate to script directory."

# === Configuration ===
OUTPUT_DIR="docs-pdoc"
TARGET_MODULE="src/leaders_scraper.py"

# === Ensure PYTHONPATH includes current project root ===
export PYTHONPATH=.

# === Remove previous output if any ===
print_blue "Cleaning previous documentation..."
rm -rf "$OUTPUT_DIR"

# === Generate documentation ===
for TARGET_MODULE in src/exporter.py src/immovlan_details_scraper.py src/immovlan_url_scraper.py src/main.py
do
    print_blue "Generating documentation for: $TARGET_MODULE"
    pdoc "$TARGET_MODULE" --output-dir "$OUTPUT_DIR" || print_error "Documentation generation failed for $TARGET_MODULE."
done


# === Open all generated HTML docs ===
HTML_FILES=$(find "$OUTPUT_DIR/challenge-collecting-data/src" -maxdepth 1 -type f -name "*.html")

if [ -z "$HTML_FILES" ]; then
    print_error "No documentation files found."
else
    print_green "Documentation successfully generated!"
    print_blue "Opening all documentation files in default web browser..."

    for FILE in $HTML_FILES; do
        WINDOWS_PATH=$(cygpath -w "$FILE")
        echo "Opening: $WINDOWS_PATH"
        powershell.exe -Command "Start-Process '$WINDOWS_PATH'" || print_error "Failed to open $WINDOWS_PATH"
    done
fi