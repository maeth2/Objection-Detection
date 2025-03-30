start cmd /c "ngrok start --all --region=eu & pause"
timeout /t 5
python init_ngrok.py
start_servers.bat