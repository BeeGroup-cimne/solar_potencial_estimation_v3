import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

from shapely.geometry import Polygon, MultiPoint, MultiPolygon, GeometryCollection, Point
from shapely import make_valid, voronoi_polygons
from shapely.ops import unary_union
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
    vorAll = Voronoi(points[:,0:2])


    # extract valid polygons
    voronoi_polygons_list = []
    clustersPolygons = []

    for i in range(len(points)):
        idx_region = vorAll.point_region[i]
        if -1 not in vorAll.regions[idx_region]:
            polygon = Polygon(vorAll.vertices[vorAll.regions[idx_region]])
            clustersPolygons.append(labels[i])
            voronoi_polygons_list.append(polygon)

    vorGDF = gpd.GeoDataFrame(geometry=voronoi_polygons_list, crs=cadasterGDF.crs)
    vorGDF.buffer(0)
    vorGDF["cluster"] = clustersPolygons
    vorGDF["geometry"] = vorGDF.geometry.apply(make_valid)
    merged_gdf = vorGDF.dissolve(by = 'cluster').reset_index()
    merged_gdf["geometry"] = merged_gdf["geometry"].apply(unary_union)
    clippedGDF = gpd.clip(merged_gdf, cadasterGDF, sort=True)

    return clippedGDF