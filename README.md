
# Global Emissions Explorer — v2 (Streamlit + Pygame)

- **Only** `streamlit` and `pygame` used (plus Python stdlib).
- **Accurate country data** pulled directly from **Our World in Data (OWID)** at runtime and cached under `data/`.
- Redder = higher emissions (choose *Total CO₂ (Mt)* or *Per-capita (t/person)*).
- U.S. state bars included as *demo*; replace with official subnational CSV in `utils.py` for production.

## Run
```bash
pip install streamlit pygame
streamlit run app1.py
```

## Data
- OWID CO₂ dataset CSV: https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv
  (See https://ourworldindata.org/co2-and-greenhouse-gas-emissions)
- Subnational demo: replace `get_us_state_emissions()` with official government CSV parsing.

## Notes
- We purposely avoid GIS libraries to honor the "Streamlit + Pygame only" requirement.
- The app uses a **PNG encoding** step so `st.image()` can display Pygame surfaces robustly.
