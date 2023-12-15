import logging

def set_verbose(verbose = False):
    if verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.ERROR)

def include_timestamp(include = False):
    if include:
        logging.basicConfig(
            force=True,
            format='%(asctime)s %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S%z')
    else:
        logging.basicConfig(
            force=True,
            format='%(message)s')
        