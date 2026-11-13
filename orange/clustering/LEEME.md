# Flujo de clustering (Etapa 6)

`clustering_departamentos.ows` agrupa los 32 departamentos según su perfil de incendios 2010-2024.

File (data/etapa6/clustering/perfil_departamentos.csv) → Select Columns → Preprocess (estandarizar a media 0 y desviación 1) → k-Means (k de 2 a 8, k-Means++, 10 repeticiones, 300 iteraciones) → Silhouette Plot y Data Table.

Preprocess → Distances (euclidiana) → Hierarchical Clustering (Ward, Top N = 3) para contrastar.
