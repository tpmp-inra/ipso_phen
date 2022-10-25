# ROI manager (deprecated)

## Description

Handles ROI edition via user input
**Real time**: True

## Usage

- **ROI (static)**: Create a ROI from coordinates
- **Visualization**: Visualization tools

## Parameters

- ROI name (roi_name): (default: unnamed_roi)
- Select action linked to ROI (roi_type): no clue (default: keep)
- Select ROI shape (roi_shape): no clue (default: rectangle)
- Target IPT (tool_target): no clue (default: none)
- Left (left): (default: 0)
- Width (Diameter for circles) (width): (default: 0)
- Top (top): (default: 0)
- Height (height): (default: 0)
- Launch ROI draw form (draw_roi): Launch OpenCV window to select a ROI (default: 0)

## Example

### Source

![Source image](images/arabido_small.jpg)

### Parameters/Code

Default values are not needed when calling function

```python
from ipapi.ipt import call_ipt

call_ipt(
    ipt_id="IptRoiManager",
    source="arabido_small.jpg",
    return_type="result",
    left=140,
    width=500,
    top=80,
    height=500
)
```

### Result

![Result image](<images/ipt_ROI_manager_(deprecated).jpg>)
