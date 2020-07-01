# Filtering regional maxima

## Description

<br> From scikit image - Filtering regional maxima: Perform a morphological reconstruction of an image.<br><br> Morphological reconstruction by dilation is similar to basic morphological dilation: high-intensity values will<br> replace nearby low-intensity values. The basic dilation operator, however, uses a structuring element to<br> determine how far a value in the input image can spread. In contrast, reconstruction uses two images: a "seed"<br> image, which specifies the values that spread, and a "mask" image, which gives the maximum allowed value at<br> each pixel. The mask image, like the structuring element, limits the spread of high-intensity values.<br> Reconstruction by erosion is simply the inverse: low-intensity values spread from the seed image and are<br> limited by the mask image, which represents the minimum allowed value.<br><br> Alternatively, you can think of reconstruction as a way to isolate the connected regions of an image.<br> For dilation, reconstruction connects regions marked by local maxima in the seed image: neighboring pixels<br> less-than-or-equal-to those seeds are connected to the seeded region.<br><br> Local maxima with values larger than the seed image will get truncated to the seed value.<br>

**Real time**: False

## Usage

- **Pre-processing**: Transform the image to help segmentation, the image may not retain it's properties. Changes here will be ignored when extracting features

## Parameters

- Activate tool (enabled): Toggle whether or not tool is active (default: 1)
- Select source file type (source_file): no clue (default: source)
- Channel (channel): (default: l)
- Offset for uneven image border (brightness_offset): Use when image border perimeter has uneven brightness (default: 0)
- Overlay text on top of images (text_overlay): Draw description text on top of images (default: 0)
- Select pseudo color map (color_map): (default: c_2)
- use color palette (use_palette): Use color palette in postprocessing (default: 0)
- Normalize channel (normalize): (default: 0)
- Real time (real_time): Set if tool reacts in real time (default: 0)

---

## Example

### Source

![Source image](images/tomato_sample_plant.jpg)

### Parameters/Code

Default values are not needed when calling function

```python
from ipapi.ipt import call_ipt

image = call_ipt(ipt_id="IptRegionalMaximaFiltering",
                 source="tomato_sample_plant.jpg",
                 brightness_offset=25,
                 use_palette=1)
```

### Result

![Result image](images/ipt_Filtering_regional_maxima.jpg)
