
import csv, io, urllib.request, datetime, os, json

OWID_URL = "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "data")
CACHE_FILE = os.path.join(CACHE_DIR, "owid_co2_cache.csv")
META_FILE = os.path.join(CACHE_DIR, "owid_meta.json")

def _download(url: str, timeout: int = 30) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return resp.read()

def _read(path: str) -> bytes:
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    return b""

def _write(path: str, data: bytes):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)

def _write_meta(meta: dict):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

def fetch_owid_latest(force_refresh: bool = False):
    """
    Returns (rows, meta) where rows is latest-year per country:
    { iso_code, country, year, co2, population, co2_per_capita }
    """
    csv_bytes = b""
    if not force_refresh:
        csv_bytes = _read(CACHE_FILE)

    if not csv_bytes:
        try:
            csv_bytes = _download(OWID_URL, timeout=30)
            _write(CACHE_FILE, csv_bytes)
            _write_meta({"cached_at": datetime.datetime.utcnow().isoformat()+"Z", "source": OWID_URL})
        except Exception as e:
            # fall back to cache if download failed
            csv_bytes = _read(CACHE_FILE)
            if not csv_bytes:
                raise RuntimeError(f"Unable to fetch OWID data and no cache exists: {e}")

    text = csv_bytes.decode("utf-8")
    rdr = csv.DictReader(io.StringIO(text))

    # latest per-ISO3 country
    latest = {}
    for r in rdr:
        iso = r.get("iso_code","")
        if not iso or len(iso) != 3:  # ignore aggregates (World, Asia, etc.)
            continue
        try:
            year = int(r.get("year","") or 0)
        except:
            continue

        def fnum(x):
            try:
                return float(x)
            except:
                return None

        co2 = fnum(r.get("co2",""))
        pop = fnum(r.get("population",""))
        pcap = fnum(r.get("co2_per_capita",""))
        if co2 is None and pcap is None:
            continue

        prev = latest.get(iso)
        if prev is None or year > prev["year"]:
            latest[iso] = {
                "iso_code": iso,
                "country": r.get("country",""),
                "year": year,
                "co2": co2,
                "population": pop,
                "co2_per_capita": pcap
            }

    rows = list(latest.values())
    try:
        with open(META_FILE, "r", encoding="utf-8") as f:
            meta = json.load(f)
    except Exception:
        meta = {"source": OWID_URL, "cached_at": None}

    return rows, meta

# Subnational (demo): U.S. states — replace with official CSV for production
US_STATE_EMISSIONS = {
    "Texas": 690.0,
    "California": 320.0,
    "Florida": 230.0,
    "New York": 150.0,
    "Pennsylvania": 220.0,
    "Illinois": 190.0,
    "Ohio": 250.0
}

def get_us_state_emissions():
    return US_STATE_EMISSIONS.copy()
