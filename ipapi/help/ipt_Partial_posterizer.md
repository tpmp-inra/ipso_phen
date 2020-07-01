# Partial posterizer

## Description

Replaces dominant colors by other colors<br>**Real time**: True

## Usage

- **Pre-processing**: Transform the image to help segmentation, the image may not retain it's properties. Changes here will be ignored when extracting features

## Parameters

- Activate tool (enabled): Toggle whether or not tool is active (default: 1)
- Color to use to replace blue dominant pixels (blue_color): Replace value of pixels where blue is dominant and represents more than % value by selected color (default: none)
- Blue channel threshold value (post_blue_value): Blue pixel value threshold (as percentage) (default: 34)
- Color to use to replace green dominant pixels (green_color): Replace value of pixels where green is dominant and represents more than % value by selected color (default: none)
- Green channel threshold value (post_green_value): Green pixel value threshold (as percentage) (default: 34)
- Color to use to replace red dominant pixels (red_color): Replace value of pixels where red is dominant and represents more than % value by selected color (default: none)
- Red channel threshold value (post_red_value): Red pixel value threshold (as percentage) (default: 34)
- Build mosaic (build_mosaic): Choose mosaic type to display (default: no)
- Overlay text on top of images (text_overlay): Draw description text on top of images (default: 0)

---

## Example

### Source

![Source image](images/tomato_sample_plant.jpg)

### Parameters/Code

Default values are not needed when calling function

```python
from ipapi.ipt import call_ipt

image = call_ipt(ipt_id="IptPartialPosterizer",
                 source="tomato_sample_plant.jpg",
                 blue_color='black',
                 post_blue_value=43)
```

### Result

![Result image](images/ipt_Partial_posterizer.jpg)
