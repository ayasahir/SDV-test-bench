#!/bin/bash

# Script to set up a Python virtual environment and install required tools

# Step 1: Install python3-venv and python3-pip
echo "Installing python3-venv and python3-pip..."
sudo apt install -y python3-venv python3-pip

# Step 2: Create a virtual environment
echo "Creating virtual environment..."
VENV_DIR="$HOME/sdv-venv"
python3 -m venv "$VENV_DIR"

# Step 3: Activate the virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Step 4: Install Python packages in the virtual environment
echo "Installing Python packages (pyyaml, kubernetes, psutil)..."
pip install pyyaml kubernetes psutil

# Step 5: Verify installation
echo "Verifying installed packages..."
pip list | grep -E "PyYAML|kubernetes|psutil"

# Step 6: Inform user about activation
echo "Setup complete! To use the virtual environment, run:"
echo "source $VENV_DIR/bin/activate"
echo "To deactivate, run: deactivate"

# Note: The venv is automatically deactivated when the script ends