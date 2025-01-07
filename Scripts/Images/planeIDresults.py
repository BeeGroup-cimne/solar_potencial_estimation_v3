import numpy as np 
import pandas as pd 
import matplotlib.pyplot as plt 
import laspy
import os
import math
from matplotlib import cm
from matplotlib.colors import ListedColormap
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize, ListedColormap, BoundaryNorm
import matplotlib.colors as mcolors

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import laspy
import os
import geopandas as gpd
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
import matplotlib.patches as mpatches
from matplotlib.ticker import ScalarFormatter


from planeIdentification import *

basePath = "/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/"
neighborhood = "Test_70_el Besòs i el Maresme"
parcelsFolder = basePath + "/Results/" + neighborhood + "/Parcels/"

fig, axs = plt.subplots(3, 3, figsize=(12.5, 12.5), dpi=200)

parcels = os.listdir(parcelsFolder)

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

    x, y, labels = np.hstack([arr[0] for arr in fullDF]), np.hstack([arr[1] for arr in fullDF]), np.hstack([arr[2] for arr in fullDF])

    ax = axs[i // 3, i % 3]
    scatter = ax.scatter(x, y, c=z, s=1, cmap='viridis')
    ax.set_aspect('equal')
    ax.set_xlabel('x (m)')
    ax.set_ylabel('y (m)')
    ax.set_title(parcel)

    norm = Normalize(vmin=labels.min(), vmax=labels.max())
    cbar = fig.colorbar(ScalarMappable(norm=norm, cmap='viridis'), ax=ax)
    cbar.set_label('Height group')

    for construction in [x for x in os.listdir(subfolder) if os.path.isdir(subfolder + x)]:
        gpkgFile = subfolder + construction + "/Map files/" + construction + ".gpkg"
        
        cadasterGDF = gpd.read_file(gpkgFile)
        cadasterGDF.plot(ax=ax, color='none', edgecolor='black')

    ax.xaxis.set_major_formatter(ScalarFormatter(useOffset=True))
    ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=True))
    ax.xaxis.set_major_locator(plt.MaxNLocator(4))

# # Create colorbar with discrete ticks
# cb = plt.colorbar(scatter)
# cb.set_label('Height clusters')
# cb.set_ticks(np.arange(len(unique_clusters)))  # Set ticks to the number of unique clusters
# cb.set_ticks(unique_clusters)  # Ensure the ticks match the clusters

plt.tight_layout()
print("Generated!")
plt.savefig("/home/jaumeasensio/Documents/Projectes/BEEGroup/solar_potencial_estimation_v3/Scripts/Images/heightSplit.png",bbox_inches='tight', dpi=300)
print("Saved!")