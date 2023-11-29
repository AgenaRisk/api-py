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
    send_command = subprocess.run(["git", "clone", "https://github.com/AgenaRisk/api.git"], capture_output=True, text=True)

    already = "already exists and is not an empty directory"
    if already in send_command.stderr:
        raise ValueError("API clone failed - destination path 'api' already exists and is not an empty directory")
    else:
        print(send_command.stdout)
        print(send_command.stderr)
        print("The local api environment is cloned to the working directory successfully")

def local_api_compile(verbose = False):
    cur_wd = os.getcwd()
    os.chdir("./api/")

    checkout = subprocess.run(["git", "checkout", "master"], capture_output=True, text=True)
    if verbose:
        print(checkout.stdout)    
    pull = subprocess.run(["git", "pull"], capture_output=True, text=True)
    if verbose:
        print(pull.stdout)
    get_tag = subprocess.run(["git", "describe", "--tags", "--abbrev=0"], capture_output=True, text=True)
    tag = get_tag.stdout.strip()
    tag_comm = ['git', 'checkout', tag]

    updated = subprocess.run(tag_comm, capture_output=True, text=True)
    if verbose:
        print(updated.stderr)

    send_command = os.system("mvn clean compile")
    os.chdir(cur_wd)

    if send_command == 0:
        print("The local api environment is compiled with maven successfully")
    else:
        raise ValueError("maven compile has failed")

def _get_license_info(mvnout):
    # summary = "{" + mvnout.stdout.split("{")[1].split("}")[0].strip() + "}"
    # return json.loads(summary)
    
    summary = mvnout.stdout.split("{")[1].split("}")[0].strip()
    statements = {}

    sum_list = summary.replace("'","").replace('"','').split("\n")
    for st in sum_list:
        st = st.strip()
        statements[st.split(": ")[0]] = st.split(": ")[1].replace(",","")
    
    return statements

def local_api_activate_license(key, verbose = False):
    cur_wd = os.getcwd()
    os.chdir("./api/")

    if platform == "win32":

        #command = ['powershell', '-command', '"mvn', 'exec:java@activate', '\\"-Dexec.args=`\\"--keyActivate', '--key', key, '`\\"\\""']
        command = 'powershell -command "mvn exec:java@activate \\"-Dexec.args=`\\"--keyActivate --key ' + key + '`\\"\\""'
        send_command = subprocess.run(command, capture_output=True, text=True)
        os.chdir(cur_wd)

    elif platform == "darwin" or platform == "linux" or platform == "linux2":

        command = ['mvn', 'exec:java@activate', '-Dexec.args="--keyActivate', '--key', key, '"']
        #command = 'mvn exec:java@activate -Dexec.args="--keyActivate --key ' + key + '"'
        send_command = subprocess.run(command, capture_output=True, text=True)
        os.chdir(cur_wd)

    license_info = _get_license_info(send_command)
    if license_info["Mode"] == "FreeTrial":
        if verbose:
            print(send_command.stdout)
            print(send_command.stderr)
        raise ValueError("Licence key activation failed")        
    else:
        already = "Product already activated"
        invalid = "Invalid license key"
        if already in send_command.stdout:
            if verbose:
                print(send_command.stdout)
            raise ValueError(already)
        elif invalid in send_command.stdout:
            if verbose:
                print(send_command.stdout)
            raise ValueError(invalid)
        else:
            if verbose:
                print(send_command.stdout)
            print("License key activated successfully")

def local_api_deactivate_license(verbose = False):
    cur_wd = os.getcwd()
    os.chdir("./api/")
    
    if platform == "win32":    
        command = 'powershell -command "mvn exec:java@activate \\"-Dexec.args=`\\"--keyDeactivate`\\"\\""'
        send_command = subprocess.run(command, capture_output=True, text=True)
        os.chdir(cur_wd)

    elif platform == "darwin" or platform == "linux" or platform == "linux2":
        #command = 'mvn exec:java@activate -Dexec.args="--keyDeactivate"'
        command = ['mvn', ' exec:java@activate', '-Dexec.args="--keyDeactivate"']
        send_command = subprocess.run(command, capture_output=True, text=True)
        os.chdir(cur_wd)

    if len(send_command.stderr) > 0:
        if verbose:
            print(send_command.stdout)
            print(send_command.stderr)
        limit_reach = "The license has reached it's allowed deactivations limit"
        if limit_reach in send_command.stderr:
            raise ValueError(limit_reach)
        else:
            raise ValueError("Deactivation failed")
    else:
        old_key = send_command.stdout.split("Key released: ")[1].split("\n")[0]
        if verbose:
            print(send_command.stdout)
        print(f"Deactivation successful - license key {old_key} is released")

def local_api_show_license(verbose = False):
    cur_wd = os.getcwd()
    os.chdir("./api/")

    if platform == "win32":
        #command = ['powershell', '-command', '"mvn', 'exec:java@activate', '\\"-Dexec.args=`\\"--licenseSummary`\\"\\""']
        command = 'powershell -command "mvn exec:java@activate \\"-Dexec.args=`\\"--licenseSummary`\\"\\""'
        send_command = subprocess.run(command, capture_output=True, text=True)
        os.chdir(cur_wd)
    
    elif platform == "darwin" or platform == "linux" or platform == "linux2":
        command = ['mvn', 'exec:java@activate', '-Dexec.args="--licenseSummary"']
        #command = 'mvn exec:java@activate -Dexec.args="--licenseSummary"'
        send_command = subprocess.run(command, capture_output=True, text=True)
        os.chdir(cur_wd)

    if len(send_command.stderr) > 0:
        if verbose:
            print(send_command.stdout)
            print(send_command.stderr)
        expired = "Trial already expired"
        if expired in send_command.stderr:
            raise ValueError(expired)
        else:
            raise ValueError("Error when attempting to show license")
    else:
        license_info = _get_license_info(send_command)

        if verbose:
            print(send_command.stdout)

        for ix, st in license_info.items():
            print(f"{ix}: {st}")
        
def local_api_calculate(model:Model, dataset_ids = None, cache_path = None, verbose = False):
    cur_wd = os.getcwd()
    os.chdir("./api/")
    
    tempdir = tempfile.TemporaryDirectory()

    if dataset_ids is not None:
        for ds in dataset_ids:
            if ds not in model._get_datasets():
                os.chdir(cur_wd)
                raise ValueError(f"The model does not have a dataset {ds}")
            
        data_json = model._ds_to_json(dataset_ids)
    else:
        data_json = model._ds_to_json() #if dataset ids are not specified, all datasets in the model are calculated

    model_path = tempdir.name + "/" + data_json[0]["id"] + "_model.cmpx"
    data_path = tempdir.name + "/" + data_json[0]["id"] + "_dataset.json"

    model_file = model.save_to_file(model_path, strip_data=True)
    with open(data_path, "w") as outfile:
        json.dump(data_json, outfile)

    if platform == "win32":

        if cache_path is None:
            out_path = tempdir.name + "/" + data_json[0]["id"] + "_output.json"
            command = 'powershell -command "mvn exec:java@calculate \\"-Dexec.args=`\\"--model \'' + model_path + '\' --out \'' + out_path + '\' --data \'' + data_path + '\'`\\"\\""'

        else:
            out_path = cache_path
            command = 'powershell -command "mvn exec:java@calculate \\"-Dexec.args=`\\"--directoryWorking \'' + cur_wd + '\' --model \'' + model_path + '\' --out \'' + out_path + '\' --data \'' + data_path + '\' --use-cache`\\"\\""'

        send_command = subprocess.run(command, capture_output=True, text=True)
        os.chdir(cur_wd)
    
    elif platform == "darwin" or platform == "linux" or platform == "linux2":       

        if cache_path is None:
            out_path = tempdir.name + "/" + data_json[0]["id"] + "_output.json"
            command = ['mvn', 'exec:java@calculate', '-Dexec.args="--model', '\''+model_path+'\'', '--out', '\''+out_path+'\'', '--data', '\''+data_path+'\'"']
            #command = 'mvn exec:java@calculate -Dexec.args="--model \'' + model_path + '\'  --out \'' + out_path + '\' --data \'' + data_path + '\'"'
        else:
            out_path = cache_path
            command = ['mvn', 'exec:java@calculate', '-Dexec.args="--model', '\''+model_path+'\'', '--out', '\''+out_path+'\'', '--data', '\''+data_path+'\'', '--use-cache"']
            #command = 'mvn exec:java@calculate -Dexec.args="--directoryWorking \'' + cur_wd + '\' --model \'' + model_path + '\'  --out \'' + out_path + '\' --data \'' + data_path + '\' --use-cache"'

        send_command = subprocess.run(command, capture_output=True, text=True)
        os.chdir(cur_wd)

    if len(send_command.stderr) > 0:
        if verbose:
            print(send_command.stdout)
            print(send_command.stderr)
        raise ValueError("Calculation failed")
    else:
        model._import_results(out_path)
        if verbose:
            print(send_command.stdout)
        print("The calculation is completed, the dataset in the model now contains new calculation results")

    
def local_api_sensitivity_analysis(model:Model, sens_config, verbose = False):

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

    model_path = tempdir.name + "/" + "model.cmpx"
    config_path = tempdir.name + "/" + "sens_config.json"
    out_path = tempdir.name + "/" + "output.json"

    model_file = model.save_to_file(model_path)
    with open(config_path, "w") as outfile:
        json.dump(sens_config, outfile)

    if platform == "win32":

        command = 'powershell -command "mvn exec:java@sensitivity \\"-Dexec.args=`\\"--model \'' + model_path + '\' --out \'' + out_path + '\' --config \'' + config_path + '\'`\\"\\""'
        send_command = subprocess.run(command, capture_output=True, text=True)
        os.chdir(cur_wd)

    elif platform == "darwin" or platform == "linux" or platform == "linux2":
        
        command = ['mvn', 'exec:java@sensitivity', '-Dexec.args="--model', '\''+model_path+'\'', '--out', '\''+out_path+'\'', '--config', '\''+config_path+'\'"']
        #command = 'mvn exec:java@sensitivity -Dexec.args="--model \'' + model_path + '\'  --out \'' + out_path + '\' --config \'' + config_path + '\'"'
        send_command = subprocess.run(command, capture_output=True, text=True)
        os.chdir(cur_wd)

    if len(send_command.stderr) > 0:
        if verbose:
            print(send_command.stdout)
            print(send_command.stderr)
        raise ValueError("Sensitivity analysis failed")
    else:
        with open(out_path, "r") as file:
            results_string = file.read()
        sens_results = json.loads(results_string)
        sens_results = _results_to_dotdict(sens_results)

        if verbose:
            print(send_command.stdout)

        return(sens_results)


