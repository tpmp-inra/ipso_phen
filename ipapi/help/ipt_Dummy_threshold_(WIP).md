# Dummy threshold (WIP)

## Description

Dummy threshold.

        Pass through threshold, expects binary mask as entry

**Real time**: True

## Usage

- **Threshold**: Creates a mask that keeps only parts of the image

## Parameters

- Activate tool (enabled): Toggle whether or not tool is active (default: 1)

## Example

### Source

![Source image](images/18HP01U17-CAM11-20180712221558.bmp)

### Parameters/Code

Default values are not needed when calling function

```python
from ipapi.ipt import call_ipt

mask = call_ipt(
    ipt_id="IptDummyThreshold",
    source="18HP01V22-CAM11-20180720081100.jpg",
    return_type="result"
)
```

### Result

![Result image](<images/ipt_Dummy_threshold_(WIP).bmp>)
