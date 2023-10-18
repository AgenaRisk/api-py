from .node import Node
from .network import Network
from .dataset import Dataset, dotdict
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

        command = 'powershell -command "mvn exec:java@activate \\"-Dexec.args=`\\"--keyActivate --key ' + key + '`\\"\\""'
        send_command = subprocess.check_output(command)

    elif platform == "darwin" or platform == "linux" or platform == "linux2":

        command = 'mvn exec:java@activate -Dexec.args="--keyActivate --key' + key + '"'
        send_command = subprocess.check_output(command)

    if send_command == 0:
        full_response = str(send_command)
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

def local_api_calculate(model:Model, dataset_ids:list[str]=None, cache_path = None):
    cur_wd = os.getcwd()
    os.chdir("./api/")
    
    tempdir = tempfile.TemporaryDirectory()

    if dataset_ids is not None:
        data_json = model._ds_to_json(dataset_ids)
    else:
        data_json = model._ds_to_json() #if dataset ids are not specified, all datasets in the model are calculated
        
    if platform == "win32":
        model_path = tempdir.name + "\\" + data_json[0]["id"] + "_model.cmpx"
        data_path = tempdir.name + "\\" + data_json[0]["id"] + "_dataset.json"

        model_file = model.save_to_file(model_path)
        with open(data_path, "w") as outfile:
            json.dump(data_json, outfile)

        if cache_path is None:
            out_path = tempdir.name + "\\" + data_json[0]["id"] + "_output.json"
            command = 'powershell -command "mvn exec:java@calculate \\"-Dexec.args=`\\"--model \'' + model_path + '\' --out \'' + out_path + '\' --data \'' + data_path + '\'`\\"\\""'

        else:
            out_path = cache_path
            command = 'powershell -command "mvn exec:java@calculate \\"-Dexec.args=`\\"--model \'' + model_path + '\' --out \'' + out_path + '\' --data \'' + data_path + '\' --use-cache`\\"\\""'

        send_command = os.system(command)
    
    elif platform == "darwin" or platform == "linux" or platform == "linux2":       
        model_path = tempdir.name + "/" + data_json[0]["id"] + "_model.cmpx"
        data_path = tempdir.name + "/" + data_json[0]["id"] + "_dataset.json"

        model_file = model.save_to_file(model_path)
        with open(data_path, "w") as outfile:
            json.dump(data_json, outfile)

        if cache_path is None:
            out_path = tempdir.name + "/" + data_json[0]["id"] + "_output.json"
            command = 'mvn exec:java@calculate -Dexec.args="--model \'' + model_path + '\'  --out \'' + out_path + '\' --data \'' + data_path + '\'"'
        else:
            out_path = cache_path
            command = 'mvn exec:java@calculate -Dexec.args="--model \'' + model_path + '\'  --out \'' + out_path + '\' --data \'' + data_path + '\' --use-cache"'

        send_command = os.system(command)

    if send_command == 0:
        model._import_results(out_path)
        print("The calculation is completed, the dataset in the model now contains new calculation results")
        os.chdir(cur_wd)
    
    else:
        os.chdir(cur_wd)
        raise ValueError("Calculation failed")

def local_api_sensitivity_analysis(model:Model, sens_config):

    def _results_to_dotdict(input):
        dot_results = dotdict(input)
        for idx, tb in enumerate(dot_results.tables):
            dot_results.tables[idx] = dotdict(dot_results.tables[idx])
        for idx, cur in enumerate(dot_results.responseCurveGraphs):
            dot_results.responseCurveGraphs[idx] = dotdict(dot_results.responseCurveGraphs[idx])
        for idx, tor in enumerate(dot_results.tornadoGraphs):
            dot_results.tornadoGraphs[idx] = dotdict(dot_results.tornadoGraphs[idx])
        dot_results.sensitivityConfig = dotdict(dot_results.sensitivityConfig)

        return dot_results


    cur_wd = os.getcwd()
    os.chdir("./api/")

    tempdir = tempfile.TemporaryDirectory()

    if platform == "win32":
        model_path = tempdir.name + "\\" + "model.cmpx"
        config_path = tempdir.name + "\\" + "sens_config.json"
        out_path = tempdir.name + "\\" + "output.json"

        model_file = model.save_to_file(model_path)
        with open(config_path, "w") as outfile:
            json.dump(sens_config, outfile)

        command = 'powershell -command "mvn exec:java@sensitivity \\"-Dexec.args=`\\"--model \'' + model_path + '\' --out \'' + out_path + '\' --config \'' + config_path + '\'`\\"\\""'
        send_command = os.system(command)

    elif platform == "darwin" or platform == "linux" or platform == "linux2":
        
        model_path = tempdir.name + "/" + "model.cmpx"
        config_path = tempdir.name + "/" + "sens_config.json"
        out_path = tempdir.name + "/" + "output.json"

        model_file = model.save_to_file(model_path)
        with open(config_path, "w") as outfile:
            json.dump(sens_config, outfile)

        command = 'mvn exec:java@sensitivity -Dexec.args="--model \'' + model_path + '\'  --out \'' + out_path + '\' --config \'' + config_path + '\'"'
        send_command = os.system(command)

    if send_command == 0:
        with open(out_path, "r") as file:
            results_string = file.read()
        sens_results = json.loads(results_string)
        sens_results = _results_to_dotdict(sens_results)

        os.chdir(cur_wd)
        return(sens_results)
    
    else:
        os.chdir(cur_wd)
        raise ValueError("Sensitivity analysis failed")
    

