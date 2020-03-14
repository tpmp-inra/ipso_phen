call ipso_env\Scripts\pip-licenses.exe --format=html > licenses.html
call pip freeze > requirements.txt

if [%1]==[no_ver] (
    .\ipso_env\Scripts\activate.bat && python .\tools\remove_version_numbers.py && .\ipso_env\Scripts\deactivate.bat
) else (
    ECHO [%1]
)
