#!/bin/bash

echo Where is Python ?

read python_path

echo Creating environment...
$python_path -m venv ipso_env

echo Activate environment
source ./ipso_env/bin/activate

echo Updating pip... 
python -m pip install --upgrade

echo Install modules...
pip install -r requirements.txt