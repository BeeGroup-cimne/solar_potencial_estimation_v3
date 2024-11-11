# Install necessary packages if not already installed
# install.packages("leaflet")
# install.packages("deldir")
library(leaflet)
library(deldir)
library(viridis)  # For viridis colormap
library(sp)  # For spatial operations

# Data (New York City bounds)
set.seed(1)
x <- runif(50, min = -74.2591, max = -73.7004)  # Longitude range for NYC
y <- runif(50, min = 40.4774, max = 40.9176)    # Latitude range for NYC

# Random values for each point (e.g., 1 to 100)
values <- runif(50, min = 1, max = 100)

# Calculate Voronoi Tesselation and tiles
tesselation <- deldir(x, y)
tiles <- tile.list(tesselation)

# Create a leaflet map centered around New York City
m <- leaflet() %>%
  addTiles() %>%  # Add default OpenStreetMap tiles
  setView(lng = mean(x), lat = mean(y), zoom = 12)

# Function to convert Voronoi tiles to leaflet polygon format
voronoi_to_polygon <- function(tile, offset = c(0, 0)) {
  data.frame(
    lat = tile$y + offset[2],
    lng = tile$x + offset[1]
  )
}

# Loop through each tile and add polygons to the map
for (tile in tiles) {
  # Find the value of the point inside the current Voronoi tile
  point_index <- tile$pt.region
  point_value <- values[point_index]  # Value corresponding to the point in the tile
  
  # Convert each Voronoi tile into a data frame of lat/lng coordinates
  polygon_data <- voronoi_to_polygon(tile)
  
  # Choose color based on the point value (e.g., scale between "blue" and "red")
  color <- viridis(100)[runif(1, min = 1, max = 100)] 
  
  # Add the Voronoi polygon to the map
  m <- m %>%
    addPolygons(lng = polygon_data$lng, lat = polygon_data$lat, 
                fillColor = color, weight = 1, opacity = 0.5, fillOpacity = 0.5)
}

# Display the map
m
