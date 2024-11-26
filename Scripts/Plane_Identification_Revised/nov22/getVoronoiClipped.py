import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

from shapely.geometry import Polygon, MultiPoint, MultiPolygon, GeometryCollection, Point
from shapely import make_valid, voronoi_polygons
from shapely.ops import unary_union
from scipy.spatial import Voronoi

def get_boundary(poly, offset = 100, steps=10):
    bound = poly.bounds #Create a large rectangle surrounding it

    # Does not work with miniVoronoi
    x_bottom_top = np.linspace(bound.minx - offset, bound.maxx + offset, steps)
    y_left_right = np.linspace(bound.miny - offset, bound.maxy + offset, steps)

    bottom_points = np.column_stack([x_bottom_top, np.repeat(bound.miny - offset, steps)])
    top_points = np.column_stack([x_bottom_top, np.repeat(bound.maxy + offset, steps)])
    left_points = np.column_stack([np.repeat(bound.minx - offset, steps), y_left_right])
    right_points = np.column_stack([np.repeat(bound.maxx + offset, steps), y_left_right])
    boundarycoords = np.vstack([bottom_points, top_points, left_points, right_points])
    boundarycoords = np.unique(boundarycoords, axis=0)
    # except:
    #     x_bottom_top = np.linspace(bound[0] - offset, bound[2] + offset, steps)
    #     y_left_right = np.linspace(bound[1] - offset, bound[3] + offset, steps)

    #     bottom_points = np.column_stack([x_bottom_top, np.repeat(bound[1] - offset, steps)])
    #     top_points = np.column_stack([x_bottom_top, np.repeat(bound[3] + offset, steps)])
    #     left_points = np.column_stack([np.repeat(bound[0] - offset, steps), y_left_right])
    #     right_points = np.column_stack([np.repeat(bound[2] + offset, steps), y_left_right])
    #     boundarycoords = np.vstack([bottom_points, top_points, left_points, right_points])
    #     boundarycoords = np.unique(boundarycoords, axis=0)
    return boundarycoords

def obtainLabelsPolygons(vorAll, labels):
    voronoi_polygons_list = []
    clustersPolygons = []

    for idx_region, region in enumerate(vorAll.regions):
        if(region):
            indices = np.where(vorAll.point_region[0:len(labels)] == idx_region)
            selectedLabels = labels[indices]
            if -1 not in region:
                if(np.all(selectedLabels == selectedLabels[0])):
                    polygon = Polygon(vorAll.vertices[region])
                    clustersPolygons.append(selectedLabels[0])
                    voronoi_polygons_list.append(polygon)
                # else:
                #     outline = Polygon(vorAll.vertices[region])
                #     points = vorAll.points[indices]
                #     boundarycoords = get_boundary(outline)
                #     allPoints = np.concatenate((points[0:len(labels),0:2], boundarycoords))
                #     miniVor = Voronoi(allPoints)
                #     subVorList, subClusterList = obtainLabelsPolygons(miniVor, selectedLabels)

                #     voronoi_polygons_list += subVorList
                #     clustersPolygons += subClusterList

    return voronoi_polygons_list, clustersPolygons

def getVoronoiClipped(points, labels, cadasterGDF):

    boundarycoords = get_boundary(cadasterGDF.geometry)
    allPoints = np.concatenate((points[:,0:2], boundarycoords))
    vorAll = Voronoi(allPoints)


    # extract valid polygons
    voronoi_polygons_list = []
    clustersPolygons = []

    # for i in range(len(points)):
    #     idx_region = vorAll.point_region[i]
    #     if -1 not in vorAll.regions[idx_region]:
    #         polygon = Polygon(vorAll.vertices[vorAll.regions[idx_region]])
    #         clustersPolygons.append(labels[i])
    #         voronoi_polygons_list.append(polygon)

    voronoi_polygons_list, clustersPolygons = obtainLabelsPolygons(vorAll, labels)

    vorGDF = gpd.GeoDataFrame({"geometry":voronoi_polygons_list, "cluster":clustersPolygons}, crs=cadasterGDF.crs)
    vorGDF.buffer(0)
    vorGDF["geometry"] = vorGDF.geometry.apply(make_valid)
    # merged_gdf = vorGDF.dissolve(by = 'cluster').reset_index()
    # merged_gdf["geometry"] = merged_gdf["geometry"].apply(unary_union)
    clippedGDF = gpd.clip(vorGDF, cadasterGDF, sort=True)

    return clippedGDF