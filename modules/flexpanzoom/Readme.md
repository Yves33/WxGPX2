FlexPanZoom
===========
A alternate (flexible) pan zoom system for matplotlib axis.  

1 - Features:
=============
- drag x/y axis to pan
- mouse wheel in x/y axis to zoom in / zoom out
- right click on x/y axis to display popup for zoom in / zoom out
- support for iconfonts

2 - Restrictions:
=================
- cartesian axes only (zoom on polar axes)
- no support for log scale

3 - Usage:  
==========
```
import matplotlib.pyplot as plt
import numpy as np

fig = plt.figure()
plt.plot([0, 1, 3, 6, 7, 4, 2, 0])
panzoomer = PanZoomFactory(fig)
plt.show()
```
