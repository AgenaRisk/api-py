#!/bin/bash

PYTHON_BIN=$( command -v python3 )
if [ -z "$PYTHON_BIN" ]
then
    PYTHON_BIN=$( command -v python )
fi

$PYTHON_BIN -m unittest discover -s ./tests -v
