#!/bin/bash

# Exit on error and print each command
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required tools
for cmd in python3 pip3 twine; do
    if ! command_exists "$cmd"; then
        echo "Error: $cmd is not installed"
        exit 1
    fi
done

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "Error: pyproject.toml not found in the current directory"
    exit 1
fi

# Extract package name and version from pyproject.toml
PACKAGE_NAME=$(grep '^name = ' pyproject.toml | cut -d'"' -f2)
VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)

# Clean up previous builds
echo -e "${YELLOW}Cleaning up previous builds...${NC}"
rm -rf build/ dist/ *.egg-info/

# Install/upgrade build tools
echo -e "${YELLOW}Installing/upgrading build tools...${NC}"
pip3 install --upgrade pip setuptools wheel twine

# Build the package
echo -e "${YELLOW}Building package...${NC}"
python3 -m build

# Check the built package
echo -e "${YELLOW}Checking built package...${NC}"
twine check dist/*

# Ask for confirmation before uploading
echo -e "${YELLOW}Package ${PACKAGE_NAME} version ${VERSION} is ready for upload.${NC}"
read -p "Do you want to upload to PyPI? [y/N] " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Upload to PyPI
    echo -e "${YELLOW}Uploading to PyPI...${NC}"
    twine upload dist/*
    
    echo -e "${GREEN}✅ Successfully published ${PACKAGE_NAME} v${VERSION} to PyPI!${NC}"
    echo -e "You can install it with: ${YELLOW}pip install ${PACKAGE_NAME}==${VERSION}${NC}"
else
    echo -e "${YELLOW}Not uploading to PyPI. You can find the built packages in the dist/ directory.${NC}"
    echo -e "To upload manually, run: ${YELLOW}twine upload dist/*${NC}"
fi