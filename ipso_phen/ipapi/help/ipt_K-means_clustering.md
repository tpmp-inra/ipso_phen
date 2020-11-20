# K-means clustering

## Description

K-means clustering:  
Performs k-means clustering, grouping object with a distance formula

**Real time**: False

## Usage

- **Pre-processing**: Transform the image to help segmentation, the image may not retain it's properties. Changes here will be ignored when extracting features

## Parameters

- Color space (color_space):
- Cluster count (cluster_count): Number of clusters to split the set by.
- Max iterations allowed (max_iter_count): An integer specifying maximum number of iterations.
- Minium precision (Epsilon) (precision): Required accuracy
- Termination criteria - Stop when: (stop_crit):
- Centers initialization method (flags):
- Attempts (attempts): Flag to specify the number of times the algorithm is executed using different initial labelling. The algorithm returns the labels that yield the best compactness. This compactness is returned as output.
- Name of ROI to be used (roi_names): Operation will only be applied inside of ROI
- ROI selection mode (roi_selection_mode):
- Normalize histograms (normalize):

## Example

### Source

![Source image](images/tomato_sample_plant.jpg)

### Parameters/Code

Default values are not needed when calling function

```python
from ipapi.ipt import call_ipt

ret, label, center = call_ipt(ipt_id="IptKMeansClustering",
                              source="tomato_sample_plant.jpg",
                              cluster_count=6)
```

### Result

![Result image](images/ipt_K-means_clustering.jpg)
