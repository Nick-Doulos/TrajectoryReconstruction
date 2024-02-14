Trajectory Reconstruction Module
=========

The Trajectory Reconstruction Module, is a cutting-edge solution designed to tackle the prevalent issue of accuracy in map-matching processes, particularly those affected by low GPS sampling rates. This module is a comprehensive assembly of sophisticated spatial analysis algorithms, including Curve Interpolation, Trajectory Refinement, and Trajectory Combination. These components work in synergy to significantly enhance map-matched trajectories produced by advanced map-matching algorithms like Valhalla's Meili, among others, incorporating all original data points to ensure no critical information is lost.


Components                                          
---
* **Trajectory Refinement**: Improves trajectory’s accuracy and detail via road networks by transforming the GPS points of a trajectory into road objects, enabling computations that allow for interpolation at crucial network points (such as the apex of a turn, and changes in the route), thereby smoothing out the trajectory and preserving its spatiotemporal integrity.
* **Curve Interpolation:** Employs bearing calculations to detect significant directional changes, using a threshold-based approach to identify curves within the trajectory. The algorithm performs interpolation in these selected curves, adding intermediate points to represent the trajectory more accurately, considering the Earth's curvature.
* **Trajectory Combination:** Improves the accuracy of a repeatable trajectory (like a bus route), by merging multiple trajectories that take place in the same route and sorting each trajectory point based on its geographical proximity, thus ensuring that the merged trajectory is organized in a logical and spatially coherent manner.

Input and Output Specifications
---
The Trajectory Reconstruction Module is adept at processing and enhancing trajectory data through a unified approach, utilizing a standardized **Pandas DataFrame** format for both input and output, ensuring extensive compatibility and user convenience. Inputs to the module require a DataFrame with columns designated for **timestamp**, **latitude**, and **longitude**, where each row signifies a distinct point in the vehicle's journey, effectively mapping its temporal and spatial progression. As data traverses the Curve Interpolation, Trajectory Refinement, and Trajectory Combination components of the module, it emerges as an enhanced DataFrame. This augmented version maintains the original data structure while integrating improvements such as precise coordinate adjustments, smooth interpolated points, and logically sequenced data points, culminating in a trajectory depiction that is significantly more accurate, detailed, and coherent. This methodology not only simplifies integration across various data processing environments but also ensures the fidelity of the original temporal and spatial information.

Trajectory Refinement Component
=========

Features
---------
* **Road Network Integration:** Leverages road network data to anchor GPS points to the most probable roads, enhancing the realism and accuracy of trajectories.
* **Intelligent Interpolation:** Performs interpolation at key points within the network, such as turns or route changes, ensuring a natural and accurate path.
* **Spatiotemporal Integrity:** Maintains the temporal sequence and spatial continuity of the trajectory, crucial for dynamic and time-sensitive applications.
* **Off Road Points Removal:** Using the road network, this feature may identify GPS locations that are not over a road and remove them for increased accuracy.

Dependencies
---

* Python 3.x
* NumPy: For numerical operations.
* Pandas: For data manipulation and analysis.
* OSMnx: For handling road network graphs.
* Shapely: For geometric operations.

Configuration Options
---
* **Off Road Points Removal:** The *delete_off_road_points* variable has boolean type, so it can be set to True or Flase, depending on the user's preference.

Getting Started
---
Ensure that you have the trajectory data in the format we previously discussed in order to use the Trajectory Refinement component.

```python
from refine import TrajectoryRefiner

# Initialize the refiner with your desired settings
refiner = TrajectoryRefiner(delete_off_road_points=True)

# Refine a trajectory
refined_trajectory = refiner.refine_trajectory(gps_trajectory_data)
```
<br />
<br />

Curve Interpolation Component
===

Features
---
* **Bearing-Based Curve Detection:** Identifies significant directional changes in the trajectory, highlighting areas that require interpolation.
* **Threshold-Based Curve Identification:** Utilizes configurable thresholds to determine which directional changes constitute a curve, allowing for customizable sensitivity.
* **Geospatially Aware Interpolation:** Considers the Earth's curvature in the interpolation process, ensuring geospatial accuracy in the enhanced trajectory.

Dependencies
---
* Python 3.x
* NumPy: For efficient numerical computations.
* Pandas: For data manipulation and analysis.
* PyProj: For geodetic computations, including distance and bearing calculations.

Configuration Options
---
* **Curve Threshold:** Adjusts the sensitivity of curve detection. A lower threshold identifies more subtle curves, while a higher threshold focuses on more pronounced turns.

Getting Started
---
Ensure you have the necessary dependencies installed, and prepare your trajectory data, as allready said.
```python
from curve_interpolation import CurveInterpolator

# Initialize the interpolator with your desired settings
interpolator = CurveInterpolator(curve_threshold=0.5)

# Interpolate curves in your trajectory data
interpolated_trajectory = interpolator.interpolate(trajectory_data)
```

<br />
<br />

Trajectory Combination Component
===

Features
---
* **Multiple Trajectory Merging:** Efficiently combines several trajectories into a single, coherent path, ideal for repeatable routes.
* **Geographical Proximity Sorting:** Organizes trajectory points by their spatial relationships, maintaining logical sequence and spatial coherence.
* **Repeatable Route Optimization:** Particularly beneficial for fixed-route systems, enhancing accuracy and reliability of the combined trajectory.

Dependencies
---
* Python 3.x
* Pandas: For data manipulation and analysis.
* PyProj: For geodetic computations, including distance and bearing calculations.

Getting Started
---
Ensure you have the required dependencies installed. Prepare your trajectory data in a format compatible with the component, ideally as Pandas DataFrame objects with latitude and longitude columns.
```python
import pandas as pd
from combine import TrajectoryCombiner

# Initialize the refiner with your desired settings
combiner = TrajectoryCombiner()

df1 = pd.read_csv('trajectory1.csv')
df2 = pd.read_csv('trajectory2.csv')
df3 = pd.read_csv('trajectory2.csv')

# Merge and sort the trajectories
combined_trajectory_df = combiner([df1, df2, df3])

# The resulting DataFrame 'combined_trajectory_df' contains the combined and sorted trajectory
```

<br />
<br />

Trajectory Reconstruction Workflow
===
To execute all the components in order to ensure the best reconstraction and accuracy, you should follow this workflow:

1. **Combine Trajectories:** Merge multiple trajectory datasets into a single coherent trajectory.
2. **Refine Trajectory:** Enhance the combined trajectory's accuracy by refining it based on road networks or other criteria.
3. **Interpolate Curves:** Apply curve interpolation to the refined trajectory to ensure smoothness and continuity.

```python
import pandas as pd
from combine import TrajectoryCombiner
from refined import TrajectoryRefiner
from curve_interpolation import CurveInterpolator

# Load trajectory datasets
df1 = pd.read_csv('path/to/trajectory1.csv')
df2 = pd.read_csv('path/to/trajectory2.csv')
df3 = pd.read_csv('path/to/trajectory2.csv')

# Combine trajectories
# Initialize the TrajectoryCombiner
combiner = TrajectoryCombiner()
combined_df = combiner([df1, df2, df3])

# Refine the combined trajectory
# Initialize the TrajectoryRefiner with necessary parameter
refiner = TrajectoryRefiner(delete_off_road_points=True)
refined_trajectory = refiner.refine_trajectory(combined_df)

# Interpolate curves on the refined trajectory
# Initialize the CurveInterpolator with desired settings (e.g., curve threshold)
interpolator = CurveInterpolator(curve_threshold=0.5)
interpolated_trajectory = interpolator.interpolate(refined_trajectory)

# The `interpolated_trajectory` now holds the final trajectory data after combining, refining, and curve interpolating.
```
