import matplotlib.pyplot as plt
import geopandas as gpd
import laspy

basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
neighborhood = "Test_70_el Besòs i el Maresme"
parcelsFolder = basePath + "/Results/" + neighborhood + "/Parcels/"

parcel = "4151302DF3845A" # "4157903DF3845E" # 
construction = 139 # 86 # 
parcel = "4157903DF3845E" # 
construction = 86 # 
# parcel = "4054901DF3845C" # 
# construction = 490 # 
construction = str(construction)

lasPath = parcelsFolder + parcel + "/" + construction + "/Map files/" + construction + ".laz"
lasDF = laspy.read(lasPath)

gpkgFile = parcelsFolder + parcel + "/" + construction + "/Map files/" + construction + ".gpkg"
cadasterGDF = gpd.read_file(gpkgFile)

# cadasterGDF.plot(ax = plt.gca(), color='none', edgecolor='black')
# plt.scatter(lasDF.x, lasDF.y, c=lasDF.z)
# plt.gca().set_aspect('equal')
# plt.show()

from planeIdentification import *
from getVoronoiClipped import getVoronoiClipped

pipeline = ClusterPipeline([
    heightSplit(distance_threshold = 0.45),  # First clustering stage
    PlanesCluster(inlierThreshold=0.15, num_iterations=10, maxPlanes=20, iterationsToConverge=10)
    # DBSCAN(eps=1.5, min_samples=8),
])

# Fit the pipeline
pipeline.fit(lasDF.xyz)
vorClipped = getVoronoiClipped(lasDF.xyz, pipeline.final_labels, cadasterGDF)

# plot_clusters(lasDF.xyz, pipeline.final_labels, title="Final Stage Clustering")

vorClipped = vorClipped[vorClipped.cluster != -1]
vorClipped['cluster'] = [i for i in range(len(vorClipped))]

vorClipped.plot(ax = plt.gca(), column = 'cluster', edgecolor='black')
plt.legend(vorClipped['cluster'])
plt.title(f"{len(vorClipped):.0f} clusters found")
plt.show()