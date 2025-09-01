import matplotlib.pyplot as plt
import geopandas as gpd
import laspy
import os
import shutil
import time
from tqdm import tqdm
import numpy as np
from sklearn.linear_model import LinearRegression
from shapely import unary_union, GeometryCollection, Polygon, MultiPolygon, make_valid, intersection, Point
from scipy.spatial import Voronoi
import math
import warnings
warnings.filterwarnings("error")

from utils import create_output_folder

def __get_boundary(bound, offset = 100, steps=10):
    x_bottom_top = np.linspace(bound[0] - offset, bound[2] + offset, steps)
    y_left_right = np.linspace(bound[1] - offset, bound[3] + offset, steps)

    bottom_points = np.column_stack([x_bottom_top, np.repeat(bound[1] - offset, steps)])
    top_points = np.column_stack([x_bottom_top, np.repeat(bound[3] + offset, steps)])
    left_points = np.column_stack([np.repeat(bound[0] - offset, steps), y_left_right])
    right_points = np.column_stack([np.repeat(bound[2] + offset, steps), y_left_right])
    boundarycoords = np.vstack([bottom_points, top_points, left_points, right_points])
    boundarycoords = np.unique(boundarycoords, axis=0)
    return boundarycoords

def __obtainLabelsPolygons(vorAll, labels):
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
                else:   
                    try:
                        outline = Polygon(vorAll.vertices[region])
                        points = vorAll.points[indices]
                        if(not np.all((points == points[0]).all())):
                            boundarycoords = __get_boundary(outline.bounds)
                            allPoints = np.concatenate((points[:,0:2], boundarycoords))
                            miniVor = Voronoi(allPoints)
                            subVorList, subClusterList = __obtainLabelsPolygons(miniVor, selectedLabels)
                            subVorList = [intersection(x.buffer(0), outline.buffer(0)) for x in subVorList]
                            voronoi_polygons_list += subVorList
                            clustersPolygons += subClusterList
                        else:
                            clustersPolygons.append(selectedLabels[0])
                            voronoi_polygons_list.append(outline)
                    except RecursionError:
                        # print("There was an Infinite Recursion Error!")
                        clustersPolygons.append(selectedLabels[0])
                        outline = Polygon(vorAll.vertices[region])
                        voronoi_polygons_list.append(outline)

    return voronoi_polygons_list, clustersPolygons

def __getVoronoiClipped(points, labels, cadasterGDF):
    # Generate Voronoi
    boundarycoords = __get_boundary(cadasterGDF.geometry.total_bounds)
    allPoints = np.concatenate((points[:,0:2], boundarycoords))
    vorAll = Voronoi(allPoints)

    # extract valid polygons
    voronoi_polygons_list = []
    clustersPolygons = []

    voronoi_polygons_list, clustersPolygons = __obtainLabelsPolygons(vorAll, labels)
    vorGDF = gpd.GeoDataFrame({"geometry":voronoi_polygons_list, "cluster":clustersPolygons}, crs=cadasterGDF.crs)
    
    vorGDF["geometry"] = vorGDF.geometry.apply(make_valid)
    vorGDF["geometry"] = vorGDF["geometry"].buffer(0.01)
    vorGDF["geometry"] = vorGDF["geometry"].buffer(-0.01)
    merged_gdf = vorGDF.dissolve(by = 'cluster').reset_index()
    merged_gdf["geometry"] = merged_gdf["geometry"].apply(unary_union)
    clippedGDF = gpd.clip(merged_gdf, cadasterGDF, sort=True)
    return clippedGDF

def __getTiltAzimuth(normal):
        """
        Given the normal vector of a plane, returns the tilt and azimuth of that plane.
        Tilt goes from 0 (horizontal) to 90 degrees (vertical) whereas azimuth goes from 0 (pointing north) to 360 degrees, growing clockwise

        #### Inputs:
        - normal: 3 element array (x,y,z from the normal vector, i.e, a,b,c parameters of the plane equation)
        
        #### Outputs:
        -  tilt, azimuth: in degreees
        """
        # Check if z is negative, plane normal must be pointing upwards
        normal = np.array(normal)
        if(normal[2] < 0):
            normal = -normal
        
        # Azimuth
        alpha = math.degrees(math.atan2(normal[1], normal[0]))
        azimuth = 90 - alpha
        if azimuth >= 360.0:
            azimuth -= 360.0
        elif azimuth < 0.0:
            azimuth += 360.0
        
        # Tilt
        t = math.sqrt(normal[0] ** 2 + normal[1] ** 2)
        if t == 0:
            tilt = 0.0
        else:
            tilt = 90 - math.degrees(math.atan(normal[2] / t)) # 0 for flat roof, 90 for wall/vertical roof
        tilt = round(tilt, 3)

        return (tilt, azimuth)

def __getSilhouette(voronoiGDF, points):
    silhouette_list = []
    labels = np.full(points.shape[0], -1)
    # Assign each point to their label (-1 if they are at no plane)
    s = gpd.GeoSeries(map(Point, zip(points[:,0], points[:,1])))
    for i in range(len(voronoiGDF)):
        inside = s.within(voronoiGDF.geometry[i])
        labels[inside] = i
    # Create outlierPlane
    mask = (labels == -1)
    unassigned = points[mask]
    planes = list(voronoiGDF.plane.values)
    if(unassigned.shape[0] >= 3):
        outlierPlane = LinearRegression().fit(unassigned[:,0:2], unassigned[:,2])
        planes.append(outlierPlane)

    # For each label (except -1):
    for label in np.unique(labels[labels!= -1]):
        mask = (labels == label)
        actualInliers = points[mask]
        

        ###################
        ### PLACEHOLDER
        # silhouette_list.append(0)
        ####################


        s_cluster_list = []

        for inlier in actualInliers:
            # compute all vertical distances from a point to every plane
            distances = np.zeros(len(planes))
            for plane_idx in range(len(planes)):
                distances[plane_idx] = abs(inlier[2] - planes[plane_idx].predict([inlier[0:2]])[0])

            a = distances[label]

            # and the next closest as the neighbor distance (b_i)        
            mask = np.ones_like(distances, dtype=bool)
            mask[label] = False  
            neighborDistances = distances[mask]
            if len(neighborDistances) == 1:
                b = neighborDistances
            else:
                b = np.min(neighborDistances)
            # Compute silhouette
            individual_s = (b - a) / np.maximum(b, a)
            s_cluster_list.append(individual_s)

        silhouette_list.append(np.mean(s_cluster_list))
        
        
        # ###############
        # ## Conflict: this is expensive as fuck
        # ###############

        # # compute all vertical distances from every point to every plane
        # distances = np.zeros((actualInliers.shape[0], len(planes)))
        # for plane_idx in range(len(planes)):
        #     distances[:, plane_idx] = abs(actualInliers[:,2] - planes[plane_idx].predict(actualInliers[:,0:2]))
        # # keep the one referring to their labels as their actual distance (a_i), 
        # a = distances[np.arange(distances.shape[0]), label]
        
        # # and the next closest as the neighbor distance (b_i)
        # rows = np.arange(distances.shape[0])
        # cols = label            
        # mask = np.ones_like(distances, dtype=bool)
        # mask[rows, cols] = False  
        # neighborDistances = distances[mask].reshape(distances.shape[0], distances.shape[1] - 1)
        # if neighborDistances.shape[1] == 1:
        #     b = neighborDistances
        # else:
        #     b = np.min(neighborDistances, axis=1)
        # # Compute silhouette
        # s = (b - a) / np.maximum(b, a)
        # silhouette_list.append(np.mean(s))

        # ###############
        # ## Conflict ends here
        # ###############

    return silhouette_list

def __delete_polygons_by_area(geometry, threshold):
    if isinstance(geometry, Polygon):
        return geometry if geometry.area >= threshold else None
    elif isinstance(geometry, MultiPolygon):
        filtered_polygons = [poly for poly in list(geometry.geoms) if poly.area >= threshold]
        if len(filtered_polygons) == 1:
            return filtered_polygons[0]
        elif len(filtered_polygons) > 1:
            return MultiPolygon(filtered_polygons)
        else:
            return None
    return geometry  # For non-polygon geometries, return as-is

def __clean_holes(geometry, threshold):
    if isinstance(geometry, Polygon):
        ext = Polygon(geometry.exterior)      
        for hole in geometry.interiors:
            if(hole.area > threshold): 
                ext = ext.difference(hole)

        return ext
    elif isinstance(geometry, MultiPolygon):
        cleaned_polygons = []
        for geom in list(geometry.geoms):
            ext = Polygon(geom.exterior)
            
            for hole in geom.interiors:
                if(hole.area > threshold): 
                    ext = ext.difference(hole)

            cleaned_polygons.append(ext)
        return MultiPolygon(cleaned_polygons)
    
    return geometry  # For non-polygon geometries, return as-is

def generatePolygons(parcelsFolder):
    for parcel in tqdm(os.listdir(parcelsFolder), desc="Looping through parcels"):
        parcelSubfolder = parcelsFolder + parcel + "/"
        for construction in tqdm([x for x in os.listdir(parcelSubfolder) if os.path.isdir(parcelSubfolder + x)],  desc="Working on constructions", leave=False):
            # Read files
            constructionFolder = parcelSubfolder + construction
            resultsFolder = constructionFolder + "/Plane Identification/"
            lasPath = resultsFolder + construction + ".laz"
            lasDF = laspy.read(lasPath)
            gpkgFile = constructionFolder + "/Map files/" + construction + ".gpkg"
            cadasterGDF = gpd.read_file(gpkgFile)
            points = lasDF.xyz
            labels = lasDF.classification
            # Obtain voronoi
            vorClipped = __getVoronoiClipped(lasDF.xyz, labels, cadasterGDF)
            vorClipped = vorClipped[vorClipped.cluster != 255].reset_index(drop=True)  

            # Obtain all parameters
            A_list = [] #Z = Ax+By+D
            B_list = []
            D_list = []
            tilt_list = []
            azimuth_list = []
            silhouette_list = []

            planes = []
            for idx in vorClipped.cluster:
                points = lasDF.xyz[np.where(lasDF.classification == idx)]
                planeParams = LinearRegression().fit(points[:, 0:2], points[:, 2])
                planes.append(planeParams)
                A_list.append(planeParams.coef_[0])
                B_list.append(planeParams.coef_[1])
                D_list.append(planeParams.intercept_)
                tilt,azimuth = __getTiltAzimuth([planeParams.coef_[0], planeParams.coef_[1], -1, planeParams.intercept_])
                tilt_list.append(tilt)
                azimuth_list.append(azimuth)

            vorClipped["A"] = A_list
            vorClipped["B"] = B_list                                                                                                                                                                                
            vorClipped["D"] = D_list
            vorClipped["tilt"] = tilt_list
            vorClipped["azimuth"] = azimuth_list
            vorClipped["plane"] = planes
            # Filter/Clean geometry
            vorClipped["geometry"] = vorClipped["geometry"].apply(lambda geom: __delete_polygons_by_area(geom, 1))
            vorClipped["geometry"] = vorClipped["geometry"].apply(lambda geom: __clean_holes(geom, 0.25))

            vorClipped = gpd.clip(vorClipped, cadasterGDF)
            vorClipped = vorClipped[~vorClipped["geometry"].apply(lambda geom: isinstance(geom, GeometryCollection))]
            vorClipped = vorClipped.reset_index(drop=True)

            # Delete overlaps between clusters, last identified plane goes first
            for i in reversed(range(len(vorClipped)-1)): 
                subsequent_geometries = unary_union(vorClipped.iloc[i+1:].geometry)
                if(vorClipped.geometry[i] != None):
                    vorClipped.at[i, 'geometry'] = vorClipped.geometry.iloc[i].difference(subsequent_geometries)

            vorClipped = vorClipped[vorClipped.geometry != None].reset_index(drop=True)
            vorClipped = vorClipped[vorClipped.geometry.area > 0].reset_index(drop=True)
            # Calculate silhouette here 
            silhouette_list = __getSilhouette(vorClipped, lasDF.xyz)
            try:
                vorClipped["silhouette"] = silhouette_list
            except Exception as e:
                print(parcel, construction, e)
            vorClipped = vorClipped.drop(columns="plane")
            # Export
            vorClipped.to_file(constructionFolder + "/Plane Identification/"+construction+".gpkg", driver="GPKG")      