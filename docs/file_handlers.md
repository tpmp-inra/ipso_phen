# File Handlers ( I did not name my images like yours)

!!! warning
    Moderated Python Object Oriented Programing knowledge needed below

## Default behaviors

As stated in the [user interface](user_interface.md) help page, IPSO Phen recognizes by default two file naming conventions:

- EXPERIMENT;PLANTNAME;CAMERA-VIEWOPTION;YYYY,MM,DD-HHhMMmSSs;NUMBER
- (PLANTNAME)--(YYYY-MM-DD HH_MM_SS)--(EXPERIMENT)--(CAMERA-VIEWOPTION)

If the name of the file does not follow any of these schemes, the fields will be set as follows:

- **EXPERIMENT**: Folder name
- **PLANTNAME**: File name without extension
- **CAMERA**: Unknown
- **VIEWOPTION**: File extension
- **DATETIME**: From file system

## Making IPSO Phen understand your naming convention

### Create the skeleton

Copy and rename fh_stub.py in the *file_handlers* folder. You should use a file name that is easy to identify, 'fh_' prefix is recommended. Change the class name to a unique value, no other file handler should have the same name.

### Fill the methods

Your new file should look like this:

```python
from datetime import datetime as dt

from file_handlers.fh_base import FileHandlerBase


class MyHandler(FileHandlerBase):

    def __init__(self, **kwargs):
        """ Fill plant, date, time, experiment, camera and view_option from file data
        """
        # Your code here

        self.update(**kwargs)

    @classmethod
    def probe(cls, file_path):
        """ Checks wether or not the file in file_path can be handled
        """
        # Your code here
        return 0
```

The two methods that should be completed are:

- **\_\_init__**: Extract needed info from file name or system info, see other file_handlers for an example.
- **probe**: Set which files will be handled, see other file_handlers for an example.
