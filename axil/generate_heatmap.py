import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import os

# Charger les données
df = pd.read_csv("app_trace.csv")

# Calcul de la moyenne UX par application et par catégorie
pivot = df.pivot_table(index="app_name", columns="category", values="global_ux_value", aggfunc="mean")

# Tracer la heatmap
plt.figure(figsize=(10, 6))
sns.heatmap(pivot, annot=True, fmt=".2f", cmap="YlGnBu")
plt.title("Heatmap des scores UX moyens par application et par catégorie")
plt.ylabel("Application")
plt.xlabel("Catégorie")
plt.tight_layout()
os.makedirs("graphs", exist_ok=True)
plt.savefig("graphs/heatmap_ux_par_categorie.png")
plt.show()
