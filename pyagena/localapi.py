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


def _output(completed):
    """
    Everything the engine printed, both streams.

    From engine 2.0.1, `--json` keeps stdout to a single line of JSON and moves the
    banner and the operation's own prose to stderr. Anything looking for a phrase has to
    read both, or it will silently stop matching against a newer engine while continuing
    to work against an older one.
    """
    return (completed.stdout or "") + (completed.stderr or "")


def _result(completed):
    """
    The JSON result line a ``--json`` licensing operation prints, or None.

    From engine 2.0.1 every licensing operation ends by printing one line: the licence
    summary, plus ``operation`` and — when the engine had something to say — ``messages``.
    Earlier engines print such a line only for ``--licenseSummary``, which is why callers
    here treat its absence as "ask separately" rather than as a failure: a published
    client has to keep working against the 2.0.0 that may already be installed.

    The last parseable line wins. Core also prints an indented summary of its own, but
    that spans several lines and so never matches — which is precisely the bug this
    replaced, where a successful activation was read as "no summary returned".
    """
    for line in reversed((completed.stdout or "").splitlines()):
        line = line.strip()
        if not (line.startswith("{") and line.endswith("}")):
            continue
        try:
            parsed = json.loads(line)
        except ValueError:
            continue
        # Keep looking unless it is actually a JSON object. A line can parse and still be
        # the wrong shape - `{}` from a failed summary, or a stray fragment - and handing
        # a list or a string back to a caller expecting `.get()` turns a recoverable miss
        # into an AttributeError three frames away.
        if isinstance(parsed, dict) and parsed:
            return parsed
    return None


def _license_info(completed):
    """As :func:`_result`, but for callers that require a summary."""
    result = _result(completed)
    if result is None:
        # Quote what did arrive: with no JSON on stdout the interesting part is whatever
        # the engine said instead, and it is usually on stderr.
        detail = (_output(completed) or "").strip().splitlines()
        raise ValueError(
            "The engine did not return a license summary"
            + (": " + detail[-1] if detail else "")
        )
    return result


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
    completed = _run(["activate", "--keyActivate", "--key", key, "--json"], verbose=verbose)

    already = "Product already activated"
    if already in _output(completed):
        logging.info(already)
        return

    # The engine's own account of what happened, when it gives one. Older engines do not,
    # so the state is checked separately below either way.
    result = _result(completed)
    messages = (result or {}).get("messages") or []
    for message in messages:
        logging.info(message)

    summary = result if result is not None else local_api_get_license_summary(verbose)
    if summary.get("Mode") == "FreeTrial" or completed.returncode != 0:
        raise ValueError(
            "Licence key activation failed" + (": " + "; ".join(messages) if messages else "")
        )
    logging.info("License key activated successfully")


def local_api_deactivate_license(verbose=False):
    completed = _run(["activate", "--keyDeactivate", "--json"], verbose=verbose)

    notyet = "Product not yet activated"
    limit_reached = "The license has reached it's allowed deactivations limit"

    output = _output(completed)
    if limit_reached in output:
        raise ValueError(limit_reached)
    if notyet in output:
        logging.info(notyet)
        return
    if completed.returncode != 0:
        raise ValueError("Deactivation failed")

    for message in (_result(completed) or {}).get("messages") or []:
        logging.info(message)
    logging.info("Deactivation successful - the license key is released")


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
