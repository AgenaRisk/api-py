from .node import Node
from .network import Network
from .dataset import Dataset, dotdict
from .model import Model

import requests as re
from getpass import getpass
import time    
import json
import logging

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
            logging.info("Authentication to agena.ai cloud servers is successful")
            self.access_token = login_response.json()["access_token"]
            self.refresh_token = login_response.json()["refresh_token"]
            self.login_time = int(time.time())
            access_duration = login_response.json()["expires_in"]
            refresh_duration = login_response.json()["refresh_expires_in"]
            self.access_expire = self.login_time + access_duration
            self.refresh_expire = self.login_time + refresh_duration
            self.debug = False
            self.server = "https://api.agena.ai"

        else:
            raise ValueError("Authentication failed")

    def __repr__(self) -> str:
        return f"agena.ai cloud user ({self.username})"
    
    def set_debug(self, debug:bool):
        if debug:
            self.debug = True
            logging.info("Cloud operation results will display detailed debugging messages")
        if not debug:
            self.debug = False
            logging.info("Clod operation results will not display detailed debug messages")

    def set_server_url(self, url):
        last_char = url[-1]
        if last_char == "/":
            url = url[:-1]

        self.server = url
        logging.info(f"The root of the server URL for cloud operations is set as {url}")

    def reset_server_url(self):
        self.server = "https://api.agena.ai"
        logging.info(f"The root of the server URL for cloud operations is reset to https://api.agena.ai")

    def refresh_auth(self):
        ref_url = "https://auth.agena.ai/realms/cloud/protocol/openid-connect/token"
        ref_header = {"Content-Type":"application/x-www-form-urlencoded"}
        ref_body = {"client_id":"agenarisk-cloud",
                "refresh_token": self.refresh_token,
                "grant_type":"refresh_token"}
    
        ref_response = re.post(ref_url, headers=ref_header, data=ref_body)
        if ref_response.status_code == 200:
            self.access_token = ref_response.json()["access_token"]   

    def calculate(self, model:Model, dataset_id=None):
        now = int(time.time())
        model_to_send = model._generate_cmpx()

        calculate_url = self.server + "/public/v1/calculate"
        
        if dataset_id is None:
            calculate_body = {"sync-wait":"true", "model":model_to_send["model"]}
        else:
            for ds in model.datasets:
                if ds.id == dataset_id:
                    dataset_to_send = {"observations":ds.observations}
            calculate_body = {"sync-wait":"true", "model":model_to_send["model"], "dataSet":dataset_to_send}

        if now > self.refresh_expire:
            raise ValueError("Login has expired")
        
        if now > self.access_expire and now < self.refresh_expire:
            self.refresh_auth()

        calculate_response = re.post(calculate_url, headers={"Authorization":f"Bearer {self.access_token}"},json=calculate_body)

        if calculate_response.status_code == 200:
            logging.info(calculate_response.json()["messages"])
            if self.debug:
                for db in calculate_response.json()["debug"]:
                    logging.info(db)
            
            if calculate_response.json()["status"]=="success":
                if dataset_id is None:
                    model.datasets[0].results = calculate_response.json()["results"]
                    model.dataset[0]._convert_to_dotdict()
                else:
                    for ds in model.datasets:
                        if ds.id == dataset_id:
                            ds.results = calculate_response.json()["results"]
                            ds._convert_to_dotdict()
        elif calculate_response.status_code == 202:           
            logging.info(calculate_response.json()["messages"])
            logging.info("Polling has started, polling for calculation results will update every 3 seconds")
            
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
                logging.info(polled_response.json()["messages"])
                if self.debug:
                    for db in polled_response.json()["debug"]:
                        logging.info(db)

                if polled_response.json()["status"]=="success":
                    if dataset_id is None:
                        model.datasets[0].results = polled_response.json()["results"]
                        model.datasets[0]._convert_to_dotdict()
                    else:
                        for ds in model.datasets:
                            if ds.id == dataset_id:
                                ds.results = polled_response.json()["results"]
                                ds._convert_to_dotdict()
                
            else:
                if self.debug:
                    for db in polled_response.json()["debug"]:
                        logging.info(db)
                raise ValueError(polled_response.json()["messages"]) 
        
        else:
            if self.debug:
                for db in calculate_response.json()["debug"]:
                    logging.info(db)
            raise ValueError(calculate_response.json()["messages"])
        
    def sensitivity_analysis(self, model:Model, sens_config):

        def _results_to_dotdict(input):
            dot_results = dotdict(input)
            dot_results.results = dotdict(dot_results.results)
            for idx, tb in enumerate(dot_results.results.tables):
                dot_results.results.tables[idx] = dotdict(dot_results.results.tables[idx])
            for idx, cur in enumerate(dot_results.results.responseCurveGraphs):
                dot_results.results.responseCurveGraphs[idx] = dotdict(dot_results.results.responseCurveGraphs[idx])
            for idx, tor in enumerate(dot_results.results.tornadoGraphs):
                dot_results.results.tornadoGraphs[idx] = dotdict(dot_results.results.tornadoGraphs[idx])
        
            return dot_results

        now = int(time.time())
        model_to_send = model._generate_cmpx()
        sa_url = self.server + "/public/v1/tools/sensitivity"
        
        sa_body = {"sync-wait":"true", "model":model_to_send["model"], "sensitivityConfig":sens_config}

        if now > self.refresh_expire:
            raise ValueError("Login has expired")
        
        if now > self.access_expire and now < self.refresh_expire:
            self.refresh_auth()

        sa_response = re.post(sa_url, headers={"Authorization":f"Bearer {self.access_token}"},json=sa_body)

        if sa_response.status_code == 200:
            logging.info(sa_response.json()["messages"])
            if self.debug:
                for db in sa_response.json()["debug"]:
                    logging.info(db)
            
            if sa_response.json()["status"]=="success":
                sa_results = {}
                fields = ["lastUpdated", "version", "log", "uuid", "debug", "duration", "messages", "results", "memory"]
                for f in fields:
                    sa_results[f] = sa_response.json()[f]
                sa_results = _results_to_dotdict(sa_results)
        
        elif sa_response.status_code == 202:
            logging.info(sa_response.json()["messages"])
            logging.info("Polling has started, polling for calculation results will update every 3 seconds")
            
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
                logging.info(polled_response.json()["messages"])
                if self.debug:
                    for db in polled_response.json()["debug"]:
                        logging.info(db)

                if polled_response.json()["status"]=="success":
                    sa_results = {}
                    fields = ["lastUpdated", "version", "log", "uuid", "debug", "duration", "messages", "results", "memory"]
                    for f in fields:
                        sa_results[f] = polled_response.json()[f]
                    sa_results = _results_to_dotdict(sa_results)
                
            else:
                if self.debug:
                    for db in polled_response.json()["debug"]:
                        logging.info(db)
                raise ValueError(polled_response.json()["messages"])
                
        else:
            if self.debug:
                for db in sa_response.json()["debug"]:
                    logging.info(db)
            raise ValueError(sa_response.json()["messages"])
        
        return sa_results
    

