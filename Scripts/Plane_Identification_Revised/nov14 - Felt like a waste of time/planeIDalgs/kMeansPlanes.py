import laspy
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.neighbors import NearestNeighbors
import time
import matplotlib.pyplot as plt
import numpy as np

def compute_gradients(lasDF, normalized=False):
    if normalized:
        nbrs = NearestNeighbors(n_neighbors=10, algorithm='ball_tree').fit(lasDF[["x_norm","y_norm","z_norm"]])
        distances, indices = nbrs.kneighbors(lasDF[["x_norm","y_norm","z_norm"]])
    else:
        nbrs = NearestNeighbors(n_neighbors=10, algorithm='ball_tree').fit(lasDF[["x", "y", "z"]])
        distances, indices = nbrs.kneighbors(lasDF[["x", "y", "z"]])

    # Compute gradient for each point
    gradients = []
    for i, neighbors in enumerate(indices):
        # Get the 10 closest points for point i
        nearest_points = lasDF.iloc[neighbors]
        
        # Calculate the average gradient (difference in z over x, y) for the neighbors
        dz_dx = (nearest_points.z - lasDF.z.iloc[i]) / (nearest_points.x - lasDF.x.iloc[i])
        dz_dy = (nearest_points.z - lasDF.z.iloc[i]) / (nearest_points.y - lasDF.y.iloc[i])
        
        # Avoid division by zero
        dz_dx.replace([np.inf, -np.inf], np.nan, inplace=True)
        dz_dy.replace([np.inf, -np.inf], np.nan, inplace=True)
        
        # Calculate the magnitude of the gradient vector and take the mean
        gradient_magnitude = np.sqrt(dz_dx**2 + dz_dy**2).mean()
        gradients.append(gradient_magnitude)

    # Add the computed gradients to lasDF
    lasDF["gradient"] = gradients
    return lasDF

def kMeans_planes(lasDF):
    start = time.time()

    lasDF["x_norm"] = (lasDF.x - lasDF.x.min()) / (lasDF.x.max() - lasDF.x.min())
    lasDF["y_norm"] = (lasDF.y - lasDF.y.min()) / (lasDF.y.max() - lasDF.y.min())
    lasDF["z_norm"] = (lasDF.z - lasDF.z.min()) / (lasDF.z.max() - lasDF.z.min())
    lasDF = compute_gradients(lasDF, normalized=True)

    X = lasDF[["x_norm","y_norm","z_norm", "gradient"]]
    print(time.time() - start)

    bestFit = 0
    bestModel = []
    for k in range(2,3):
        kmeans = KMeans(n_clusters=k)
        y_pred = kmeans.fit_predict(X)
        score = silhouette_score(X, kmeans.labels_)
        if score > bestFit:
            bestFit = score
            bestModel = kmeans
            print(k, bestFit)
    
    lasDF["cluster"] = bestModel.predict(X)
    finish = time.time()
    print(finish-start)
    plt.scatter(lasDF.x, lasDF.y, c=lasDF.cluster, cmap='viridis', s=10)
    plt.axis("equal")  # Ensures the same scale for both axes
    plt.show()

if __name__ == "__main__":
    lazPath = "Results/Test_70_el Besòs i el Maresme/Parcels/4054901DF3845C/490/Map files/490.laz"
    lazFile = laspy.read(lazPath)
    xyz = lazFile.xyz

    lasDF = pd.DataFrame(xyz, columns=['x', 'y', 'z'])
    lasDF['r'] = lazFile.red/65535.0
    lasDF['b'] = lazFile.blue/65535.0
    lasDF['g'] = lazFile.green/65535.0
    lasDF['intensity'] = lazFile.intensity/65535.0
    kMeans_planes(lasDF)