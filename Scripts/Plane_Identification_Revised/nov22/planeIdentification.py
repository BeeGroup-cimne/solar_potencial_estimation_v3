import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
import laspy
from shapely.geometry import MultiPolygon, Polygon
from sklearn.linear_model import LinearRegression
from sklearn.metrics import root_mean_squared_error

class ClusterPipeline:
    def __init__(self, clustering_stages):
        self.clustering_stages = clustering_stages # Each stage is a clustering class

    def fit(self, X, y=None):
        self.stage_labels = []
        self.final_labels = np.zeros(X.shape[0], dtype=str)
        
        current_data = X 
        current_labels = np.zeros(X.shape[0], dtype=int)  # Initialize labels

        for stage in self.clustering_stages:
            
            new_labels = np.zeros_like(current_labels)  # New labels for this stage
            unique_clusters = np.unique(current_labels)  # Unique clusters in current stage
            cluster_offset = 0 

            for cluster_id in unique_clusters:
                
                cluster_data = current_data[current_labels == cluster_id]
                if len(cluster_data) < 3:  # Skip small clusters
                    continue
                
                # Fit the clustering algorithm to the current cluster
                stage.fit(cluster_data)
                cluster_stage_labels = stage.labels_

                # Assign new labels offset by cluster_offset
                new_labels[current_labels == cluster_id] = (cluster_stage_labels + cluster_offset)
                cluster_offset += len(np.unique(cluster_stage_labels)) # Update cluster offset for the next unique label
                

            # Store the stage labels and update current labels
            self.stage_labels.append(new_labels.copy())
            current_labels = new_labels
            
        self.final_labels = self.stage_labels[-1]
        return self

class heightSplit():
    def __init__(self, distance_threshold=0.45):
        self.distance_threshold = distance_threshold
        
    def fit(self, X):
        n_samples, n_features = X.shape

        X = X[X[:, 2].argsort()]
        
        deltaZ = np.diff(X[:,2], prepend=0)
        
        labels = np.zeros_like(deltaZ, dtype=int)

        current_label = 0
        for i in range(1, len(deltaZ)):
            if deltaZ[i] > self.distance_threshold:
                current_label += 1
            labels[i] = current_label

        self.labels_ = labels
        return self

    def predict(self, X):
        pass

    def fit_predict(self, X, y=None):
        self.fit(X)
        return self.labels_
    
class PlanesCluster():
    def __init__(self, inlierThreshold=0.15, num_iterations=10, maxPlanes=20, iterationsToConverge=10):
        self.inlierThreshold = inlierThreshold
        self.num_iterations = num_iterations
        self.maxPlanes = maxPlanes
        self.iterationsToConverge = iterationsToConverge

    def sampleFar(self, X, n_planes):
        centroids = np.zeros((n_planes, X.shape[1]))
        index = np.random.choice(X.shape[0], 1)
        centroids[0, :] = X[index,:]
        distances = np.zeros((X.shape[0], n_planes-1))
        for i in range(1, n_planes):
            distances[:, i-1] = (np.linalg.norm(X[:,:] - centroids[i-1,:], axis=1))
            average_distances = distances.mean(axis=1)
            normalized_distances = average_distances / average_distances.sum()
            selected_index = np.random.choice(len(X), p=normalized_distances)
            centroids[i, :] = X[selected_index,:]
        return centroids
        
    def sample2Close(self, X, centroids):
        triplets = np.zeros((centroids.shape[0], X.shape[1], 3)) # n_planes * 3 coordinates * 3 points/plane
        for i in range(len(centroids)):
            triplets[i, 0, :] = centroids[i]
            # sample two points
            distances = np.linalg.norm(X[:,:] - centroids[i,:], axis=1)
            closeness = distances.max() - distances
            probabilities = closeness / closeness.sum()
            # probabilities = probabilities**2
            # probabilities /= probabilities.sum()
            selected_indexes = np.random.choice(len(X), 2, p=probabilities)
            # selected_indexes = np.random.choice(len(X), 2)
            triplets[i, 1:3, :] = X[selected_indexes,:]
        return triplets

    def fit(self, X):
        best_score = -np.inf
        best_labels = []    

        scores_ = []
        for n_planes in range(1, self.maxPlanes+1):
            best_score_n = -np.inf
            best_labels_n = []    

            for i in range(self.num_iterations):
                # Sample points and get planes
                centroids = self.sampleFar(X, n_planes)
                triplets = self.sample2Close(X, centroids)

                planes = []
                for triplet in triplets:
                    reg = LinearRegression().fit(triplet[:,0:2], triplet[:,2])
                    planes.append(reg)
                
                # Compute distances and find inliers
                distances = np.zeros((X.shape[0], n_planes))
                for plane_idx in range(len(planes)):
                    distances[:, plane_idx] = abs(X[:,2] - planes[plane_idx].predict(X[:,0:2]))
                labels = np.argmin(distances, axis=1)

                selected_distances = np.array([distances[i, idx] for i, idx in enumerate(labels)])
                labels[np.where(selected_distances > self.inlierThreshold)[0]] = -1
                
                lastLabels = labels
                oldPlanes = planes
                for j in range(self.iterationsToConverge):
                    planes = []
                    for k in range(n_planes):
                        try:
                            reg = LinearRegression().fit(X[np.where(labels == k)[0],0:2], X[np.where(labels == k)[0],2])
                            planes.append(reg)
                        except:
                            pass
                    distances = np.zeros((X.shape[0], n_planes))

                    for plane_idx in range(len(planes)):
                        distances[:, plane_idx] = abs(X[:,2] - planes[plane_idx].predict(X[:,0:2]))
                    labels = np.argmin(distances, axis=1)

                    selected_distances = np.array([distances[i, idx] for i, idx in enumerate(labels)])
                    labels[np.where(selected_distances > self.inlierThreshold)[0]] = -1
                    
                    if(np.array_equal(lastLabels, labels)):
                        break
                    else:
                        lastLabels = labels
                        oldPlanes = planes

                if(not np.array_equal(lastLabels, labels)): print("Did not converge")
                
                inliers = X[np.where(labels != -1)[0]]
                labelsScore = labels[np.where(labels != -1)[0]]
                prediction = np.zeros((inliers.shape[0]))
                for plane_idx in range(len(planes)):
                    try:
                        prediction[np.where(labelsScore == plane_idx)[0]] = planes[plane_idx].predict(inliers[np.where(labelsScore == plane_idx)[0],0:2])
                    except:
                        pass
                rmse = root_mean_squared_error(inliers[:,2], prediction)
                if(len(planes) == 0):
                    score = 0
                else:
                    score = len(inliers)/len(X)*1/rmse #1/len(planes)
                
                if(score > best_score_n):
                    best_score_n = score
                    best_labels_n = labels    

            if(best_score_n > best_score):
                best_score = best_score_n
                best_labels = best_labels_n

            scores_.append(best_score_n)
            # else:
            #     break
        self.scores_ = scores_ 
        self.labels_ = best_labels
        return self

    def predict(self, X):
        pass

    def fit_predict(self, X, y=None):
        self.fit(X)
        return self.labels_