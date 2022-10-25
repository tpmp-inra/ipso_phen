# Heliasen Quality Control (WIP)

## Description

Needs vertical and horizontal noise removal before been called.

        Checks light barrier image quality.

        Outputs main error and partial errors.

**Real time**: False

## Usage

- **Feature extraction**: Tools to extract features from a segmented image

## Parameters

- Activate tool (enabled): Toggle whether or not tool is active (default: 1)

## Example

### Source

![Source image](images/18HP01V22-CAM11-20180720081100.bmp)

### Parameters/Code

Default values are not needed when calling function

```python
from ipapi.ipt import call_ipt

call_ipt(
    ipt_id="IptHeliasenQualityControl",
    source="18HP01V22-CAM11-20180720081100.jpg",
    return_type="result"
)
```

### Result image

![Result image](<images/ipt_Heliasen_Quality_Control_(WIP).jpg>)

### Result data

|               key               |                                       Value                                        |
| :-----------------------------: | :--------------------------------------------------------------------------------: |
|        hor_lines_removed        |                                         21                                         |
|       hor_pixels_removed        |                                         0                                          |
|   hor_lines_removed_hit_plant   |                                         8                                          |
|   expected_plant_top_position   |                                        251                                         |
|       vert_lines_removed        |                                         3                                          |
|       vert_pixels_removed       |                                        202                                         |
|       plant_top_position        |                                        251                                         |
| horizontal_lines_hard_to_remove |                                         0                                          |
|    final_plant_top_position     |                                        245                                         |
|        guide_only_pixels        |                                        1332                                        |
|      guide_average_pixels       |                                 5.620253164556962                                  |
|       guide_average_span        |                                 5.620253164556962                                  |
|       plant_bottom_error        |                                         0                                          |
|          leaning_error          |                                         0                                          |
|            hrz_error            |                                         3                                          |
|           guide_error           |                                         0                                          |
|         plant_top_error         |                                         0                                          |
|           error_level           |                                         3                                          |
|             report              | - Horizontal noise: Noise level critical (1 line per (46.75)), please clean sensor |
|             report              |       - Horizontal noise: 13 detected outside of plant, please clean sensor        |
