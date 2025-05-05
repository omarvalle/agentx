#!/bin/bash
cd "$PWD"

# Set up permissions
echo "[INFO] Setting up Q CLI tool permissions..."
echo "/tools trust fs_write" | q chat --trust-all-tools
echo "/tools trust fs_read" | q chat --trust-all-tools
echo "/tools trustall" | q chat --trust-all-tools

# Add a sleep to make sure permissions take effect
sleep 1

# Verify permissions
echo "[INFO] Verifying Q CLI permissions..."
echo "/tools" | q chat --trust-all-tools

# Run Q CLI with the prompt file
echo ""
echo "[INFO] Running Q CLI with the provided prompt..."
echo "This may take a few minutes. You'll see progress below:"
echo "=================================================="
cat prompt.txt | q chat --trust-all-tools 2>&1 | tee q_output.log
echo "=================================================="
echo "[INFO] Q CLI execution completed with result code $?"

# Check for HTML files
if [ -f index.html ]; then
  echo "[INFO] index.html file created successfully"
  echo "[INFO] File size: $(ls -lh index.html | awk '{print $5}')"
else
  echo "[WARN] index.html file NOT found after Q CLI execution"
  
  # Try an alternative approach with explicit permissions
  echo "[INFO] Trying alternative approach with explicit permissions..."
  echo "/tools trust fs_write" | q chat --trust-all-tools
  echo "/tools trustall" | q chat --trust-all-tools
  REQ=$(cat requirements.txt)
  echo "Create an HTML file for this request: $REQ" | q chat --trust-all-tools | tee q_explicit_output.log
fi

# List created files
echo "[INFO] Files created:"
ls -la
