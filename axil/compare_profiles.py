import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

df = pd.read_csv("metrics.csv")
df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")

# Si pas de colonne 'profile', utiliser 'mode'
if "profile" not in df.columns:
    df["profile"] = df["mode"]

# Résumé par profil
summary = df.groupby("profile")[["global_ux", "apps_deployed", "total_bw"]].mean().reset_index()

# Créer le dossier
os.makedirs("graphs", exist_ok=True)

# UX moyenne par profil
plt.figure(figsize=(10, 6))
sns.barplot(data=summary, x="profile", y="global_ux")
plt.title("UX moyenne par profil")
plt.ylabel("UX globale")
plt.xlabel("Profil utilisateur")
plt.tight_layout()
plt.savefig("graphs/profil_vs_ux_globale.png")
plt.close()

# Apps déployées
plt.figure(figsize=(10, 6))
sns.barplot(data=summary, x="profile", y="apps_deployed")
plt.title("Nombre moyen d'apps déployées")
plt.ylabel("Applications")
plt.xlabel("Profil")
plt.tight_layout()
plt.savefig("graphs/profil_vs_apps_deployees.png")
plt.close()

# Bande passante utilisée
plt.figure(figsize=(10, 6))
sns.barplot(data=summary, x="profile", y="total_bw")
plt.title("Bande passante moyenne par profil")
plt.ylabel("kbps")
plt.xlabel("Profil")
plt.tight_layout()
plt.savefig("graphs/profil_vs_bandwidth.png")
plt.close()
