import BuildingExtraction
import RequestLiDAR
import WeatherDownload
import SegmentatorLiDAR
from utils import create_output_folder

wd = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Final Version/"

parcelsFilePath = wd + "Data/SelectedParcels.gpkg"
constructionsFilePath = wd + "Data/SelectedConstructions.gpkg"

resultsFolder = wd + "Results/Experiment 1/"
create_output_folder(resultsFolder)

# Step 1: extract parcels and building
# BuildingExtraction.extract_parcels(parcelsFilePath, resultsFolder)
# BuildingExtraction.extract_constructions(constructionsFilePath, resultsFolder) # The filter msak may be upgraded

# Step 2: request LiDAR data
lidarFolder = wd + "Data/LiDAR/"
parcelsFolder = resultsFolder
# RequestLiDAR.download_LiDAR(lidarFolder, parcelsFolder, buffer=50)

# Step 3: download TMY data
TMYFolder = wd + "Data/TMY/"
# WeatherDownload.downloadTMY(parcelsFilePath, TMYFolder)

# Step 4, 5: clip LiDAR building and neighborhood
parcelsFolder = resultsFolder
lidarFolder = lidarFolder
# SegmentatorLiDAR.building_clip(lidarFolder, parcelsFolder)
SegmentatorLiDAR.building_clip(lidarFolder, parcelsFolder, buffer=50, filterConstructions=False)
