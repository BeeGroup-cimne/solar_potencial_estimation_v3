import numpy as np
import pandas as pd 
import matplotlib.pyplot as plt 
import os
import shutil
import json
import geopandas as gpd
import math
from shapely.geometry import Polygon
from PIL import Image
from tqdm import tqdm

import warnings
warnings.filterwarnings("ignore")

def create_output_folder(directory, deleteFolder = False):
    if not(os.path.isdir(directory)):
        os.makedirs(directory)
    else:
        if(deleteFolder):
            shutil.rmtree(directory)
            os.makedirs(directory)

# Load all Google Results into a giant dataframe
basePathGoogle = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/GoogleAPItests/Results/"
basePathParcels = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Results/Test_70_el Besòs i el Maresme/Parcels/"
basePathResults = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Results/Test_70_el Besòs i el Maresme/GoogleComparison/"

parcelList = []
contructionList = []
planeIDList = []
centroidLatList = []
centroidLonList = []
azimuthList = []
tiltList =  []
areaList = []

import tifffile as tiff

for parcel in tqdm(os.listdir(basePathGoogle)):
    for construction in os.listdir(basePathGoogle + parcel):
        create_output_folder(basePathResults + parcel + "/" + construction + "/Google Annual Flux/")
        responseFile = basePathGoogle + parcel + "/" + construction + "/annualFlux.tiff"

        with tiff.TiffFile(responseFile) as tif:
            for i, page in enumerate(tif.pages):
                image = page.asarray()
                
        topY = tif.geotiff_metadata["ModelTransformation"][1][3]
        leftX = tif.geotiff_metadata["ModelTransformation"][0][3]

        PoAfolder = basePathParcels + parcel + "/" + construction + "/Solar Estimation PySAM_POA_Yearly/"
        for file in os.listdir(PoAfolder):
            points = pd.read_csv(PoAfolder + file)
            googleFluxList = []
            for idx, point in points.iterrows():
                pixelX = int((point["x"]-leftX)/0.1)
                pixelY = int((topY-point["y"])/0.1)
                googleFluxList.append(image[pixelX][pixelY])
            points.rename(columns={"annual":"simulatedFlux"})
            points["googleFlux"] = googleFluxList
            points.to_csv(basePathResults + parcel + "/" + construction + "/Google Annual Flux/" + file, index=None)