import json

def build_roads():
    features = []

    # 1. MAJOR INTERSTATES & FREEWAYS SPANNING GREATER HOUSTON
    # Interstate 10 (Katy Fwy / East Fwy) - Spans west from Katy to east Baytown
    features.append({
        'type': 'Feature',
        'geometry': {
            'type': 'LineString',
            'coordinates': [
                [-95.850, 29.785], [-95.770, 29.784], [-95.690, 29.784],
                [-95.630, 29.784], [-95.560, 29.783], [-95.460, 29.781],
                [-95.400, 29.775], [-95.365, 29.765], [-95.330, 29.768],
                [-95.270, 29.774], [-95.180, 29.785], [-95.050, 29.800],
                [-94.950, 29.805]
            ]
        },
        'properties': {'name': 'I-10 (Katy / East Freeway)', 'type': 'interstate', 'tier': 1}
    })

    # Interstate 45 (North Fwy / Gulf Fwy) - Spans north from The Woodlands to south Galveston approach
    features.append({
        'type': 'Feature',
        'geometry': {
            'type': 'LineString',
            'coordinates': [
                [-95.460, 30.200], [-95.455, 30.155], [-95.445, 30.080],
                [-95.430, 30.000], [-95.410, 29.950], [-95.390, 29.880],
                [-95.375, 29.810], [-95.365, 29.760], [-95.350, 29.730],
                [-95.320, 29.690], [-95.280, 29.650], [-95.210, 29.580],
                [-95.130, 29.520], [-95.070, 29.450]
            ]
        },
        'properties': {'name': 'I-45 (North / Gulf Freeway)', 'type': 'interstate', 'tier': 1}
    })

    # Interstate 69 / US-59 (Eastex Fwy / Southwest Fwy) - Kingwood down to Sugar Land
    features.append({
        'type': 'Feature',
        'geometry': {
            'type': 'LineString',
            'coordinates': [
                [-95.210, 30.060], [-95.240, 30.000], [-95.280, 29.930],
                [-95.320, 29.850], [-95.355, 29.770], [-95.365, 29.740],
                [-95.410, 29.725], [-95.480, 29.715], [-95.560, 29.680],
                [-95.620, 29.600], [-95.690, 29.560], [-95.770, 29.520]
            ]
        },
        'properties': {'name': 'I-69 / US-59 (Southwest / Eastex Freeway)', 'type': 'interstate', 'tier': 1}
    })

    # Interstate 610 (The Inner Loop) - Complete 38-mile orbital
    loop_610 = [
        [-95.460, 29.780], [-95.410, 29.810], [-95.360, 29.815],
        [-95.300, 29.805], [-95.275, 29.770], [-95.280, 29.720],
        [-95.310, 29.680], [-95.380, 29.675], [-95.440, 29.680],
        [-95.465, 29.720], [-95.460, 29.780]
    ]
    features.append({
        'type': 'Feature',
        'geometry': {'type': 'LineString', 'coordinates': loop_610},
        'properties': {'name': 'I-610 Loop (Inner Orbital)', 'type': 'loop', 'tier': 1}
    })

    # Beltway 8 / Sam Houston Tollway - Middle orbital ring (88 miles)
    beltway_8 = [
        [-95.565, 29.784], [-95.560, 29.860], [-95.520, 29.920],
        [-95.430, 29.945], [-95.340, 29.940], [-95.240, 29.900],
        [-95.170, 29.840], [-95.140, 29.760], [-95.150, 29.680],
        [-95.210, 29.600], [-95.320, 29.590], [-95.450, 29.600],
        [-95.550, 29.640], [-95.570, 29.710], [-95.565, 29.784]
    ]
    features.append({
        'type': 'Feature',
        'geometry': {'type': 'LineString', 'coordinates': beltway_8},
        'properties': {'name': 'Beltway 8 / Sam Houston Tollway', 'type': 'loop', 'tier': 1}
    })

    # Grand Parkway / TX-99 - Outer mega-orbital
    tx_99 = [
        [-95.770, 29.540], [-95.775, 29.650], [-95.770, 29.784],
        [-95.750, 29.880], [-95.700, 29.980], [-95.600, 30.060],
        [-95.460, 30.110], [-95.350, 30.120], [-95.200, 30.080]
    ]
    features.append({
        'type': 'Feature',
        'geometry': {'type': 'LineString', 'coordinates': tx_99},
        'properties': {'name': 'Grand Parkway (TX-99)', 'type': 'loop', 'tier': 1}
    })

    # US-290 (Northwest Freeway) - Out to Cypress & Waller
    features.append({
        'type': 'Feature',
        'geometry': {
            'type': 'LineString',
            'coordinates': [
                [-95.440, 29.790], [-95.500, 29.840], [-95.580, 29.890],
                [-95.670, 29.950], [-95.770, 30.020], [-95.880, 30.080]
            ]
        },
        'properties': {'name': 'US-290 (Northwest Freeway)', 'type': 'highway', 'tier': 1}
    })

    # TX-288 (South Freeway) - Downtown down to Pearland & Manvel
    features.append({
        'type': 'Feature',
        'geometry': {
            'type': 'LineString',
            'coordinates': [
                [-95.365, 29.740], [-95.378, 29.710], [-95.385, 29.660],
                [-95.390, 29.590], [-95.392, 29.520], [-95.395, 29.450]
            ]
        },
        'properties': {'name': 'TX-288 (South Freeway)', 'type': 'highway', 'tier': 1}
    })

    # TX-225 (La Porte Freeway) - 610 East to Pasadena & La Porte
    features.append({
        'type': 'Feature',
        'geometry': {
            'type': 'LineString',
            'coordinates': [
                [-95.275, 29.725], [-95.200, 29.715], [-95.120, 29.710],
                [-95.030, 29.690]
            ]
        },
        'properties': {'name': 'TX-225 (La Porte Freeway)', 'type': 'highway', 'tier': 1}
    })

    # Westpark Tollway - Uptown to Cinco Ranch
    features.append({
        'type': 'Feature',
        'geometry': {
            'type': 'LineString',
            'coordinates': [
                [-95.460, 29.725], [-95.530, 29.720], [-95.610, 29.715],
                [-95.700, 29.700], [-95.780, 29.690]
            ]
        },
        'properties': {'name': 'Westpark Tollway', 'type': 'highway', 'tier': 1}
    })

    # Hardy Toll Road - North Houston to Spring
    features.append({
        'type': 'Feature',
        'geometry': {
            'type': 'LineString',
            'coordinates': [
                [-95.360, 29.815], [-95.355, 29.890], [-95.360, 29.980],
                [-95.380, 30.060]
            ]
        },
        'properties': {'name': 'Hardy Toll Road', 'type': 'highway', 'tier': 1}
    })

    # 2. KEY REGIONAL CROSS-TOWN ARTERIALS (CONNECTING ALL SUBURBS & NEIGHBORHOODS)
    arterials = [
        # East-West Major Arterials
        ("Westheimer Road (Regional Spine)", [[-95.365, 29.742], [-95.440, 29.740], [-95.530, 29.736], [-95.630, 29.735], [-95.730, 29.735]]),
        ("Memorial Drive (Buffalo Bayou Corridor)", [[-95.365, 29.762], [-95.420, 29.763], [-95.490, 29.768], [-95.570, 29.775], [-95.640, 29.780]]),
        ("Bellaire Boulevard (Southwest Spine)", [[-95.420, 29.705], [-95.490, 29.704], [-95.580, 29.703], [-95.680, 29.702]]),
        ("FM 1960 (North Regional Cross-Corridor)", [[-95.680, 29.980], [-95.560, 29.990], [-95.430, 30.005], [-95.300, 30.010], [-95.180, 30.015]]),
        ("Bissonnet Street", [[-95.430, 29.715], [-95.510, 29.690], [-95.600, 29.660]]),
        ("Clear Lake City Blvd & NASA Parkway", [[-95.180, 29.560], [-95.100, 29.550], [-95.030, 29.540]]),
        ("Woodlands Parkway", [[-95.550, 30.170], [-95.480, 30.165], [-95.450, 30.160]]),
        ("Spencer Highway (Pasadena - La Porte)", [[-95.230, 29.660], [-95.150, 29.660], [-95.060, 29.660]]),
        ("Little York Road", [[-95.480, 29.870], [-95.380, 29.870], [-95.280, 29.870]]),
        ("Tidwell Road", [[-95.460, 29.845], [-95.370, 29.845], [-95.280, 29.845]]),

        # North-South Major Arterials
        ("Highway 6 (West Orbital Corridor)", [[-95.640, 29.580], [-95.635, 29.700], [-95.630, 29.784], [-95.640, 29.880], [-95.660, 29.980]]),
        ("Gessner Road", [[-95.540, 29.650], [-95.540, 29.730], [-95.545, 29.784], [-95.535, 29.850]]),
        ("Eldridge Parkway", [[-95.620, 29.670], [-95.620, 29.740], [-95.620, 29.784], [-95.615, 29.860]]),
        ("Shepherd & Durham Drive Corridor", [[-95.410, 29.720], [-95.410, 29.760], [-95.410, 29.820]]),
        ("Veterans Memorial Drive", [[-95.430, 29.880], [-95.435, 29.950], [-95.440, 30.010]]),
        ("Kuykendahl Road", [[-95.435, 29.980], [-95.460, 30.080], [-95.480, 30.170]]),
        ("Wayside Drive", [[-95.300, 29.670], [-95.300, 29.740], [-95.300, 29.810]]),
        ("Broadway Street (Pearland - Hobby)", [[-95.280, 29.550], [-95.280, 29.620], [-95.280, 29.660]]),
    ]

    for name, coords in arterials:
        features.append({
            'type': 'Feature',
            'geometry': {'type': 'LineString', 'coordinates': coords},
            'properties': {'name': name, 'type': 'arterial', 'tier': 2}
        })

    fc = {'type': 'FeatureCollection', 'features': features}
    raw = json.dumps(fc, separators=(',', ':'))
    open('web/mapdata/roads.geojson', 'w', encoding='utf-8').write(raw)
    print(f"COMPLETE: Built {len(features)} major regional highways & arteries covering Greater Houston in web/mapdata/roads.geojson ({len(raw)/1024:.1f} KB)")

if __name__ == '__main__':
    build_roads()
