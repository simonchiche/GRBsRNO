import numpy as np
import matplotlib.pyplot as plt

# Exemple de données (remplace par ton catalogue SVOM)
ra = np.array([10, 120, 200, 250])     # en degrés
dec = np.array([-20, 0, 30, 60])       # en degrés

plt.figure(figsize=(8, 4.5))

# Scatter plot
plt.scatter(ra, dec, s=40, c='red', label='GRBs')

# Axes
plt.xlabel("Right Ascension (deg)")
plt.ylabel("Declination (deg)")
plt.title("Sky map (RA, Dec)")

# Convention astro: RA augmente vers la gauche (optionnel mais standard)
plt.gca().invert_xaxis()

# Limits
plt.xlim(0, 360)
plt.ylim(-90, 90)

plt.grid(True, alpha=0.3)
plt.legend()

plt.show()