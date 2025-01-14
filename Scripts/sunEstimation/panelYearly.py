import matplotlib.pyplot as plt 
import pandas as pd 
import numpy as np 
import geopandas as gpd 
import os
import json
from itertools import accumulate
from shapely.geometry import Point, Polygon
import matplotlib.colors as mcolors
from tqdm import tqdm
import shutil


import warnings
warnings.filterwarnings("ignore")


days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

def create_output_folder(directory, deleteFolder = False):
    if not(os.path.isdir(directory)):
        os.makedirs(directory)
    else:
        if(deleteFolder):
            shutil.rmtree(directory)
            os.makedirs(directory)


basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
neighborhood = "Test_70_el Besòs i el Maresme"
# neighborhood = "70_el Besòs i el Maresme"
parcelsFolder = basePath + "/Results/" + neighborhood + "/Parcels/"

for parcel in tqdm(os.listdir(parcelsFolder), desc="Parcels", leave=True):
    # if(parcel == "4649601DF3844H"): 
        parcelSubfolder = parcelsFolder + parcel + "/"
        for construction in tqdm([x for x in os.listdir(parcelSubfolder) if os.path.isdir(parcelSubfolder + x)],  desc="Constructions", leave=False):
            # if(construction == "546"):
                try:
                    constructionFolder = parcelSubfolder + construction + "/"
                    solarFolder = constructionFolder + "Solar Estimation Panels Simulated/"
                    create_output_folder(solarFolder, deleteFolder=True)
                            
                    allSunDC = pd.DataFrame()
                    sunPath = parcelsFolder + parcel + "/" + construction + "/Solar Estimation PySAM_DC_Yearly/"

                    for file in os.listdir(sunPath):
                        allSunDC = pd.concat([allSunDC, pd.read_csv(sunPath + file)], ignore_index=True)

                    allSunDC["annual"] = allSunDC["annual"]/1000*(1.879*1.045)

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