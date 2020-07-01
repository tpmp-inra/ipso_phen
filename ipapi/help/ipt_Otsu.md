# Otsu

## Description

Thresholds image using Otsu binarization<br>**Real time**: True

## Usage

- **Threshold**: Creates a mask that keeps only parts of the image

## Parameters

- Select source file type (source_file): no clue (default: source)
- Channel (channel): (default: h)
- Invert mask (invert_mask): Invert result (default: 0)
- Build mosaic (build_mosaic): If true source and result will be displayed side by side (default: 0)
- Median filter size (odd values only) (median_filter_size): (default: 0)
- Morphology operator (morph_op): (default: none)
- Kernel size (kernel_size): (default: 3)
- Kernel shape (kernel_shape): (default: ellipse)
- Iterations (proc_times): (default: 1)
- Overlay text on top of images (text_overlay): Draw description text on top of images (default: 0)

## Example

### Source

![Source image](images/arabido_sample_plant.jpg)

### Parameters/Code

Default values are not needed when calling function

```python
from ipapi.ipt import call_ipt

mask = call_ipt(ipt_id="IptOtsu",
                source="arabido_sample_plant.jpg",
                channel='b')
```

### Result

![Result image](images/ipt_Otsu.jpg)
