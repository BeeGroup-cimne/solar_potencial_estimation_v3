import os
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import Voronoi
from shapely.geometry import Point, Polygon, LineString, MultiPolygon, box
from shapely.errors import TopologicalError

from shapely.ops import unary_union, polygonize
from shapely.affinity import translate

def read_txt_files_to_dataframe(txt_dir):
    """Reads all .txt files in the given directory, combining them into a single DataFrame with a 'cluster' column."""
    all_data = []
    for filename in os.listdir(txt_dir):
        if filename.endswith('.csv'):
            cluster_name = os.path.splitext(filename)[0]  # filename without extension
            filepath = os.path.join(txt_dir, filename)
            data = pd.read_csv(filepath, header=None, names=['x', 'y', 'z'])
            data['cluster'] = cluster_name
            all_data.append(data)
    return pd.concat(all_data, ignore_index=True)

def compute_voronoi(df, clip_boundary):
    """Computes a Voronoi diagram and clips it with the given boundary."""
    points = df[['x', 'y']].values
    vor = Voronoi(points)
    
    # Voronoi regions generation
    voronoi_regions = []
    for point_index, region_index in enumerate(vor.point_region):
        region = vor.regions[region_index]
        # Skip regions that have vertices at infinity
        if -1 in region or not region:
            print("skipped")
            continue
        
        # Create polygon for the finite region
        polygon = Polygon([vor.vertices[i] for i in region])
        
        # Clip the polygon with the boundary
        clipped_polygon = polygon.intersection(clip_boundary)
        if not clipped_polygon.is_empty:
            voronoi_regions.append((point_index, clipped_polygon))

    return voronoi_regions

def compute_voronoi_with_bbox(df, clip_boundary):
    """Computes a Voronoi diagram with a bounding box around the points and clips with the boundary."""
    points = df[['x', 'y']].values
    vor = Voronoi(points)
    
    # Create a bounding box slightly larger than the data points
    min_x, min_y = points.min(axis=0) - 10
    max_x, max_y = points.max(axis=0) + 10
    bounding_box = box(min_x, min_y, max_x, max_y)
    
    print(vor.point_region)

    # Container for voronoi regions
    voronoi_regions = []
    for point_index, region_index in enumerate(vor.point_region):
        region = vor.regions[region_index]
        # Skip empty regions
        if not region:
            continue

        # For infinite regions (-1 in region), approximate them by extending to the bounding box
        polygon_vertices = []
        for vertex_index in region:
            if vertex_index == -1:
                # Handle infinite regions by intersecting the edge with the bounding box
                edge = LineString([vor.vertices[region[i]] for i in range(len(region)) if region[i] != -1])
                extended_edge = edge.intersection(bounding_box)
                if extended_edge.is_empty:
                    continue
                if isinstance(extended_edge, LineString):
                    polygon_vertices.extend(list(extended_edge.coords))
                elif isinstance(extended_edge, MultiPolygon):
                    polygon_vertices.extend([p.exterior.coords[0] for p in extended_edge])
            else:
                polygon_vertices.append(vor.vertices[vertex_index])
        
        # Create polygon and clip with boundary
        if len(polygon_vertices) >= 3:
            polygon = Polygon(polygon_vertices)
            try:
                # Attempt to clip the polygon with the boundary
                clipped_polygon = polygon.intersection(clip_boundary)
                # Buffer with zero to fix potential topology issues
                clipped_polygon = clipped_polygon.buffer(0)
                
                # Check if the clipped polygon is valid and non-empty before adding it
                if clipped_polygon.is_valid and not clipped_polygon.is_empty:
                    voronoi_regions.append((point_index, clipped_polygon))
            except TopologicalError as e:
                print(f"Skipped a region due to topology error: {e}")
    
    return voronoi_regions

def plot_voronoi(voronoi_regions, clip_boundary, df):
    """Plot the Voronoi diagram with the clipping boundary and cluster points."""
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Plot the clipped Voronoi regions
    for idx, region in voronoi_regions:
        gpd.GeoSeries(region).plot(ax=ax, edgecolor="black", alpha=0.3)
    
    # Plot the clipping boundary
    gpd.GeoSeries(clip_boundary).boundary.plot(ax=ax, color="red", linewidth=2, label="Clip Boundary")

    # Plot the original points with cluster labels
    for cluster, group in df.groupby("cluster"):
        plt.scatter(group['x'], group['y'], label=f"Cluster {cluster}", s=10)
    
    ax.set_title("Voronoi Diagram with Clipping Boundary")
    ax.legend()
    plt.xlabel("X coordinate")
    plt.ylabel("Y coordinate")
    plt.show()

def merge_polygons_by_cluster(voronoi_regions, df):
    """Merges adjacent polygons that belong to the same cluster."""
    gdf_regions = gpd.GeoDataFrame([
        {'geometry': poly, 'cluster': df.iloc[idx]['cluster']}
        for idx, poly in voronoi_regions
    ], crs="EPSG:25831")  # Adjust EPSG code as necessary
    
    # Group by cluster and merge polygons
    merged_gdf = gdf_regions.dissolve(by='cluster')
    return merged_gdf

def export_polygons(merged_gdf, output_dir):
    """Exports each merged polygon to a file named by its cluster."""
    os.makedirs(output_dir, exist_ok=True)
    for idx, row in merged_gdf.iterrows():
        filename = f"{idx}.gpkg"
        filepath = os.path.join(output_dir, filename)
        gpd.GeoDataFrame([row], columns=merged_gdf.columns, crs=merged_gdf.crs).to_file(filepath, driver="gpkg")

if __name__ == "__main__":
    # Parameters
    gpkg_file = 'Results/70_el Besòs i el Maresme/Parcels/4058610DF3845G/58/Map files/58.gpkg'
    txt_dir = 'Results/70_el Besòs i el Maresme/Parcels/4058610DF3845G/58/Plane Processing/Plane Deleting/Plane Points'
    output_dir = 'Results/70_el Besòs i el Maresme/Parcels/4058610DF3845G/58/Plane Processing/Cadaster Fit'

    # Load the clipping boundary from the .gpkg file
    clip_boundary = gpd.read_file(gpkg_file).union_all()
 
    # Step 1: Read all .txt files
    df = read_txt_files_to_dataframe(txt_dir)

    # Step 2: Compute Voronoi diagram and clip with boundary
    voronoi_regions = compute_voronoi_with_bbox(df, clip_boundary) # compute_voronoi(df, clip_boundary)
    

    # plot_voronoi(voronoi_regions, clip_boundary, df)


    # Step 3: Merge adjacent polygons by cluster
    merged_gdf = merge_polygons_by_cluster(voronoi_regions, df)
    
    # Step 4: Export merged polygons to the output directory
    export_polygons(merged_gdf, output_dir)
    print(f"Polygons exported to {output_dir}")