import numpy as np
from sklearn.linear_model import LinearRegression

def planarSilhouette(X, labels):
    # Fit a plane for each group of labels
    planes = []
    uniqueLabels, inverse = np.unique(labels, return_inverse=True)
    for label in uniqueLabels:
        mask = (labels == label)
        subsetX = X[mask]
        plane = LinearRegression().fit(subsetX[:,0:2], subsetX[:,2])
        planes.append(plane)

    # Drop planes with a -1 label
    mask = (labels != -1)
    actualInliers = X[mask]
    identifiedLabels = labels[mask]
    inverseIdentified = inverse[mask]

    # if dataset if empty, return 0
    if(len(actualInliers) == 0):
        return 0
    
    # if there's only a plane and no outliers, return 0 (we don't trust it)
    if(len(uniqueLabels) == 1):
        return 0

    # compute all vertical distances from every point to every plane
    distances = np.zeros((actualInliers.shape[0], len(planes)))
    for plane_idx in range(len(planes)):
        distances[:, plane_idx] = abs(actualInliers[:,2] - planes[plane_idx].predict(actualInliers[:,0:2]))

    # keep the one referring to their labels as their actual distance (a_i), 
    a = distances[np.arange(distances.shape[0]), inverseIdentified]
    
    # and the next closest as the neighbor distance (b_i)
    rows = np.arange(distances.shape[0])
    cols = inverseIdentified            
    mask = np.ones_like(distances, dtype=bool)
    mask[rows, cols] = False  
    neighborDistances = distances[mask].reshape(distances.shape[0], distances.shape[1] - 1)
    if neighborDistances.shape[1] == 1:
        b = neighborDistances
    else:
        b = np.min(neighborDistances, axis=1)
    # compute silhouette s_i = (b_i - a_i)/max(b_i, a_i)
    s = (b - a) / np.maximum(b, a)
    return np.mean(s)