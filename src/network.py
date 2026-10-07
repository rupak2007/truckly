"""
TRUCKLY — network layer.

Node coordinates are REAL (public gazetteer / OpenStreetMap place nodes)  -> OBS
Road distances in this build are DERIVED from great-circle distance times a
declared circuity factor                                                  -> ASM/DRV

WHY NOT OSRM: the execution sandbox used to build this project has no route to
the OSRM demo server (connection attempt returned no HTTP status). Rather than
fabricate road distances and label them observed, the distance layer is an
explicit, documented approximation. `build_matrices_from_osrm()` below is the
drop-in replacement to run once network access is available; it writes the same
cache files, and nothing else in the codebase changes.
"""
from __future__ import annotations

import json
import os
import numpy as np

EARTH_R_KM = 6371.0088

# ---------------------------------------------------------------------------
# NODES  — provenance OBS (coordinates), ASM (roles and demand weights)
# ---------------------------------------------------------------------------
# node_id, name, lat, lon, role, demand_out, demand_in
NODES_RAW = [
    ("CHN", "Chennai",          13.0827, 80.2707, "hub",      1.00, 1.00),
    ("SPB", "Sriperumbudur",    12.9675, 79.9430, "industrial",0.85, 0.55),
    ("ORG", "Oragadam",         12.8100, 79.9500, "industrial",0.80, 0.50),
    ("GMD", "Gummidipoondi",    13.4084, 80.1082, "industrial",0.55, 0.40),
    ("KPM", "Kanchipuram",      12.8342, 79.7036, "customer",  0.35, 0.45),
    ("RNP", "Ranipet",          12.9249, 79.3308, "industrial",0.45, 0.35),
    ("VLR", "Vellore",          12.9165, 79.1325, "customer",  0.40, 0.50),
    ("CTR", "Chittoor",         13.2172, 79.1003, "customer",  0.30, 0.35),
    ("TPT", "Tirupati",         13.6288, 79.4192, "customer",  0.35, 0.45),
    ("KGI", "Krishnagiri",      12.5186, 78.2137, "hub",       0.50, 0.45),
    ("HSR", "Hosur",            12.7409, 77.8253, "industrial",0.80, 0.60),
    ("BLR", "Bengaluru",        12.9716, 77.5946, "hub",       0.95, 1.00),
    ("BID", "Bidadi",           12.7942, 77.3854, "industrial",0.60, 0.40),
    ("NLM", "Nelamangala",      13.0996, 77.3936, "industrial",0.55, 0.40),
    ("TUM", "Tumakuru",         13.3379, 77.1173, "customer",  0.35, 0.35),
    ("MYS", "Mysuru",           12.2958, 76.6394, "customer",  0.40, 0.45),
    ("DPI", "Dharmapuri",       12.1211, 78.1583, "customer",  0.25, 0.30),
    ("SLM", "Salem",            11.6643, 78.1460, "hub",       0.60, 0.60),
    ("NMK", "Namakkal",         11.2189, 78.1674, "customer",  0.30, 0.30),
    ("ERD", "Erode",            11.3410, 77.7172, "customer",  0.45, 0.40),
    ("TRP", "Tiruppur",         11.1085, 77.3411, "industrial",0.70, 0.45),
    ("CBE", "Coimbatore",       11.0168, 76.9558, "hub",       0.75, 0.75),
    ("KRR", "Karur",            10.9601, 78.0766, "customer",  0.30, 0.30),
    ("TRY", "Tiruchirappalli",  10.7905, 78.7047, "hub",       0.50, 0.55),
    ("TNJ", "Thanjavur",        10.7870, 79.1378, "customer",  0.25, 0.30),
    ("DGL", "Dindigul",         10.3624, 77.9695, "customer",  0.25, 0.30),
    ("MDU", "Madurai",           9.9252, 78.1198, "hub",       0.50, 0.60),
    ("TTN", "Thoothukudi",       8.7642, 78.1348, "port",      0.55, 0.35),
    ("NGC", "Nagercoil",         8.1833, 77.4119, "customer",  0.20, 0.25),
    ("KCH", "Kochi",             9.9312, 76.2673, "port",      0.60, 0.55),
    ("PDY", "Puducherry",       11.9416, 79.8083, "customer",  0.30, 0.35),
    ("CDL", "Cuddalore",        11.7480, 79.7714, "industrial",0.35, 0.30),
    ("NLR", "Nellore",          14.4426, 79.9865, "customer",  0.30, 0.30),
    ("ONG", "Ongole",           15.5057, 80.0499, "customer",  0.25, 0.25),
    ("GNT", "Guntur",           16.3067, 80.4365, "customer",  0.35, 0.35),
    ("VJA", "Vijayawada",       16.5062, 80.6480, "hub",       0.50, 0.50),
    ("ATP", "Anantapur",        14.6819, 77.6006, "customer",  0.25, 0.25),
    ("KNL", "Kurnool",          15.8281, 78.0373, "customer",  0.30, 0.30),
    ("HBL", "Hubballi",         15.3647, 75.1240, "hub",       0.40, 0.40),
    ("MLR", "Mangaluru",        12.9141, 74.8560, "port",      0.45, 0.35),
]

# Regions used for the demand-asymmetry model (ASM)
SOURCE_REGION = {"CHN", "SPB", "ORG", "GMD", "RNP", "KPM", "CDL", "PDY",
                 "TTN", "KCH", "MLR", "VJA", "GNT"}


def haversine_km(lat1, lon1, lat2, lon2):
    p = np.pi / 180.0
    dlat = (lat2 - lat1) * p
    dlon = (lon2 - lon1) * p
    a = (np.sin(dlat / 2) ** 2
         + np.cos(lat1 * p) * np.cos(lat2 * p) * np.sin(dlon / 2) ** 2)
    return 2 * EARTH_R_KM * np.arcsin(np.sqrt(a))


def bearing_deg(lat1, lon1, lat2, lon2):
    p = np.pi / 180.0
    dlon = (lon2 - lon1) * p
    y = np.sin(dlon) * np.cos(lat2 * p)
    x = (np.cos(lat1 * p) * np.sin(lat2 * p)
         - np.sin(lat1 * p) * np.cos(lat2 * p) * np.cos(dlon))
    return (np.degrees(np.arctan2(y, x)) + 360.0) % 360.0


class RoadNetwork:
    """Distance (km) and duration (minutes) matrices over the node set."""

    def __init__(self, cfg):
        self.cfg = cfg
        self.ids = [n[0] for n in NODES_RAW]
        self.names = {n[0]: n[1] for n in NODES_RAW}
        self.idx = {nid: i for i, nid in enumerate(self.ids)}
        self.lat = np.array([n[2] for n in NODES_RAW])
        self.lon = np.array([n[3] for n in NODES_RAW])
        self.role = {n[0]: n[4] for n in NODES_RAW}
        self.demand_out = np.array([n[5] for n in NODES_RAW])
        self.demand_in = np.array([n[6] for n in NODES_RAW])
        self.n = len(self.ids)
        self._build()

    # -- distance / duration -------------------------------------------------
    def _build(self):
        c = self.cfg["network"]
        LA1 = self.lat[:, None]; LO1 = self.lon[:, None]
        LA2 = self.lat[None, :]; LO2 = self.lon[None, :]
        gc = haversine_km(LA1, LO1, LA2, LO2)

        circ = np.where(gc < 50, c["circuity"]["short_lt_50km"],
               np.where(gc < 200, c["circuity"]["mid_50_200km"],
                                  c["circuity"]["long_gt_200km"]))
        self.dist = gc * circ
        np.fill_diagonal(self.dist, 0.0)

        spd = np.where(self.dist < 50, c["speeds_kmh"]["short_lt_50km"],
              np.where(self.dist < 200, c["speeds_kmh"]["mid_50_200km"],
                                        c["speeds_kmh"]["long_gt_200km"]))
        self.dur = self.dist / spd * 60.0          # minutes
        np.fill_diagonal(self.dur, 0.0)

        self.gc = gc
        self.circuity_applied = circ
        self.bearing = bearing_deg(LA1, LO1, LA2, LO2)

        # deterministic per-arc road-difficulty index in [0,1] (ASM)
        rng = np.random.default_rng(self.cfg["meta"]["master_seed"] + 7717)
        rf = rng.normal(self.cfg["fuel_model"]["road_factor_mean"],
                        self.cfg["fuel_model"]["road_factor_sd"],
                        size=(self.n, self.n))
        rf = np.clip((rf + rf.T) / 2.0, 0.05, 0.95)   # symmetric
        np.fill_diagonal(rf, 0.0)
        self.road_factor = rf

    # -- accessors -----------------------------------------------------------
    def d(self, a, b):   return float(self.dist[self.idx[a], self.idx[b]])
    def t(self, a, b):   return float(self.dur[self.idx[a], self.idx[b]])
    def rf(self, a, b):  return float(self.road_factor[self.idx[a], self.idx[b]])
    def brg(self, a, b): return float(self.bearing[self.idx[a], self.idx[b]])

    def path_km(self, seq):
        return sum(self.d(seq[i], seq[i + 1]) for i in range(len(seq) - 1))

    def save_cache(self, folder):
        os.makedirs(folder, exist_ok=True)
        np.save(os.path.join(folder, "dist_matrix.npy"), self.dist)
        np.save(os.path.join(folder, "dur_matrix.npy"), self.dur)
        np.save(os.path.join(folder, "road_factor.npy"), self.road_factor)
        with open(os.path.join(folder, "network_meta.json"), "w") as f:
            json.dump({
                "node_ids": self.ids,
                "distance_provenance": "DRV/ASM - haversine x declared circuity",
                "coordinate_provenance": "OBS - public gazetteer / OpenStreetMap",
                "osrm_used": False,
                "note": ("OSRM demo server unreachable from the build sandbox; "
                         "see docs/limitations.md. Replace with "
                         "build_matrices_from_osrm() when network access exists.")
            }, f, indent=2)

    # -- the drop-in real-road replacement -----------------------------------
    @staticmethod
    def build_matrices_from_osrm(node_ids, lats, lons, out_folder,
                                 base="https://router.project-osrm.org"):
        """Run ONCE when a routing engine is reachable, then never again.

        Writes dist_matrix.npy (km) and dur_matrix.npy (minutes) in exactly the
        format the rest of TRUCKLY consumes, so switching to real road data is a
        one-command change with no edits anywhere else.
        """
        import urllib.request
        coords = ";".join(f"{lo:.6f},{la:.6f}" for la, lo in zip(lats, lons))
        url = f"{base}/table/v1/driving/{coords}?annotations=distance,duration"
        with urllib.request.urlopen(url, timeout=120) as r:
            js = json.loads(r.read().decode())
        dist = np.array(js["distances"], dtype=float) / 1000.0     # m -> km
        dur = np.array(js["durations"], dtype=float) / 60.0        # s -> min
        os.makedirs(out_folder, exist_ok=True)
        np.save(os.path.join(out_folder, "dist_matrix.npy"), dist)
        np.save(os.path.join(out_folder, "dur_matrix.npy"), dur)
        with open(os.path.join(out_folder, "network_meta.json"), "w") as f:
            json.dump({"node_ids": list(node_ids), "osrm_used": True,
                       "distance_provenance": "OBS - OSRM over OpenStreetMap"},
                      f, indent=2)
        return dist, dur
