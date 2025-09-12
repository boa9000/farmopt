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

def country_finder(centroid):
    world = gpd.read_file("data/shapes/ne_110m_admin_0_countries.shp")
    world = world.to_crs("EPSG:4326")
    country = world[world.contains(centroid)]

    return country["NAME"].values[0]