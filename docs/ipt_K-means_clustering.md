# K-means clustering
## Description
Performs k-means clustering, grouping object with a distance formula<br>**Real time**: False
## Usage
- **Pre-processing**: Transform the image to help segmentation, the image may not retain it's properties. Changes here will be ignored when extracting features
## Parameters
- Color space (color_space): no clue (default: HSV)
- Cluster count (cluster_count):  (default: 3)
## Example
### Source
![Source image](images/tomato_sample_plant.jpg)

### Parameters/Code
Default values are not needed when calling function
```python
from ip_tools import call_ipt

ret, label, center = call_ipt(ipt_id="IptKMeansClustering",
                              source="tomato_sample_plant.jpg",
                              cluster_count=6)
```
### Result
![Result image](images/ipt_K-means_clustering.jpg)
