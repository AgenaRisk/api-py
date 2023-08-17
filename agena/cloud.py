from node import Node
from network import Network
from dataset import Dataset
from model import Model

import requests as re
from getpass import getpass
import time    
import json

class login():

    access_token = None
    refresh_token = None

    def __init__(self, username = None, password = None):
        self.username = input("Enter username: ") if username is None else username
        self.password = getpass("Enter password: ") if password is None else password

        self.authenticate()

    def authenticate(self):
        login_url = "https://auth.agena.ai/realms/cloud/protocol/openid-connect/token" #auth endpoint
        login_header = {"Content-Type":"application/x-www-form-urlencoded"}
        login_body = {"client_id":"agenarisk-cloud",
                "username":self.username,
                "password":self.password,
                "grant_type":"password"}       

        login_response = re.post(login_url, headers=login_header, data=login_body)

        if login_response.status_code == 200:
            print("Authentication to agena.ai cloud servers is successful")
            self.access_token = login_response.json()["access_token"]
            self.refresh_token = login_response.json()["refresh_token"]
            self.login_time = int(time.time())
            access_duration = login_response.json()["expires_in"]
            refresh_duration = login_response.json()["refresh_expires_in"]
            self.access_expire = self.login_time + access_duration
            self.refresh_expire = self.login_time + refresh_duration

        else:
            raise ValueError("Authentication failed")

    def __repr__(self) -> str:
        return f"agena.ai cloud user ({self.username})"
    
    def refresh_auth(self):
        ref_url = "https://auth.agena.ai/realms/cloud/protocol/openid-connect/token"
        ref_header = {"Content-Type":"application/x-www-form-urlencoded"}
        ref_body = {"client_id":"agenarisk-cloud",
                "refresh_token": self.refresh_token,
                "grant_type":"refresh_token"}
    
        ref_response = re.post(ref_url, headers=ref_header, data=ref_body)
        if ref_response.status_code == 200:
            self.access_token = ref_response.json()["access_token"]   

    def calculate(self, model:Model, dataset=None, debug=False):
        now = int(time.time())
        model_to_send = model._generate_cmpx()

        calculate_url =  "https://api.agena.ai/public/v1/calculate" #calculate endpoint
        if dataset is None:
            calculate_body = {"sync-wait":"true", "model":model_to_send["model"]}
        else:
            for ds in model.datasets:
                if ds.id == dataset:
                    dataset_to_send = {"observations":ds.observations}
            calculate_body = {"sync-wait":"true", "model":model_to_send["model"], "dataSet":dataset_to_send}

        if now > self.refresh_expire:
            raise ValueError("Login has expired")
        
        if now > self.access_expire and now < self.refresh_expire:
            self.refresh_auth()

        calculate_response = re.post(calculate_url, headers={"Authorization":f"Bearer {self.access_token}"},json=calculate_body)

        if calculate_response.status_code == 200:
            print(calculate_response.json()["messages"])
            if debug:
                for db in calculate_response.json()["debug"]:
                    print(db)
            
            if calculate_response.json()["status"]=="success":
                if dataset is None:
                    model.datasets[0].results = calculate_response.json()["results"]
                else:
                    for ds in model.datasets:
                        if ds.id == dataset:
                            ds.results = calculate_response.json()["results"]
        elif calculate_response.status_code == 202:           
            print(calculate_response.json()["messages"])
            print("Polling has started, polling for calculation results will update every 3 seconds")
            if debug:
                for db in calculate_response.json()["debug"]:
                    print(db)
            
            polling_url = calculate_response.json()["pollingUrl"]
            poll_status = 202

            while poll_status == 202:
                poll_now = int(time.time())
                if poll_now > self.refresh_expire:
                    raise ValueError("Login has expired")
        
                if poll_now > self.access_expire and poll_now < self.refresh_expire:
                    self.refresh_auth()

                polled_response = re.get(polling_url, headers={"Authorization":f"Bearer {self.access_token}"})
                poll_status = polled_response.status_code
                time.sleep(3)

            if polled_response.status_code == 200:
                print(polled_response.json()["messages"])
                if debug:
                    for db in polled_response.json()["debug"]:
                        print(db)

                if polled_response.json()["status"]=="success":
                    if dataset is None:
                        model.datasets[0].results = polled_response.json()["results"]
                    else:
                        for ds in model.datasets:
                            if ds.id == dataset:
                                ds.results = polled_response.json()["results"]
                
            else:
                if debug:
                    for db in polled_response.json()["debug"]:
                        print(db)
                raise ValueError(polled_response.json()["messages"]) 
        
        else:
            if debug:
                for db in calculate_response.json()["debug"]:
                    print(db)
            raise ValueError(calculate_response.json()["messages"])
        
    def sensitivity_analysis(self, model:Model, sens_config, debug=False):
        now = int(time.time())
        model_to_send = model._generate_cmpx()
        
        sa_url = "https://api.agena.ai/public/v1/tools/sensitivity"
        sa_body = {"sync-wait":"true", "model":model_to_send["model"], "sensitivityConfig":sens_config}

        if now > self.refresh_expire:
            raise ValueError("Login has expired")
        
        if now > self.access_expire and now < self.refresh_expire:
            self.refresh_auth()

        sa_response = re.post(sa_url, headers={"Authorization":f"Bearer {self.access_token}"},json=sa_body)

        if sa_response.status_code == 200:
            print(sa_response.json()["messages"])
            if debug:
                for db in sa_response.json()["debug"]:
                    print(db)
            
            if sa_response.json()["status"]=="success":
                sa_results = sa_response.json()["results"]
                filename = model.id + "_sensitivity_results"

                with open(filename + ".json", "w") as outfile:
                    json.dump(sa_results, outfile)
                print("Sensitivity analysis results are saved to the directory")
        
        elif sa_response.status_code == 202:
            print(sa_response.json()["messages"])
            print("Polling has started, polling for calculation results will update every 3 seconds")
            if debug:
                for db in sa_response.json()["debug"]:
                    print(db)
            
            polling_url = sa_response.json()["pollingUrl"]
            poll_status = 202

            while poll_status == 202:
                poll_now = int(time.time())
                if poll_now > self.refresh_expire:
                    raise ValueError("Login has expired")
        
                if poll_now > self.access_expire and poll_now < self.refresh_expire:
                    self.refresh_auth()

                polled_response = re.get(polling_url, headers={"Authorization":f"Bearer {self.access_token}"})
                poll_status = polled_response.status_code
                time.sleep(3)

            if polled_response.status_code == 200:
                print(polled_response.json()["messages"])
                if debug:
                    for db in polled_response.json()["debug"]:
                        print(db)

                if polled_response.json()["status"]=="success":
                    sa_results = polled_response.json()["results"]
                    filename = model.id + "_sensitivity_results"
                    with open(filename + ".json", "w") as outfile:
                        json.dump(sa_results, outfile)
                    print("Sensitivity analysis results are saved to the directory")
                
            else:
                if debug:
                    for db in polled_response.json()["debug"]:
                        print(db)
                raise ValueError(polled_response.json()["messages"])
                
        else:
            if debug:
                for db in sa_response.json()["debug"]:
                    print(db)
            raise ValueError(sa_response.json()["messages"])