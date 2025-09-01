import BuildingExtraction
import RequestLiDAR
import WeatherDownload
import SegmentatorLiDAR
import Cluster
import PolygonObtention
import Shading
import PanelPlacement
import SolarSimulation

from utils import create_output_folder, copy_folder

wd = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Final Version/"

parcelsFilePath = wd + "Data/SelectedParcels.gpkg"
constructionsFilePath = wd + "Data/SelectedConstructions.gpkg"

resultsFolder = wd + "Results/Experiment 1/"
parcelsFolder = resultsFolder
create_output_folder(parcelsFolder)

# Step 1: extract parcels and building
# BuildingExtraction.extract_parcels(parcelsFilePath, resultsFolder)
# BuildingExtraction.extract_constructions(constructionsFilePath, resultsFolder) # The filter msak may be upgraded

# Step 2: request LiDAR data
lidarFolder = wd + "Data/LiDAR/"
# RequestLiDAR.download_LiDAR(lidarFolder, parcelsFolder, buffer=50)

# Step 3: download TMY data
TMYFolder = wd + "Data/TMY/"
# WeatherDownload.downloadTMY(parcelsFilePath, TMYFolder)

# Step 4, 5: clip LiDAR building and neighborhood
lidarFolder = lidarFolder
# SegmentatorLiDAR.building_clip(lidarFolder, parcelsFolder) # This could be optimized if buffered and nonbuffered laz were simultaneously generated
# SegmentatorLiDAR.building_clip(lidarFolder, parcelsFolder, buffer=50, filterConstructions=False)

# Optional steps 12345: copy from another directoy (for multiple experiments)
# originalFolder = resultsFolder
# outputFolder = wd + "Results/Experiment 3/"
# copy_folder(originalFolder, outputFolder)
# parcelsFolder = outputFolder

# Step 6: cluster
pipeline = Cluster.ClusterPipeline([
    Cluster.HeightSplit(distance_threshold = 0.45),  # First clustering stage
    Cluster.kPlanes(inlierThreshold=0.15, num_iterations=5, maxPlanes=6)
    # Cluster.PlaneExtraction(inlierThreshold=0.3, num_iterations=50)
])
Cluster.assign_clusters(parcelsFolder, pipeline)

# Step 7: convert clusters to polygons
PolygonObtention.generatePolygons(parcelsFolder)

# # # Step 8: compute shading
# # Shading.computeShading(parcelsFolder)

# # # Step 9: place panels
# # PanelPlacement.placePanels(parcelsFolder)

# # # Step 10: simulate energy
# # tmyfile = TMYFolder + "419806_41.41_2.22_tmy-2022.csv"
# # pysam_files = ["/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Scripts/sunEstimation/pysam_template_pvwattsv8.json",
# #     "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Scripts/sunEstimation/pysam_template_grid.json"]
# # SolarSimulation.simulatePySAM(parcelsFolder, tmyfile, pysam_files) # Results are in Wh/m² for genertaed energy and kWh/m² for radiation
# # SolarSimulation.panelYearly(parcelsFolder)