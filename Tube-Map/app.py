#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, flash
import folium

# Import your existing backend functions and data structures
from routes import get_shortest_route, journey_summary
from visualisation import create_route_map
from setup import graph, vertex_data, line_colours, vertex_ID
from model import time_DC, model_transfer_time

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # needed for flashing messages

# Prepare a sorted list of all station names from your vertex_data for the datalist
station_names = sorted([vertex_data[vid][0] for vid in vertex_data])

def lookup_station_id(name):
    """
    Given a station name (case-insensitive match), return the corresponding station id.
    Uses the vertex_ID dictionary, if available, or searches vertex_data.
    """
    # First try the vertex_ID mapping if your key exactly matches
    if name in vertex_ID:
        return vertex_ID[name]
    # Otherwise try a case-insensitive search in vertex_data
    for vid, (sname, _, _) in vertex_data.items():
        if sname.lower() == name.lower():
            return vid
    return None

@app.route("/", methods=["GET", "POST"])
def index():
    map_html = None
    journey = ""
    total_time = ""
    selected_start = ""
    selected_end = ""

    if request.method == "POST":
        selected_start = request.form.get("start_station", "").strip()
        selected_end = request.form.get("end_station", "").strip()

        # look up the station id's
        start_id = lookup_station_id(selected_start)
        end_id = lookup_station_id(selected_end)

        if not start_id or not end_id:
            flash("One or both station names were not found. Please check your spelling.")
            return redirect(url_for("index"))

        # Get the shortest route - here we assume get_shortest_route returns (route_path, total_weight)
        route_path, route_distance = get_shortest_route(
            graph, start_id, end_id,
            time_function=time_DC,
            transfer_time=model_transfer_time
        )

        if not route_path:
            flash("No route could be found between the selected stations.")
            return redirect(url_for("index"))

        # Get a route summary (e.g. a brief text description)
        journey = journey_summary(route_path)
        total_time_seconds = int(route_distance)

        hours = total_time_seconds // 3600
        minutes = (total_time_seconds % 3600) // 60
        seconds = total_time_seconds % 60

        time_parts = []
        if hours > 0:
            time_parts.append(f"{hours} hour{'s' if hours > 1  else ''}")
        if minutes > 0:
            time_parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
        if seconds > 0:
            time_parts.append(f"{seconds} second{'s' if seconds > 1 else ''}")

        total_time = ', '.join(time_parts)
        print(total_time)  # Output: '1 hour, 1 minute, 7 seconds'

        # Create the Folium map.
        # You can set a center coordinate (e.g. central London) or compute a bounding box.
        m = create_route_map(
            graph,
            vertex_data,
            line_colours,
            route_path,
            route_distance,
            center_coords=(51.5074, -0.1278)
        )
        map_html = m._repr_html_()

    return render_template("index.html",
                           station_names=station_names,
                           map_html=map_html,
                           journey=journey,
                           total_time=total_time,
                           selected_start=selected_start,
                           selected_end=selected_end)

if __name__ == "__main__":
    app.run(debug=True)