import json
import os 

os.system("curl http://localhost:4040/api/tunnels > ./frontend/tunnels.json")

with open('./frontend/tunnels.json') as data_file:    
    datajson = json.load(data_file)

msg = "ngrok URL's: \n"
for i in datajson['tunnels']:
  msg = msg + i['public_url'] +'\n'

print(msg)