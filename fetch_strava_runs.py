#!/usr/bin/env python3
"""
fetch_strava_latest.py

- Refreshes Strava access_token using STRAVA_REFRESH_TOKEN
- Fetches the most recent activity of type "Run"
- Fetches streams (latlng, altitude, time)
- Computes per-km pace markers (average pace per km)
- Writes:
    data/latest_run.json      -> summary + pace markers
    data/latest_route.geojson -> GeoJSON LineString (lng,lat,alt)
- Prints new refresh_token to stdout so you can update your GitHub secret manually.
"""

import os
import sys
import json
import math
import time
import requests
from datetime import datetime

STRAVA_OAUTH_TOKEN = "https://www.strava.com/oauth/token"
STRAVA_API = "https://www.strava.com/api/v3"

# ---- Helpers ----
def haversine(lat1, lon1, lat2, lon2):
    # return meters between two lat/lon
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2.0)**2 + math.cos(phi1)*math.cos(phi2)*(math.sin(dlambda/2.0)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def sec_to_pace_str(sec_per_km):
    # Returns "MM:SS /km"
    if sec_per_km is None:
        return None
    mm = int(sec_per_km // 60)
    ss = int(round(sec_per_km - mm*60))
    return f"{mm:d}:{ss:02d} /km"

# ---- Strava auth ----
def refresh_access_token(client_id, client_secret, refresh_token):
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    r = requests.post(STRAVA_OAUTH_TOKEN, data=payload, timeout=30)
    r.raise_for_status()
    return r.json()  # contains access_token, refresh_token, expires_at, athlete, etc.

# ---- Fetch latest run ----
def get_latest_run_id(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {'per_page': 30, 'page': 1}
    r = requests.get(f"{STRAVA_API}/athlete/activities", headers=headers, params=params, timeout=30)
    r.raise_for_status()
    activities = r.json()
    for act in activities:
        if act.get('type') == 'Run':
            return act  # return the whole activity dict for the latest Run
    return None

# ---- Fetch streams ----
def get_streams(access_token, activity_id, types=['latlng','altitude','time','moving']):
    headers = {'Authorization': f'Bearer {access_token}'}
    types_param = ",".join(types)
    params = {'keys': types_param, 'key_by_type': 'true'}
    r = requests.get(f"{STRAVA_API}/activities/{activity_id}/streams", headers=headers, params=params, timeout=30)
    # Note: sometimes Strava needs us to request each type separately; but key_by_type works frequently.
    # If you get 404 or empty, consider requesting each type separately.
    if r.status_code == 404 or r.status_code == 204:
        return {}
    r.raise_for_status()
    return r.json()

# ---- Main ----
def main():
    client_id = os.getenv('STRAVA_CLIENT_ID')
    client_secret = os.getenv('STRAVA_CLIENT_SECRET')
    refresh_token = os.getenv('STRAVA_REFRESH_TOKEN')

    if not client_id or not client_secret or not refresh_token:
        print("ERROR: set STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REFRESH_TOKEN as env vars.", file=sys.stderr)
        sys.exit(2)

    # 1) refresh access token
    print("Refreshing access token...")
    token_resp = refresh_access_token(client_id, client_secret, refresh_token)
    access_token = token_resp.get('access_token')
    new_refresh_token = token_resp.get('refresh_token')
    expires_at = token_resp.get('expires_at')

    if not access_token:
        print("ERROR: Could not get access token from Strava.", file=sys.stderr)
        sys.exit(3)

    # Print the new refresh token so the user can update the secret in GitHub (single-use tokens)
    print("\n*** IMPORTANT: Strava returned a NEW refresh_token. Save this token as the repo secret STRAVA_REFRESH_TOKEN for next runs. ***\n")
    print("NEW_REFRESH_TOKEN:", new_refresh_token)
    print("EXPIRES_AT:", expires_at)
    print("-----\n")

    # 2) get latest run
    print("Fetching latest run...")
    latest_activity = get_latest_run_id(access_token)
    if latest_activity is None:
        print("No recent Run found.", file=sys.stderr)
        sys.exit(0)

    activity_id = latest_activity['id']
    print(f"Found latest run: id={activity_id} name='{latest_activity.get('name')}' date={latest_activity.get('start_date_local')}")

    # 3) fetch streams
    print("Fetching streams (latlng, altitude, time)...")
    streams = get_streams(access_token, activity_id, types=['latlng','altitude','time'])
    # streams should be keyed by type (if key_by_type=true)
    latlng = streams.get('latlng', {}).get('data') or streams.get('latlng') or []
    altitude = streams.get('altitude', {}).get('data') or streams.get('altitude') or []
    times = streams.get('time', {}).get('data') or streams.get('time') or []

    if not latlng:
        print("No latlng stream available for this activity. Exiting.", file=sys.stderr)
        sys.exit(4)

    # Combine streams
    pts = []
    for i, ll in enumerate(latlng):
        lat = float(ll[0])
        lon = float(ll[1])
        alt = None
        if i < len(altitude):
            try:
                alt = float(altitude[i])
            except:
                alt = None
        t = None
        if i < len(times):
            t = float(times[i])  # seconds from start
        pts.append({'lat': lat, 'lon': lon, 'alt': alt, 'time': t})

    # compute cumulative distance and per-km pace markers
    cum_dist = 0.0
    km_mark = 1
    last_point = None
    km_markers = []  # list of dicts: {km, lat, lon, time_s, pace_s_per_km}
    cum_dist_at_prev = 0.0
    last_time = None

    for i, p in enumerate(pts):
        if last_point is not None:
            d = haversine(last_point['lat'], last_point['lon'], p['lat'], p['lon'])
            cum_dist += d
        else:
            d = 0.0
        # store cumdist in point
        pts[i]['cumdist_m'] = cum_dist
        if p.get('time') is not None:
            last_time = p['time']

        # check if we reached >= km_mark*1000
        while cum_dist >= km_mark * 1000:
            # find approximate point for that km mark by linear interpolation between last_point and current
            # last_point has cumdist < km_mark*1000, current has >=
            if last_point is None:
                marker_lat = p['lat']
                marker_lon = p['lon']
                marker_time = p.get('time')
            else:
                need = km_mark*1000 - (cum_dist - d)
                frac = 0.0 if d == 0 else (need / d)
                # interpolate lat/lon/time/alt
                lat_i = last_point['lat'] + (p['lat'] - last_point['lat']) * frac
                lon_i = last_point['lon'] + (p['lon'] - last_point['lon']) * frac
                alt_i = None
                if last_point.get('alt') is not None and p.get('alt') is not None:
                    alt_i = last_point['alt'] + (p['alt'] - last_point['alt']) * frac
                time_i = None
                if last_point.get('time') is not None and p.get('time') is not None:
                    time_i = last_point['time'] + (p['time'] - last_point['time']) * frac
                marker_lat = lat_i
                marker_lon = lon_i
                marker_time = time_i

            # compute pace for this km: time difference between this km marker and previous km marker (or start)
            if km_mark == 1:
                # from start (time ~ 0) to marker_time
                prev_time = 0.0
            else:
                prev_entry = km_markers[-1]
                prev_time = prev_entry.get('time_s', 0.0) if prev_entry.get('time_s') is not None else 0.0

            pace_s = None
            if marker_time is not None:
                pace_s = marker_time - prev_time  # seconds for this km
            km_markers.append({
                'km': km_mark,
                'lat': marker_lat,
                'lon': marker_lon,
                'time_s': marker_time,
                'pace_s': pace_s,
                'pace_str': sec_to_pace_str(pace_s) if pace_s is not None else None
            })
            km_mark += 1

        last_point = p

    # Prepare GeoJSON for route (LineString) - coordinates are [lon, lat, alt?]
    coords = []
    for p in pts:
        if p.get('alt') is not None:
            coords.append([p['lon'], p['lat'], p['alt']])
        else:
            coords.append([p['lon'], p['lat']])

    geojson = {
        "type": "Feature",
        "properties": {
            "activity_id": activity_id,
            "name": latest_activity.get('name'),
            "start_date": latest_activity.get('start_date_local'),
            "distance_m": latest_activity.get('distance'),
            "moving_time_s": latest_activity.get('moving_time'),
            "elapsed_time_s": latest_activity.get('elapsed_time'),
            "average_speed_m_s": latest_activity.get('average_speed'),
        },
        "geometry": {
            "type": "LineString",
            "coordinates": coords
        }
    }

    # Summary for latest_run.json
    summary = {
        "activity_id": activity_id,
        "name": latest_activity.get('name'),
        "start_date_local": latest_activity.get('start_date_local'),
        "distance_m": latest_activity.get('distance'),
        "distance_km": (latest_activity.get('distance') or 0) / 1000.0,
        "moving_time_s": latest_activity.get('moving_time'),
        "elapsed_time_s": latest_activity.get('elapsed_time'),
        "average_speed_m_s": latest_activity.get('average_speed'),
        "average_pace_s_per_km": None if not latest_activity.get('average_speed') else (1000.0 / latest_activity.get('average_speed')),
        "km_markers": km_markers,
        "points_count": len(pts),
    }

    # Ensure data directory
    os.makedirs('data', exist_ok=True)
    with open('data/latest_route.geojson', 'w') as f:
        json.dump(geojson, f)

    with open('data/latest_run.json', 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\nWrote data/latest_route.geojson ({len(coords)} coords) and data/latest_run.json")
    print("Done.")

if __name__ == "__main__":
    main()
