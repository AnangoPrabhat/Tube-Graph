from setup import *
from routes import *
from functools import *

relative_speeds = {
    "Bakerloo": 1,
    "Central": 1,
    "Circle": 1,
    "District": 1,
    "Hammersmith & City": 1,
    "Jubilee": 1,
    "Metropolitan": 1,
    "Northern": 1,
    "Piccadilly": 1,
    "Victoria": 1,
    "Waterloo & City": 1
}

#@cache
def time_to_seconds(time_str):
    minutes, seconds = map(int, time_str.split(':'))
    return minutes * 60 + seconds

def seconds_to_time(time_str):
    minutes, seconds = time_str//60, time_str%60
    return str(minutes).zfill(2)+':'+str(seconds).zfill(2)

with open('primary_data.txt', 'r') as file:
    lines = file.readlines()


formatted_data = []

for line in lines[1:]:  
    parts = line.strip().split(',')

    start_station = parts[1].strip()
    end_station = parts[2].strip()
    line_name = parts[0].strip()
    time_in_seconds = time_to_seconds(parts[3])

    formatted_data.append((start_station, end_station, line_name, time_in_seconds))

for entry in formatted_data:
    print("Reading Primary Data: ",entry)


@cache  #functools lru cache used here to save time, BE CAREFUL to clear the cache when training
def get_top_speed(start_station, end_station, line):
    distance = get_distance(start_station, end_station)
    distance_relevance_coefficient = 0.24683055802825526
    distance_base_coefficient = 0.11539970618192215    #defined at 1m

    result = top_speeds[line]
    result *= distance_base_coefficient * distance ** (distance_relevance_coefficient) * relative_speeds[line]


    #220 is waterloo
    distance_to_waterloo = (get_distance(220, start_station) + get_distance(220, end_station))/2
    fudge = 1/2 + ((log(distance_to_waterloo+3000)-log(3000)))/15
    result = result * fudge

    return result

@cache
def get_adjacent_time(distance, line, top_speed):
    accel = accelerations[line]
    decel = decelerations[line]
    #first we need to check if we even reach top speed
    distance_if_momentary_top_speed = top_speed**2 / (2 * accel) + top_speed**2 / (2 * decel)
    if distance_if_momentary_top_speed>distance:
        #we don't even reach top speed
        #if the delta v is fixed, distance becomes inversely proportional to acceleration (s=v^2/2a)
        #so the distance travelled which acceling is proportional to decel/(accel+decel)
        accel_dist = distance * decel / (accel + decel)
        decel_dist = distance * accel / (decel + accel)
        velocity_reached = sqrt(2*accel_dist*accel)
        time_accel = accel_dist / (velocity_reached / 2)
        time_decel = decel_dist / (velocity_reached / 2)
        return time_accel + time_decel
    #we reach top speed
    accel_time = top_speed / accel
    decel_time = top_speed / decel
    accel_dist = accel_time * (top_speed / 2)
    decel_dist = decel_time * (top_speed / 2)
    remaining_dist = distance - accel_dist - decel_dist
    assert(remaining_dist >= 0)
    total_time = accel_time + decel_time + (remaining_dist / top_speed)
    return total_time

@cache
def calculate_route_time(start_station, end_station, line, top_speed_function, silent=0):
    #stations have the same line
    start_ID = vertex_ID[start_station]
    end_ID = vertex_ID[end_station]
    route = get_forced_route(graph, start_ID, end_ID, line)[0]
    total_time = 0
    for i in range(len(route)-1):
        first = route[i]
        second = route[i+1]
        distance = get_distance(first[0], second[0])
        line = first[1]
        assert(line==second[1]) #make sure all stations on the route are on the same line
        delta_time = get_adjacent_time(distance, line, top_speed_function(first[0], second[0], first[1]))
        total_time += delta_time
        if (vertex_data[first[0]][0], line) in average_dwell_times:
            total_time += average_dwell_times[(vertex_data[first[0]][0], line)] #sum all the dwell times from the first station to the penultimate station
        else:
            if not silent:
                print('Warning: No dwell data present for',(vertex_data[first[0]][0], line))
    return total_time

def get_loss():
    loss = 0
    get_top_speed.cache_clear()
    get_adjacent_time.cache_clear()
    calculate_route_time.cache_clear()
    for entry in formatted_data:
        s,t,line,tim = entry
        result = calculate_route_time(s,t,line,get_top_speed,silent=1)
        loss += abs(result - entry[-1])**2
    return loss
def fine_tune():
    #ternary search on the relative speeds!
    global relative_speeds
    for line in relative_speeds:
        l=0
        r=3
        while r-l>1e-3:
            m1 = l+(r-l)/3
            m2 = l+(r-l)*2/3
            relative_speeds[line] = m1
            a1 = get_loss()
            relative_speeds[line] = m2
            a2 = get_loss()
            if a1<a2:
                r=m2
            else:
                l=m1
        print(line, l)
        relative_speeds[line] = l
    print('Fine tune finished. Total Squared Error:',get_loss())
    return relative_speeds
def time_DC(current_station, next_station, used_line, silent=1):
    result = 0
    if (vertex_data[current_station][0], used_line) in average_dwell_times:
        result += average_dwell_times[(vertex_data[current_station][0], used_line)] #sum all the dwell times from the first station to the penultimate station
    else:
        if not silent:
            print('Warning: No dwell data present for',(vertex_data[current_station][0], used_line))
    result += get_adjacent_time(get_distance(current_station,next_station), used_line, get_top_speed(current_station, next_station, used_line))

    return result
def model_transfer_time(node, prev_line, new_line):
    answer = (len(graph[node])/2)**0.5*60 + (3600/frequencies[new_line])/2
    return answer