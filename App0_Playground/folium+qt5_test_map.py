
# this is a way we can get data back from folium maps

from PyQt5 import QtWidgets, QtWebEngineWidgets
from folium.plugins import Draw
import folium, io, sys, json

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    m = folium.Map(location=[18.481924, -66.8375546], zoom_start=13)

    draw = Draw(
        draw_options={
            'polyline': False,
            'rectangle': True,
            'polygon': True,
            'circle': False,
            'marker': True,
            'circlemarker': False},
        edit_options={'edit': False})
    m.add_child(draw)

    data = io.BytesIO()
    m.save(data, close_file=False)


    class WebEnginePage(QtWebEngineWidgets.QWebEnginePage):
        def javaScriptConsoleMessage(self, level, msg, line, sourceID):
            coords_dict = json.loads(msg)
            coords = coords_dict['geometry']['coordinates'][0]
            print(coords)

view = QtWebEngineWidgets.QWebEngineView()
page = WebEnginePage(view)
view.setPage(page)
view.setHtml(data.getvalue().decode())
view.show()
sys.exit(app.exec_())

#see source recommendation on https://github.com/python-visualization/folium/issues/520
