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


def create_output_folder(directory, deleteFolder = False):
    if not(os.path.isdir(directory)):
        os.makedirs(directory)
    else:
        if(deleteFolder):
            shutil.rmtree(directory)
            os.makedirs(directory)

def loadModules(file_names):
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

def get_matrix(tilts):
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

def getInfoRoof(plane):
    tilt = plane.tilt.values[0]
    azimuth = plane.azimuth.values[0]
    area = plane.area.values[0]/math.cos(tilt*math.pi/180)
    return  area, tilt, azimuth


def runPySAMSimulation(file_names, tilts, plane, tmyfile, returnType):
    pv, grid = loadModules(file_names)
    shadingMatrix = get_matrix(tilts)
    # print(shadingMatrix)

    area, tilt, azimuth = getInfoRoof(plane)
    
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

    if(returnType=="AC"):
        generation = pv.export()["Outputs"]["ac"]
        generation = np.array(generation).reshape(365, 24)
        generation_df = pd.DataFrame(generation)
        generation_df = generation_df/area
        annual_ac = generation_df.sum().sum() 
        return annual_ac
    elif(returnType=="POA_Y"):
        return sum(pv.export()["Outputs"]["poa_monthly"])

    elif(returnType=="DC"):
        days = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        cumulative_sum = list(accumulate(days))
        DCOut = np.array(pv.export()["Outputs"]["dc"]).reshape(365, 24)/area
        averages = np.zeros((12,24))
        for month in range(12):
            for hour in range(24):
                averages[month,hour] = np.average(DCOut[cumulative_sum[month]:cumulative_sum[month+1],hour])
        averages = averages.reshape(12*24)
        averages = ','.join(map("{:.6f}".format, annual))
        return averages
    
    elif(returnType=="DC_Year"):
        DCOut = np.array(pv.export()["Outputs"]["dc"])
        return np.sum(DCOut)/area

file_names = ["/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Scripts/sunEstimation/pysam_template_pvwattsv8.json",
    "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Scripts/sunEstimation/pysam_template_grid.json"]

tmyfile = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/RAW_Data/TMY/NREL/419806_41.41_2.22_tmy-2022.csv"

basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
neighborhood = "Test_70_el Besòs i el Maresme"
# neighborhood = "70_el esòs i el Maresme"
parcelsFolder = basePath + "/Results/" + neighborhood + "/Parcels/"

annual_ac = 0

for parcel in tqdm(os.listdir(parcelsFolder), desc="Parcels", leave=True):
    if((parcel == "4054901DF3845C") or (parcel == "4649601DF3844H")):
        parcelSubfolder = parcelsFolder + parcel + "/"
        for construction in tqdm([x for x in os.listdir(parcelSubfolder) if os.path.isdir(parcelSubfolder + x)],  desc="Constructions", leave=False):
            if((construction == "242") or (construction == "342") or (construction == "550") or (construction == "557")):
                # try:
                    constructionFolder = parcelSubfolder + construction + "/"
                    solarFolder = constructionFolder + "Solar Estimation PySAM_DC_Yearly/"
                    create_output_folder(solarFolder, deleteFolder=True)

                    planesGDF = gpd.read_file(constructionFolder + "Plane Identification/" + construction + ".gpkg")
                    for cluster in tqdm(planesGDF.cluster.values, desc="Clusters", leave=False):
                        shadingFile = constructionFolder + "/Shading/" + str(cluster) + ".csv"
                        plane = planesGDF[planesGDF.cluster == cluster]
                        point_list = []
                        annual_list = []
                        if os.path.isfile(shadingFile):
                            if(os.stat(shadingFile).st_size > 0):
                                shadingProfilesDF = pd.read_csv(shadingFile, header=None)
                                for i in tqdm(range(len(shadingProfilesDF)), desc="Sampled points", leave=False):
                                    coords = shadingProfilesDF.iloc[i][0:3]
                                    tilts = shadingProfilesDF.iloc[i][3:363]

                                    annual = runPySAMSimulation(file_names, tilts, plane, tmyfile, "DC_Year")
                                    point_list.append(coords)
                                    annual_list.append(annual)

                        solarDF = pd.DataFrame({"x": [point[0] for point in point_list], 
                                                "y": [point[1] for point in point_list], 
                                                "z": [point[2] for point in point_list], 
                                                "annual": annual_list})
                        solarDF.to_csv(solarFolder + str(cluster) + ".csv", index=False)       
                # except:
                #     print(parcel, construction)