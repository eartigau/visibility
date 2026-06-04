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
    '74PscB', '31Cas', 'gamTri', 'HR875', 'HR1314', 'pi.02Ori',
    'HR1832', 'zetLep', 'HR2180', 'HR2209', '24Lyn', 'HR3131',
    '33Lyn', 'etaPyx', '23LMi', 'lLeo', 'phiLeo', 'HR4687',
    'HR4722', 'zetVir', '82UMa', 'HD130917', 'betSer', 'HR6025',
    'HD159170', 'gamSct', '51Dra', 'iotCyg', 'omiCapA', 'chiCap',
    '17Peg', 'HR8489', '59Peg'
]

def query_simbad(star_name):
    """Query SIMBAD name resolver for star coordinates."""
    # Use the sim-id resolver which is more robust for abbreviated names
    url = f"https://simbad.cds.unistra.fr/simbad/sim-id"
    
    params = {
        'Ident': star_name,
        'output.format': 'votable',
        'obj.coo1': 'on'  # Request coordinates
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        # Parse the VOTable response for coordinates
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.content)
        
        # Find RA and DEC in the VOTable
        # Look for the TABLEDATA section
        ns = {'vot': 'http://www.ivoa.net/xml/VOTable/v1.3'}
        tabledata = root.find('.//vot:TABLEDATA', ns)
        
        if tabledata is None:
            # Try without namespace
            tabledata = root.find('.//TABLEDATA')
        
        if tabledata is not None:
            tr = tabledata.find('.//TR') or tabledata.find('.//{http://www.ivoa.net/xml/VOTable/v1.3}TR')
            if tr is not None:
                tds = list(tr.findall('TD')) or list(tr.findall('{http://www.ivoa.net/xml/VOTable/v1.3}TD'))
                # RA and DEC are typically in first two TD elements
                if len(tds) >= 2:
                    ra_text = tds[0].text
                    dec_text = tds[1].text
                    if ra_text and dec_text:
                        return {
                            'ra': float(ra_text),
                            'dec': float(dec_text),
                            'name': star_name
                        }
    except Exception as e:
        print(f"  Error querying {star_name}: {e}")
    
    return None

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

def main():
    script_dir = Path(__file__).parent
    yaml_path = script_dir / 'telluric_stars.yaml'
    tex_path = script_dir / 'hot star guidelines.tex'
    
    # Load existing data
    data = load_existing_yaml(yaml_path)
    
    # Extract stars from TeX if file exists
    if tex_path.exists():
        print(f"Extracting stars from {tex_path}...")
        stars_from_tex = extract_stars_from_tex(tex_path)
        print(f"Found {len(stars_from_tex)} unique stars in TeX document")
        
        for star_name, star_data in stars_from_tex.items():
            if star_name in data['stars']:
                print(f"✓ {star_name} already in database")
            else:
                data['stars'][star_name] = star_data
                print(f"  + Added {star_name}: RA={star_data['ra']:.5f}°, Dec={star_data['dec']:.5f}°")
    
    # Query SIMBAD for new stars
    print(f"\nQuerying SIMBAD for {len(NEW_STARS)} additional stars...")
    added_count = 0
    for star_name in NEW_STARS:
        if star_name in data['stars']:
            print(f"✓ {star_name} already in database")
            continue
        
        print(f"  Fetching {star_name} from SIMBAD...")
        star_data = query_simbad(star_name)
        
        if star_data:
            data['stars'][star_name] = star_data
            print(f"  ✓ Added {star_name}: RA={star_data['ra']:.5f}°, Dec={star_data['dec']:.5f}°")
            added_count += 1
        else:
            print(f"  ✗ Could not fetch {star_name}")
        
        # Be nice to SIMBAD servers
        time.sleep(0.5)
    
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
