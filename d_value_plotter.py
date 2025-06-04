import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

# Fixed SEM
sem = 0.1

# Range of distances from the mean
distances_from_mean = np.linspace(0, 1, 500)

standard_errors = distances_from_mean / sem



# Compute confidence for each distance
confidence = 2 * norm.cdf(standard_errors) - 1

# Plot
plt.figure(figsize=(8, 5))
plt.plot(distances_from_mean, confidence * 100)
plt.xlabel("Distance from True Mean")
plt.ylabel("Confidence (%)")
plt.title(f"Confidence vs Distance from Mean (SEM = {sem})")
plt.grid(True)
plt.ylim(0, 100)
plt.show()
