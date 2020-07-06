call ..\env\Scripts\pip-licenses.exe --format=html > ..\extra\licenses.html
call pip freeze > ..\requirements.txt

if [%1]==[no_ver] (
    ..\env\Scripts\activate.bat && python remove_version_numbers.py
) else (
    ECHO [%1]
)
