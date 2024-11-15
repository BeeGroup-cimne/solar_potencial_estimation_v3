
divide the cadaster map into heightgroup regions using voronoi
get the points of each heightgroup

for each heightgroup:
    n = 1
    while(termination criteria not met):
        for i = range(num_iterations) # let's do 5
            sample n points
            fit a plane for each point (consider inliers within 0.15 of each plane)
            while(not converging):
                compute centroids
                fit a plane for each point (consider inliers within 0.15 of each plane)
        select best score for current n
        compare this n best score with previous n's
        n++

    split the heighthroup polygon according to plane equations
    decide where each region belongs based on majority of points
    export polygons and plane info for each cluster