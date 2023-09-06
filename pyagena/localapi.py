from .node import Node
from .network import Network
from .dataset import Dataset
from .model import Model

from sys import platform
import os
import tempfile
import json
import subprocess

def local_api_clone():
    send_command = os.system("git clone https://github.com/AgenaRisk/api.git")

    if send_command == 0:
        print("The local api environment is cloned to the working directory successfully")

def local_api_compile():
    cur_wd = os.getcwd()
    os.chdir("./api/")

    os.system("git checkout master")
    os.system("git pull")
    rel_tag = os.popen("git describe --tags --abbrev=0").read()
    os.system("git checkout " + rel_tag[:-1])
    send_command = os.system("mvn clean compile")

    if send_command == 0:
        print("The local api environment is compiled with maven successfully")
        os.chdir(cur_wd)
    else:
        os.chdir(cur_wd)
        raise ValueError("maven compile has failed")

def local_api_activate_license(key):
    cur_wd = os.getcwd()
    os.chdir("./api/")

    if platform == "win32":
        shell_command = '"mvn exec:java@activate \'-Dexec.args=\\"--keyActivate --key ' + key + '\\"\'"'
        command = 'powershell -command ' + shell_command
        send_command = os.system(command)

    elif platform == "darwin" or platform == "linux" or platform == "linux2":
        command = 'mvn exec:java@activate \'-Dexec.args="--keyActivate --key ' + key + '"\''
        send_command = os.system(command)

    if send_command == 0:
        full_response = str(subprocess.check_output(command))
        already = "AgenaRisk already activated"
        if already in full_response:
            os.chdir(cur_wd)
            raise ValueError("AgenaRisk already activated")
        else:
            print("License key activated successfully")
            os.chdir(cur_wd)
    else:
        os.chdir(cur_wd)
        raise ValueError("License key activation failed")


def local_api_calculate(model, dataset_id):
    cur_wd = os.getcwd()
    os.chdir("./api/")
    
    tempdir = tempfile.TemporaryDirectory()

    for ds in model.datasets:
        if ds.id == dataset_id:
            data_json = ds._to_json()
        
    if platform == "win32":
        model_path = tempdir.name + "\\" + model.id + ".cmpx"
        data_path = tempdir.name + "\\" + data_json[0]["id"] + ".json"
        out_path = tempdir.name + "\\" + model.id + "_out.json"

        model_file = model.save_to_file(model_path)
        with open(data_path, "w") as outfile:
            json.dump(data_json, outfile)

        command = 'powershell -command "mvn exec:java@calculate \\"-Dexec.args=`\\"--model \'' + model_path + '\' --out \'' + out_path + '\' --data \'' + data_path + '\'`\\"\\""'
        send_command = os.system(command)
    
    elif platform == "darwin" or platform == "linux" or platform == "linux2":       
        model_path = tempdir.name + "/" + model.id + ".cmpx"
        data_path = tempdir.name + "/" + data_json[0]["id"] + ".json"
        out_path = tempdir.name + "/" + model.id + "_out.json"

        model_file = model.save_to_file(model_path)
        with open(data_path, "w") as outfile:
            json.dump(data_json, outfile)

        command = 'mvn exec:java@calculate -Dexec.args="--model \'' + model_path + '\'  --out \'' + out_path + '\' --data \'' + data_path + '\'"'
        send_command = os.system(command)

    if send_command == 0:
        model.import_results(out_path)
        print("The calculation is completed, the dataset in the model now contains new calculation results")
        os.chdir(cur_wd)
    
    else:
        os.chdir(cur_wd)
        raise ValueError("Calculation failed")

def local_api_sensitivity_analysis(model, sens_config):
    cur_wd = os.getcwd()
    os.chdir("./api/")

    tempdir = tempfile.TemporaryDirectory()

    if platform == "win32":
        model_path = tempdir.name + "\\" + model.id + ".cmpx"
        config_path = tempdir.name + "\\" + model.id + "_sens_config.json"
        out_path = tempdir.name + "\\" + model.id + "_out.json"

        model_file = model.save_to_file(model_path)
        with open(config_path, "w") as outfile:
            json.dump(sens_config, outfile)

        command = 'powershell -command "mvn exec:java@sensitivity \\"-Dexec.args=`\\"--model \'' + model_path + '\' --out \'' + out_path + '\' --config \'' + config_path + '\'`\\"\\""'
        send_command = os.system(command)

    elif platform == "darwin" or platform == "linux" or platform == "linux2":
        
        model_path = tempdir.name + "/" + model.id + ".cmpx"
        config_path = tempdir.name + "/" + model.id + "_sens_config.json"
        out_path = tempdir.name + "/" + model.id + "_out.json"

        model_file = model.save_to_file(model_path)
        with open(config_path, "w") as outfile:
            json.dump(sens_config, outfile)

        command = 'mvn exec:java@sensitivity -Dexec.args="--model \'' + model_path + '\'  --out \'' + out_path + '\' --config \'' + config_path + '\'"'
        send_command = os.system(command)

    if send_command == 0:
        with open(out_path, "r") as file:
            results_string = file.read()
        sens_results = json.loads(results_string)
        
        #print("The sensitivity analysis is completed and the results are saved to working directory")
        os.chdir(cur_wd)
        return(sens_results)
    
    else:
        os.chdir(cur_wd)
        raise ValueError("Sensitivity analysis failed")

def local_api_batch_calculate(model):
    
    for ds in model.datasets:
        this_ds = ds.id
        local_api_calculate(model, this_ds)
    

