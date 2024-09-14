import geopandas as gpd
import folium
from dotenv import load_dotenv
import os

load_dotenv()

def get_popup_html(row, color):
    risks_text = ""
    if(row['flood']):
        risks_text = risks_text + "Flood, "
    if(row['wildfire']):
        risks_text = risks_text + "Wildfire, "
    if(row['pole_rot']):
        risks_text = risks_text + "Pole Rot, "
    if(row['pole_rot']):
        risks_text = risks_text + "Subsidence, "

    if (risks_text == ""):
        risks_text = "-"
    else:
        risks_text = risks_text[:-2]
    html=f"""<div class="card col " style="border-radius:6px;border-top: 6px solid {color}; margin-bottom: 0;"><div class="card-body">
                        <div style='display:flex;justify-content:space-between'">
                            <h6 class="card-title mb-4" style="font-size: 14px;"><a href="{row['url']}" target="_blank">{row['address']}</a> - {row['zip_code']} {row['city']}</h6>
                            <!--<h6 class="card-title mb-1" style="font-size: 14px;color: {color}"><br></h6>-->
                        </div>
                    </div>
                    <div class="table-responsive">
                        <table class="table align-middle table-nowrap mb-0">
                            <thead>
                                <tr>
                                    <th scope="col">Price</th>
                                    <th scope="col">Floor</th>
                                    <th scope="col">Plot</th>
                                    <th scope="col">Energy</th>
                                    <th scope="col">Risks</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>

                                    <td>{row['price']}</td>
                                    <td>{row['floor_area']}</td>
                                    <td>{row['plot_area']}</td>
                                    <td>{row['energy_label']}</td>
                                    <td >{risks_text}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <div><a href="{row['url']}" target="_blank"><img style="width:100%;" src="{row['image']}" /></a></div>

                </div>
            </div>          
            """
    return html    

def refresh_map():
    safe_path = os.getenv('file_path_safe')
    flood_path = os.getenv('file_path_flood')
    wildfire_path = os.getenv('file_path_wildfire')
    subsidence_path = os.getenv('file_path_subsidence')

    m=folium.Map(location=[52.156590, 5.388920], zoom_start=8)
    gdf_safe = gpd.read_file(f'{safe_path}.geojson', driver="GeoJSON")
    gdf_safe.explore(m=m,color="green", name="Safe", marker_kwds={'radius':4})
    gdf_subsidence_risk = gpd.read_file(f'{subsidence_path}.geojson', driver="GeoJSON")
    gdf_subsidence_risk.explore(m=m,color="yellow", name="Subsidence/Pole Rot Risk", marker_kwds={'radius':4})
    gdf_flood_risk = gpd.read_file(f'{flood_path}.geojson', driver="GeoJSON")
    gdf_flood_risk.explore(m=m,color="blue", name="Flood Risk", marker_kwds={'radius':4})
    gdf_wildfire_risk = gpd.read_file(f'{wildfire_path}.geojson', driver="GeoJSON")
    gdf_wildfire_risk.explore(m=m,color="red", name="Wildfire Risk", marker_kwds={'radius':4})
    print('End explore')
    folium.LayerControl().add_to(m)

    i = 0
    for idx, row in gdf_safe.iterrows():
        try:
            popup_html = get_popup_html(row, "green")
            folium.Marker(
                location=[row.latitude, row.longitude],
                popup=folium.Popup(popup_html, max_width=400),
                icon=folium.DivIcon(html=f"""<div style=""></div>""")

            ).add_to(m)
        except Exception as e:
            print(e)
            i = i+1


    for idx, row in gdf_flood_risk.iterrows():
        try:
            popup_html = get_popup_html(row, "blue")
            folium.Marker(
                location=[row.latitude, row.longitude],
                popup=folium.Popup(popup_html, max_width=400),
                icon=folium.DivIcon(html=f"""<div style=""></div>""")

            ).add_to(m)
        except:
            i = i+1

    for idx, row in gdf_wildfire_risk.iterrows():
        try:
            popup_html = get_popup_html(row, "red")
            folium.Marker(
                location=[row.latitude, row.longitude],
                popup=folium.Popup(popup_html, max_width=400),
                icon=folium.DivIcon(html=f"""<div style=""></div>""")

            ).add_to(m)
        except:
            i = i+1
    for idx, row in gdf_subsidence_risk.iterrows():
        try:
            popup_html = get_popup_html(row, "yellow")
            folium.Marker(
                location=[row.latitude, row.longitude],
                popup=folium.Popup(popup_html, max_width=400),
                icon=folium.DivIcon(html=f"""<div style=""></div>""")

            ).add_to(m)
        except:
            i = i+1
    print('End M')
    print(f'{i} errors')
    
    m.save('./files/output/house_map.html')
    return
