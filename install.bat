@echo off
if [%1]==[] goto missing_param
%1 -m venv ipso_pip_env && .\ipso_pip_env\Scripts\activate.bat && python -m pip install --upgrade pip && pip install -r requirements.txt && .\ipso_pip_env\Scripts\deactivate.bat
:missing_param
echo Please indicate the path to your python.exe file
echo Exemple: install.bat C:\Users\<user_name>\AppData\Local\Programs\Python\Python37\python.exe
echo.
echo If there is a folder called "ipso_pip_env" the installation may not be needed, try running launch_me.bat