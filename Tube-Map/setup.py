#we will store the graph as a collection of vertices (tube stations) and edges (each edge will have a start point, end point, label, distance and weight)
#to start I need to get a list of the tube stations and lines in computer readable format, as well as a list of the geographical coordinates of the stations
from collections import *
from math import *
import csv
from collections import defaultdict

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  

    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = (sin(dlat / 2) ** 2 +
         cos(lat1_rad) * cos(lat2_rad) * (sin(dlon / 2) ** 2))
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c 
    return distance


line_colours = {
        'VIC': (0, 160, 226),
        'PIC': (0, 25, 168),
        'WAC': (118, 208, 189),
        'NTN': (0, 0, 0),
        'HAM': (215, 153, 175),
        'BAK': (137, 78, 36),
        'CIR': (255, 206, 0),
        'DIS': (0, 114, 41),
        'CEN': (220, 36, 31),
        'JUB': (134, 143, 152),
        'MET': (117, 16, 86),
}

line_speeds = {
    "Bakerloo": 27.04,
    "Central": 37.27,
    "Circle": 23.73,
    "District": 29.19,
    "Hammersmith & City": 25.33,
    "Jubilee": 39.11,
    "Metropolitan": 45.61,
    "Northern": 33.28,
    "Piccadilly": 33.11,
    "Victoria": 40.66,
    "Waterloo & City": 33.3
}

line_speeds = {j:i/3.6 for j,i in line_speeds.items()} #to get everything in m/s
top_speeds = {
    "Bakerloo": 72,
    "Central": 85,
    "Circle": 100,
    "District": 100,
    "Hammersmith & City": 100,
    "Jubilee": 100,
    "Metropolitan": 100,
    "Northern": 72,
    "Piccadilly": 72,
    "Victoria": 80,
    "Waterloo & City": 34
}
top_speeds = {j:i/3.6 for j,i in top_speeds.items()}

accelerations = {
    "Bakerloo": 0.95,
    "Central": 1.15,
    "Circle": 1.3,
    "District": 1.3,
    "Hammersmith & City": 1.3,
    "Jubilee": 1.4,
    "Metropolitan": 1.3,
    "Northern": 1.3,
    "Piccadilly": 1.3,
    "Victoria": 1.4,
    "Waterloo & City": 1.3
}

decelerations = {
    "Bakerloo": 1.17,
    "Central": 1.20,
    "Circle": 1.4,
    "District": 1.4,
    "Hammersmith & City": 1.4,
    "Jubilee": 1.2,
    "Metropolitan": 1.4,
    "Northern": 1.4,
    "Piccadilly": 1.4,
    "Victoria": 1.4,
    "Waterloo & City": 1.14
}

frequencies = {
    "Bakerloo": 16,
    "Central": 24,
    "Circle": 6,
    "District": 18,
    "Hammersmith & City": 6,
    "Jubilee": 24,
    "Metropolitan": 12,
    "Northern": 20,
    "Piccadilly": 21,
    "Victoria": 27,
    "Waterloo & City": 12
}

graph = {}
vertex_data = {}
vertex_ID = {}


with open('london_tube_vertices.txt','r') as f:
    vertex_metadata = f.readlines()


with open('london_tube_edge_list.txt','r') as f:
    edge_metadata = f.readlines()

for i in vertex_metadata[1:]:
    i = i.strip()
    comma_indices = []
    for j in range(len(i)):
        if i[j]==',':
            comma_indices.append(j)
    ID, name, latitude, longitude = i[:comma_indices[0]], i[comma_indices[0]+2:comma_indices[-2]-1], i[comma_indices[-2]+1:comma_indices[-1]], i[comma_indices[-1]+1:]
    ID = int(ID)
    latitude = float(latitude)
    longitude = float(longitude)
    vertex_data[ID] = (name, latitude, longitude)
    graph[ID] = []

for i in edge_metadata[1:]:
    i=i.strip()
    fr, to, line, color = i.split(',')
    fr=int(fr)
    to=int(to)
    lat1, lon1 = vertex_data[fr][1:]
    lat2, lon2 = vertex_data[to][1:]
    line = line[1:-6]
    if line not in line_speeds:
        continue
    graph[fr].append((to, line, haversine(lat1,lon1,lat2,lon2)))
    graph[to].append((fr, line, haversine(lat1,lon1,lat2,lon2)))

valid_IDs = []
for i in graph:
    if len(graph[i])>0:
        valid_IDs.append(i)
svIDs = set(valid_IDs)
new_IDs = {}
for i in range(len(valid_IDs)):
    new_IDs[valid_IDs[i]] = i
vertex_data = {new_IDs[k]:v for k,v in vertex_data.items() if k in svIDs}
new_graph = {}
for i in graph:
    if i not in svIDs:
        continue
    new = []
    for j in graph[i]:
        new.append((new_IDs[j[0]], j[1], j[2]))
    new_graph[new_IDs[i]] = new
graph = new_graph
#this entire code is to get rid of DLR stations and other irrelevant stuff
for i in vertex_data:
    vertex_ID[vertex_data[i][0]] = i

distance_based_graph = {}
for i in graph:
    distance_based_graph[i] = []
for i in graph:
    for j in graph[i]:
        distance_based_graph[i].append((j[0], j[1], j[2] / line_speeds[j[1]]))

def get_distance(fr, to):
    lat1, lon1 = vertex_data[fr][1:]
    lat2, lon2 = vertex_data[to][1:]
    return haversine(lat1,lon1,lat2,lon2)



def compute_average_dwell(file_path):
    with open(file_path,'r') as f:
        try:
            return eval(f.read())
        except:
            raise Exception("Failed to read the average dwell times.")
    return average_dwell

file_path = 'average_dwell_times.txt'  
average_dwell_times = compute_average_dwell(file_path)

station_names = []
for i in vertex_data:
    station_names.append(vertex_data[i][0])