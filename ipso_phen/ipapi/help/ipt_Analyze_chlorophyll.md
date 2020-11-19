# Analyze chlorophyll

## Description

Analyses chlorophyll data and returns mean and standard deviation.<br>
Needs a mask as an input.<br>
Normally used in a pipeline after a clean mask is created.<br>

**Real time**: Does not apply

## Usage

- **Feature extraction**: Tools to extract features from a segmented image

## Parameters

- chlorophyll_mean (chlorophyll_mean): (default: 1)
- chlorophyll_std_dev (chlorophyll_std_dev): (default: 1)
- Select pseudo color map (color_map): (default: c_2)
- Debug image background (background): (default: bw)

---

## Example

### Source

![Source image](images/arabido_sample_plant.jpg)

### Parameters/Code

Default values are not needed when calling function

```python
from ipapi.ipt import call_ipt

dictionary = call_ipt(ipt_id="IptAnalyzeChlorophyll",
                      source="arabido_sample_plant.jpg",
                      )
```

### Result image

![Result image](images/ipt_Analyze_chlorophyll.jpg)

### Result data

|         key         |       Value        |
| :-----------------: | :----------------: |
|  chlorophyll_mean   | 94.09068824939581  |
| chlorophyll_std_dev | 21.918805417490592 |
