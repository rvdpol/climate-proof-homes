from flask import Flask, render_template, render_template_string
import climate
import funda
import folium_map
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()

app = Flask(__name__)

def refresh_data():
    print("-----Starting Background Refresh-----")
    print("-----Scraping Funda-----")
    funda.scrape_data(500)
    print("-----Geocoding Listing-----")
    funda.geocode_data()
    print("-----Combining with Climate Data----")
    climate.refresh_data()
    print("-----Updating Climate Plots-----")
    climate.refresh_plots()
    print("-----Updating Map-----")
    folium_map.refresh_map()
    print("-----Background Refresh Finished-----")

scheduler = BackgroundScheduler()
#scheduler.add_job(refresh_data, 'interval', id="refresh_data", replace_existing=True, hours=6)
#scheduler.add_job(refresh_data, id="refresh_data_initially",replace_existing=True)
refresh_data()
#scheduler.start()

#@app.route('/')
#def root():
#    return render_template('index.html')

#if __name__ == '__main__':
#    app.run(host="localhost", port=8080, debug=True)
