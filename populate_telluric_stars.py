#!/usr/bin/env python3
"""
Populate telluric_stars.yaml with coordinates extracted from the TeX document.
The coordinates are embedded in the airmass.org URLs in the LaTeX file.
"""

import yaml
import re
from pathlib import Path

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
    """Save data to YAML file."""
    with open(filepath, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

def main():
    script_dir = Path(__file__).parent
    yaml_path = script_dir / 'telluric_stars.yaml'
    tex_path = script_dir / 'hot star guidelines.tex'
    
    if not tex_path.exists():
        print(f"Error: {tex_path} not found")
        return
    
    # Extract stars from TeX
    print(f"Extracting stars from {tex_path}...")
    stars_from_tex = extract_stars_from_tex(tex_path)
    print(f"Found {len(stars_from_tex)} unique stars in TeX document")
    
    # Load existing data
    data = load_existing_yaml(yaml_path)
    
    # Merge stars (keep existing, add new)
    updated_count = 0
    added_count = 0
    
    for star_name, star_data in stars_from_tex.items():
        if star_name in data['stars']:
            print(f"✓ {star_name} already in database")
            updated_count += 1
        else:
            data['stars'][star_name] = star_data
            print(f"  + Added {star_name}: RA={star_data['ra']:.5f}°, Dec={star_data['dec']:.5f}°")
            added_count += 1
    
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
    
    # Save updated YAML
    save_yaml(yaml_path, data)
    print(f"\n✓ Saved {len(data['stars'])} total stars to {yaml_path}")
    print(f"  ({added_count} added, {updated_count} already existed)")

if __name__ == '__main__':
    main()
