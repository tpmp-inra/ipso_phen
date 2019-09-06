# Installing

Following a number of issues with OpenCV and Qt packages on windows, we recommend using pip instead of conda.

## Pip

### Windows

Follow this steps

1. Install Python minimum version 3.6 if needed - [https://www.python.org/downloads/](https://www.python.org/downloads/) during installation keep track of the folder where Python is installed and find the path to the python.exe file *PYTHON_EXE_PATH*
2. Extract/copy/clone IPSO Phen files to a new folder
3. Launch a command line shell and go to the created folder
4. Execute on the prompt: install.bat *PYTHON_EXE_PATH*
5. To launch IPSO Phen just double click on run.bat

### Linux/OSX (or Windows if previous method failed)

Follow this steps

1. Install Python minimum version 3.6 if needed - [https://www.python.org/downloads/](https://www.python.org/downloads/)  during installation keep track of the folder where Python is installed and find the path to the Python executable file *PYTHON_EXE_PATH*
2. Extract/copy/clone IPSO Phen files to a new folder
3. Open a terminal session ond go to the folder containing IPSO Phen
4. Run the following commands
   1. *PYTHON_EXE_PATH* -m venv ipso_pip_env 
   2. .\ipso_pip_env\Scripts\activate
   3. python -m pip install --upgrade pip 
   4. pip install -r requirements.txt 
   5. .\ipso_pip_env\Scripts\deactivate *(optional)*
5. To launch IPSO Phen run the following commands
   1. ./ipso_pip_env/Scripts/activate
   2. ./ipso_pip_env/Scripts/python ./main.py
   3. ./ipso_pip_env/Scripts/deactivate *(once IPSO Phen has been closed)*

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
