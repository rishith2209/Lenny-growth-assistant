content = """[Unit]
Description=Ollama Service
After=network-online.target

[Service]
ExecStart=/usr/local/bin/ollama serve
User=ollama
Group=ollama
Restart=always
RestartSec=3
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_MODELS=/mnt/c/Users/ksree/.ollama/models"
Environment="OLLAMA_MAX_LOADED_MODELS=3"
Environment="OLLAMA_NUM_PARALLEL=4"
Environment="OLLAMA_KEEP_ALIVE=24h"

[Install]
WantedBy=default.target
"""
with open("/etc/systemd/system/ollama.service", "w") as f:
    f.write(content)
print("Updated /etc/systemd/system/ollama.service successfully.")
