@echo off
if [%1]==[] goto missing_param
%1 -m venv env && .\env\Scripts\activate.bat && python -m pip install --upgrade pip && pip install -r requirements.txt

:missing_param
echo Please indicate the path to your python.exe file
echo Exemple: install.bat C:\Users\<user_name>\AppData\Local\Programs\Python\Python37\python.exe
echo.
echo If there is a folder called "env" the installation may not be needed, try running launch_me.bat