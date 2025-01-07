import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import laspy
import os
import geopandas as gpd
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from matplotlib.ticker import ScalarFormatter
from matplotlib.colors import BoundaryNorm


from planeIdentification import *

basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
neighborhood = "Test_70_el Besòs i el Maresme"
parcelsFolder = basePath + "/Results/" + neighborhood + "/Parcels/"

fig, axs = plt.subplots(3, 3, figsize=(15, 15))

parcels = os.listdir(parcelsFolder)

colorMap = plt.cm.get_cmap('viridis')  # Adjust the colormap as needed
all_labels = []

for i, parcel in enumerate(parcels):
    subfolder = parcelsFolder + "/" + parcel + "/"
    fullDF = []

    for construction in [x for x in os.listdir(subfolder) if os.path.isdir(subfolder + x)]:
        lazFile = subfolder + construction + "/Map files/" + construction + ".laz"
      
        lasDF = laspy.read(lazFile)
        x, y, z = lasDF.xyz[:,0], lasDF.xyz[:,1], lasDF.xyz[:,2]
        pipeline = ClusterPipeline([
            HeightSplit(distance_threshold = 0.5)
        ])

        pipeline.fit(lasDF.xyz)
        lasDF.classification  = pipeline.final_labels
        labels = pipeline.final_labels

        fullDF.append((x, y, labels))

        all_labels.extend(labels)  # Collect all labels globally for normalization

    x, y, labels = np.hstack([arr[0] for arr in fullDF]), np.hstack([arr[1] for arr in fullDF]), np.hstack([arr[2] for arr in fullDF])

    ax = axs[i // 3, i % 3]
    scatter = ax.scatter(x, y, c=labels, s=1, cmap=colorMap)
    ax.set_aspect('equal')
    ax.set_xlabel('x (m)')
    ax.set_ylabel('y (m)')
    ax.set_title(parcel)

    for construction in [x for x in os.listdir(subfolder) if os.path.isdir(subfolder + x)]:
        gpkgFile = subfolder + construction + "/Map files/" + construction + ".gpkg"
        
        cadasterGDF = gpd.read_file(gpkgFile)
        cadasterGDF.plot(ax=ax, color='none', edgecolor='black')

    ax.xaxis.set_major_formatter(ScalarFormatter(useOffset=True))
    ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=True))
    ax.xaxis.set_major_locator(plt.MaxNLocator(4))

# Create a unique discrete colorbar for all results
fig.tight_layout()
min_label, max_label = min(all_labels), max(all_labels)
boundaries = range(min_label, max_label + 2)  # Define boundaries for discrete intervals
norm = BoundaryNorm(boundaries, ncolors=colorMap.N, clip=True)  # Use BoundaryNorm for discrete blocks

sm = ScalarMappable(cmap=colorMap, norm=norm)
sm._A = []  # Required for ScalarMappable

cbar = fig.colorbar(sm, ax=axs.ravel().tolist(), shrink=0.8, location='right', pad=0.05, aspect=30, ticks=range(min_label, max_label + 1))
cbar.set_label("Height Group")
cbar.ax.set_yticklabels([str(level) for level in range(min_label, max_label + 1)])  # Ensure labels are integers

print("Generated!")
plt.savefig("/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Scripts/Plane_Identification_Revised/nov22/heightSplit.png",bbox_inches='tight', dpi=300)
print("Saved!")