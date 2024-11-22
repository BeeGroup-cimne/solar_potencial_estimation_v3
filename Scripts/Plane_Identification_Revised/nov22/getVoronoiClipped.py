import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

from shapely.geometry import Polygon, MultiPolygon
from scipy.spatial import Voronoi

def getVoronoiClipped(points, labels, cadasterGDF):
    bound = cadasterGDF.geometry.bounds #Create a large rectangle surrounding it

    x_bottom_top = np.linspace(bound.minx - 100, bound.maxx + 100, 10)
    y_left_right = np.linspace(bound.miny - 100, bound.maxy + 100, 10)

    bottom_points = np.column_stack([x_bottom_top, np.repeat(bound.miny - 100, 10)])
    top_points = np.column_stack([x_bottom_top, np.repeat(bound.maxy + 100, 10)])
    left_points = np.column_stack([np.repeat(bound.minx - 100, 10), y_left_right])
    right_points = np.column_stack([np.repeat(bound.maxx + 100, 10), y_left_right])

    boundarycoords = np.vstack([bottom_points, top_points, left_points, right_points])
    boundarycoords = np.unique(boundarycoords, axis=0)

    allPoints = np.concatenate((points[:,0:2], boundarycoords))
    vorAll = Voronoi(allPoints)

    # extract valid polygons
    voronoi_polygons = []
    clustersPolygons = []

    for i in range(len(points)):
        idx_region = vorAll.point_region[i]
        if -1 not in vorAll.regions[idx_region]:
            polygon = Polygon(vorAll.vertices[vorAll.regions[idx_region]])
            clustersPolygons.append(labels[i])
            voronoi_polygons.append(polygon)

    vorGDF = gpd.GeoDataFrame(geometry=voronoi_polygons, crs=cadasterGDF.crs)
    vorGDF["cluster"] = clustersPolygons
    vorGDF = vorGDF[vorGDF.is_valid]
    merged_gdf = vorGDF.dissolve(by = 'cluster').reset_index()
    clippedGDF = gpd.clip(merged_gdf, cadasterGDF, sort=True)

    return clippedGDF