# 🌍 Global Emissions Explorer (v2.5)

An interactive **Streamlit + Pygame** dashboard that visualizes **global environmental metrics** — including  
✅ Total CO₂ emissions  
✅ CO₂ emissions per capita  
✅ PM₂.₅ air pollution (population-weighted mean, µg/m³)

Color intensity represents the pollution severity:
🟢 *Good* → 🟡 *Moderate* → 🔴 *High* → 🔴🩸 *Dangerous*  

---

## 🚀 Features

### 🌐 Multiple Environmental Metrics
- **Total CO₂ (Mt)** — total carbon emissions by country *(Our World in Data)*  
- **CO₂ per capita (t/person)** — average carbon output per person *(Our World in Data)*  
- **PM₂.₅ (µg/m³)** — air pollution concentration *(World Bank API)*

### 🎨 Intuitive Color Scale
- **Green → Yellow → Red → Dark Red** shows increasing pollution severity.  
- Adjust the **“Danger threshold (top %)”** slider to decide what percentile of countries are flagged as *dangerous*.

### 📈 Real Data, Real Sources
- **CO₂ data:** [Our World in Data – CO₂ and Greenhouse Gas Emissions](https://ourworldindata.org/co2-and-greenhouse-gas-emissions)  
- **PM₂.₅ data:** [World Bank – Indicator EN.ATM.PM25.MC.M3](https://data.worldbank.org/indicator/EN.ATM.PM25.MC.M3)

### 🗺️ Country-level Focus
- Select any country to view its latest emission or pollution stats.
- U.S. includes an example **state-level bar chart** (editable in `utils.py`).

---

## 🧠 How It Works

| Component | Function |
|------------|-----------|
| **Streamlit** | UI, dropdowns, and chart rendering |
| **Pygame** | Draws colored panels and bar charts |
| **utils.py** | Downloads & caches OWID CO₂ data |
| **World Bank API** | Provides latest PM₂.₅ pollution values |

---

## 🧩 Installation

```bash
pip install streamlit pygame
```

Then run:

```bash
streamlit run app1.py
```

Open your browser at:
```
http://localhost:8501
```

---

## ⚙️ Controls

| Control | Description |
|----------|-------------|
| **Metric dropdown** | Choose “Total CO₂”, “CO₂ per capita”, or “PM₂.₅” |
| **Danger threshold (top %)** | Defines where dark-red danger starts (e.g., 90 % = top 10 % emitters) |
| **Search country** | Quickly find a specific country |

---

## 🧾 Data Refresh & Caching

- CO₂ data downloads once and is cached in the `data/` folder.  
- PM₂.₅ data is fetched live from the World Bank API and cached automatically by Streamlit.

---

## 🧩 Customization

- Update `get_us_state_emissions()` in `utils.py` with real U.S. or sub-national data.
- To use other pollutants (e.g., CH₄, NOₓ, O₃), add new indicators from the World Bank or WHO in the same format.

---

## ⚠️ Notes & Limitations

- Colors represent **relative severity** (percentile-based), not fixed health thresholds.  
- Actual health guidelines for PM₂.₅ (WHO):  
  - ≤ 5 µg/m³ — *Good*  
  - 5–10 µg/m³ — *Moderate*  
  - > 35 µg/m³ — *Unhealthy / Dangerous*  

---

## 📜 License

- **Code:** MIT License  
- **Data:** governed by respective data source licenses (OWID & World Bank).
