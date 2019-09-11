# Welcome to the documentation for IPSO Phen

The rise in popularity of high throughput plant phenotyping facilities leads to a large volume of images. To address the increasing demand and diversity of image analysis needs, we developed "IPSO Phen", an all-in-one program to build, test and execute image-processing pipelines by chaining easily customizable tools.

## Introduction

Toulouse Plant Microbe Phenotyping (TPMP) is a high throughput platform located on the INRA Occitanie-Toulouse campus in France. It has five camera groups in two robots settings taking pictures from the top or the side of the plant. Species studied to date have been *Marchantia*, *Arabidopsis*, *Medicago*, Tomato, Tobacco, Sunflower, Eucalyptus, Wheat and *Brachypodium*. This large amount of possible combinations generated the need for a tool to create, test and run analysis pipelines. After evaluating the software tools freely available, we created IPSO Phen, an all-in-one image processing toolbox.
IPSO Phen groups in a single interface around fifty different image-processing tools that can be combined into pipelines. The settings of both tools and pipelines can be thoroughly tested on fixed or random sets of images from the experiments. IPSO Phen can access images either from a file system or through a database.

## [Image processing tools](tools.md)

![Image processing tool](images/md_image_2.jpg)
IPSO Phen comes with a variety of image-processing tools that belong to different categories such as pre-processing, threshold, segmentation, feature extraction, etc… Each tool generates its own interface to customize and test its settings.  
Among the available tools, there is an image pre-processor based on Otsu’s  automatic clustering-based threshold method, various classic threshold methods and an advanced contour cleaning tool able to remove noise while keeping split contours.  
Each tool can be used directly in a Python script by copying and pasting the code generated in the "code" tab next to the "Help" tab.

## [Testing](testing.md)

At any point, the user can choose to test the current tool or pipeline configuration on any number of images with a single click. Test images can be selected manually, taken from a saved selection or randomly, or, any combination of these three methods. The results of the test can be accessed with a combo box or saved as a video to be reviewed later. This feature facilitates a large number of tests, which in turn will improve the quality of the analysis.

## [Grid search](grid_search.md)

The grid search allows the exploration of a whole solution space defined by a customized range for each setting. It is an easy way to check a large amount of settings with just one click. The results  can be reviewed on the user interface or be converted into a video.

## [Pipelines](pipelines.md)

The user can arrange any number of image processing tools into a customizable pipeline (Image below) that can be fully edited, saved and restored for later usage. Before executing the pipeline (IPSO Phen supports parallel execution) the user may select which features to extract from images. Once the process ends, IPSO Phen generates a CSV file.

## Advanced features

### [Script pipelines](pipelines.md)

For advanced Python users there is also the possibility to generate fully functional Python script reproducing the behavior of the pipeline, this allows customization in any way needed.

### [Class pipelines](class_pipelines.md)

Also for advanced python users. Class pipelines can be automatically selected by the program when using the default tool. They allow the same level of customization than script pipelines.

### [Adding tools](custom_tools.md)

Even if IPSO Phen comes with a large (and expanding) set of image processing tools, some users may want to add additional tools that they have created or from an existing toolkit like PlantCV [1]. To that end, we offer an easy way to create or add tools to the user interface (UI) where widgets are added in a descriptive way and all callbacks and notifications are handled by the program.

### [File handlers](file_handlers.md)

By default IPSO Phen extracts the information needed for image managing from the file name as seen on the [user interface section](user_interface.md).
