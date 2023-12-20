import os
import json

def _get_creds():
    with open(os.path.dirname(os.path.realpath(__file__))+"/.local/credentials.json") as file:
        json_credentials=json.loads(file.read())
    return json_credentials

creds = _get_creds()
username = creds['username']
password = creds['password']
agena_key = creds['agena-key']
