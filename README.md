# ✦ Constellation Finder & Visibility Planner

**A powerful, interactive astronomical observation planning tool** — visualize target visibility, airmass, barycentric velocity, and twilight windows for any observatory worldwide.

[![Live Demo](https://img.shields.io/badge/Live-Demo-blue?style=for-the-badge)](https://eartigau.github.io/constellation/)

## 🌟 Features

### 🎯 Star Lookup & Constellation Identification
- **SIMBAD Integration**: Query any star by name or coordinates
- **Flexible Input**: Decimal degrees (`101.287 −16.716`), sexagesimal (`06:44:59 −16:42:58`), or HMS/DMS format
- **IAU Boundaries**: Automatic constellation identification using official IAU/Roman (1987) boundaries
- **Smart Caching**: 30-day browser localStorage cache for instant repeat lookups

### 📊 Interactive Visualization

#### Year-Long Airmass Heatmap
- **365-day overview** with hourly resolution
- **Dual time axes**: Local time (left) and UTC (right)
- **Smart centering**: Plot centered on local midnight for optimal viewing
- **Twilight curves**: Astronomical, nautical, and civil twilight overlays
- **Daytime shading**: Visual distinction between night and day
- **Click-to-zoom**: Click any day to see detailed single-night plot

#### Single-Night Airmass Plot
- **High-resolution** airmass evolution from 3pm to 9am local time
- **Sorted time series**: Continuous curves spanning midnight boundary
- **Airmass range**: 1.0 (zenith) to 2.5 (horizon limit)
- **Current day marker**: Automatic highlighting of today's date

#### Barycentric Radial Velocity (BERV)
- **Annual BERV curve** for precise radial velocity work
- **Telluric zone**: ±4 km/s contamination window highlighted
- **Optimal timing**: Identify best observing epochs for RV precision

### 🔭 Telluric Star Recommendations

**Smart calibrator selection** for near-infrared spectroscopy (NIRPS, SPIRou):

- **Even/Odd Day Strategy**: 
  - Even days → Low airmass stars (1.0-1.8) — highlighted
  - Odd days → High airmass stars (1.8-2.5) — highlighted
- **30-minute cadence**: Full night coverage from sunset to sunrise
- **Dual recommendations**: High (near-zenith) and low (near-horizon) options
- **Sun altitude tracking**: Real-time solar elevation for twilight planning
- **DST-aware timing**: Automatic summer/winter time labels

### 🌍 Observatory Support

**11 pre-configured observatories** + custom location support:

| Observatory | Location | Elevation | Timezone |
|------------|----------|-----------|----------|
| **OMM** | Mont-Mégantic, QC | 1111 m | UTC-5 (DST: US) |
| **Mauna Kea** | Hawaii, USA | 4205 m | UTC-10 |
| **Gemini South** | Cerro Pachón, Chile | 2715 m | UTC-4 (DST: CL) |
| **VLT** | Paranal, Chile | 2635 m | UTC-4 (DST: CL) |
| **Las Campanas** | Chile | 2380 m | UTC-4 (DST: CL) |
| **La Silla** | Chile | 2400 m | UTC-4 (DST: CL) |
| **La Palma** | Canary Islands | 2396 m | UTC+0 (DST: EU) |
| **LBT** | Mt. Graham, Arizona | 3190 m | UTC-7 (DST: US) |
| **Kitt Peak** | Arizona, USA | 2096 m | UTC-7 |
| **SAAO** | Sutherland, South Africa | 1798 m | UTC+2 |
| **SSO** | Siding Spring, Australia | 1165 m | UTC+10 (DST: AU) |

**Custom Coordinates**: Enter any latitude/longitude for your location

### 🧭 Smart Location Detection

- **Automatic geolocation**: Browser-based position detection
- **Nearest observatory**: Automatically selects closest predefined site
- **Special rule**: Garching, Germany (ESO HQ) → defaults to La Silla
- **Haversine distance**: Accurate great-circle distance calculation

### ⏰ Intelligent DST Handling

**Automatic daylight saving time detection** based on observatory timezone:

- **United States**: 2nd Sunday March → 1st Sunday November
- **European Union**: Last Sunday March → Last Sunday October  
- **Chile**: 1st Saturday September → 1st Saturday April (Southern Hemisphere)
- **Australia**: 1st Sunday October → 1st Sunday April (Southern Hemisphere)
- **Auto-toggle**: DST checkbox updates automatically when switching observatories
- **Dynamic labels**: "Local time (summer)" appears when DST active

### 🌐 Bilingual Interface

**Full English/French support**:
- 🇬🇧 **English**: Visibility Planner
- 🇫🇷 **Français**: Planificateur d'observabilité
- Language preference saved in browser

## 🚀 Quick Start

### Online (Recommended)
Visit **[https://eartigau.github.io/constellation/](https://eartigau.github.io/constellation/)**

### Local Development
```bash
git clone https://github.com/eartigau/constellation.git
cd constellation
python3 -m http.server 8000
```
Open `http://localhost:8000` in your browser

## 📖 Usage Guide

### 1. Select Observatory
Click any preset observatory button **OR** use geolocation detection **OR** enter custom coordinates

### 2. Look Up Your Target
**Option A**: Click a quick-select star (Sirius, Vega, etc.)  
**Option B**: Enter star name: `Proxima Centauri`  
**Option C**: Enter coordinates: `14:29:42.95 -62:40:46.1`  
**Option D**: Enter decimal degrees: `217.42896 -62.67947`

### 3. Analyze Visibility
- **Year plot**: Scroll to find optimal observing months
- **Click any day**: See detailed airmass evolution
- **BERV plot**: Check for telluric contamination windows
- **Telluric table**: Select calibrator stars for your night

### 4. Plan Your Observations
Use the telluric recommendations table:
- **Even nights**: Focus on low-airmass stars (better SNR)
- **Odd nights**: Include high-airmass stars (atmospheric gradient)
- Check sun altitude to plan twilight observations

## 🛠️ Technical Details

### Architecture
- **Single-file application**: All HTML/CSS/JavaScript/Python in `index.html`
- **PyScript 2025.3.1**: Python runtime in browser via Pyodide
- **Plotly.js 2.35.2**: Interactive plotting library
- **Pure Python astronomy**: No NumPy/SciPy — works in any modern browser

### Astronomical Calculations
- **Coordinate systems**: ICRS J2000 → Ecliptic → Observer Alt/Az
- **Airmass formula**: Plane-parallel atmosphere model with sec(z) approximation
- **BERV**: Earth's orbital velocity projection onto line of sight
- **Twilight**: Solar altitude thresholds (−18°, −12°, −6° for astronomical/nautical/civil)
- **Time resolution**: 10-minute intervals for airmass (144/day), 1-minute for twilight (1440/day)

### Data Sources
- **SIMBAD TAP**: [CDS Strasbourg](https://simbad.cds.unistra.fr/)
- **Constellation boundaries**: IAU Roman (1987) / Delporte (1930)
- **Telluric stars**: Curated B/A-type calibrator catalog for NIRPS

### Browser Compatibility
- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ⚠️ Requires JavaScript and localStorage enabled

## 📦 Offline Capability

**Smart caching system**:
- SIMBAD results cached for **30 days** in browser localStorage
- Telluric stars **hardcoded** (no network required)
- Works offline for previously searched targets
- Cache key format: `constellation_cache_v1_[starname]`

## 🌠 Telluric Star Catalog

Current catalog includes **15 B/A-type stars** optimized for southern observatories:

`HR875`, `HR1903`, `HR3117`, `HR3131`, `HR3314`, `HR4023`, `HR4467`, `HR5107`, `HR5671`, `HR6743`, `HR7590`, `HR7830`, `HR8709`, `HR9098`, `HR806`

*Note: Additional stars (74PscB, 31Cas, gamTri, etc.) are staged for future inclusion*

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional telluric calibrator stars
- More observatory presets
- Alternative airmass models (Hardie, Kasten-Young)
- Moon visibility calculations
- Export functionality (iCal, JSON)

## 📄 License

MIT License — see [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- **CDS SIMBAD**: Astronomical database queries
- **IAU**: Official constellation boundaries
- **PyScript Team**: Python-in-browser runtime
- **Plotly**: Interactive visualization library
- **NIRPS/SPIRou Teams**: Telluric observing strategy

## 📧 Contact

Questions? Issues? Open a [GitHub Issue](https://github.com/eartigau/constellation/issues)

---

**Made with ✦ for astronomers, by astronomers**
