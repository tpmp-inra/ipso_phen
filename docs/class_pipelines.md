# Class pipelines (taking full control)

!!! warning
    Python Object Oriented Programing knowledge needed below

There's another way to build pipelines that needs Python and Object Oriented Programming knowledge: Class pipelines. The main advantage of class pipelines is that can be associated with a particular experiment or group of images and be executed without loading it.  
When the pipeline processor is set in default mode, it will parse class pipelines to see if one can handle the current image, if one is found, the image will be processed, if not the analysis will fail.

## Steps to create a class pipeline

!!! warning
    Before creating your awn tools set  
    ```python
    USE_PROCESS_THREAD = False
    ```  
    in *ui_consts.py*.
    Otherwise you will not be able to debug your tool

1. Copy and rename *ip_stub.py* from the class_pipeline folder. The name should start with "ip_"
2. Set the class name to a unique value, no other class pipeline should have the same value, I tend to turn the file name into camel case for this.
3. Use the help/docstrings in the file to fill the methods.
4. Test your class

!!! hint
    Try to be strict in the *can_process* method so your class won't catch unwanted images.

!!! warning "DO NOT FORGET"
    ```python
    USE_PROCESS_THREAD = True
    ```  
    After you've finished editing.
