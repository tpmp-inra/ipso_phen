# Install

### System requirements

 IPSO Phen has been tested on:

- Linux: Ubuntu 18.04+
- Windows 10,11
- Mac OSX 14

### Requirements

#### Conda
- https://docs.anaconda.com/free/miniconda/

#### PlantCV (optional)

If you want to use IPSO Phen with PlantCV, you must install it from the source code and modify *requirements.txt* so it installs OpenCV v3 instead of v4.


### Dependencies

Python, 3.8+.  
Python packages:

- numpy
- opencv-contrib-python
- pandas
- paramiko
- psutil
- psycopg2-binary
- PySide2
- scikit-image
- scikit-learn
- seaborn
- SQLAlchemy
- SQLAlchemy-Utils
- tqdm
- Unidecode


### Install from source

Source code is available from: <https://github.com/tpmp-inra/ipso_phen>  
Install on an existing python environment with command line:

```shell
conda env create -f environment.yml
```
