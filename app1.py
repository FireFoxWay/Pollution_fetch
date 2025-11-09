
import streamlit as st
import pygame
import tempfile, os, io, json, math, urllib.request

# We reuse country list and CO2 data from utils (already in your folder)
from utils import fetch_owid_latest, get_us_state_emissions

st.set_page_config(page_title="Global Emissions Explorer", layout="wide")
st.title("🌍 Global Emissions Explorer (Streamlit + Pygame)")
st.caption("Select the metric you want (CO₂ totals, CO₂ per capita, or PM2.5 air pollution). Colors: green → yellow → red → dark red (danger). Uses only Streamlit + Pygame + stdlib.")

# ---------------- PM2.5 FETCH (World Bank API) ----------------
# Indicator: EN.ATM.PM25.MC.M3  (PM2.5 air pollution, population-weighted mean, µg/m³)
# API returns paginated JSON. We take the latest available value per ISO3 country.
WB_PM25_URL = "https://api.worldbank.org/v2/country/all/indicator/EN.ATM.PM25.MC.M3?format=json&per_page=20000"

@st.cache_data(show_spinner=True)
def fetch_pm25_latest():
    try:
        with urllib.request.urlopen(WB_PM25_URL, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {}, {"source": "World Bank API", "error": str(e)}

    # data[0] has paging/meta; data[1] has series list
    if not isinstance(data, list) or len(data) < 2 or not isinstance(data[1], list):
        return {}, {"source": "World Bank API", "error": "Unexpected API format"}

    latest = {}
    for item in data[1]:
        # item example keys: date (year), value, countryiso3code, country, etc.
        iso3 = item.get("countryiso3code")
        year_str = item.get("date")
        val = item.get("value")
        try:
            year = int(year_str) if year_str is not None else None
        except:
            year = None
        if not iso3 or year is None or val is None:
            continue
        prev = latest.get(iso3)
        if prev is None or year > prev["year"]:
            latest[iso3] = {"year": year, "pm25": float(val)}
    meta = {"source": "World Bank – EN.ATM.PM25.MC.M3", "cached": True}
    return latest, meta

# ---------------- Controls ----------------
c1, c2, c3 = st.columns([2,1,1])
with c2:
    refresh = st.button("Refresh CO₂ data")
with c3:
    metric = st.selectbox(
        "Metric",
        ["Total CO₂ (Mt)", "CO₂ per capita (t/person)", "PM₂.₅ (µg/m³)"],
        index=0
    )

# Add danger threshold slider
danger_top_percent = st.slider(
    "Danger threshold (top %)",
    min_value=50,
    max_value=99,
    value=90,
    help="Top emitters (or most-polluted for PM2.5) at/above this percentile turn dark red."
)
danger_cut = danger_top_percent / 100.0

# ---------------- Data ----------------
rows, co2_meta = fetch_owid_latest(force_refresh=refresh)

# PM2.5 only fetched/used if user selects it (saves API calls)
pm25_map, pm25_meta = ({}, {"source": None})
if metric == "PM₂.₅ (µg/m³)":
    pm25_map, pm25_meta = fetch_pm25_latest()

def metric_value(row):
    if metric == "Total CO₂ (Mt)":
        return row["co2"]
    elif metric == "CO₂ per capita (t/person)":
        return row["co2_per_capita"]
    else:  # PM2.5 by ISO3
        # OWID row has iso_code ISO3
        iso3 = row["iso_code"]
        entry = pm25_map.get(iso3)
        return entry["pm25"] if entry else None

def metric_year(row):
    if metric.startswith("CO₂"):
        return row["year"]
    else:
        iso3 = row["iso_code"]
        entry = pm25_map.get(iso3)
        return entry["year"] if entry else None

def metric_unit():
    if metric == "Total CO₂ (Mt)":
        return "Mt"
    elif metric == "CO₂ per capita (t/person)":
        return "t/person"
    else:
        return "µg/m³"

vals = [metric_value(r) for r in rows if metric_value(r) is not None]
vmin, vmax = (min(vals), max(vals)) if vals else (0.0, 1.0)

rows_sorted = sorted(rows, key=lambda r: (metric_value(r) is None, -(metric_value(r) or 0)))

# ---------------- Selection ----------------
with c1:
    q = st.text_input("Search country", "")
    if q:
        filtered = [r for r in rows_sorted if q.lower() in r["country"].lower()]
    else:
        filtered = rows_sorted
    options = [r["country"] for r in filtered]
    if not options:
        st.error("No matching country.")
        st.stop()
    selected = st.selectbox("Select a country", options, index=0)

# ---------------- Color logic ----------------
def lerp(a, b, t):
    return a + (b - a) * max(0.0, min(1.0, t))

def lerp_color(c1, c2, t):
    return (
        int(lerp(c1[0], c2[0], t)),
        int(lerp(c1[1], c2[1], t)),
        int(lerp(c1[2], c2[2], t)),
    )

def color_from_value(v, vmin, vmax):
    GREEN   = (50, 180, 75)
    YELLOW  = (235, 235, 40)
    RED     = (220, 40, 40)
    DARKRED = (110, 0, 0)

    if v is None or vmax <= vmin:
        return (120, 120, 120)

    t = (v - vmin) / (vmax - vmin)
    t = max(0.0, min(1.0, t))
    mid_cut = 0.60

    if t <= mid_cut:
        return lerp_color(GREEN, YELLOW, t / mid_cut)
    elif t < danger_cut:
        return lerp_color(YELLOW, RED, (t - mid_cut) / (danger_cut - mid_cut + 1e-9))
    else:
        return DARKRED

# ---------------- Render panel ----------------
def render_panel(country_row):
    pygame.init()
    W, H = 1100, 520
    surf = pygame.Surface((W, H))
    surf.fill((24,28,36))
    font = pygame.font.SysFont("Arial", 22)
    small = pygame.font.SysFont("Arial", 18)

    val = metric_value(country_row)
    year = metric_year(country_row)
    unit = metric_unit()
    col = color_from_value(val, vmin, vmax)

    pygame.draw.rect(surf, col, (20, 20, 420, 340), border_radius=18)
    pygame.draw.rect(surf, (60,60,70), (20,20,420,340), 2, border_radius=18)

    title = f"{country_row['country']} (Year {year if year is not None else 'n/a'})"
    surf.blit(font.render(title, True, (240,240,240)), (460, 30))
    if val is not None:
        valtxt = f"Value: {val:.2f} {unit}"
    else:
        valtxt = "Value: n/a"
    surf.blit(small.render(valtxt, True, (230,230,230)), (460, 70))

    # U.S. subnational demo still based on CO₂ (can be swapped later for PM2.5 if you have a state-level source)
    if country_row["country"].lower() in ("united states", "united states of america", "usa") and metric != "PM₂.₅ (µg/m³)":
        states = get_us_state_emissions()
        maxv = max(states.values()) if states else 1.0
        bx, by, bw, bh = 460, 120, 600, 320
        pygame.draw.rect(surf, (32,36,46), (bx, by, bw, bh), border_radius=12)
        barw = int(bw / max(1, len(states)))
        for idx, (stname, sval) in enumerate(sorted(states.items(), key=lambda kv: kv[1], reverse=True)):
            h = int((sval / maxv) * (bh - 60))
            x = bx + idx*barw + 6
            y = by + bh - h - 24
            c = color_from_value(sval, 0, maxv)
            pygame.draw.rect(surf, c, (x, y, barw-12, h), border_radius=6)
            lbl = stname[:8]
            surf.blit(small.render(lbl, True, (230,230,230)), (x, by+bh-20))
        surf.blit(small.render("U.S. state demo (replace with official CSV via utils.py)", True, (200,200,200)), (bx, by-28))

    # Encode surface to PNG bytes (robust across platforms)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    tmp_path = tmp.name
    tmp.close()
    pygame.image.save(surf, tmp_path)
    with open(tmp_path, "rb") as f:
        data = f.read()
    os.unlink(tmp_path)

    pygame.quit()
    return data, (W, H)

row = next(r for r in rows if r["country"] == selected)
png_bytes, (W, H) = render_panel(row)

# Compose a combined caption with data sources
src_bits = [f"CO₂ source: OWID (cached: {co2_meta.get('cached_at','-')})"]
if metric == "PM₂.₅ (µg/m³)":
    src_bits.append(pm25_meta.get("source","PM2.5 source: World Bank"))

st.image(png_bytes, caption=" | ".join(src_bits) + f" | Metric: {metric}", width=W)

with st.expander("Data source details"):
    st.write("CO₂ data: Our World in Data – CO₂ and Greenhouse Gas Emissions (CSV pulled live & cached).")
    if metric == "PM₂.₅ (µg/m³)":
        st.write("PM₂.₅ data: World Bank API, indicator EN.ATM.PM25.MC.M3 (population-weighted mean, µg/m³).")
    st.code({"co2_meta": co2_meta, "pm25_meta": pm25_meta}, language="json")

