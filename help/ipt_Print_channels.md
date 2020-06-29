# Print channels

## Description

Print channels<br>**Real time**: True

## Usage

- **Visualization**: Visualization tools

## Parameters

- Channel (channel): (default: h)
- Normalize channel (normalize): (default: 0)
- Median filter size (odd values only) (median_filter_size): (default: 0)
- Overlay text on top of images (text_overlay): Draw description text on top of images (default: 0)

## Example

### Source

![Source image](images/tomato_sample_plant.jpg)

### Parameters/Code

Default values are not needed when calling function

```python
from ipapi.ipt import call_ipt

call_ipt(ipt_id="IptPrintChannels",
         source="tomato_sample_plant.jpg",
         normalize=1)
```

### Result

![Result image](images/ipt_Print_channels.jpg)
