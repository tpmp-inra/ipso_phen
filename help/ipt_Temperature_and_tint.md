# Temperature and tint

## Description

Simple method to alter an image temperature and tint  
http://www.tannerhelland.com/5675/simple-algorithms-adjusting-image-temperature-tint/  
**Real time**: True

## Usage

- **Exposure fixing**: Fix image exposure, the resulting image will be used for color analysis
- **Pre processing**: Transform the image to help segmentation, the image may not retain it's
  properties. Changes here will be ignored when extracting features

## Parameters

- Activate tool (enabled): Toggle whether or not tool is active (default: 1)
- Clip method (clip_method): (default: clip)
- Temperature adjustment (temperature_adjustment): Adjust image temperature (default: 0)
- Tint adjustment (tint_adjustment): Adjust image tint (default: 0)
- Show over an under exposed parts (show_over_under): (default: 0)

## Example

### Source

![Source image](images/arabido_sample_plant.jpg)

### Parameters/Code

Default values are not needed when calling function

```python
from ipapi.ipt import call_ipt

image = call_ipt(
    ipt_id="IptTemperatureTint",
    source="arabido_sample_plant.jpg",
    return_type="result",
    temperature_adjustment=10,
    tint_adjustment=20
)
```

### Result

![Result image](images/ipt_Temperature_and_tint.jpg)
