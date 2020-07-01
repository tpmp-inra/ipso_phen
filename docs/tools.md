# Tools overview by category

!!! info
    Some tools may be in more than one category  
## Ancillary

Tools mostly used inside other tools

### Edge detectors

Performs edge detection with various common operators.  
Mostly used by other tools.  
Details [here](ipt_Edge_detectors.md)

## Assert...

Assert something, returns wether or not assertion is passed

### Assert mask position

Check that the mask intersects with a named ROI  
Details [here](ipt_Assert_mask_position.md)

### Check source image

Checks image and returns error if something is wrong.  
Details [here](ipt_Check_source_image.md)

## Clustering

Clustering tools

### Felsenszwalb

From scikit-image: Computes Felsenszwalb’s efficient graph based image segmentation.  
Details [here](ipt_Felsenszwalb.md)

### Quick shift

From scikit-image: Quick shift segments image using quickshift clustering in Color-(x,y) space.  
Details [here](ipt_Quick_shift.md)

### Slic

From scikit-image: Segments image using k-means clustering in Color-(x,y,z) space.  
Details [here](ipt_Slic.md)

## Create an ROI

Create a ROI

### Annulus ROI

Creates annulus ROIs  
Details [here](ipt_Annulus_ROI.md)

### Circle ROI

Create circle ROIs  
Details [here](ipt_Circle_ROI.md)

### Hough circles detector

Hough circles detector: Perform a circular Hough transform.  
Can generate ROIs  
Details [here](ipt_Hough_circles_detector.md)

### ROI manager (deprecated)

Handles ROI edition via user input  
Details [here](ipt_ROI_manager_(deprecated).md)

### Rectangle ROI

Create rectangle ROIs  
Details [here](ipt_Rectangle_ROI.md)

## Demo

Demo tools, start here if you want to understand how to create/edit tools

### IPT Demo

IPT Demo (Image Processing Tool Demo)  
A simple showcase of some of the available widgets  
Best starting point if you want to build your own widgets  
Details [here](ipt_IPT_Demo.md)

## Execute default process

Execute a class pipeline linked to the selected image experiment,
    if no class pipeline is available an error will be reported

### Default process

Performs the default process associated with the experiment.  
If no default process is available, all channels will be printed.  
Details [here](ipt_Default_process.md)

## Exposure fixing

Fix image exposure, the resulting image will be used for color analysis

### Fix perspective

Fixes perspective using four dots to detect rectangle boundary.  
        Use the included threshold utility to detect the dots.  
Details [here](ipt_Fix_perspective.md)

### Image transformations

Performs various transformations on the image  
Details [here](ipt_Image_transformations.md)

### Rotate

Rotates an image according to selected angle  
Details [here](ipt_Rotate.md)

### Simple white balance

Simple white balance: Performs a simple white balance.  
https://www.ipol.im/pub/art/2011/llmps-scb/article.pdf  
Details [here](ipt_Simple_white_balance.md)

### Temperature and tint

Simple method to alter an image temperature and tint  
http://www.tannerhelland.com/5675/simple-algorithms-adjusting-image-temperature-tint/  
Details [here](ipt_Temperature_and_tint.md)

## Feature extraction

Tools to extract features from a segmented image

### Analyze bound

Analyses object bound.  
        Needs a mask as an input.  
        Normally used in a pipeline after a clean mask is created.  
          
Details [here](ipt_Analyze_bound.md)

### Analyze chlorophyll

Analyses chlorophyll data and returns mean and standard deviation   
Details [here](ipt_Analyze_chlorophyll.md)

### Analyze color

Analyses object color.  
Needs a mask as an input.  
        Normally used in a pipeline after a clean mask is created.  
Details [here](ipt_Analyze_color.md)

### Analyze object

Analyses object and returns morphologic data.  
Needs a mask as an input.  
Normally used in a pipeline after a clean mask is created.  
Details [here](ipt_Analyze_object.md)

### Heliasen Quality Control (WIP)

Needs vertical and horizontal noise removal before been called.  
        Checks light barrier image quality.  
        Outputs main error and partial errors.  
Details [here](ipt_Heliasen_Quality_Control_(WIP).md)

### Hough lines detector

Use the OpenCV functions HoughLines and HoughLinesP to detect lines in an image.  
Details [here](ipt_Hough_lines_detector.md)

### Image statistics

Displays image color statistics  
Details [here](ipt_Image_statistics.md)

### Observation data

Returns observation data retrieved from the image file  
Details [here](ipt_Observation_data.md)

## Image generator

Creates one or more images from a selected image

### Augment data

Copies image to target folder after modifying it  
        Can have a ROI as a pre-processor  
Details [here](ipt_Augment_data.md)

### Copy or rename image

Copies an image, renaming it if needed  
Details [here](ipt_Copy_or_rename_image.md)

## Image info

Gives info about current image

### Hough lines detector

Use the OpenCV functions HoughLines and HoughLinesP to detect lines in an image.  
Details [here](ipt_Hough_lines_detector.md)

## Mask cleanup

Cleans a coarse mask generated by threshold tools

### Apply ROI

Apply selected ROI to image/mask  
ROI can be of type "keep", "delete", "erode", "dilate", "open", "close"  
 Select correct IO type for pipeline use  
Details [here](ipt_Apply_ROI.md)

### Clean horizontal noise

Removes noise in the form of horizontal lines from masks.  
Used with light barriers  
Details [here](ipt_Clean_horizontal_noise.md)

### Clean horizontal noise (Hough method)

Removes noise in the form of horizontal lines from masks using Hough transformation.  
Used with light barriers  
Details [here](ipt_Clean_horizontal_noise_(Hough_method).md)

### Fill mask holes

Fills holes in mask  
Details [here](ipt_Fill_mask_holes.md)

### Keep Biggest Contours

Keeps the contours inside the biggest one.  
Needs to be part of a pipeline where a mask has already been generated  
Details [here](ipt_Keep_Biggest_Contours.md)

### Keep countours near ROIs

Keep big contours inside a series of ROIs.  
Small contours inside ROIs may be added on conditions.  
Contours outsside ROIs may be added to root contours if close enough  
Details [here](ipt_Keep_countours_near_ROIs.md)

### Keep linked Contours

Keeps contours related to the main object, removes the others.  
Needs to be part of a pipeline where a mask has already been generated  
Details [here](ipt_Keep_linked_Contours.md)

### Morphology

Morphology: Applies the selected morphology operator.  
Needs to be part of a pipeline where a mask has already been generated  
Details [here](ipt_Morphology.md)

### Remove plant guide

Removes plant guide. Built for Heliasen light barrier  
Details [here](ipt_Remove_plant_guide.md)

### Skeletonize

Skeletonize: Thins the input mask to one pixel width lines.  
Input needs to be a binary mask.  
Details [here](ipt_Skeletonize.md)

## Pre processing

Transform the image to help segmentation, 
    the image may not retain it's 
    properties. Changes here will be ignored when extracting features

### Apply ROI

Apply selected ROI to image/mask  
ROI can be of type "keep", "delete", "erode", "dilate", "open", "close"  
 Select correct IO type for pipeline use  
Details [here](ipt_Apply_ROI.md)

### CLAHE

Contrast Limited Adaptive Histogram Equalization (CLAHE).  
Equalizes image using multiple histograms  
Details [here](ipt_CLAHE.md)

### Channel mixer

Creates an new image by combining 3 channels from of the color spaces available.  
Details [here](ipt_Channel_mixer.md)

### Channel operation

Performs arithmetic operation between up to 3 channels  
Details [here](ipt_Channel_operation.md)

### Channel subtraction

Creates a new channel by subtracting one channel to another.  
Details [here](ipt_Channel_subtraction.md)

### Check exposure

Displays over/under exposed parts of the image  
Also displays average brightness of the image  
Details [here](ipt_Check_exposure.md)

### Custom channels

Builds a mask or a channel by comparing pixels to the average value.  
Details [here](ipt_Custom_channels.md)

### Filtering regional maxima

From scikit image - Filtering regional maxima: Perform a morphological reconstruction of an image.  
Morphological reconstruction by dilation is similar to basic morphological dilation: high-intensity values willreplace nearby low-intensity values. The basic dilation operator, however, uses a structuring element todetermine how far a value in the input image can spread. In contrast, reconstruction uses two images: a "seed"image, which specifies the values that spread, and a "mask" image, which gives the maximum allowed value ateach pixel. The mask image, like the structuring element, limits the spread of high-intensity values.Reconstruction by erosion is simply the inverse: low-intensity values spread from the seed image and arelimited by the mask image, which represents the minimum allowed value.  
Alternatively, you can think of reconstruction as a way to isolate the connected regions of an image.For dilation, reconstruction connects regions marked by local maxima in the seed image: neighboring pixelsless-than-or-equal-to those seeds are connected to the seeded region.  
Local maxima with values larger than the seed image will get truncated to the seed value.  
Details [here](ipt_Filtering_regional_maxima.md)

### Fix perspective

Fixes perspective using four dots to detect rectangle boundary.  
        Use the included threshold utility to detect the dots.  
Details [here](ipt_Fix_perspective.md)

### Horizontal line remover

Horizontal line remover.  
Developped for Heliasen light barrier.  
Removes horizontal noise lines  
Details [here](ipt_Horizontal_line_remover.md)

### Image from distances

Build an image from distance calculation  
Details [here](ipt_Image_from_distances.md)

### Image transformations

Performs various transformations on the image  
Details [here](ipt_Image_transformations.md)

### K-means clustering

Performs k-means clustering, grouping object with a distance formula  
Details [here](ipt_K-means_clustering.md)

### Otsu merger

Based on Otsu's binarization, create a new image from OTSU channel binarization.  
Details [here](ipt_Otsu_merger.md)

### Partial posterizer

Replaces dominant colors by other colors  
Details [here](ipt_Partial_posterizer.md)

### Pyramid mean shift

Pyramid mean shift: A kind of posterization  
Details [here](ipt_Pyramid_mean_shift.md)

### Rotate

Rotates an image according to selected angle  
Details [here](ipt_Rotate.md)

### Simple white balance

Simple white balance: Performs a simple white balance.  
https://www.ipol.im/pub/art/2011/llmps-scb/article.pdf  
Details [here](ipt_Simple_white_balance.md)

### Temperature and tint

Simple method to alter an image temperature and tint  
http://www.tannerhelland.com/5675/simple-algorithms-adjusting-image-temperature-tint/  
Details [here](ipt_Temperature_and_tint.md)

## Threshold

Creates a mask that keeps only parts of the image

### Adaptive threshold

Perform a adaptive threshold.  
Morphology operation can be performed afterwards  
Details [here](ipt_Adaptive_threshold.md)

### Chan Vese

From scikit-image: Chan-Vese segmentation algorithm.  
Active contour model by evolving a level set.  
Can be used to segment objects without clearly defined boundaries.  
  
Details [here](ipt_Chan_Vese.md)

### Dummy threshold (WIP)

Dummy threshold.  
        Pass through threshold, expects binary mask as entry  
Details [here](ipt_Dummy_threshold_(WIP).md)

### Multi range threshold

Performs range threshold keeping only pixels with values between min and max  
        for up to 3 channels.  
        Morphology operation can be performed afterwards.  
        Masks can be attached, they will be treated as keep masks  
Details [here](ipt_Multi_range_threshold.md)

### Niblack binarization

Niblack binarization: From skimage - Applies Niblack local threshold to an array.A threshold T is calculated for every pixel in the image using the following formula:T = m(x,y) - k * s(x,y)where m(x,y) and s(x,y) are the mean and standard deviation of pixel (x,y) neighborhood defined by arectangular window with size w times w centered around the pixel. k is a configurable parameter thatweights the effect of standard deviation.  
Details [here](ipt_Niblack_binarization.md)

### Otsu

Thresholds image using Otsu binarization  
Details [here](ipt_Otsu.md)

### Otsu overthinked

Based on Otsu's binarization, uses a costum set of channels.  
Details [here](ipt_Otsu_overthinked.md)

### Range threshold

Performs range threshold keeping only pixels with values between min and max.  
        Morphology operation can be performed afterwards  
Details [here](ipt_Range_threshold.md)

### Sauvola binarization

Sauvola binarization: From skimage - Applies Sauvola local threshold to an array.  
Sauvola is a modification of Niblack technique.In the original method a threshold T is calculated for every pixel in the image using the following formula:T = m(x,y) * (1 + k * ((s(x,y) / R) - 1))where m(x,y) and s(x,y) are the mean and standard deviation of pixel (x,y)neighborhood defined by a rectangular window with size w times w centered around the pixel.k is a configurable parameter that weights the effect of standard deviation. R is the maximum standard deviationof a greyscale image.  
Details [here](ipt_Sauvola_binarization.md)

### Splitted range threshold

Performs range threshold with two sets of borders applied inside and outside of linked ROIs.  
        If no ROIs are provided, all image will be considered within ROI.  
Details [here](ipt_Splitted_range_threshold.md)

### Triangle threshold

Thresholds image using triangle binarization  
Details [here](ipt_Triangle_threshold.md)

## Visualization

Visualization tools

### IPT Demo

IPT Demo (Image Processing Tool Demo)  
A simple showcase of some of the available widgets  
Best starting point if you want to build your own widgets  
Details [here](ipt_IPT_Demo.md)

### Calculate chlorophyll

  
  
Details [here](ipt_Calculate_chlorophyll.md)

### Edge detectors

Performs edge detection with various common operators.  
Mostly used by other tools.  
Details [here](ipt_Edge_detectors.md)

### Print channels

Print channels  
Details [here](ipt_Print_channels.md)

### Print color spaces

Print color spaces as individual channels or mosaics.  
Details [here](ipt_Print_color_spaces.md)

### Quick shift

From scikit-image: Quick shift segments image using quickshift clustering in Color-(x,y) space.  
Details [here](ipt_Quick_shift.md)

### ROI manager (deprecated)

Handles ROI edition via user input  
Details [here](ipt_ROI_manager_(deprecated).md)

### Rotate

Rotates an image according to selected angle  
Details [here](ipt_Rotate.md)

## White balance

Tools to help change white balance, depending on where those tools are set in the pipeline they or
    may not be ignored when extracting features

### CLAHE

Contrast Limited Adaptive Histogram Equalization (CLAHE).  
Equalizes image using multiple histograms  
Details [here](ipt_CLAHE.md)

### Fix white balance with ROI

 Fixes image white balance from ROI that is supposed to be white.  
        ROI must be present in pipeline.  
        ROIs must be of type 'keep' or 'delete'.  
        Only static ROIs are allowed.  
Details [here](ipt_Fix_white_balance_with_ROI.md)

### Simple white balance

Simple white balance: Performs a simple white balance.  
https://www.ipol.im/pub/art/2011/llmps-scb/article.pdf  
Details [here](ipt_Simple_white_balance.md)

