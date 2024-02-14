import numpy as np
import pandas as pd
import pyproj


class CurveInterpolator:
    def __init__(self, threshold=0.5, granularity=5):
        self.threshold = threshold  # Bearing change threshold to detect curves
        self.granularity = granularity  # Number of points to interpolate

    def __call__(self, df):
        """
            Detect curves in a path defined by latitude and longitude points in a DataFrame,
            and interpolate additional points on these curves.

            This function identifies points where the change in bearing exceeds a specified threshold,
            indicating a curve. It then interpolates additional points along these curves to provide
            a more detailed path representation. The function also linearly interpolates time between
            points.

            Parameters:
            df (DataFrame): DataFrame containing 'Time', 'lat', and 'lon' columns.
            threshold (float, optional): Bearing change threshold to detect curves. Defaults to 0.5.
            granularity (int, optional): Number of points to interpolate on each curve. Defaults to 5.

            Returns:
            DataFrame: A new DataFrame with interpolated points along detected curves.
            """
        # Convert time column to datetime objects
        df['Time'] = pd.to_datetime(df['Time'], format='%Y-%m-%d %H:%M:%S')

        # Check if the DataFrame contains necessary columns
        if 'lat' not in df.columns or 'lon' not in df.columns:
            raise ValueError("DataFrame must contain 'lat' and 'lon' columns")

        # Calculate bearings and bearing changes between consecutive points
        shifted_lat = df['lat'].shift(-1)
        shifted_lon = df['lon'].shift(-1)
        bearings = calculate_initial_compass_bearing(df[['lat', 'lon']], shifted_lat, shifted_lon)
        df['bearing'] = bearings[:-1]
        df['bearing_change'] = df['bearing'].diff().abs()

        # Identify points where the bearing change is above the threshold (curve points)
        curve_points = df[df['bearing_change'] > self.threshold]

        # Interpolate points on detected curves
        if not curve_points.empty:
            interpolated_points = []

            for idx, row in curve_points.iterrows():
                if idx < df.index.max():
                    next_idx = idx + 1
                    # Interpolate geographic coordinates
                    inter_points = geodesic_interpolate(df.at[idx, 'lat'], df.at[idx, 'lon'],
                                                        df.at[next_idx, 'lat'], df.at[next_idx, 'lon'],
                                                        self.granularity)

                    # Linearly interpolate time
                    time1 = df.at[idx, 'Time'].timestamp()
                    time2 = df.at[next_idx, 'Time'].timestamp()
                    time_interp = np.linspace(time1, time2, num=self.granularity)
                    new_times = pd.to_datetime(time_interp, unit='s')

                    # Compile interpolated latitude, longitude, and time points
                    for inter_lat, inter_lon, new_time in zip([p[0] for p in inter_points],
                                                              [p[1] for p in inter_points],
                                                              new_times):
                        interpolated_points.append((inter_lat, inter_lon, new_time))

            # Create a new DataFrame with the interpolated points if any were added
            if interpolated_points:
                new_df = pd.DataFrame(interpolated_points, columns=['lat', 'lon', 'Time'])
                new_df = new_df.drop_duplicates(subset=['lat', 'lon'])
                new_df = new_df.reset_index(drop=True)
                return new_df
            else:
                return df
        else:
            return df


def calculate_initial_compass_bearing(points, lat2, lon2):
    """
    Calculate the initial compass bearing between each point in a DataFrame and a given point.

    The function employs a vectorized approach to compute the bearing between multiple points
    and a single destination point. The formula used is based on the haversine formula which
    accounts for the Earth's curvature.

    Parameters:
    points (DataFrame): A DataFrame containing 'lat' and 'lon' columns representing the start points.
    lat2 (float): Latitude of the destination point.
    lon2 (float): Longitude of the destination point.

    Returns:
    numpy.ndarray: Array of initial bearings from each start point to the destination point.
    """
    # Convert latitude and longitude from degrees to radians
    lat1 = np.radians(points['lat'])
    lon1 = np.radians(points['lon'])
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)

    # Calculate the change in coordinates
    dlon = lon2 - lon1

    # Calculate the components of the bearing calculation
    x = np.sin(dlon) * np.cos(lat2)
    y = np.cos(lat1) * np.sin(lat2) - (np.sin(lat1) * np.cos(lat2) * np.cos(dlon))

    # Compute the initial bearing, convert from radians to degrees, and adjust for compass bearing
    initial_bearing = np.arctan2(x, y)
    initial_bearing = np.degrees(initial_bearing)
    initial_bearing = (initial_bearing + 360) % 360

    return initial_bearing


def calculate_bearing(start_lat, start_lon, end_lat, end_lon):
    """
    Calculate the bearing from a start point to an end point using the pyproj library.

    This function uses the pyproj library, which provides an interface to PROJ (cartographic
    projections and coordinate transformations library). The calculation is based on the WGS84
    ellipsoid model of the Earth.

    Parameters:
    start_lat (float): Latitude of the start point.
    start_lon (float): Longitude of the start point.
    end_lat (float): Latitude of the end point.
    end_lon (float): Longitude of the end point.

    Returns:
    float: Forward azimuth, representing the bearing from the start point to the end point.
    """
    # Initialize the Geod object with WGS84 ellipsoid model
    geod = pyproj.Geod(ellps='WGS84')
    # Calculate forward azimuth (bearing), back azimuth, and distance between the two points
    fwd_azimuth, _, _ = geod.inv(start_lon, start_lat, end_lon, end_lat)
    return fwd_azimuth


def geodesic_interpolate(start_lat, start_lon, end_lat, end_lon, granularity):
    """
    Interpolate a number of points between two geographic coordinates on the Earth's surface.

    This function considers the Earth's curvature by using the WGS84 ellipsoid model. It
    generates a specified number of intermediate points between the start and end coordinates,
    ensuring a more accurate path representation than simple linear interpolation.

    Parameters:
    start_lat (float): Latitude of the start point.
    start_lon (float): Longitude of the start point.
    end_lat (float): Latitude of the end point.
    end_lon (float): Longitude of the end point.
    granularity (int): Number of intermediate points to generate.

    Returns:
    list of tuples: A list of tuples (latitude, longitude) representing the interpolated points.
    """
    geod = pyproj.Geod(ellps='WGS84')
    # Generate intermediate points between the start and end points
    line = geod.npts(start_lon, start_lat, end_lon, end_lat, granularity - 1)
    interpolated_points = [(start_lat, start_lon)]  # Start with the initial point

    # Add the generated intermediate points, adjusting the order to (latitude, longitude)
    for lon, lat in line:
        interpolated_points.append((lat, lon))

    interpolated_points.append((end_lat, end_lon))  # End with the final point
    return interpolated_points
