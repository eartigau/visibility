#!/usr/bin/env python3
"""
Populate telluric_stars.yaml with coordinates from SIMBAD or TeX file.
Sorts stars by RA in the output YAML.
"""

import yaml
import re
import requests
import time
from pathlib import Path

# New stars to add via SIMBAD
NEW_STARS = [
    '74 Psc B', '31 Cas', 'gam Tri', 'HR 875', 'HR 1314', 'pi.02Ori',
    'HR 1832', 'zet Lep', 'HR 2180', 'HR 2209', '24 Lyn', 'HR 3131',
    '33 Lyn', 'eta Pyx', '23 LMi', 'l Leo', 'phi Leo', 'HR 4687',
    'HR 4722', 'zet Vir', '82 UMa', 'HD 130917', 'bet Ser', 'HR6025',
    'HD 159170', 'gam Sct', '51 Dra', 'iot Cyg', 'omi Cap A', 'chi Cap',
    '17 Peg', 'HR 8489', '59 Peg'
]

MIN_DEC_DEG = 40.0
SIMBAD_TAP_URL = 'https://simbad.cds.unistra.fr/simbad/sim-tap/sync'


def normalize_star_name(name):
    """Normalize a star name for duplicate matching across naming variants."""
    return re.sub(r'[^a-z0-9]', '', name.lower())


def _tap_query(adql, timeout=20):
    """Execute an ADQL query against SIMBAD TAP and return rows."""
    params = {
        'request': 'doQuery',
        'lang': 'adql',
        'format': 'json',
        'query': adql
    }
    response = requests.get(SIMBAD_TAP_URL, params=params, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    return payload.get('data', [])


def _sanitize_mag(value, max_mag=10.0):
    """Return magnitude if plausible for bright telluric calibrators."""
    if value is None:
        return None
    try:
        mag = float(value)
    except (TypeError, ValueError):
        return None
    if -2.0 <= mag <= max_mag:
        return mag
    return None


def _star_name_variants(name):
    """Build likely SIMBAD identifier variants for robust matching."""
    variants = [name]
    compact = re.sub(r'\s+', '', name)
    if compact not in variants:
        variants.append(compact)

    # HR1314 -> HR 1314
    m_hr = re.match(r'(?i)^hr\s*(\d+)$', compact)
    if m_hr:
        variants.append(f"HR {m_hr.group(1)}")

    # 82UMa -> 82 UMa
    m_num_letters = re.match(r'^(\d+)([A-Za-z].*)$', compact)
    if m_num_letters:
        variants.append(f"{m_num_letters.group(1)} {m_num_letters.group(2)}")

    deduped = []
    seen = set()
    for v in variants:
        key = v.lower()
        if key not in seen:
            deduped.append(v)
            seen.add(key)
    return deduped


def query_simbad(star_name):
    """Query SIMBAD TAP resolver for coordinates and G/H magnitudes."""
    for variant in _star_name_variants(star_name):
        safe_name = variant.replace("'", "''")
        adql = f"""
        SELECT TOP 1 b.main_id, b.ra, b.dec, f.G, f.H
        FROM basic AS b
        JOIN ident AS i ON i.oidref = b.oid
        LEFT JOIN allfluxes AS f ON f.oidref = b.oid
        WHERE i.id = '{safe_name}'
        """

        try:
            rows = _tap_query(adql)
            if rows:
                row = rows[0]
                return {
                    'ra': float(row[1]),
                    'dec': float(row[2]),
                    'name': variant,
                    'g_mag': _sanitize_mag(row[3]),
                    'h_mag': _sanitize_mag(row[4])
                }
        except Exception as e:
            print(f"  Error querying {star_name}: {e}")

    return None


def query_magnitudes_by_name(star_name):
    """Fetch G/H magnitudes by SIMBAD identifier."""
    for variant in _star_name_variants(star_name):
        safe_name = variant.replace("'", "''")
        adql = f"""
        SELECT TOP 1 f.G, f.H
        FROM basic AS b
        JOIN ident AS i ON i.oidref = b.oid
        LEFT JOIN allfluxes AS f ON f.oidref = b.oid
        WHERE i.id = '{safe_name}'
        """
        try:
            rows = _tap_query(adql)
            if rows:
                row = rows[0]
                return {
                    'g_mag': _sanitize_mag(row[0]),
                    'h_mag': _sanitize_mag(row[1])
                }
        except Exception:
            continue

    return {'g_mag': None, 'h_mag': None}


def query_magnitudes_by_position(ra_deg, dec_deg, radius_deg=0.001):
    """Fetch G/H magnitudes by nearest SIMBAD object at sky position."""
    adql = f"""
    SELECT TOP 1 b.main_id, f.G, f.H
    FROM basic AS b
    LEFT JOIN allfluxes AS f ON f.oidref = b.oid
    WHERE 1 = CONTAINS(
        POINT('ICRS', b.ra, b.dec),
        CIRCLE('ICRS', {ra_deg:.8f}, {dec_deg:.8f}, {radius_deg:.5f})
    )
    ORDER BY DISTANCE(POINT('ICRS', b.ra, b.dec), POINT('ICRS', {ra_deg:.8f}, {dec_deg:.8f})) ASC
    """

    try:
        rows = _tap_query(adql)
        if rows:
            row = rows[0]
            return {
                'g_mag': _sanitize_mag(row[1]),
                'h_mag': _sanitize_mag(row[2])
            }
    except Exception:
        pass

    return {'g_mag': None, 'h_mag': None}

def extract_stars_from_tex(tex_path):
    """Extract star names and coordinates from the TeX file."""
    stars = {}
    
    with open(tex_path, 'r') as f:
        content = f.read()
    
    # Pattern to match: object:STARNAME/ra:RADEG/dec:DECDEG
    pattern = r'object:([^/]+)/ra:([\d.]+)/dec:([-\d.]+)'
    
    matches = re.findall(pattern, content)
    
    for star_name, ra, dec in matches:
        # Only add each star once (first occurrence)
        if star_name not in stars:
            stars[star_name] = {
                'ra': float(ra),
                'dec': float(dec),
                'name': star_name
            }
    
    return stars


def load_manual_coords(filepath):
    """Load fallback coordinates from a simple text file."""
    manual = {}
    if not filepath.exists():
        return manual

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split()
            if len(parts) != 3:
                continue

            name, ra, dec = parts
            try:
                star_data = {
                    'ra': float(ra),
                    'dec': float(dec),
                    'name': name,
                    'g_mag': None,
                    'h_mag': None
                }
                manual[normalize_star_name(name)] = star_data
            except ValueError:
                continue

    return manual

def load_existing_yaml(filepath):
    """Load existing YAML file."""
    if filepath.exists():
        with open(filepath, 'r') as f:
            return yaml.safe_load(f)
    return {'stars': {}, 'guidelines': {}}

def save_yaml(filepath, data):
    """Save data to YAML file with stars sorted by RA."""
    # Sort stars by RA
    if 'stars' in data:
        sorted_stars = dict(sorted(data['stars'].items(), key=lambda item: item[1]['ra']))
        data['stars'] = sorted_stars
    
    with open(filepath, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def enrich_star_magnitudes(data):
    """Backfill g_mag/h_mag for all stars without removing existing data."""
    updated = 0
    for star_name, star in data.get('stars', {}).items():
        # Clear previously stored implausible values before recomputing.
        if _sanitize_mag(star.get('g_mag')) is None and star.get('g_mag') is not None:
            star['g_mag'] = None
            updated += 1
        if _sanitize_mag(star.get('h_mag')) is None and star.get('h_mag') is not None:
            star['h_mag'] = None
            updated += 1

        name_candidates = [star_name]
        if star.get('name') and star['name'] != star_name:
            name_candidates.append(star['name'])

        best_g_mag = None
        best_h_mag = None
        for cand in name_candidates:
            mags_by_name = query_magnitudes_by_name(cand)
            if mags_by_name.get('g_mag') is not None:
                best_g_mag = mags_by_name['g_mag']
            if mags_by_name.get('h_mag') is not None:
                best_h_mag = mags_by_name['h_mag']
            if best_g_mag is not None and best_h_mag is not None:
                break

        if best_g_mag is None or best_h_mag is None:
            mags_by_pos = query_magnitudes_by_position(star['ra'], star['dec'])
            if best_g_mag is None:
                best_g_mag = mags_by_pos.get('g_mag')
            if best_h_mag is None:
                best_h_mag = mags_by_pos.get('h_mag')

        if best_g_mag is not None and star.get('g_mag') != best_g_mag:
            star['g_mag'] = best_g_mag
            updated += 1
        if best_h_mag is not None and star.get('h_mag') != best_h_mag:
            star['h_mag'] = best_h_mag
            updated += 1

    return updated

def main():
    script_dir = Path(__file__).parent
    yaml_path = script_dir / 'telluric_stars.yaml'
    tex_path = script_dir / 'hot star guidelines.tex'
    manual_coords_path = script_dir / 'new_stars_coords.txt'
    
    # Load existing data
    data = load_existing_yaml(yaml_path)
    existing_norm_names = {normalize_star_name(name) for name in data.get('stars', {})}
    manual_coords = load_manual_coords(manual_coords_path)
    
    # Extract stars from TeX if file exists
    if tex_path.exists():
        print(f"Extracting stars from {tex_path}...")
        stars_from_tex = extract_stars_from_tex(tex_path)
        print(f"Found {len(stars_from_tex)} unique stars in TeX document")
        
        for star_name, star_data in stars_from_tex.items():
            if star_name in data['stars']:
                print(f"✓ {star_name} already in database")
            else:
                if star_data['dec'] >= MIN_DEC_DEG:
                    data['stars'][star_name] = star_data
                    print(f"  + Added {star_name}: RA={star_data['ra']:.5f}°, Dec={star_data['dec']:.5f}°")
                else:
                    print(f"  - Skipped {star_name}: Dec={star_data['dec']:.5f}° is south of +{MIN_DEC_DEG:.0f}°")
    
    # Query SIMBAD for new stars
    print(f"\nQuerying SIMBAD for {len(NEW_STARS)} additional stars...")
    added_count = 0
    for star_name in NEW_STARS:
        normalized_name = normalize_star_name(star_name)
        if star_name in data['stars'] or normalized_name in existing_norm_names:
            print(f"✓ {star_name} already in database")
            continue
        
        print(f"  Fetching {star_name} from SIMBAD...")
        star_data = query_simbad(star_name)
        
        if not star_data and normalized_name in manual_coords:
            star_data = manual_coords[normalized_name]
            print(f"  ~ Using fallback coordinates for {star_name} from {manual_coords_path.name}")

        if star_data:
            if star_data['dec'] >= MIN_DEC_DEG:
                output_name = star_data.get('name', star_name)
                data['stars'][output_name] = {
                    'ra': star_data['ra'],
                    'dec': star_data['dec'],
                    'name': output_name,
                    'g_mag': star_data.get('g_mag'),
                    'h_mag': star_data.get('h_mag')
                }
                existing_norm_names.add(normalized_name)
                print(f"  ✓ Added {output_name}: RA={star_data['ra']:.5f}°, Dec={star_data['dec']:.5f}°")
                added_count += 1
            else:
                print(f"  - Skipped {star_name}: Dec={star_data['dec']:.5f}° is south of +{MIN_DEC_DEG:.0f}°")
        else:
            print(f"  ✗ Could not fetch {star_name}")
        
        # Be nice to SIMBAD servers
        time.sleep(0.5)

    # Add missing magnitude fields for all stars
    print("\nEnriching star magnitudes (Gaia G, 2MASS H)...")
    mag_updates = enrich_star_magnitudes(data)
    print(f"  Updated {mag_updates} magnitude fields")
    
    # Ensure guidelines section exists
    if 'guidelines' not in data:
        data['guidelines'] = {
            'purpose': 'Telluric stars should be observed in evening twilight to gather a library of featureless spectra with only telluric absorption imprint.',
            'timing': [
                'Observe either in evening OR morning twilight (not both)',
                'As long as the Sun is below the horizon, sky is dark enough'
            ],
            'airmass_strategy': {
                'even_days': 'Observe LOW airmass target (closer to zenith)',
                'odd_days': 'Observe HIGH airmass target (1.8-2.5 airmass)',
                'note': 'Check day of month at beginning of night'
            },
            'modes': [
                'Observe in both HA and HE modes',
                'At least one HA observation per week required'
            ],
            'flexibility': [
                'Missing one night is fine - we want ~1 per night on average',
                'Do NOT add random hot stars - use only listed targets',
                'Any star from the list can be observed on any night',
                'If only one fiber available, prioritize HE but keep HA quota'
            ]
        }
    
    # Save updated YAML (sorted by RA)
    save_yaml(yaml_path, data)
    print(f"\n✓ Saved {len(data['stars'])} total stars to {yaml_path} (sorted by RA)")
    print(f"  ({added_count} new stars added)")

if __name__ == '__main__':
    main()
