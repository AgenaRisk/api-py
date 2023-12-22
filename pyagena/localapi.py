from .node import Node
from .network import Network
from .dataset import Dataset, dotdict
from .model import Model

from sys import platform
import os, shutil, stat
import tempfile
import json
import subprocess
import logging

def local_api_clone():
    send_command = subprocess.run(["git", "clone", "https://github.com/AgenaRisk/api.git"], capture_output=True, text=True)

    already = "already exists and is not an empty directory"
    if already in send_command.stderr:
        raise ValueError("API clone failed - destination path 'api' already exists and is not an empty directory")
    else:
        logging.info(send_command.stdout)
        logging.info(send_command.stderr)
        logging.info("The local api environment is cloned to the working directory successfully")

def local_api_compile(verbose = False):
    cur_wd = os.getcwd()
    os.chdir(os.path.join('.', 'api'))

    checkout = subprocess.run(["git", "checkout", "master"], capture_output=True, text=True)
    if verbose:
        logging.info(checkout.stdout)
        logging.info(checkout.stderr)
    
    pull = subprocess.run(["git", "pull"], capture_output=True, text=True)
    if verbose:
        logging.info(pull.stdout)
        logging.info(pull.stderr)
    get_tag = subprocess.run(["git", "describe", "--tags", "--abbrev=0"], capture_output=True, text=True)
    tag = get_tag.stdout.strip()
    tag_comm = ['git', 'checkout', tag]

    updated = subprocess.run(tag_comm, capture_output=True, text=True)
    if verbose:
        logging.info(updated.stdout)
        logging.info(updated.stderr)
    if platform == "win32":
        send_command = subprocess.run('powershell -command "mvn clean compile -DskipTests"', capture_output=True, text=True)
    else:
        if not (platform == "darwin" or platform == "linux" or platform == "linux2"):
            logging.warning(f'This function was not tested for platform {platform} and may not work properly')
        send_command = subprocess.run(['mvn', 'clean', 'compile', '-DskipTests'], capture_output=True, text=True)
        
    os.chdir(cur_wd)
    if verbose:
        logging.info(send_command.stdout)
        logging.info(send_command.stderr)
    if send_command.returncode == 0:
        logging.info("The local api environment is compiled with maven successfully")
    else:
        raise ValueError("maven compile has failed")


def local_api_init(verbose = False):
    api_path=os.path.join('.', 'api')
    if os.path.isdir(api_path):
        def rm_dir_readonly(func, path, _):
            if platform == 'darwin':
                os.system('chflags nouchg {}'.format(path))
            os.chmod(path, stat.S_IWRITE)
            func(path)

        shutil.rmtree(api_path, onerror=rm_dir_readonly)

    local_api_clone()
    local_api_compile(verbose = verbose)


def _get_license_info(mvnout):
    summary = "{" + mvnout.stdout.split("{")[1].split("}")[0].strip() + "}"
    return json.loads(summary)

def local_api_activate_license(key, verbose = False):
    cur_wd = os.getcwd()
    os.chdir(os.path.join('.', 'api'))

    if platform == "win32":
        command = 'powershell -command "mvn exec:java@activate \\"-Dexec.args=`\\"--keyActivate --key ' + key + '`\\"\\""'
        send_command = _exec_shell_command(command, capture_output=True, text=True)

    else:
        if not (platform == "darwin" or platform == "linux" or platform == "linux2"):
            logging.warning(f'This function was not tested for platform {platform} and may not work properly')

        command = ['mvn', 'exec:java@activate', '-Dexec.args=--keyActivate --key ' + key]
        send_command = _exec_shell_command(command, capture_output=True, text=True)

    os.chdir(cur_wd)

    if verbose:
        logging.info(send_command.stdout)
        logging.info(send_command.stderr)

    already = "Product already activated"
    invalid = "Invalid license key"
    if already in send_command.stdout:
        logging.info(already)
    elif invalid in send_command.stdout:
        raise ValueError(invalid)
    else:
        license_info = _get_license_info(send_command)
        if license_info["Mode"] == "FreeTrial":
            raise ValueError("Licence key activation failed")        
        else:
            logging.info("License key activated successfully")

def local_api_deactivate_license(verbose = False):
    cur_wd = os.getcwd()
    os.chdir(os.path.join('.', 'api'))
    
    if platform == "win32":    
        command = 'powershell -command "mvn exec:java@activate \\"-Dexec.args=`\\"--keyDeactivate`\\"\\""'
        send_command = _exec_shell_command(command, capture_output=True, text=True)

    else:
        if not (platform == "darwin" or platform == "linux" or platform == "linux2"):
            logging.warning(f'This function was not tested for platform {platform} and may not work properly')

        command = ['mvn', 'exec:java@activate', '-Dexec.args=--keyDeactivate']
        send_command = _exec_shell_command(command, capture_output=True, text=True)

    os.chdir(cur_wd)

    if verbose:
        logging.info(send_command.stdout)
        logging.info(send_command.stderr)

    notyet = "Product not yet activated"
    if len(send_command.stderr) > 0:
        limit_reach = "The license has reached it's allowed deactivations limit"
        if limit_reach in send_command.stderr:
            raise ValueError(limit_reach)
        elif notyet in send_command.stdout:
            logging.info(notyet)
        else:
            raise ValueError("Deactivation failed")
    else:
        if notyet in send_command.stdout:
            logging.info(notyet)
        else:
            old_key = send_command.stdout.split("Key released: ")[1].split("\n")[0]
            logging.info(f"Deactivation successful - license key {old_key} is released")

def local_api_get_license_summary(verbose = False):
    cur_wd = os.getcwd()
    os.chdir(os.path.join('.', 'api'))

    if platform == "win32":
        command = 'powershell -command "mvn exec:java@activate \\"-Dexec.args=`\\"--licenseSummary`\\"\\""'
        send_command = _exec_shell_command(command, capture_output=True, text=True)
    
    else:
        if not (platform == "darwin" or platform == "linux" or platform == "linux2"):
            logging.warning(f'This function was not tested for platform {platform} and may not work properly')

        command = ['mvn', 'exec:java@activate', '-Dexec.args=--licenseSummary']
        send_command = _exec_shell_command(command, capture_output=True, text=True)
    
    os.chdir(cur_wd)

    if verbose:
        logging.info(send_command.stdout)
        logging.info(send_command.stderr)

    return _get_license_info(send_command)

def local_api_show_license(verbose = False):
    license_info = local_api_get_license_summary(verbose)
    for ix, st in license_info.items():
            print(f"{ix}: {st}")
        
def local_api_calculate(model:Model, dataset_ids = None, cache_path = None, verbose = False):
    cur_wd = os.getcwd()
    os.chdir(os.path.join('.', 'api'))
    
    tempdir = tempfile.TemporaryDirectory()

    if dataset_ids is not None:
        for ds in dataset_ids:
            if ds not in model._get_datasets():
                os.chdir(cur_wd)
                raise ValueError(f"The model does not have a dataset {ds}")
            
        data_json = model._ds_to_json(dataset_ids)
    else:
        data_json = model._ds_to_json() #if dataset ids are not specified, all datasets in the model are calculated

    model_path = os.path.join(tempdir.name, data_json[0]["id"] + "_model.cmpx")
    data_path = os.path.join(tempdir.name, data_json[0]["id"] + "_dataset.json")

    model_file = model.save_to_file(model_path, strip_data=True)
    with open(data_path, "w") as outfile:
        json.dump(data_json, outfile)

    if cache_path is None:
        out_path = os.path.join(tempdir.name, data_json[0]["id"] + "_output.json")
    else:
        out_path = cache_path

    if platform == "win32":
        if cache_path is None:
            command = 'powershell -command "mvn exec:java@calculate \\"-Dexec.args=`\\"--model \'' + model_path + '\' --out \'' + out_path + '\' --data \'' + data_path + '\'`\\"\\""'
        else:
            command = 'powershell -command "mvn exec:java@calculate \\"-Dexec.args=`\\"--directoryWorking \'' + cur_wd + '\' --model \'' + model_path + '\' --out \'' + out_path + '\' --data \'' + data_path + '\' --use-cache`\\"\\""'
        send_command = _exec_shell_command(command, capture_output=True, text=True)
    
    else:
        if not (platform == "darwin" or platform == "linux" or platform == "linux2"):
            logging.warning(f'This function was not tested for platform {platform} and may not work properly')

        if cache_path is None:
            command = ['mvn', 'exec:java@calculate', '-Dexec.args=--model "' + model_path + '"  --out "' + out_path + '" --data "' + data_path + '"']
        else:
            command = ['mvn', 'exec:java@calculate', '-Dexec.args=--directoryWorking "' + cur_wd + '" --model "' + model_path + '"  --out "' + out_path + '" --data "' + data_path + '" --use-cache']
        send_command = _exec_shell_command(command, capture_output=True, text=True)

    os.chdir(cur_wd)

    if verbose:
        logging.info(send_command.stdout)
        logging.info(send_command.stderr)

    if send_command.returncode != 0:
        tempdir.cleanup()
        raise ValueError("Calculation failed")
    else:
        model._import_results(out_path)
        logging.info("The calculation is completed, the dataset in the model now contains new calculation results")
        tempdir.cleanup()
    
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
    os.chdir(os.path.join('.', 'api'))

    tempdir = tempfile.TemporaryDirectory()

    model_path = os.path.join(tempdir.name, "model.cmpx")
    config_path = os.path.join(tempdir.name, "sens_config.json")
    out_path = os.path.join(tempdir.name, "output.json")

    model_file = model.save_to_file(model_path)
    with open(config_path, "w") as outfile:
        json.dump(sens_config, outfile)

    if platform == "win32":
        command = 'powershell -command "mvn exec:java@sensitivity \\"-Dexec.args=`\\"--model \'' + model_path + '\' --out \'' + out_path + '\' --config \'' + config_path + '\'`\\"\\""'
        send_command = _exec_shell_command(command, capture_output=True, text=True)

    else:
        if not (platform == "darwin" or platform == "linux" or platform == "linux2"):
            logging.warning(f'This function was not tested for platform {platform} and may not work properly')

        command = ['mvn', 'exec:java@sensitivity', '-Dexec.args=--model "' + model_path + '"  --out "' + out_path + '" --config "' + config_path + '"']
        send_command = _exec_shell_command(command, capture_output=True, text=True)

    os.chdir(cur_wd)

    if verbose:
        logging.info(send_command.stdout)
        logging.info(send_command.stderr)

    if len(send_command.stderr) > 0:
        tempdir.cleanup()
        raise ValueError("Sensitivity analysis failed")
    else:
        with open(out_path, "r") as file:
            results_string = file.read()
        sens_results = json.loads(results_string)
        sens_results = _results_to_dotdict(sens_results)
        tempdir.cleanup()
        return(sens_results)

def _exec_shell_command(*args, **kwargs):
    send_command = subprocess.run(*args, **kwargs)
    error_marker="Only Enterprise version can run in a headless environment"
    if error_marker in send_command.stdout or error_marker in send_command.stderr:
        raise RuntimeError(error_marker)
    return send_command
