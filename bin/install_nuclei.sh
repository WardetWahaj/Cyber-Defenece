#!/bin/bash
echo "Installing Nuclei..."
NUCLEI_VERSION="3.7.1"
wget -q https://github.com/projectdiscovery/nuclei/releases/download/v${NUCLEI_VERSION}/nuclei_${NUCLEI_VERSION}_linux_amd64.zip
unzip -o -q nuclei_${NUCLEI_VERSION}_linux_amd64.zip
mkdir -p /app/bin
mv nuclei /app/bin/nuclei
chmod +x /app/bin/nuclei
rm nuclei_${NUCLEI_VERSION}_linux_amd64.zip
echo "Nuclei installed successfully!"