# Default process

## Description

Performs the default process associated with the experiment.<br>
If no default process is available, all channels will be printed.<br>

**Real time**: False

## Usage

- **Execute default process**: Execute a class pipeline linked to the selected image experiment, if no class pipeline is available an error will be reported

## Parameters

- Threshold only (threshold_only): Do not extract data, just build the mask (default: 0)
- Horizontal boundary position (boundary_position): Bondary position, used to calculate above and underground data (default: -1)
- Build mosaic (build_mosaic): Build mosaic showing the process steps (default: none)
- Channel (channel): Select channel for pseudo color image (default: h)

## Example

### Source

![Source image](images/tomato_sample_plant.jpg)

### Parameters/Code

Default values are not needed when calling function

```python
from ipapi.ipt import call_ipt

mask = call_ipt(ipt_id="IptDefault",
                source="(TomatoSamplePlant)--(2019-07-04 10_00_00)--(TomatoSampleExperiment)--(vis-side0).jpg",
                )
```

### Result

![Result image](images/ipt_Default_process.gif)
