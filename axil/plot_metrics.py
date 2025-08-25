import pandas as pd
import matplotlib.pyplot as plt
import os

# Dossier de sortie
output_dir = "graphs"
os.makedirs(output_dir, exist_ok=True)

# Charger les métriques
metrics_df = pd.read_csv("metrics.csv")
metrics_df["timestamp"] = pd.to_datetime(metrics_df["timestamp"], unit="s")

# Séparer AXIL et baseline
df_axil = metrics_df[metrics_df["mode"] == "AXIL"]
df_baseline = metrics_df[metrics_df["mode"] == "baseline"]

# Courbes globales
fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

axes[0].plot(df_axil["timestamp"], df_axil["global_ux"], label="AXIL", marker='o')
axes[0].plot(df_baseline["timestamp"], df_baseline["global_ux"], label="Baseline", marker='x')
axes[0].set_ylabel("UX globale")
axes[0].legend()
axes[0].set_title("Comparaison UX globale")

axes[1].plot(df_axil["timestamp"], df_axil["apps_deployed"], label="AXIL", marker='o')
axes[1].plot(df_baseline["timestamp"], df_baseline["apps_deployed"], label="Baseline", marker='x')
axes[1].set_ylabel("Apps déployées")
axes[1].legend()
axes[1].set_title("Nombre d'applications déployées")

axes[2].plot(df_axil["timestamp"], df_axil["total_bw"], label="AXIL", marker='o')
axes[2].plot(df_baseline["timestamp"], df_baseline["total_bw"], label="Baseline", marker='x')
axes[2].set_ylabel("Bande passante (kbps)")
axes[2].set_xlabel("Temps")
axes[2].legend()
axes[2].set_title("Bande passante utilisée")

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "comparison_AXIL_vs_baseline.png"))
plt.close()

# Graphe par application (si app_trace.csv existe)
trace_file = "app_trace.csv"
if os.path.exists(trace_file):
    app_df = pd.read_csv(trace_file)

    for app in app_df["app_name"].unique():
        app_data = app_df[app_df["app_name"] == app]
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(app_data["cycle"], app_data["global_ux_value"], label="UX Value", marker='o')
        ax.set_title(f"UX de l'application '{app}' au fil du temps")
        ax.set_xlabel("Cycle")
        ax.set_ylabel("UX Value")
        ax.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f"{app}_ux_trace.png"))
        plt.close()
