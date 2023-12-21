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
        jlogin_response = _parse_json(login_response)

        if login_response.status_code == 200:
            logging.info("Authentication to agena.ai cloud servers is successful")
            self.access_token = jlogin_response["access_token"]
            self.refresh_token = jlogin_response["refresh_token"]
            self.login_time = int(time.time())
            access_duration = jlogin_response["expires_in"]
            refresh_duration = jlogin_response["refresh_expires_in"]
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
            self.access_token = _parse_json(ref_response)["access_token"]   

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

        jcalculate_response = _parse_json(calculate_response)

        if calculate_response.status_code == 200:
            logging.info(jcalculate_response["messages"])
            if self.debug:
                for db in jcalculate_response["debug"]:
                    logging.info(db)
            
            if jcalculate_response["status"]=="success":
                if dataset_id is None:
                    model.datasets[0].results = jcalculate_response["results"]
                    model.dataset[0]._convert_to_dotdict()
                else:
                    for ds in model.datasets:
                        if ds.id == dataset_id:
                            ds.results = jcalculate_response["results"]
                            ds._convert_to_dotdict()
        elif calculate_response.status_code == 202:           
            logging.info(jcalculate_response["messages"])
            logging.info("Polling has started, polling for calculation results will update every 3 seconds")
            
            polling_url = jcalculate_response["pollingUrl"]
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

            jpolled_response = _parse_json(polled_response)

            if polled_response.status_code == 200:
                logging.info(jpolled_response["messages"])
                if self.debug:
                    for db in jpolled_response["debug"]:
                        logging.info(db)

                if jpolled_response["status"]=="success":
                    if dataset_id is None:
                        model.datasets[0].results = jpolled_response["results"]
                        model.datasets[0]._convert_to_dotdict()
                    else:
                        for ds in model.datasets:
                            if ds.id == dataset_id:
                                ds.results = jpolled_response["results"]
                                ds._convert_to_dotdict()
                
            else:
                if self.debug:
                    for db in jpolled_response["debug"]:
                        logging.info(db)
                raise ValueError(jpolled_response["messages"]) 
        
        else:
            if self.debug:
                for db in jcalculate_response["debug"]:
                    logging.info(db)
            raise ValueError(jcalculate_response["messages"])
        
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
        jsa_response = _parse_json(sa_response)

        if sa_response.status_code == 200:
            logging.info(jsa_response["messages"])
            if self.debug:
                for db in jsa_response["debug"]:
                    logging.info(db)
            
            if jsa_response["status"]=="success":
                sa_results = {}
                fields = ["lastUpdated", "version", "log", "uuid", "debug", "duration", "messages", "results", "memory"]
                for f in fields:
                    sa_results[f] = jsa_response[f]
                sa_results = _results_to_dotdict(sa_results)
        
        elif sa_response.status_code == 202:
            logging.info(jsa_response["messages"])
            logging.info("Polling has started, polling for calculation results will update every 3 seconds")
            
            polling_url = jsa_response["pollingUrl"]
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

            jpolled_response = _parse_json(polled_response)
            if polled_response.status_code == 200:
                logging.info(jpolled_response["messages"])
                if self.debug:
                    for db in jpolled_response["debug"]:
                        logging.info(db)

                if jpolled_response["status"]=="success":
                    sa_results = {}
                    fields = ["lastUpdated", "version", "log", "uuid", "debug", "duration", "messages", "results", "memory"]
                    for f in fields:
                        sa_results[f] = jpolled_response[f]
                    sa_results = _results_to_dotdict(sa_results)
                
            else:
                if self.debug:
                    for db in jpolled_response["debug"]:
                        logging.info(db)
                raise ValueError(jpolled_response["messages"])
                
        else:
            if self.debug:
                for db in jsa_response["debug"]:
                    logging.info(db)
            raise ValueError(jsa_response["messages"])
        
        return sa_results
    
def _parse_json(response):
    try:
        jResponse = response.json()
    except:
        if str(response.text) == '':
            err = 'Server response is empty'
        else:
            err = 'Server response not a valid JSON: ' + response.text
        raise RuntimeError(err)
    return jResponse