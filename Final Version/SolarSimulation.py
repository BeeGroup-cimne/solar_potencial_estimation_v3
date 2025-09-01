import json
import pandas as pd
import numpy as np
import PySAM.Pvwattsv8 as PVWatts
import PySAM.Grid as Grid
import csv
import os
import geopandas as gpd
import math
import shutil 
from tqdm import tqdm
from itertools import accumulate
from shapely.geometry import Point, Polygon

from utils import create_output_folder

def __loadModules(file_names):
    pv = PVWatts.new()
    grid = Grid.from_existing(pv)

    with open(file_names[0], 'r') as file:
        data = json.load(file)
        for k, v in data.items():
                pv.value(k, v)

    with open(file_names[1], 'r') as file:
        data = json.load(file)
        for k, v in data.items():
                grid.value(k, v)

    return pv, grid


def __get_matrix(tilts):
    tilts = tilts.round()
    angles = np.unique(tilts)
    angles = np.arange(1, 90)

    azimuths = np.arange(0, 360, 1)

    matrix = []
    singleRow = []
    singleRow.append(0)
    for angle in azimuths:
        singleRow.append(angle)

    matrix.append(singleRow)
    for i, angle in enumerate(angles):
        singleRow = []
        singleRow.append(angle)
        for j, tilt in enumerate(tilts):
            if angle <= tilt:
                singleRow.append(100)
            else:
                singleRow.append(0)
        matrix.append(singleRow)
    return matrix

def __getInfoRoof(plane):
    tilt = plane.tilt.values[0]
    azimuth = plane.azimuth.values[0]
    area = plane.area.values[0]/math.cos(tilt*math.pi/180)
    return  area, tilt, azimuth

def __runPySAMSimulation(pysam_files, tilts, plane, tmyfile):
    pv, grid = __loadModules(pysam_files)
    shadingMatrix = __get_matrix(tilts)

    area, tilt, azimuth = __getInfoRoof(plane)
    
    ratio=0.400/(1.879*1.045)

    modifiedParams = {"shading_azal": shadingMatrix,
        "system_capacity": area*ratio, #*self.pv.value("gcr"), #We don't need the area by the ground coverage ratio
        "tilt": tilt,
        "azimuth": azimuth,
        "solar_resource_file": tmyfile}

    for i in range(len(modifiedParams)): 
        pv.value(list(modifiedParams.keys())[i], list(modifiedParams.values())[i])

    modules = [pv, grid]
    
    for m in modules:
        m.execute()

    # AC
    generation = pv.export()["Outputs"]["ac"]
    generation = np.array(generation).reshape(365, 24)
    generation_df = pd.DataFrame(generation)
    generation_df = generation_df/area
    annual_ac = generation_df.sum().sum() 
    # POA
    annual_poa = sum(pv.export()["Outputs"]["poa_monthly"])
    # DC
    DCOut = np.array(pv.export()["Outputs"]["dc"])
    annual_dc = np.sum(DCOut)/area

    return {"AC_Yearly": annual_ac,
            "POA_Yearly": annual_poa,
            "DC_Yearly": annual_dc}

    # elif(returnType=="DC"):
    #     days = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    #     cumulative_sum = list(accumulate(days))
    #     DCOut = np.array(pv.export()["Outputs"]["dc"]).reshape(365, 24)/area
    #     averages = np.zeros((12,24))
    #     for month in range(12):
    #         for hour in range(24):
    #             averages[month,hour] = np.average(DCOut[cumulative_sum[month]:cumulative_sum[month+1],hour])
    #     averages = averages.reshape(12*24)
    #     averages = ','.join(map("{:.6f}".format, annual))
    #     return averages



def simulatePySAM(parcelsFolder, tmyfile, pysam_files):
    for parcel in tqdm(os.listdir(parcelsFolder), desc="Parcels", leave=True):
        parcelSubfolder = parcelsFolder + parcel + "/"
        for construction in tqdm([x for x in os.listdir(parcelSubfolder) if os.path.isdir(parcelSubfolder + x)],  desc="Constructions", leave=False):
            try:
                constructionFolder = parcelSubfolder + construction + "/"
                solarFolder = constructionFolder  + "Solar Estimation PySAM Yearly/"
                create_output_folder(solarFolder, deleteFolder=True)
                
                planesGDF = gpd.read_file(constructionFolder + "Plane Identification/" + construction + ".gpkg")
                
                for cluster in tqdm(planesGDF.cluster.values, desc="Clusters", leave=False):
                    shadingFile = constructionFolder + "/Shading/" + str(cluster) + ".csv"
                    plane = planesGDF[planesGDF.cluster == cluster]
                    point_list = []
                    ac_annual_list = []
                    dc_annual_list = []
                    poa_annual_list = []

                    if os.path.isfile(shadingFile):
                        if(os.stat(shadingFile).st_size > 0):
                            shadingProfilesDF = pd.read_csv(shadingFile, header=None)
                            for i in tqdm(range(len(shadingProfilesDF)), desc="Sampled points", leave=False):
                                coords = shadingProfilesDF.iloc[i][0:3]
                                tilts = shadingProfilesDF.iloc[i][3:363]

                                annual = __runPySAMSimulation(pysam_files, tilts, plane, tmyfile)
                                point_list.append(coords)
                                ac_annual_list.append(annual["AC_Yearly"])
                                dc_annual_list.append(annual["DC_Yearly"])
                                poa_annual_list.append(annual["POA_Yearly"])

                    solarDF = pd.DataFrame({"x": [point[0] for point in point_list], 
                                            "y": [point[1] for point in point_list], 
                                            "z": [point[2] for point in point_list], 
                                            "POA_yearly": poa_annual_list,
                                            "DC_yearly": dc_annual_list,
                                            "AC_yearly": ac_annual_list,
                                            })
                    solarDF.to_csv(solarFolder + str(cluster) + ".csv", index=False)              
            except Exception as e:
                print(parcel, construction, e)

def panelYearly(parcelsFolder):
    for parcel in tqdm(os.listdir(parcelsFolder), desc="Parcels", leave=True):
        parcelSubfolder = parcelsFolder + parcel + "/"
        for construction in tqdm([x for x in os.listdir(parcelSubfolder) if os.path.isdir(parcelSubfolder + x)],  desc="Constructions", leave=False):
            try:
                constructionFolder = parcelSubfolder + construction + "/"
                solarFolder = constructionFolder + "Solar Estimation Panels Simulated/"
                create_output_folder(solarFolder, deleteFolder=True)
                        
                allSunDC = pd.DataFrame()
                sunPath = parcelsFolder + parcel + "/" + construction + "/Solar Estimation PySAM Yearly/"

                for file in os.listdir(sunPath):
                    allSunDC = pd.concat([allSunDC, pd.read_csv(sunPath + file)], ignore_index=True)

                allSunDC["annual"] = allSunDC["DC_yearly"]/1000*(1.879*1.045)

                panelsGDFs = []
                panelsPath = parcelsFolder + parcel + "/" + construction + "/Solar Estimation Panels/"

                for file in os.listdir(panelsPath):
                    panelsGDFs.append(gpd.read_file(panelsPath + file))

                for panels in panelsGDFs:
                    yearlyList = []
                    for panelID in range(len(panels)):
                        panel = panels.iloc[panelID].geometry

                        allSunDC["inside_panel"] = allSunDC.apply(lambda row: panel.contains(Point(row["x"], row["y"])), axis=1)
                        if(len(allSunDC[allSunDC["inside_panel"]]) == 0):
                            print("No shading in", parcel, construction)
                        # Filter points inside the panel and calculate the average annual
                        average_annual = allSunDC[allSunDC["inside_panel"]]["annual"].mean()
                        yearlyList.append(average_annual)
                    panels["yearly"] = yearlyList

                combined_gdf = gpd.GeoDataFrame(pd.concat(panelsGDFs, ignore_index=True))
                combined_gdf.to_file(solarFolder + construction + ".gpkg")
            except:
                print(" ", parcel, construction, " ")