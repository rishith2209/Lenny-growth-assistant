#!/bin/bash
set -e
mkdir -p /etc/systemd/system/ollama.service.d
cat << 'EOF' > /etc/systemd/system/ollama.service.d/override.conf
[Service]
Environment="OLLAMA_MODELS=/mnt/c/Users/ksree/.ollama/models"
Environment="OLLAMA_HOST=0.0.0.0:11434"
EOF
systemctl daemon-reload
systemctl restart ollama
sleep 3
ollama list
echo "OLLAMA_SYSTEMD_READY"
