import sys
import io
import folium
import json 
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import random

from sklearn.cluster import MeanShift
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QSlider, QLabel, QPushButton
from PyQt5.QtWebEngineWidgets import QWebEngineView # pip install PyQtWebEngine
from PyQt5.QtCore import Qt

DATA_FILE = '' #path to location history json file from google takeout

numOfPoints = 250
currentPoint = 0
mode = 0 # 0 - points; 1 - clusters; 2 - 0 and 1;
loc = []
X = []

def readFile():
    with open(DATA_FILE, encoding='utf-8') as f: # take data
        templates = json.load(f)

    locations = templates.get('locations') # dict: { locations: <list of data> }

    for i in range(len(locations)):
        tl = [locations[i]['timestampMs'], locations[i]['latitudeE7'], locations[i]['longitudeE7']]
        tx = [locations[i]['latitudeE7'], locations[i]['longitudeE7']]
        loc.append(tl) 
        X.append(tx)

def toTXT(temp, path):
    ftxt = open(path, "w+")
    ftxt.write(json.dumps(temp))
    ftxt.close()

def plot():  
    plt.xlabel('x')
    plt.ylabel('y')
    plt.plot(loc[:numOfPoints, 1], loc[:numOfPoints, 2], 'r.')    
    plt.show()


class MyApp(QWidget):
    def __init__(self):
        super(MyApp, self).__init__()
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()
        self.setGeometry(0, 0, 1080, 720)
        self.setLayout(self.layout)

        self.timeSlider = QSlider(Qt.Horizontal, self)
        self.timeSlider.setFixedSize(320, 30)
        self.timeSlider.setMinimum(0)
        self.timeSlider.setMaximum(loc.shape[0] - 1500 - 1)
        self.timeSlider.valueChanged[int].connect(self.timeSlider_changeValue) 
        self.layout.addWidget(self.timeSlider)
        

        self.pointsSlider = QSlider(Qt.Horizontal, self)
        self.pointsSlider.setFixedSize(320, 30)
        self.pointsSlider.setMinimum(250)
        self.pointsSlider.setMaximum(1500)
        self.pointsSlider.valueChanged[int].connect(self.pointsSlider_changeValue)
        self.layout.addWidget(self.pointsSlider)
       

        self.labelTimeBegin = QLabel(getDataTime(int(str(loc[0][0]))), self)
        self.labelTimeBegin.setFixedSize(320, 30)
        self.layout.addWidget(self.labelTimeBegin)

        self.labelTimeEnd = QLabel(getDataTime(int(str(loc[numOfPoints - 1][0]))), self)
        self.labelTimeEnd.setFixedSize(320, 30)
        self.layout.addWidget(self.labelTimeEnd)

        self.labelNumOfPoints = QLabel(str(numOfPoints), self)
        self.labelNumOfPoints.setFixedSize(320, 30)       
        self.layout.addWidget(self.labelNumOfPoints)

        self.buttonRefreshMap = QPushButton('Refresh', self)
        self.buttonRefreshMap.setGeometry(0, 690, 360, 30)
        self.buttonRefreshMap.clicked.connect(self.buttonRefreshMap_click)

        self.buttonSwitchMode = QPushButton('Poinst', self)
        self.buttonSwitchMode.setGeometry(0, 660, 360, 30)
        self.buttonSwitchMode.clicked.connect(self.buttonSwitchMode_click)

        self.setWindowTitle('ML: map clustering')      
                      
        #map
        coordinate = (loc[0, 1], loc[0, 2])
        m = folium.Map(
        	tiles='Stamen Terrain',
        	zoom_start=13,
        	location=coordinate
        )

        for i in range(250):
            folium.Marker(                
                [loc[i, 1], loc[i, 2]], popup=str(datetime.fromtimestamp(int(str(loc[i][0])) / 1000))
            ).add_to(m)    

        # save map data to data object
        data = io.BytesIO()
        m.save(data, close_file=False)

        webView = QWebEngineView()
        webView.setHtml(data.getvalue().decode())
        webView.move(360, 0)
        webView.resize(720, 720)
        layMap = QHBoxLayout()
        layMap.addWidget(webView)   
        self.layout.addChildLayout(layMap)
        

    def timeSlider_changeValue(self, value):
        global currentPoint 
        currentPoint = value
        self.labelTimeBegin.setText(getDataTime(int(str(loc[value][0]))))
        self.labelTimeEnd.setText(getDataTime(int(str(loc[value + self.pointsSlider.value() - 1][0]))))

    def pointsSlider_changeValue(self, value):
        global numOfPoints 
        numOfPoints = value
        self.labelNumOfPoints.setText(str(value))
        self.labelTimeEnd.setText(getDataTime(int(str(loc[self.timeSlider.value() + value][0]))))

    def buttonSwitchMode_click(self):
        global mode
        if mode == 0:
            mode = 1
            self.buttonSwitchMode.setText("Clusters")
        elif mode == 1: 
            mode = 2
            self.buttonSwitchMode.setText("Clusters and points")
        elif mode == 2: 
            mode = 0
            self.buttonSwitchMode.setText("Poinst")
        print("Mode: ", mode)

    def buttonRefreshMap_click(self):
        global mode
        global numOfPoints
        global currentPoint 
        print("Mode: ", mode)
        print("Current Points:", currentPoint)
        print("Num Of Points:", numOfPoints)

        if mode == 1 or mode == 2:
            clustering = MeanShift(bandwidth=0.0016).fit(X[currentPoint:(currentPoint + numOfPoints)])
            print(clustering.cluster_centers_.shape)
            print(clustering.cluster_centers_[:10])
            print(X[:10])

        coordinate = (loc[currentPoint, 1], loc[currentPoint, 2])
        m = folium.Map(tiles='Stamen Terrain', zoom_start=13, location=coordinate)

        #all points
        if mode == 0 or mode == 2:
            for i in range(currentPoint, currentPoint + numOfPoints):
                folium.Marker(                
                    [loc[i, 1], loc[i, 2]], popup=str(datetime.fromtimestamp(int(str(loc[i][0])) / 1000))
                ).add_to(m)

        #center of clusters
        if mode == 1 or mode == 2:
            for i in range(clustering.cluster_centers_.shape[0]):
                folium.Marker(                
                    [clustering.cluster_centers_[i, 0], clustering.cluster_centers_[i, 1]], popup='Center of points', icon=folium.Icon(color="red"),
                ).add_to(m)

        # save map data to data object
        data = io.BytesIO()
        m.save(data, close_file=False)

        webView = QWebEngineView()
        webView.setHtml(data.getvalue().decode())
        webView.move(360, 0)
        webView.resize(720, 720)
        layMap = QHBoxLayout()
        layMap.addWidget(webView)
        self.layout.addChildLayout(layMap)
    
def print_data(timestamp):
    print(timestamp / 1000)
    print(getDataTime(timestamp))
    print(type(getDataTime(timestamp)))

def getDataTime(timestamp):
    dateTime = datetime.fromtimestamp(timestamp / 1000).strftime("%m/%d/%Y, %H:%M:%S")
    return dateTime

if __name__ == "__main__":
    readFile()
    loc = np.array(loc)
    X = np.array(X, dtype='float')
    print(loc.shape[0]) # num of points
    for i in range(loc.shape[0]):
        loc[i, 1] = float(loc[i, 1]) * 0.0000001
        loc[i, 2] = float(loc[i, 2]) * 0.0000001
    for i in range(loc.shape[0]):
        X[i, 0] = float(X[i, 0]) * 0.0000001
        X[i, 1] = float(X[i, 1]) * 0.0000001
    print(loc)     

    print_data(int(str(loc[0][0])))
    print_data(int(str(loc[5000 - 1][0])))

    app = QApplication(sys.argv)     
    myApp = MyApp()
    myApp.show()
    sys.exit(app.exec_()) 

    
