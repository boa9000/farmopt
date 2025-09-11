import geopandas as gpd

def best_epsg(centroid):
    # input should be epsg 4326
    lon, lat = centroid.x, centroid.y
    zone_number = int((lon + 180) / 6) + 1
    if lat >= 0:
        epsg_code = 32600 + zone_number  # Northern hemisphere
    else:
        epsg_code = 32700 + zone_number  # Southern hemisphere
    return epsg_code