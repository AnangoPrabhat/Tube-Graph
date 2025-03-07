import folium
from folium import plugins
import numpy as np
from setup import *
from routes import *
def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])

def calculate_offset_points(p1, p2, offset_distance):
    #move these points a bit perpendicular to the line connecting them togethers
    p1 = np.array(p1)
    p2 = np.array(p2)
    d = p2 - p1
    perp = np.array([-d[1], d[0]])
    perp = perp / np.linalg.norm(perp)
    return p1 + perp * offset_distance, p2 + perp * offset_distance

def get_min_time(graph, station1, station2):
    #min weight over all lines
    min_time = float('inf')
    for dest, line, weight in graph[station1]:
        if dest == station2:
            min_time = min(min_time, weight)
    return min_time

def create_route_map(graph, vertex_data, line_colours, route_path, route_distance, 
                    center_coords=(51.5074, -0.1278)):
    #create a tube map html file, with a route highlighted on the file
    m = folium.Map(location=center_coords, zoom_start=12, tiles='cartodbpositron')
    lines_group = folium.FeatureGroup(name="All Lines")
    stations_group = folium.FeatureGroup(name="All Stations")
    route_lines_group = folium.FeatureGroup(name="Route")
    route_stations_group = folium.FeatureGroup(name="Route Stations")
    station_connections = {}
    for station_id in graph:
        for dest, line, _ in graph[station_id]:
            pair_key = tuple(sorted([station_id, dest]))
            if pair_key not in station_connections:
                station_connections[pair_key] = []
            if line not in [l for l, _ in station_connections[pair_key]]:
                station_connections[pair_key].append((line, _))
    route_segments = set()
    route_stations = set()
    if route_path:
        for i in range(len(route_path)-1):
            station1, line1 = route_path[i]
            station2, line2 = route_path[i+1]
            route_segments.add(((station1, station2), line2))
            route_stations.add(station1)
        route_stations.add(route_path[-1][0])
    for (station_id, dest), connections in station_connections.items():
        station_lat = vertex_data[station_id][1]
        station_lon = vertex_data[station_id][2]
        dest_lat = vertex_data[dest][1]
        dest_lon = vertex_data[dest][2]
        num_lines = len(connections)
        offset_step = 0.00004
        for i, (line, _) in enumerate(connections):
            if num_lines > 1:
                offset = offset_step * (i - (num_lines - 1) / 2)
            else:
                offset = 0
            line_code = None
            for code in line_colours.keys():
                if line.lower().startswith(code.lower()):
                    line_code = code
                    break
            color = rgb_to_hex(line_colours[line_code]) if line_code else '#000000'
            if num_lines > 1:
                p1_offset, p2_offset = calculate_offset_points([station_lat, station_lon], [dest_lat, dest_lon], offset)
                points = [tuple(p1_offset), tuple(p2_offset)]
            else:
                points = [(station_lat, station_lon), (dest_lat, dest_lon)]
            folium.PolyLine(points, weight=3, color=color, opacity=0.8, popup=f"{line} Line").add_to(lines_group)
            #check if this edge is in the actual route
            if ((station_id, dest), line) in route_segments:
                route_line = folium.PolyLine(points, weight=8, color=color, opacity=1.0, popup=f"Route: {line} Line").add_to(route_lines_group)
                plugins.PolyLineTextPath(route_line, text='>', repeat=True, offset=18, attributes={'font-size': '48px', 'fill': color}).add_to(route_lines_group)
            elif ((dest, station_id), line) in route_segments:
                route_line = folium.PolyLine(points[::-1], weight=8, color=color, opacity=1.0, popup=f"Route: {line} Line").add_to(route_lines_group)
                plugins.PolyLineTextPath(route_line, text='>', repeat=True, offset=18, attributes={'font-size': '48px', 'fill': color}).add_to(route_lines_group)

    #draw stations as circles
    #draw radius bigger for start and end station > other stations on the route > off-route stations
    for station_id in graph:
        station_name = vertex_data[station_id][0]
        station_lat = vertex_data[station_id][1]
        station_lon = vertex_data[station_id][2]
        if station_id not in route_stations:
            folium.CircleMarker(location=[station_lat, station_lon], radius=4, color='#000000', fill=True, popup=folium.Popup(station_name, parse_html=True), weight=1).add_to(stations_group)
        else:
            radius = 9 if station_id in [route_path[0][0], route_path[-1][0]] else 8
            folium.CircleMarker(location=[station_lat, station_lon], radius=radius, color='#000000', fill=True, fill_color='#ffffff', popup=folium.Popup(station_name, parse_html=True), weight=2).add_to(route_stations_group)
    #check if there's actually a route and add in the total journey time as a popup window
    if route_path:
        route_info = f"Total journey time: {route_distance} seconds"
        folium.Rectangle(bounds=[[51.45, -0.2], [51.46, -0.1]], color="none", fill=True, popup=route_info).add_to(m)
    lines_group.add_to(m)
    stations_group.add_to(m)
    route_lines_group.add_to(m)
    route_stations_group.add_to(m)
    folium.LayerControl().add_to(m)
    return m

def visualize_route(graph, vertex_data, line_colours, start_station, end_station, time_function = None, transfer_time = lambda node, prev_line, new_line: 180, mode='time'):
    #creates and saves a map with the shortest route marked on
    route_path, route_distance = get_shortest_route(graph, start_station, end_station, time_function=time_function, transfer_time = transfer_time, mode=mode)
    print('Shortest route calculated:')
    print(format_route(route_path))
    print(journey_summary(route_path))
    print('Total weight:', route_distance)

    if route_path == None:
        print("No route found")
        return None

    m = create_route_map(graph, vertex_data, line_colours, route_path, route_distance)
    m.save('london_tube_route.html')
    return route_path, route_distance