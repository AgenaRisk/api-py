"""
Local (on this machine) agena.ai calculations.

Every function here used to ``cd`` into a cloned ``./api`` directory and shell out to
``mvn exec:java@<goal>``, building one command string for PowerShell and another for
sh. The API is now a downloaded runtime bundle invoked as ``java -jar`` with a
subcommand, so there is no clone, no build, no shell and nothing to quote by hand —
see :mod:`pyagena.localtools`, which owns provisioning.
"""

import json
import logging
import os
import subprocess
import tempfile
import warnings

from .dataset import dotdict
from .model import Model
from .localtools import (  # noqa: F401  (re-exported for callers)
    engine_command,
    install_api,
    install_java,
    install_licensing,
    installed_version,
    jar_path,
    java_path,
    licensing_path,
    local_api_install,
    resolve_version,
)


def _run(args, working_directory=None, verbose=False):
    """
    Run one engine invocation and return the completed process.

    ``shell=False`` throughout: the argument list goes to the JVM as given, so a path
    containing a space or a quote is no longer a quoting problem to be solved twice.
    """
    command = engine_command(args, working_directory=working_directory)
    if verbose:
        logging.info("Executing: %s", " ".join(command))
    completed = subprocess.run(command, capture_output=True, text=True)

    # Running headless without an Enterprise licence is refused by design. Surfaced as
    # an exception rather than a confusing downstream failure.
    marker = "Only Enterprise version can run in a headless environment"
    if marker in (completed.stdout or "") or marker in (completed.stderr or ""):
        raise RuntimeError(marker)

    if verbose:
        logging.info(completed.stdout)
        logging.info(completed.stderr)
    return completed


def _license_info(completed):
    """
    Parse a licence summary.

    ``activate --licenseSummary --json`` prints the summary as a single JSON object on
    its own line. The previous version had to split the Maven log on braces and hope the
    first ``{`` it found belonged to the summary rather than to anything else the build
    had printed; the last JSON object on stdout is taken here, which is the summary
    whatever precedes it.
    """
    candidates = []
    for line in (completed.stdout or "").splitlines():
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            candidates.append(line)
    if not candidates:
        raise ValueError("The engine did not return a license summary")
    return json.loads(candidates[-1])


# --------------------------------------------------------------------------------------
# Superseded provisioning entry points
# --------------------------------------------------------------------------------------


def _deprecated(old, note):
    warnings.warn(
        "{}() is deprecated: the agena.ai API is distributed as a pre-built bundle and "
        "is no longer cloned or compiled. {}Call local_api_install() instead.".format(
            old, note
        ),
        DeprecationWarning,
        stacklevel=3,
    )


def local_api_clone():
    """Deprecated. Installs the API bundle; nothing is cloned."""
    _deprecated("local_api_clone", "Nothing was cloned. ")
    return local_api_install()


def local_api_compile(verbose=False):
    """Deprecated. Installs the API bundle; nothing is compiled."""
    _deprecated("local_api_compile", "Nothing was compiled. ")
    return local_api_install()


def local_api_init(verbose=False):
    """Deprecated. Reinstalls the API bundle; nothing is cloned or compiled."""
    # This one kept its force: the old local_api_init() deleted ./api and rebuilt from
    # scratch, so a caller reaching for it is asking for a clean slate.
    _deprecated("local_api_init", "")
    return local_api_install(force=True)


# --------------------------------------------------------------------------------------
# Licensing
# --------------------------------------------------------------------------------------


def local_api_activate_license(key, verbose=False):
    completed = _run(["activate", "--keyActivate", "--key", key], verbose=verbose)

    already = "Product already activated"
    invalid = "Invalid license key"
    if already in completed.stdout:
        logging.info(already)
        return
    if invalid in completed.stdout:
        raise ValueError(invalid)

    if _license_info(completed).get("Mode") == "FreeTrial":
        raise ValueError("Licence key activation failed")
    logging.info("License key activated successfully")


def local_api_deactivate_license(verbose=False):
    completed = _run(["activate", "--keyDeactivate"], verbose=verbose)

    notyet = "Product not yet activated"
    limit_reached = "The license has reached it's allowed deactivations limit"

    if limit_reached in completed.stderr:
        raise ValueError(limit_reached)
    if notyet in completed.stdout:
        logging.info(notyet)
        return
    if completed.returncode != 0:
        raise ValueError("Deactivation failed")

    old_key = completed.stdout.split("Key released: ")[1].split("\n")[0]
    logging.info("Deactivation successful - license key %s is released", old_key)


def local_api_get_license_summary(verbose=False):
    return _license_info(_run(["activate", "--licenseSummary", "--json"], verbose=verbose))


def local_api_show_license(verbose=False):
    for name, value in local_api_get_license_summary(verbose).items():
        print(f"{name}: {value}")


# --------------------------------------------------------------------------------------
# Calculation
# --------------------------------------------------------------------------------------


def local_api_calculate(model: Model, dataset_ids=None, cache_path=None, verbose=False):
    working_directory = os.getcwd()

    if dataset_ids is not None:
        for dataset_id in dataset_ids:
            if dataset_id not in model._get_datasets():
                raise ValueError(f"The model does not have a dataset {dataset_id}")
        data_json = model._ds_to_json(dataset_ids)
    else:
        # No ids given: every dataset in the model is calculated.
        data_json = model._ds_to_json()

    with tempfile.TemporaryDirectory() as tempdir:
        model_path = os.path.join(tempdir, data_json[0]["id"] + "_model.cmpx")
        data_path = os.path.join(tempdir, data_json[0]["id"] + "_dataset.json")

        model.save_to_file(model_path, strip_data=True)
        with open(data_path, "w") as outfile:
            json.dump(data_json, outfile)

        out_path = cache_path or os.path.join(tempdir, data_json[0]["id"] + "_output.json")

        args = ["calculate", "--model", model_path, "--out", out_path, "--data", data_path]
        if cache_path is not None:
            args.append("--use-cache")

        completed = _run(args, working_directory=working_directory, verbose=verbose)
        if completed.returncode != 0:
            raise ValueError("Calculation failed")

        model._import_results(out_path)

    logging.info(
        "The calculation is completed, the dataset in the model now contains new "
        "calculation results"
    )


def local_api_sensitivity_analysis(model: Model, sens_config, verbose=False):
    def _results_to_dotdict(results):
        dot_results = dotdict(results)
        for key in ("tables", "responseCurveGraphs", "tornadoGraphs"):
            for index, entry in enumerate(dot_results[key]):
                dot_results[key][index] = dotdict(entry)
        dot_results.sensitivityConfig = dotdict(dot_results.sensitivityConfig)
        return dot_results

    working_directory = os.getcwd()

    with tempfile.TemporaryDirectory() as tempdir:
        model_path = os.path.join(tempdir, "model.cmpx")
        config_path = os.path.join(tempdir, "sens_config.json")
        out_path = os.path.join(tempdir, "output.json")

        model.save_to_file(model_path)
        with open(config_path, "w") as outfile:
            json.dump(sens_config, outfile)

        completed = _run(
            ["sensitivity", "--model", model_path, "--out", out_path, "--config", config_path],
            working_directory=working_directory,
            verbose=verbose,
        )
        # Checked on the exit code rather than on stderr being non-empty: the JVM writes
        # ordinary progress and warnings there, so the old test failed runs that had in
        # fact succeeded.
        if completed.returncode != 0:
            raise ValueError("Sensitivity analysis failed")

        with open(out_path) as handle:
            return _results_to_dotdict(json.loads(handle.read()))
