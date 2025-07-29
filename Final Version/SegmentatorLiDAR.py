import os
import laspy
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
import tqdm
import matplotlib.pyplot as plt

def building_clip(lidarFolder, parcelsFolder, buffer=0, filterConstructions=True):
    for parcel in tqdm.tqdm(os.listdir(parcelsFolder), desc="Clipping parcels"):
        subFolder = parcelsFolder + "/" + parcel + "/"

        # Find necessary LiDAR file(s)
        if(buffer == 0):
            lidarRequirements = subFolder + "necessaryLiDAR.txt"
            exportLasPath = subFolder + "/" + parcel + ".las"
        else:
            lidarRequirements = subFolder + "necessaryLiDAR_" + str(buffer)+ "m.txt"
            exportLasPath = subFolder + "/" + parcel + "_" + str(buffer)+ "m.las"

        with open(lidarRequirements, "r") as file:
            lidarList = [line.strip() for line in file if line.strip()]
        
        # Load gpkg
        parcelGeopackage = subFolder + "/" + parcel + ".gpkg"
        parcelGDF = gpd.read_file(parcelGeopackage)
        parcelGDF = parcelGDF.buffer(buffer)

        # Load necessary LiDAR files and clip (merge if needed)
        clippedlasDFs = []
        for filePath in tqdm.tqdm(lidarList, desc="Merging laz files", leave=False):
            fullFilePath = lidarFolder + "/" + filePath
            lasDF = laspy.read(fullFilePath)
        
            # Clip
            x = lasDF.x
            y = lasDF.y

            points = gpd.GeoSeries([Point(xy) for xy in zip(x, y)])
            # within_mask = points.within(parcelGDF.unary_union)
            within_mask = np.zeros(len(points), dtype=bool)
            for geom in parcelGDF.geometry:
                within_mask |= points.within(geom)
            clipped_points = lasDF.points[within_mask.values]
            clipped_las = laspy.LasData(lasDF.header)
            clipped_las.points = clipped_points
            
            clippedlasDFs.append(clipped_las)

        merged_las = clippedlasDFs[0]
        for las in clippedlasDFs[1:]:
            for dimension in merged_las.point_format.dimension_names:
                merged_data = np.concatenate([
                    getattr(merged_las, dimension),
                    getattr(las, dimension)
                ])
                setattr(merged_las, dimension, merged_data)

        # Export clipped (to be used later with constructions)
        merged_las.write(exportLasPath)

        # Now with constructions
        if(filterConstructions):
            for construction in tqdm.tqdm([x for x in os.listdir(subFolder) if os.path.isdir(subFolder + x)], desc="Clipping constructions", leave=False):
                # Load gpkg
                constructionFolder = subFolder + "/" + construction + "/"
                constructionGeopackage = constructionFolder + "/Map files/" + construction + ".gpkg"
                constructionGDF = gpd.read_file(constructionGeopackage)
                # Clip
                x = clipped_las.x
                y = clipped_las.y

                points = gpd.GeoSeries([Point(xy) for xy in zip(x, y)])
                within_mask = np.zeros(len(points), dtype=bool)
                for geom in constructionGDF.geometry:
                    within_mask |= points.within(geom)
                # within_mask = points.within(constructionGDF.unary_union)
                clipped_points_construction = clipped_las.points[within_mask.values]
                clipped_las_construction = laspy.LasData(clipped_las.header)
                clipped_las_construction.points = clipped_points_construction
                # Export clipped 
                exportLasPath = constructionFolder + "/Map files/" + construction + ".las"
                clipped_las_construction.write(exportLasPath)