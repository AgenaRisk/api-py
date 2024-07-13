#!/bin/bash

PYTHON_BIN=$( command -v python3 )
if [ -z "$PYTHON_BIN" ]
then
    PYTHON_BIN=$( command -v python )
fi

LIBS=('wheel' 'twine')
for LIB in ${LIBS[@]}; do
    $PYTHON_BIN -c "import $LIB"
    if [ "$?" -gt 0 ]
    then
        echo "Installing missing $LIB"
        $PYTHON_BIN -m pip install --upgrade pip
        $PYTHON_BIN -m pip install $LIB
    fi
done

$PYTHON_BIN setup.py sdist bdist_wheel

API_TOKEN=$(cat ./.local/credentials.json | jq -jr '.publish_token')

$PYTHON_BIN -m twine upload -u __token__ -p "$API_TOKEN" --repository-url https://upload.pypi.org/legacy/ dist/*
