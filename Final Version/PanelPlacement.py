import json
import pandas as pd
import numpy as np
import os
import geopandas as gpd
import math
from tqdm import tqdm
import shapely.geometry
from shapely import oriented_envelope

from utils import create_output_folder

panelWidth = 1.879
panelHeight = 1.045

def __rect(polygon, tilt=0, size=[panelWidth, panelHeight], tol=0, clip=True, include_poly=False):

    a, b, c, d = gpd.GeoSeries(polygon).total_bounds

    xa = np.arange(a, c + 1, size[0])
    ya = np.arange(b, d + 1, size[1]*math.cos(tilt*math.pi/180))

    # offsets for tolerance
    if tol != 0:
        tol_xa = np.arange(0, tol * len(xa), tol)
        tol_ya = np.arange(0, tol * len(ya), tol)

    else:
        tol_xa = np.zeros(len(xa))
        tol_ya = np.zeros(len(ya))

    # combine placements of x&y with tolerance
    xat = np.repeat(xa, 2)[1:] + np.repeat(tol_xa, 2)[:-1]
    yat = np.repeat(ya, 2)[1:] + np.repeat(tol_ya, 2)[:-1]

    # create a grid
    grid = gpd.GeoSeries(
        [
            shapely.geometry.box(minx, miny, maxx, maxy)
            for minx, maxx in xat[:-1].reshape(len(xa) - 1, 2)
            for miny, maxy in yat[:-1].reshape(len(ya) - 1, 2)
        ]
    )

    if clip:
        grid = gpd.sjoin(
            gpd.GeoDataFrame(geometry=grid),
            gpd.GeoDataFrame(geometry=[polygon]),
            how="inner",
            predicate="within",
        )["geometry"]

    count = len(grid)

    if include_poly:
        grid = pd.concat(
            [
                grid,
                gpd.GeoSeries(
                    polygon.geoms
                    if isinstance(polygon, shapely.geometry.MultiPolygon)
                    else polygon
                ),
            ]
        )
    return grid, count

def placePanels(parcelsFolder):  
    for parcel in tqdm(os.listdir(parcelsFolder), desc="Panels: Parcels", leave=True):

        parcelSubfolder = parcelsFolder + parcel + "/"
        # if(parcel == "4649601DF3844H"):
        for construction in tqdm([x for x in os.listdir(parcelSubfolder) if os.path.isdir(parcelSubfolder + x)],  desc="Panels: Constructions", leave=False):
            # if(construction == "546"):
            try:
                constructionFolder = parcelSubfolder + construction + "/"
                solarFolder = constructionFolder + "Solar Estimation Panels/"
                create_output_folder(solarFolder, deleteFolder=True)

                planesFiles = constructionFolder + "Plane Identification/" + construction + ".gpkg"
                planeGDF = gpd.read_file(planesFiles)

                for i in range(len(planeGDF)):
                    row = planeGDF.iloc[i]

                    tilt = row.tilt
                    azimuth = row.azimuth
                    geom = row.geometry
                    centroid = geom.centroid
                
                    if(tilt > 5): # Non-horizontal
                        angle = azimuth
                    else: # Horizontal
                        orientedBB = oriented_envelope(geom)
                        coords = list(orientedBB.exterior.coords)

                        p1, p2 = coords[0], coords[1]
                        dx = p2[0] - p1[0]
                        dy = p2[1] - p1[1]
                        angle_radians = math.atan2(dy, dx)
                        angle = math.degrees(angle_radians)
        
                    try:
                        landscape_rotated = gpd.GeoSeries(geom).rotate(angle, origin=centroid)
                        landscape_grid, landscape_count = __rect(landscape_rotated.geometry[0], tilt=tilt, include_poly=False)

                        portrait_rotated = gpd.GeoSeries(geom).rotate(angle+90, origin=centroid)
                        portrait_grid, portrait_count = __rect(landscape_rotated.geometry[0], tilt=tilt, include_poly=False)

                        if(portrait_count > landscape_count):
                            grid_r = portrait_grid.rotate(-angle-90, origin=centroid)
                            count = portrait_count

                        else:
                            grid_r = landscape_grid.rotate(-angle, origin=centroid)
                            count = landscape_count

                        grid_r = gpd.GeoDataFrame(geometry=grid_r, crs=planeGDF.crs)
                        # grid_r["cluster"] = row.cluster

                        grid_r.to_file(solarFolder  + str(row.cluster) + ".gpkg")
                    except:
                        print(parcel, construction, row.cluster)
            except:
                print(parcel, construction, "ERROR")