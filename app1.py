
import streamlit as st
import pygame
import io
from utils import fetch_owid_latest, get_us_state_emissions

st.set_page_config(page_title="Global Emissions Explorer", layout="wide")
st.title("🌍 Global Emissions Explorer")
st.caption("Accurate country-level CO₂ data fetched from Our World in Data (OWID)")

# Controls
col1, col2, col3 = st.columns([2,1,1])
with col2:
    refresh = st.button("Refresh data")
with col3:
    view_mode = st.selectbox("Value to color", ["Total CO₂ (Mt)", "CO₂ per capita (t)"])

# Data
rows, meta = fetch_owid_latest(force_refresh=refresh)
# filter exclude None
if view_mode == "Total CO₂ (Mt)":
    vals = [r["co2"] for r in rows if r["co2"] is not None]
else:
    vals = [r["co2_per_capita"] for r in rows if r["co2_per_capita"] is not None]
vmin, vmax = (min(vals), max(vals)) if vals else (0,1)

rows_sorted = sorted(rows, key=lambda r: (
    (r["co2"] if view_mode=="Total CO₂ (Mt)" else r["co2_per_capita"]) is None,
    -((r["co2"] if view_mode=="Total CO₂ (Mt)" else r["co2_per_capita"]) or 0)
))

# Sidebar country search
with col1:
    q = st.text_input("Search country", "")
    if q:
        rows_filtered = [r for r in rows_sorted if q.lower() in r["country"].lower()]
    else:
        rows_filtered = rows_sorted
    country_names = [r["country"] for r in rows_filtered]
    selected_country = st.selectbox("Select a country", country_names, index=0 if country_names else None)

def color_from_value(v, vmin, vmax):
    if v is None or vmax<=vmin:
        return (100,100,100)
    t = max(0.0, min(1.0, (v - vmin) / (vmax - vmin)))
    r = int(70 + 185*t)
    g = int(40 + 0*t)
    b = int(40 + 0*t)
    return (r,g,b)

def render_panel(country_row):
    # Create a pygame surface and draw
    pygame.init()
    W, H = 1100, 480
    surf = pygame.Surface((W,H))
    surf.fill((24,28,36))
    font = pygame.font.SysFont("Arial", 22)
    small = pygame.font.SysFont("Arial", 18)

    if view_mode == "Total CO₂ (Mt)":
        val = country_row["co2"]
        unit = "Mt"
    else:
        val = country_row["co2_per_capita"]
        unit = "t per person"

    col = color_from_value(val, vmin, vmax)
    pygame.draw.rect(surf, col, (20, 20, 420, 300), border_radius=18)
    pygame.draw.rect(surf, (60,60,70), (20,20,420,300), 2, border_radius=18)

    title = f"{country_row['country']} (Year {country_row['year']})"
    surf.blit(font.render(title, True, (240,240,240)), (460, 30))
    valtxt = f"Value: {val:.2f} {unit}" if val is not None else "Value: n/a"
    surf.blit(small.render(valtxt, True, (230,230,230)), (460, 70))

    # If US, draw simple state bars as demo
    if country_row["country"].lower() in ("united states", "united states of america", "usa"):
        states = get_us_state_emissions()
        maxv = max(states.values()) if states else 1.0
        bx, by, bw, bh = 460, 120, 600, 260
        pygame.draw.rect(surf, (32,36,46), (bx, by, bw, bh), border_radius=12)
        barw = int(bw / max(1, len(states)))
        for idx, (st, s_val) in enumerate(sorted(states.items(), key=lambda kv: kv[1], reverse=True)):
            h = int((s_val / maxv) * (bh - 60))
            x = bx + idx*barw + 6
            y = by + bh - h - 24
            c = color_from_value(s_val, 0, maxv)
            pygame.draw.rect(surf, c, (x, y, barw-12, h), border_radius=6)
            lbl = st[:8]
            surf.blit(small.render(lbl, True, (230,230,230)), (x, by+bh-20))
        surf.blit(small.render("U.S. state demo (replace with official CSV via utils.py)", True, (200,200,200)), (bx, by-28))

# Encode surface as PNG bytes so Streamlit/PIL can read it
import io
buf = io.BytesIO()
try:
    # Pygame can save to file-like objects
    pygame.image.save(surf, buf)
    buf.seek(0)
    data = buf.read()
except TypeError:
    # Fallback: write to a temp file if your pygame build needs a filename
    import tempfile, os
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    tmp.close()
    pygame.image.save(surf, tmp.name)
    with open(tmp.name, "rb") as f:
        data = f.read()
    os.unlink(tmp.name)

pygame.quit()
return data, (W, H)
if country_names:
    row = next(r for r in rows_filtered if r["country"] == selected_country)
    img_bytes, (W,H) = render_panel(row)
    st.image(img_bytes, caption=f"Source: OWID (cached: {meta.get('cached_at','-')}) | Mode: {view_mode}", width=W)
else:
    st.info("No countries found.")

with st.expander("Data source details"):
    st.write("Our World in Data – CO₂ and Greenhouse Gas Emissions dataset. The app downloads the latest CSV directly and caches it locally.")
    st.code(meta, language="json")
