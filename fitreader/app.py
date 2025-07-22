from flask import Flask, render_template, request, redirect, url_for
import folium
import os
import csv
from garmin_fit_sdk import Decoder, Stream
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    map_html = None
    if request.method == 'POST':
        file = request.files['fitfile']
        if file and file.filename.endswith('.fit'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            # Parse FIT file
            # Pass the file object directly to Stream, not BytesIO
            stream = Stream.from_file(filepath)
            decoder = Decoder(stream)
            is_fit = decoder.is_fit()
            app.logger.debug(f"is_fit: {is_fit}")
            if is_fit:
                messages, errors = decoder.read()
                # Extract lat/lon from records
                latlons = []
                #app.logger.debug("Decoded messages: %s", messages)
                with open(os.path.join(app.config['UPLOAD_FOLDER'], filename + '.log'), 'w') as log_file:
                    for msg_type, msg_list in messages.items():
                        for msg in msg_list:
                            log_file.write(f"{msg_type}: {msg}\n")
                # For each lap, find the latest record message within its time range
                laps = messages.get('lap_mesgs', [])
                records = messages.get('record_mesgs', [])
                latest_records_per_lap = []
                app.logger.debug(f"Number of laps: {len(laps)}")
                app.logger.debug(f"Number of records: {len(records)}")
                for lap in laps:
                    lap_start = lap.get('start_time')
                    lap_end = lap.get('timestamp')
                    # Find records within this lap's time range
                    records_in_lap = [
                        r for r in records
                        if r.get('timestamp') is not None and r.get('position_lat') is not None and r.get('position_long') is not None
                        and lap_start <= r.get('timestamp') <= lap_end
                    ]
                    if records_in_lap:
                        # Get the latest record (max timestamp)
                        latest_record = max(records_in_lap, key=lambda r: r['timestamp'])
                        latest_records_per_lap.append(latest_record)
                        app.logger.debug(f"Latest record for lap {lap['timestamp']}: {latest_record}")
                # Optionally, log the latest records per lap
                for msg in latest_records_per_lap:
                    lat = msg.get('position_lat')
                    lon = msg.get('position_long')
                    if lat and lon:
                        # Convert semicircles to degrees
                        lat = lat * (180 / 2**31)
                        lon = lon * (180 / 2**31)
                        latlons.append((lat, lon))
                    holes = []
                    current_hole = []
                    for idx, lap in enumerate(laps):
                        if idx == 0:
                            continue  # skip the first lap (activity start)
                        if lap.get('total_distance', 1) == 0 and current_hole:
                            holes.append(current_hole)
                            current_hole = []
                        current_hole.append(lap)
                    if current_hole:
                        holes.append(current_hole)

                    # Assign a color for each hole
                    colors = [
                        'blue', 'red', 'green', 'purple', 'orange', 'darkred', 'lightred',
                        'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple',
                        'white', 'pink', 'lightblue', 'lightgreen', 'gray', 'black'
                    ]
                    m = None
                    csv_filename = os.path.join(app.config['UPLOAD_FOLDER'], filename + '_shots.csv')
                    with open(csv_filename, 'w', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(['Hole', 'Shot#', 'Lat', 'Lon'])
                    for hole_idx, hole_laps in enumerate(holes):
                        # Get all records for this hole
                        hole_records = []
                        for lap in hole_laps:
                            lap_start = lap.get('start_time')
                            lap_end = lap.get('timestamp')
                            records_in_lap = [
                                r for r in records
                                if r.get('timestamp') is not None and r.get('position_lat') is not None and r.get('position_long') is not None
                                and lap_start <= r.get('timestamp') <= lap_end
                            ]
                            if records_in_lap:
                                latest_record = max(records_in_lap, key=lambda r: r['timestamp'])
                                hole_records.append(latest_record)
                        # Convert to lat/lon
                        hole_latlons = []
                        for msg in hole_records:
                            lat = msg.get('position_lat')
                            lon = msg.get('position_long')
                            if lat and lon:
                                lat = lat * (180 / 2**31)
                                lon = lon * (180 / 2**31)
                                hole_latlons.append((lat, lon))
                        if hole_latlons:
                            if m is None:
                                m = folium.Map(location=hole_latlons[0], zoom_start=14, tiles='CartoDB Positron')
                            color = colors[hole_idx % len(colors)]
                            for idx, latlon in enumerate(hole_latlons, start=1):
                                folium.CircleMarker(location=latlon, radius=3, color=color, fill=True, fill_color=color, popup=f"Hole {hole_idx+1} - Shot {idx}").add_to(m)
                                with open(csv_filename, 'a', newline='') as csvfile:
                                    writer = csv.writer(csvfile)
                                    writer.writerow([hole_idx+1, idx, latlon[0], latlon[1]])
                    if m:
                        map_html = m._repr_html_()
            else:
                app.logger.error(f"Uploaded file is not a valid FIT file. is_fit: {is_fit}")
    return render_template('index.html', map_html=map_html)

if __name__ == '__main__':
    app.run(debug=True)
