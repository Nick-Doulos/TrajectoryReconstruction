import pandas as pd
from pyproj import Geod


class TrajectoryCombiner:
    def __init__(self):
        # Initialize the Geod object for distance calculations
        self.geod = Geod(ellps="WGS84")

    def __call__(self, dataframes):
        """
        Enables the class instance to be called directly with a list of DataFrames,
        combining and sorting them based on geographical proximity.

        Parameters:
        dataframes (list of pd.DataFrame): A list of DataFrames containing trip data with latitude ('lat') and longitude
         ('lon') columns.

        Returns:
        pd.DataFrame: A DataFrame sorted based on the proximity of the geographical coordinates, starting from the first
         row
        of the combined DataFrame.
        """

        # Concatenating the list of DataFrames and resetting the index for the combined DataFrame
        combined_df = pd.concat(dataframes, ignore_index=True)

        # Extracting the latitude and longitude columns as a NumPy array
        coordinates = combined_df[['lat', 'lon']].values

        # Initializing the sorting process
        sorted_indices = [0]  # Starting from the first point
        current_index = 0  # Current point index
        visited = set(sorted_indices)  # Set to keep track of visited points

        # Iterating over coordinates to sort them based on nearest neighbors
        while len(sorted_indices) < len(combined_df):
            min_dist = float('inf')
            nearest_index = None

            for i, coord in enumerate(coordinates):
                if i not in visited:
                    # Calculate geodesic distance
                    _, _, dist = self.geod.inv(coordinates[current_index][1], coordinates[current_index][0],
                                               coord[1], coord[0])
                    if dist < min_dist:
                        min_dist = dist
                        nearest_index = i

            if nearest_index is None:
                break  # Break loop if no unvisited points are left

            visited.add(nearest_index)
            sorted_indices.append(nearest_index)
            current_index = nearest_index

        # Reordering the DataFrame based on the sorted indices and resetting the index
        sorted_df = combined_df.iloc[sorted_indices].reset_index(drop=True)

        return sorted_df
