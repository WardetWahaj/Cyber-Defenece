#!/bin/bash
# CYBERDEFENCE ANALYST PLATFORM v3.1
# Setup script for Kali Linux

echo "============================================"
echo "  CyberDefence Platform v3.1 — Kali Setup"
echo "============================================"

echo "[*] Updating pip..."
pip3 install --upgrade pip --break-system-packages

echo "[*] Installing Python dependencies..."
pip3 install requests rich fpdf2 python-nmap --break-system-packages

echo "[*] Checking Nmap..."
if command -v nmap &> /dev/null; then
    echo "[✓] Nmap installed"
else
    sudo apt-get install -y nmap
fi

echo "[*] Checking Nuclei..."
if command -v nuclei &> /dev/null; then
    echo "[✓] Nuclei installed — updating templates..."
    nuclei -update-templates
else
    echo "[*] Installing Nuclei..."
    sudo apt-get install -y nuclei 2>/dev/null || \
    go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest 2>/dev/null || \
    echo "[!] Could not auto-install Nuclei. Install manually: sudo apt install nuclei"
fi

echo "[*] Creating data directories..."
mkdir -p data/recon data/vuln data/defence data/siem \
         data/policies data/reports data/virustotal \
         data/nuclei data/sucuri

chmod +x cyberdefence_platform_v31.py

echo ""
echo "============================================"
echo "  Setup complete!"
echo "============================================"
echo ""
echo "BEFORE RUNNING — open config.json and add:"
echo "  wpscan_api_key    → your WPScan key (wpscan.com/profile)"
echo "  virustotal_api_key → your VT key (virustotal.com/gui/my-apikey)"
echo ""
echo "TO RUN:"
echo "  sudo python3 cyberdefence_platform_v31.py"
echo ""
echo "NOTE: sudo required for Nmap + Nuclei"
echo "============================================"
