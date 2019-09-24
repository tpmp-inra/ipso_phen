# Getting the source code

Source code is available from our [GitHub](https://github.com/tpmp-inra/ipso_phen)

# Installing

!!! warning
    Following a number of issues with OpenCV and Qt packages on windows, we recommend using pip instead of conda.

## Pip

### Windows

Follow this steps

1. Install Python minimum version 3.6 if needed - [https://www.python.org/downloads/](https://www.python.org/downloads/) during installation keep track of the folder where Python is installed and find the path to the python.exe file *PYTHON_EXE_PATH*
2. Extract/copy/clone IPSO Phen files to a new folder
3. Launch a command line shell and go to the created folder
4. Execute on the prompt: install.bat *PYTHON_EXE_PATH*
5. To launch IPSO Phen just double click on run.bat

### Linux/OSX

Follow this steps

1. Install Python minimum version 3.6 if needed - [https://www.python.org/downloads/](https://www.python.org/downloads/)  during installation keep track of the folder where Python is installed and find the path to the Python executable file *PYTHON_EXE_PATH*
2. Extract/copy/clone IPSO Phen files to a new folder
3. Open a terminal session ond go to the folder containing IPSO Phen
4. Execute ./install.pip.x (you may need to execute chmod u+x install.pip.x before to turn the file into an executable)
5. When asked "*Where is Python?*" enter *PYTHON_EXE_PATH*
6. To launch IPSO Phen just double click on run.pip.x (you may need to execute chmod u+x run.pip.x before to turn the file into an executable)

## Conda

### Windows

Follow this steps

1. Install Miniconda if needed - [https://docs.conda.io/en/latest/miniconda.html](https://docs.conda.io/en/latest/miniconda.html) 64bits version
2. Extract/copy IPSO Phen files to a new folder
3. Launch Anaconda prompt from the start menu
4. From the prompt go to the IPSO Phen folder
5. Execute on the prompt: conda env create -f environment.yml
6. If any question is asked answer "y"
7. Execute on the prompt: activate ipso_phen_env
8. Execute on the prompt: python main.py

### Linux/OSX (or Windows if previous method failed)

Follow this steps

1. Install Miniconda if needed - [https://docs.conda.io/en/latest/miniconda.html](https://docs.conda.io/en/latest/miniconda.html) 64bits version
2. Extract/copy IPSO Phen files to a new folder
3. Launch Anaconda prompt and
4. Create a new environment: conda create --name ipso_phen_env
5. Activate environment: conda activate ipso_phen_env
6. Install the following packages by executing the commands after the column on the conda prompt
    - **OpenCV**: conda install -c conda-forge opencv 
    - **scikit-learn**: conda install -c anaconda scikit-learn
    - **scikit-image**: conda install -c anaconda scikit-image
    - **pyqt**: conda install -c anaconda pyqt
    - **paramiko**: conda install -c anaconda paramiko
    - **psutil**: conda install -c anaconda psutil
    - **psycopg2**: conda install -c anaconda psycopg2
    - **pandas**: conda install -c anaconda pandas
    - **sqlalchemy**: conda install -c anaconda sqlalchemy
    - **sqlalchemy-utils**: conda install -c conda-forge sqlalchemy-utils
    - **pyyaml**: conda install -c anaconda pyyaml
    - **mkdocs**: conda install -c conda-forge mkdocs
    - **mkdocs-material**: conda install -c conda-forge mkdocs-material
    - **unidecode**: conda install -c anaconda unidecode

## PlantCV

!!! warning
    At the moment of writing this documentation I could not install PlantCV with pip, only the conda method worked.

If you want to use PlantCV you will have to install it. If PlantCV is installed all available PlantCV tools will be loaded when the program starts.  
Please go to their documentation page fond here: [https://plantcv.readthedocs.io/en/stable/](https://plantcv.readthedocs.io/en/stable/)
