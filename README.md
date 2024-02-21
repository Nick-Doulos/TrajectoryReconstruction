# WP3 Service: 3.2 - Trajectory Reconstruction


## Description
This repository contains the first version of the service Trajectory Reconstruction, developed as part of 3.2 of WP3 within EMERALDS project. Trajectory Reconstruction is a cutting-edge solution designed to tackle the prevalent issue of accuracy in map-matching processes, particularly those affected by low GPS sampling rates. This module is a comprehensive assembly of sophisticated spatial analysis algorithms, including Curve Interpolation, Trajectory Refinement, and Trajectory Combination. These components work in synergy to significantly enhance map-matched trajectories produced by advanced map-matching algorithms like Valhalla's Meili, among others, incorporating all original data points to ensure no critical information is lost.

## Table of Contents
- [WP3 Service: 3.2 - Trajectory Reconstruction](#wp3-service-32---trajectory-reconstruction)
  - [Description](#description)
  - [Table of Contents](#table-of-contents)
  - [Components](#components)
  - [Requirements](#requirements)
  - [Sample data input/output structures](#sample-data-inputoutput-structures)
  - [Input/Output interfaces \& interactions](#inputoutput-interfaces--interactions)
  - [Deployment](#deployment)
  - [Usage - Executing program](#usage---executing-program)
  - [Authors](#authors)


## Components                                          
* **Trajectory Refinement:** Improves trajectory’s accuracy and detail via road networks by transforming the GPS points of a trajectory into road objects, enabling computations that allow for interpolation at crucial network points (such as the apex of a turn, and changes in the route), thereby smoothing out the trajectory and preserving its spatiotemporal integrity.
* **Curve Interpolation:** Employs bearing calculations to detect significant directional changes, using a threshold-based approach to identify curves within the trajectory. The algorithm performs interpolation in these selected curves, adding intermediate points to represent the trajectory more accurately, considering the Earth's curvature.
* **Trajectory Combination:** Improves the accuracy of a repeatable trajectory (like a bus route), by merging multiple trajectories that take place in the same route and sorting each trajectory point based on its geographical proximity, thus ensuring that the merged trajectory is organized in a logical and spatially coherent manner.


## Requirements
* **Python 3.x**
* **NumPy**: For numerical operations.
* **Pandas**: For data manipulation and analysis.
* **OSMnx**: For handling road network graphs.
* **Shapely**: For geometric operations.
* **PyProj**: For geodetic computations, including distance and bearing calculations.


## Sample data input/output structures
An example of an input/output trajectory:
| Time         | lat     | lon |
|--------------|-----------|------------|
| 8/30/2019  11:54:36 AM | 56.876078      | 24.26032        |
| 8/30/2019  11:55:07 AM | 56.878207  | 24.255258       |
| ... | ...      | ...        |
| 8/30/2019  11:59:53 AM      | 56.89154  | 24.223596       |


## Input/Output interfaces & interactions
Trajectory Reconstruction is processing trajectory data utilizing a **Pandas DataFrame** format for both input and output, ensuring extensive compatibility and user convenience. Inputs to the module require a DataFrame with columns designated for **Time**, **lat**, and **lon**, where each row signifies a distinct point in the vehicle's journey, effectively mapping its temporal and spatial progression. As data traverses the Curve Interpolation, Trajectory Refinement, and Trajectory Combination components of the module, it emerges as an enhanced DataFrame. This way, we can maintains the original data structure while integrating improvements such as precise coordinate adjustments, smooth interpolated points, and logically sequenced data points. This method not only simplifies integration across various data processing environments but also ensures the fidelity of the original temporal and spatial information.


## Deployment
Each component is encapsulated within a distinct Python file, each containing an executable class. These classes can be instantiated and executed within a Python environment to deploy and utilize the respective component's functionality.


## Usage - Executing program

Example for Trajectory Refinement Component:

* **Off Road Points Removal:** The *delete_off_road_points* variable has boolean type, so it can be set to True or Flase, depending on the user's preference.
* **Tolerance:** The *tolerance* variable defines the maximum distance from the road network for points in the trajectory, determining their inclusion or exclusion based on proximity.

```python
from refine import TrajectoryRefiner

# Initialize the refiner with your desired settings
refiner = TrajectoryRefiner(delete_off_road_points=True, tolerance=0.0001)

# Refine a trajectory
refined_trajectory = refiner.refine_trajectory(gps_trajectory_data)
```

Example for Curve Interpolation Component:

* **Curve Threshold:** Adjusts the sensitivity of curve detection. A lower threshold identifies more subtle curves, while a higher threshold focuses on more pronounced turns.

```python
from curve_interpolation import CurveInterpolator

# Initialize the interpolator with your desired settings
interpolator = CurveInterpolator(curve_threshold=0.5)

# Interpolate curves in your trajectory data
interpolated_trajectory = interpolator.interpolate(trajectory_data)
```

Example for Trajectory Combination Component:

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
```

Demonstration of Integrating All Components:

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

## Authors
Nikolaos Doulos, Christos Doulkeridis; University of Piraeus.
