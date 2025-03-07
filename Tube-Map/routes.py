from heapq import heappush, heappop
from collections import defaultdict
from setup import *
import math

def create_extended_graph(graph, transfer_time):
    #this function creates a graph such that (node, line) pairs are vertices
    #such pairs which share the node are connected by transfer time
    #such pairs which are adjacent are connected by 'weight' 
    #(for reference, weight is just the primitive estimation of distance/avg speed, not the REAL modelled time)
    #the real modelled time is dealt with in the other function

    extended_graph = defaultdict(lambda:[])

    for station in graph:
        for dest, line, weight in graph[station]:
            extended_graph[(station, line)].append((dest, line, weight))

    for station in graph:
        lines_at_station = set(edge[1] for edge in graph[station])
        for line1 in lines_at_station:
            for line2 in lines_at_station:
                if line1 != line2:
                    extended_graph[(station, line1)].append((station, line2, transfer_time(station, line1, line2)))

    return extended_graph

def get_shortest_route(graph, start_id, end_id, mode='time', time_function=None, transfer_time=lambda node, prev_line, new_line: 180):
    INF = float('inf')
    if start_id not in graph or end_id not in graph:
        return None, INF

    extended_graph = create_extended_graph(graph, transfer_time)

    def get_time(current_station, next_station, used_line):
        dist = get_distance(current_station, next_station)
        result =  dist/line_speeds[used_line]
        #print(current_station, next_station, used_line, result)
        return result

    if (time_function==None):
        time_function = get_time
    get_time = time_function
    #these weird lines actually just make time_function default to the primitive estimation


    def get_weight(edge, current_line, current_station, mode):
        dest, line, weight = edge
        if mode == 'stops':
            return 1
        elif mode == 'distance':
            return weight if line == current_line else weight*line_speeds[current_line] + transfer_time(current_station, current_line, line)
        elif mode == 'time':
            one_stop = get_time(current_station, next_station, line)
            return one_stop if line == current_line else one_stop + transfer_time(current_station, current_line, line)
        elif mode == 'transfers':
            return 0 if line == current_line else 1
        else:
            raise Exception("Dear coder, you have entered an invalid mode. Please select a valid one... unless you want more bugs")

    distances = defaultdict(lambda:INF)
    predecessors = defaultdict(lambda:None) #parent list

    start_lines = set(edge[1] for edge in graph[start_id])
    queue = []
    for line in start_lines:
        distances[(start_id, line)] = 0
        heappush(queue, (0, (start_id, line)))
    #dijkstra distance method
    while queue:
        current_distance, (current_station, current_line) = heappop(queue)
        if current_station == end_id and current_distance == distances[(current_station, current_line)]:
            #step backwards through the dijkstra tree
            path = []
            current = (current_station, current_line)
            while current is not None:
                path.append(current)
                current = predecessors[current]
            return path[::-1], current_distance

        for next_station, next_line, weight in graph[current_station]:
            edge_weight = get_weight((next_station, next_line, weight), current_line, current_station, mode)
            distance = current_distance + edge_weight

            if distance < distances[(next_station, next_line)]:
                distances[(next_station, next_line)] = distance
                predecessors[(next_station, next_line)] = (current_station, current_line)
                heappush(queue, (distance, (next_station, next_line)))
    return None, INF

def get_forced_route(graph, start_id, end_id, forced_line):
    #so this is just for situations where the shortest path isn't necessarily the one on the same line
    #e.g. stuff like morden to euston, it's optimal to shortcut to victoria line at stockwell
    INF = float('inf')
    if start_id not in graph or end_id not in graph:
        return None, INF

    extended_graph = create_extended_graph(graph, lambda a,b,c: 180)    #we don't care about transfer time for this one



    def get_weight(edge, current_line, current_station):
        return INF if current_line!=forced_line else 1

    distances = defaultdict(lambda:INF)
    predecessors = defaultdict(lambda:None)

    #start from all start station lines...
    start_lines = set(edge[1] for edge in graph[start_id])
    queue = []
    for line in start_lines:
        distances[(start_id, line)] = 0
        heappush(queue, (0, (start_id, line)))

    while queue:
        current_distance, (current_station, current_line) = heappop(queue)
        if current_station == end_id and current_distance == distances[(current_station, current_line)]:
            path = []
            current = (current_station, current_line)
            while current is not None:
                path.append(current)
                current = predecessors[current]
            return path[::-1], current_distance

        for next_station, next_line, weight in graph[current_station]:
            if next_line!=forced_line:
                #if we go off our forced line, we've made a mistake, so it's not valid
                continue
            edge_weight = get_weight((next_station, next_line, weight), current_line, current_station)
            distance = current_distance + edge_weight

            if distance < distances[(next_station, next_line)]:
                distances[(next_station, next_line)] = distance
                predecessors[(next_station, next_line)] = (current_station, current_line)
                heappush(queue, (distance, (next_station, next_line)))
    return None, INF

def format_route(route):
    if not route:
        return "No route found"
    formatted_route = []
    last_station_name = "The_Last_Station_You_Ever_Want_To_Be_At"   #if this is printed we have a bug
    for i, (station, line) in enumerate(route):
        station_name = vertex_data[station][0]
        if i == 0:
            formatted_route.append(f"Start at {station_name} on {line} line")
        elif route[i-1][1] != line:
            formatted_route.append(f"Transfer to {line} line at {last_station_name}")
            formatted_route.append(f"Continue to {station_name}")
        elif i == len(route)-1:
            formatted_route.append(f"Arrive at {station_name}")
        else:
            formatted_route.append(f"Continue to {station_name}")
        last_station_name = station_name

    return "\n".join(formatted_route)

def journey_summary(route):
    #shorter formatting of route
    journey_summary = []
    if not route:
        return "No route found"
    for i, (station, line) in enumerate(route):
        station_name = vertex_data[station][0]

        if i == 0:
            journey_summary.append(f"Start at {station_name} on {line} line")
        elif route[i-1][1] != line:
            journey_summary.append(f"Transfer to {line} line at {previous_station_name}")
        elif i == len(route) - 1:
            journey_summary.append(f"Arrive at {station_name}")
        previous_station_name = station_name

    summary_output = " -> ".join(journey_summary)
    return summary_output