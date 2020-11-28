# Attempt at the classic folium "volcanoes map" program that pins volcanoes based on csv file
# and splits areas in map using geojson map that has lists of polygons

import folium
import pandas

data = pandas.read_csv("Volcanoes.txt")
lat = list(data["LAT"])
lon = list(data["LON"])
elev = list(data["ELEV"])
name = list(data["NAME"])


# function to define the color variations
def color_producer(elevation):
    if elevation < 1000:
        return 'green'
    elif 1000 <= elevation < 3000:
        return 'orange'
    else:
        return 'red'


# Set the layer theme
titles = "Stamen Terrain"

# HTML code to be used in the pins/bubbles
html = """
<h4> Volcano Information:</h4>
Height: %s m<br>
Name: <a href=\"https://www.google.com/search?q=%%22%s%%22\" target=\"_blank\">%s</a><br>
"""

# Starting area on map, zoom level and map layout
map = folium.Map(location=[36.1249185, -115.3150854], zoom_start=5, titles=titles)

# Feature groups to split layers
fgv = folium.FeatureGroup(name="US Volcanoes")
fgp = folium.FeatureGroup(name="Population")

# Create the volcano layer, iterate through the volcanos.txt CSV
for lt, ln, el, nm in zip(lat, lon, elev, name):  # zip function iterates through all parameters from same index

    # iframe will contain the folium IFrame object to display our HTML in the popup
    iframe = folium.IFrame(html=html % (el, nm, nm), width=200, height=100)

    # Now we add the pins OR circlemarkers (Bubbles)
    """ When using pins the map.add_child also works here, but using feature group helps us have a single layer
        with all pins instead of a layer per pin """
    # fgv.add_child(folium.Marker(location=[lt, ln], popup=str(el) + "m", icon=folium.Icon(color='green')))

    """there might be a blank page error if there are quotes in the strings.  To avoid that, change the popup
     argument to: popup=folium.Popup(str(el), parse_html=True)"""
    # using pins
    # fgv.add_child(folium.Marker(location=[lt, ln], radius=6, popup=folium.Popup(iframe), icon=folium.Icon(color=color_producer(el))))

    # using circlemarker/bubbles
    fgv.add_child(folium.CircleMarker(location=[lt, ln], radius=6, popup=folium.Popup(iframe),
                                      fill_color=color_producer(el), color='gray', fill_opacity=0.7))

# polygons are enclosed areas - this instruction consumes a json file with geodata; a "geojson" file.
# geojson is a special 'standard' for geographic information - world.json already contains polygon information
# see https://en.wikipedia.org/wiki/GeoJSON for details on these types of datasets

# create the population layer - consume the geojson with 'folium'
fgp.add_child(folium.GeoJson(data=(open('world.json', 'r', encoding='utf-8-sig').read()),
                             style_function=lambda x: {'fillColor': 'green' if x['properties']['POP2005'] < 1000000
                             else 'orange' if 10000000 <= x['properties']['POP2005'] < 20000000 else 'red'}))

# here i assign the feature group to the map layer and create the file - the order of layers matter
# make sure pins/bubbles are the last layer if you need to interact with them
map.add_child(fgp)
map.add_child(fgv)

# After adding the field groups, call the layer control
map.add_child(folium.LayerControl())

map.save("Map.html")
print("File saved.. see .py file directory for Map.html file")
