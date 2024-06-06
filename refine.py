import numpy as np
import pandas as pd
import osmnx as ox
from shapely.geometry import Point, LineString, MultiPoint
from shapely.ops import unary_union, nearest_points


class TrajectoryRefiner:
    def __init__(self, delete_off_road_points=False, tolerance=0.0001):
        self.delete_off_road_points = delete_off_road_points
        self.tolerance = tolerance

    def __call__(self, matched):
        """
        Refines a trajectory of GPS points based on the road network graph G, addressing sharp turns and edge
        transitions.

        This function iterates through a series of geographic points, refining the trajectory by accounting for sharp
        changes in direction and differences in the underlying road network's OSM IDs. It uses a vectorized approach for
        efficiency and includes corner interpolation when transitioning between different road segments.

        Args:
        matched (DataFrame): Contains 'lon' and 'lat' columns with longitude and latitude coordinates of the trajectory.

        Returns:
        DataFrame: Refined trajectory as a DataFrame with 'lat' and 'lon' columns.
        """
        points = [Point(lon, lat) for lon, lat in zip(matched['lon'], matched['lat'])]
        lons, lats = zip(*[(point.x, point.y) for point in points])
        west, east, south, north = min(lons), max(lons), min(lats), max(lats)
        G = ox.graph_from_bbox(bbox=(north, south, east, west), network_type='drive', simplify=False)

        matched['Time'] = pd.to_datetime(matched['Time'])  # Convert to datetime objects
        matched['Timestamp'] = matched['Time'].apply(lambda x: x.timestamp())  # Convert to Unix timestamp

        # Convert longitude and latitude coordinates into Point objects for spatial analysis.
        points = np.array([Point(lon, lat) for lon, lat in zip(matched['lon'], matched['lat'])])
        refined_trajectory = []  # Stores the refined trajectory points.
        interpolated_timestamps = []  # Stores the timestamps for the refined trajectory points.
        osm_id_cache = {}  # Cache to store OSM IDs for each point for quick lookup.

        # Populating the OSM ID cache by finding the nearest edge in the graph for each point.
        edges = ox.distance.nearest_edges(G, matched['lon'], matched['lat'])
        for point, edge in zip(points, edges):
            osm_id_cache[point] = G.edges[edge]['osmid']  # Map each point to its corresponding OSM ID.

        # Iterate through the points to refine the trajectory based on OSM ID transitions.
        for i in range(len(points) - 1):
            current_point, next_point = points[i], points[i + 1]
            current_time, next_time = matched['Time'].iloc[i], matched['Time'].iloc[i + 1]
            current_osm_id, next_osm_id = osm_id_cache[current_point], osm_id_cache[next_point]

            # Check if there is a change in the OSM ID indicating a transition to a different road segment.
            if current_osm_id != next_osm_id:
                # Interpolate points and timestamps at the corner
                interp_points, interp_times = interpolate_corner_point(current_point, next_point, current_time,
                                                                       next_time,
                                                                       G, osm_id_cache)
                if interp_points:
                    refined_trajectory.extend(interp_points)
                    interpolated_timestamps.extend(interp_times)
            else:
                refined_trajectory.extend([current_point, next_point])
                interpolated_timestamps.extend([current_time, next_time])

        # Add the last point to the trajectory.
        refined_trajectory.append(points[-1])
        interpolated_timestamps.append(matched['Time'].iloc[-1])

        refined_df = pd.DataFrame({
            'lat': [p.y for p in refined_trajectory],
            'lon': [p.x for p in refined_trajectory],
            'Time': interpolated_timestamps
        })

        # Combine the original and refined trajectories
        combined_df = pd.concat([matched, refined_df])

        # Sort by Time
        combined_df.sort_values(by='Time', inplace=True)

        # Remove duplicate coordinates
        combined_df.drop_duplicates(subset=['lat', 'lon'], inplace=True)

        # Remove off-road points
        if self.delete_off_road_points:
            combined_df = remove_off_road_points(combined_df, G, self.tolerance)

        combined_df = combined_df.reset_index(drop=True)
        return combined_df


def interpolate_corner_point(p1, p2, t1, t2, G, osm_id_cache):
    """
    Interpolates points at the corner formed by two road segments to smoothen the trajectory.

    This function handles the intersection of two road segments (edges) and interpolates points at the corner
    to create a smoother transition between these segments. This is particularly useful in cases where there
    is a sharp turn or change in the road.

    Args:
    p1, p2 (Point): Two consecutive points in the trajectory.
    G (NetworkX Graph): The graph representing the road network.
    osm_id_cache (dict): A cache mapping points to their corresponding OSM IDs.

    Returns:
    list: A list of interpolated Point(s) at the corner, if any.
    """
    # Retrieve the edge geometries for the two points.
    edge1, edge2 = get_edge_geometry(G, p1, osm_id_cache), get_edge_geometry(G, p2, osm_id_cache)
    interpolated_points = []
    interpolated_times = []

    if edge1 and edge2:
        line1, line2 = (edge1 if isinstance(edge1, LineString) else nearest_line_in_multilinestring(edge1, edge2),
                        edge2 if isinstance(edge2, LineString) else nearest_line_in_multilinestring(edge2, edge1))
        intersect = line1.intersection(line2)

        if intersect.is_empty:
            nearest1, nearest2 = nearest_points(line1, line2)
            interpolated_points = [Point([(nearest1.x + nearest2.x) / 2, (nearest1.y + nearest2.y) / 2])]
        elif isinstance(intersect, Point):
            interpolated_points = [intersect]
        elif isinstance(intersect, MultiPoint):
            interpolated_points = list(intersect.geoms)
        else:
            return [], []  # Ensure to return two empty lists in case of no intersections

        total_distance = p1.distance(p2)
        for interp_point in interpolated_points:
            distance_from_p1 = p1.distance(interp_point)
            interp_time = t1 + ((t2 - t1) * (distance_from_p1 / total_distance))
            interpolated_times.append(interp_time)

    return interpolated_points, interpolated_times


def nearest_line_in_multilinestring(multilinestring, line):
    """
    Identifies the nearest line segment in a MultiLineString to a given LineString.

    This function is used to find the closest line segment in a collection of line segments to a specific line.
    This is useful in situations where road geometries are complex and consist of multiple segments.

    Args:
    multilinestring (MultiLineString): A collection of LineStrings.
    line (LineString): A LineString to compare against the MultiLineString.

    Returns:
    LineString: The nearest LineString from the MultiLineString to the given line.
    """
    min_distance = float('inf')
    nearest_line = None
    # Iterate through each LineString in the MultiLineString to find the closest one to the given line.
    for linestring in multilinestring.geoms:
        distance = linestring.distance(line)
        if distance < min_distance:
            min_distance = distance
            nearest_line = linestring
            # Early break if an exact match (zero distance) is found.
            if distance == 0:
                break
    return nearest_line


def get_edge_geometry(G, point, osm_id_cache):
    """
    Retrieves the combined geometry of all edges in the graph corresponding to a specific OSM ID.

    This function aggregates the geometries of all edges that share the same OSM ID as the given point.
    It is essential for accurately determining the road segment associated with each point in the trajectory.

    Args:
    G (NetworkX Graph): The graph representing the road network.
    point (Point): The Shapely Point for which the edge geometry is needed.
    osm_id_cache (dict): A cache mapping points to their corresponding OSM IDs.

    Returns:
    Geometry: The combined geometry of all edges associated with the given point.
    """
    osm_id = osm_id_cache[point]
    # Find all edges in the graph that have the same OSM ID as the point.
    edges = [(u, v, k) for u, v, k, data in G.edges(keys=True, data=True) if data['osmid'] == osm_id]
    # Retrieve or construct the geometry for each edge.
    geometries = [G.edges[edge].get('geometry', construct_geometry(G, edge[0], edge[1])) for edge in edges]
    # Combine all geometries into a single unified geometry.
    return unary_union(geometries)


def construct_geometry(G, u, v):
    """
    Constructs the geometric representation (LineString) of an edge in the graph from its nodes.

    This function creates a LineString based on the coordinates of the start and end nodes of an edge.
    It is used when the edge geometry is not explicitly stored in the graph.

    Args:
    G (NetworkX Graph): The graph representing the road network.
    u, v (nodes): The nodes representing the start and end of an edge.

    Returns:
    LineString: The geometric representation of the edge between nodes u and v.
    """
    u_node, v_node = G.nodes[u], G.nodes[v]
    # Create a LineString from the coordinates of the start and end nodes.
    return LineString([(u_node['x'], u_node['y']), (v_node['x'], v_node['y'])])


def remove_off_road_points(refined_trajectory, G, tolerance):
    """
    Removes points from the trajectory that do not lie on a road, based on the specified tolerance.

    This function filters out points from a given trajectory that are not within a certain distance (tolerance)
    from any road segment in the road network graph. This is useful for ensuring that the trajectory strictly
    adheres to the road network.

    Args:
        refined_trajectory (pd.DataFrame): A DataFrame containing the refined trajectory with 'lat' and 'lon' columns.
        G (NetworkX Graph): A Graph representing the road network.
        tolerance (float): The maximum distance a point can be from a road to be considered on the road.

    Returns:
        pd.DataFrame: A DataFrame containing the trajectory points that are on the road.
    """
    # Convert trajectory points to Shapely Point objects for spatial analysis.
    points = [Point(lon, lat) for lon, lat in zip(refined_trajectory['lon'], refined_trajectory['lat'])]

    # Perform a batch operation to find the nearest edges in the graph for all points.
    nearest_edges = ox.distance.nearest_edges(G, refined_trajectory['lon'], refined_trajectory['lat'],
                                              return_dist=False)

    # Create a dictionary of edge geometries for quick lookup.
    edge_geometries = preprocess_edge_geometries(G)

    # Create a mask to identify points that are on a road segment within the specified tolerance.
    on_road_mask = [is_point_on_road(point, nearest_edges[i], edge_geometries, tolerance) for i, point in
                    enumerate(points)]

    # Apply the mask to filter the trajectory points.
    on_road_trajectory = np.array(points)[on_road_mask]

    # Convert the filtered points back to a DataFrame format.
    return pd.DataFrame({'lat': [p.y for p in on_road_trajectory], 'lon': [p.x for p in on_road_trajectory]})


def preprocess_edge_geometries(G):
    """
    Preprocesses and stores the geometries of all edges in a road network graph.

    This function iterates through all edges in the provided graph and stores their geometries in a dictionary.
    The geometries are either retrieved directly from the graph if available or constructed from the edge's nodes.

    Args:
        G (NetworkX Graph): A Graph representing the road network.

    Returns:
        dict: A dictionary where each key is a tuple representing an edge (u, v, key),
              and the value is the geometry of that edge.
    """
    edge_geometries = {}
    for u, v, key, data in G.edges(keys=True, data=True):
        # Retrieve or construct the geometry for each edge.
        geom = data.get('geometry',
                        LineString([(G.nodes[u]['x'], G.nodes[u]['y']), (G.nodes[v]['x'], G.nodes[v]['y'])]))
        edge_geometries[(u, v, key)] = geom
    return edge_geometries


def is_point_on_road(point, nearest_edge, edge_geometries, tolerance):
    """
    Determines if a point is on a road segment within the specified tolerance.

    This function checks if a given point is within a specified distance (tolerance) from its nearest road segment.
    The function relies on a precomputed dictionary of edge geometries for efficient computation.

    Args:
        point (Point): The Shapely Point object to check.
        nearest_edge (tuple): A tuple representing the nearest edge to the point.
        edge_geometries (dict): A dictionary containing the geometries of edges in the road network.
        tolerance (float): The distance tolerance for determining if the point is on the road.

    Returns:
        bool: True if the point is within the specified tolerance of the nearest road segment, False otherwise.
    """
    # Handle the case where the nearest edge is not found in the precomputed geometries.
    if nearest_edge not in edge_geometries:
        # If the edge is not found, the point is considered off-road.
        return False

    # Retrieve the geometry of the nearest road segment.
    edge_geom = edge_geometries[nearest_edge]

    # Calculate the distance from the point to this nearest road segment.
    distance = point.distance(edge_geom)

    # Determine if the point is within the specified tolerance of the road segment.
    return distance <= tolerance
