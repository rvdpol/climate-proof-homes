import geopandas as gpd
from dotenv import load_dotenv
import os
import matplotlib.pyplot as plt
import contextily as cx

load_dotenv()

def join_risk_gdf(left_gdf, right_gdf, column_title):
    gdf_new = left_gdf.sjoin(right_gdf, how='left', predicate='within') 
    gdf_new[column_title] = gdf_new['index_right'].notna()
    gdf_new = gdf_new.drop(columns=['index_right'])
    return gdf_new
    
def refresh_data():
    input_path = os.getenv('file_path_recent')
    gdf = gpd.read_file(f'{input_path}.geojson', driver='GeoJSON')

    gdf_flood, gdf_wildfire, gdf_pole_rot, gdf_subsidence = get_dataframes()

    gdf_f = join_risk_gdf(gdf, gdf_flood, 'flood')
    gdf_w = join_risk_gdf(gdf_f, gdf_wildfire, 'wildfire')
    gdf_p = join_risk_gdf(gdf_w, gdf_pole_rot, 'pole_rot')
    gdf_s = join_risk_gdf(gdf_p, gdf_subsidence, 'subsidence')
    gdf_filtered = gdf_s

    columns = ['url','address','zip_code','city','floor_area','plot_area','energy_label','price', 'full_address','geometry','latitude','longitude', 'image','flood','pole_rot','subsidence','wildfire']
    gdf_filtered = gdf_filtered.filter(columns)
    gdf_filtered

    gdf_flood_risk = gdf_filtered[gdf_filtered['flood']]
    gdf_wildfire_risk = gdf_filtered[gdf_filtered['wildfire']]
    gdf_subsidence_risk = gdf_filtered[gdf_filtered['subsidence'] | gdf_filtered['pole_rot']]

    gdf_safe = gdf_filtered[~gdf_filtered['flood'] & ~gdf_filtered['wildfire'] & ~gdf_filtered['pole_rot'] & ~gdf_filtered['subsidence']]
    safe_path = os.getenv('file_path_safe')
    flood_path = os.getenv('file_path_flood')
    wildfire_path = os.getenv('file_path_wildfire')
    subsidence_path = os.getenv('file_path_subsidence')
    gdf_flood_risk.to_file(f'{flood_path}.geojson', driver="GeoJSON")
    gdf_wildfire_risk.to_file(f'{wildfire_path}.geojson', driver="GeoJSON")
    gdf_subsidence_risk.to_file(f'{subsidence_path}.geojson', driver="GeoJSON")

    gdf_safe.to_file(f'{safe_path}.geojson', driver="GeoJSON")

def get_dataframes():
    gdf_flood = gpd.read_file('./files/source/overstroming_kleine_kans.gpkg')
    gdf_flood = gdf_flood[gdf_flood['DN'] > 1]
    gdf_wildfire = gpd.read_file('./files/source/natuurbrand_hoog.gpkg')
    gdf_wildfire = gdf_wildfire[gdf_wildfire['DN'] > 2]
    gdf_pole_rot = gpd.read_file('./files/source/paalrot_2050_laag.gpkg')
    gdf_pole_rot = gdf_pole_rot[gdf_pole_rot['mild_cc__1'] > 0.8]
    gdf_subsidence = gpd.read_file('./files/source/verschilzetting_2050_laag.gpkg')
    gdf_subsidence = gdf_subsidence[gdf_subsidence['mild_cc_ri'] > 1]

    return gdf_flood, gdf_wildfire, gdf_pole_rot, gdf_subsidence

def save_plot(gdf, title, filename, color):
    xlim = 0, 300000
    ylim = 250000, 650000

    print (f"---Creating {title} Map---")
    fig, ax = plt.subplots(1,1)
    fig.set_size_inches(10,10)
    ax.set_title(title, fontdict={'fontsize':60})
    ax.tick_params(bottom=False, left=False, labelbottom=False, labelleft=False)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    cx.add_basemap(ax, crs=gdf.crs, source=cx.providers.CartoDB.Positron)
    gdf.plot(ax=ax, alpha=1, color=color)
    plt.savefig(f'./files/output/{filename}.png')
    ax.clear()

def refresh_plots():    
    gdf_flood, gdf_wildfire, gdf_pole_rot, gdf_subsidence = get_dataframes()

    save_plot(gdf_flood, 'Flood risk', 'flood_risk', "blue")
    save_plot(gdf_wildfire, 'Wildfire risk', 'wildfire_risk', "red")
    save_plot(gdf_pole_rot, 'Pole rot risk', 'pole_rot_risk', "yellow")
    save_plot(gdf_subsidence, 'Subsidence risk', 'subsidence_risk', "brown")
