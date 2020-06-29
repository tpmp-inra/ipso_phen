# Installing

## Getting the source code

Source code is available from our [GitHub](https://github.com/tpmp-inra/ipso_phen). Cloning or forking the repo with git is recommended.

## Installing python

!!! warning
Following a number of issues with OpenCV and Qt packages on windows, we recommend using pip instead of conda.

Download and install python and install python, if needed, it can be found here [https://www.python.org/downloads/](https://www.python.org/downloads/). Please remember/store python's install path, we will be needing it later and we will call it PYTHON_EXE_PATH.

## [About PlantCV](https://plantcv.readthedocs.io/en/latest/)

IPSO Phen can be used to add an UI to PlantCV's tools. But since at the moment of writing this documentation PlantCV uses OpenCV 3 and IPSO Phen uses OpenCV 4 as default you will have to remove the line _opencv-contrib-python_ from _requirements.txt_ and add an additional step to the installation by typing _pip install plantcv_ into the command line/terminal.

## Creating an environment

### Windows

1. Open a command line console with windows start menu and go to the folder containing IPSO Phen.
2. Execute on the command line: install.pip.bat PYTHON_EXE_PATH.

### Linux/OSX

1. Open a terminal session ond go to the folder containing IPSO Phen.
2. Execute ./install.pip.x (you may need to execute chmod u+x install.pip.x before to turn the file into an executable).
3. When asked "_Where is Python?_" enter _PYTHON_EXE_PATH_

## Launching IPSO Phen

1. Open a terminal session ond go to the folder containing IPSO Phen.
2. Activate the environment.
   - On Windows execute _activate.bat_ on the terminal
   - On Linux/OSX execute _source ./ipso_pip_env/bin/activate_ on the terminal
3. execute _python run_qt.py_ on the terminal

On Windows you can skip all these steps and double click on the _run.bat_ file from the explorer.
