# install.packages("deldir")
library(deldir)

# Data
set.seed(1)
x <- runif(50)
y <- runif(50)

# Calculate Voronoi Tesselation and tiles
tesselation <- deldir(x, y)
tiles <- tile.list(tesselation)

# Circle
s <- seq(0, 2 * pi, length.out = 3000)
circle <- list(x = 0.5 * (1 + cos(s)),
               y = 0.5 * (1 + sin(s)))

plot(tiles, pch = 19,
     col.pts = "white",
     border = "white",
     fillcol = hcl.colors(50, "viridis"),
     clipp = circle)