# Edge detectors

## Description

Performs edge detection with various common operators.<br>Mostly used by other tools.<br>**Real time**: True

## Usage

- **Visualization**: Visualization tools
- **Ancillary**: Tools mostly used inside other tools

## Parameters

- Activate tool (enabled): Toggle whether or not tool is active (default: 1)
- Select source file type (source_file): no clue (default: source)
- Channel (channel): (default: l)
- Select edge detection operator (operator): (default: canny_opcv)
- Canny's sigma (canny_sigma): Sigma. (default: 2)
- Canny's first Threshold (canny_first): First threshold for the hysteresis procedure. (default: 0)
- Canny's second Threshold (canny_second): Second threshold for the hysteresis procedure. (default: 255)
- Kernel size (kernel_size): (default: 5)
- Threshold (threshold): Threshold for kernel based operators (default: 130)
- Apply threshold (apply_threshold): (default: 1)
- Overlay text on top of images (text_overlay): Draw description text on top of images (default: 0)

## Example

### Source

![Source image](images/arabido_sample_plant.jpg)

### Parameters/Code

Default values are not needed when calling function

```python
from ipapi.ipt import call_ipt

raw_edges = call_ipt(ipt_id="IptEdgeDetector",
                     source="arabido_sample_plant.jpg",
                     )
```

### Result

![Result image](images/ipt_Edge_detectors.jpg)
