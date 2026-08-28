"""
MTH5000 - Step 0: get the data.

Three jobs, in the order you will need them:

  1. Find the candidate monitoring stations and see how far back each one goes,
     before downloading anything.

        python step00_fetch_openaq.py --find

  2. Download one station's daily PM2.5 series from the OpenAQ v3 API.

        python step00_fetch_openaq.py --location-id 8118 --from 2016-01-01 \
               --out data/delhi.csv

  3. If the API will not serve the full history, fall back to the public S3
     archive, which is complete and needs no AWS account.

        python step00_fetch_openaq.py --location-id 8118 --archive \
               --from 2016-01-01 --out data/delhi.csv

Set your key once, and never put it in a file you commit:

    export OPENAQ_KEY="..."

WHAT THIS SCRIPT DECIDES FOR YOU, AND WHY

A daily mean computed from four hourly readings is not the same quantity as a
daily mean computed from twenty-four, and treating them as the same silently
adds noise that looks like real variation. The API tells you how complete each
day is, so this script uses that: days below --min-coverage (default 75 percent)
are written as NaN in the PM2.5 column and kept in PM2.5_raw so you can test
whether the rule changed your conclusions. Downstream, missing is missing, which
is what step 1 and step 2 already expect.

Dates come from the LOCAL day boundary, not UTC. Delhi is UTC+5:30, so using the
UTC date would slice each local day across two calendar days and smear the
diurnal cycle into the daily series. This matters more than it sounds.

WHAT IS VERIFIED AND WHAT IS NOT

The endpoints, parameter ids and response field names come from the OpenAQ
OpenAPI specification, and the S3 listing was confirmed to work anonymously.
None of it has been run against the live API with a real key, because I do not
have one. If a field name is wrong on your first run, use --raw to dump the
response and the fix will be one line. The parsing is covered by --test against
fixtures built from the documented schema.
"""

import argparse
import csv
import gzip
import io
import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta

API = "https://api.openaq.org/v3"
ARCHIVE_HOST = "https://openaq-data-archive.s3.amazonaws.com"
PM25_PARAMETER_ID = 2

# Connaught Place, central Delhi. 25000 m is the maximum radius the API allows.
DEFAULT_LAT, DEFAULT_LON = 28.6139, 77.2090
DEFAULT_RADIUS = 25000

# Rate limits are 60 per minute and 2000 per hour. One second between requests
# keeps you comfortably inside both. Repeatedly exceeding them can get a key
# banned, and there is no hurry here: a full history is a few dozen requests.
SLEEP_BETWEEN_REQUESTS = 1.05


# ----------------------------------------------------------------------------
# HTTP
# ----------------------------------------------------------------------------

def get_key(cli_key=None):
    key = cli_key or os.environ.get("OPENAQ_KEY")
    if not key:
        sys.exit(
            "No API key. Register free at https://explore.openaq.org/register, "
            "then:\n    export OPENAQ_KEY=\"your-key\"\n"
            "or pass --key. Do not paste it into a file you commit."
        )
    return key.strip()


def api_get(path, key, params=None, raw=False, _attempt=1):
    """One GET against the v3 API, with polite backoff on 429."""
    import requests

    url = f"{API}{path}"
    resp = requests.get(url, headers={"X-API-Key": key}, params=params or {}, timeout=60)

    if resp.status_code == 401:
        sys.exit("401 from OpenAQ. The key is missing, wrong, or not yet active.")
    if resp.status_code == 404:
        sys.exit(f"404 from OpenAQ for {url}. Check the id you passed.")
    if resp.status_code == 429:
        if _attempt > 5:
            sys.exit("Rate limited five times in a row. Stop and try again later.")
        wait = int(resp.headers.get("Retry-After", 0)) or 15 * _attempt
        print(f"  rate limited, waiting {wait}s")
        time.sleep(wait)
        return api_get(path, key, params, raw, _attempt + 1)
    if resp.status_code >= 400:
        sys.exit(f"HTTP {resp.status_code} from {url}\n{resp.text[:400]}")

    body = resp.json()
    if raw:
        print(json.dumps(body, indent=2)[:4000])
    return body


def paginate(path, key, params, limit=1000, max_pages=200, label="", quiet=False):
    """Walk pages until the API stops giving full ones."""
    out, page = [], 1
    while page <= max_pages:
        p = dict(params, limit=limit, page=page)
        body = api_get(path, key, p)
        results = body.get("results") or []
        out.extend(results)
        found = (body.get("meta") or {}).get("found")
        if not quiet:
            print(f"  {label} page {page}: {len(results)} rows (total {len(out)})")
        if len(results) < limit:
            break
        # "found" can be a string like ">1000", so only trust it when numeric.
        if isinstance(found, int) and len(out) >= found:
            break
        page += 1
        time.sleep(SLEEP_BETWEEN_REQUESTS)
    return out


# ----------------------------------------------------------------------------
# Finding a station
# ----------------------------------------------------------------------------

def _dt(obj, which):
    """Pull a date string out of a DatetimeObject, preferring local time."""
    d = (obj or {}).get(which) or {}
    s = d.get("local") or d.get("utc") or ""
    return s[:10]


def pm25_sensors(location):
    out = []
    for s in location.get("sensors") or []:
        param = s.get("parameter") or {}
        if param.get("id") == PM25_PARAMETER_ID or param.get("name") == "pm25":
            out.append(s)
    return out


def find_stations(key, lat, lon, radius, limit=100):
    """Rank nearby PM2.5 stations by how much history they hold."""
    body = api_get("/locations", key, {
        "coordinates": f"{lat},{lon}",
        "radius": radius,
        "parameters_id": PM25_PARAMETER_ID,
        "limit": limit,
    })
    rows = []
    for loc in body.get("results") or []:
        sens = pm25_sensors(loc)
        if not sens:
            continue
        first, last = _dt(loc, "datetimeFirst"), _dt(loc, "datetimeLast")
        try:
            years = (date.fromisoformat(last) - date.fromisoformat(first)).days / 365.25
        except ValueError:
            years = 0.0
        rows.append({
            "location_id": loc.get("id"),
            "name": loc.get("name") or "",
            "locality": (loc.get("locality") or ""),
            "first": first, "last": last, "years": years,
            "sensor_id": sens[0].get("id"),
            "provider": ((loc.get("provider") or {}).get("name") or ""),
        })
    rows.sort(key=lambda r: r["years"], reverse=True)
    return rows


def report_stations(rows, min_years=4.0):
    if not rows:
        print("\nNo PM2.5 stations returned. Widen the radius, move the centre "
              "point, or check the key.")
        return
    print("\n" + "=" * 96)
    print("PM2.5 STATIONS, LONGEST RECORD FIRST")
    print("=" * 96)
    print(f"{'loc_id':>7}  {'sensor':>7}  {'first':10}  {'last':10}  {'yrs':>5}  "
          f"{'provider':16}  name")
    print("-" * 96)
    for r in rows[:25]:
        flag = " " if r["years"] >= min_years else "."
        print(f"{r['location_id']:>7}  {r['sensor_id']:>7}  {r['first']:10}  "
              f"{r['last']:10}  {r['years']:5.1f}{flag} {r['provider'][:16]:16}  "
              f"{r['name'][:40]}")
    print("-" * 96)
    print(f"  Rows marked . hold under {min_years:.0f} years and will estimate the "
          "annual cycle poorly.")

    today = date.today()
    live = [r for r in rows if r["last"] and
            (today - date.fromisoformat(r["last"])).days <= 30]
    good = [r for r in live if r["years"] >= min_years]

    print(f"\n  {len(rows)} stations, {len(live)} still reporting in the last 30 days, "
          f"{len(good)} of those with {min_years:.0f}+ years.")
    if good:
        top = good[0]
        print(f"\n  Best candidate: location {top['location_id']}, "
              f"{top['years']:.1f} years, {top['name'][:50]}")
        print("\n  Next:")
        print(f"    python step00_fetch_openaq.py --location-id {top['location_id']} "
              f"--from {top['first']} --out data/delhi.csv")
        print("\n  Pull the top two or three and compare coverage before committing.")
    else:
        print("\n  Nothing both long and current. Try a second centre point, or use "
              "the Kaggle prototype series while you keep looking.")


# ----------------------------------------------------------------------------
# Daily series from the API
# ----------------------------------------------------------------------------

def sensor_for_location(key, location_id):
    body = api_get(f"/locations/{location_id}/sensors", key, {"limit": 100})
    for s in body.get("results") or []:
        param = s.get("parameter") or {}
        if param.get("id") == PM25_PARAMETER_ID or param.get("name") == "pm25":
            return s.get("id"), (param.get("units") or "")
    sys.exit(f"Location {location_id} exposes no PM2.5 sensor.")


def parse_daily(results, min_coverage=75.0):
    """Turn DailyData records into rows keyed by local date.

    Kept separate from the HTTP so it can be tested without a key. The shape
    comes from the OpenAPI spec: value, summary.avg, period.datetimeFrom.local,
    coverage.percentComplete.
    """
    rows = {}
    for r in results:
        period = r.get("period") or {}
        day = _dt(period, "datetimeFrom") or _dt({"x": period.get("datetimeFrom")}, "x")
        if not day:
            continue

        value = r.get("value")
        if value is None:
            value = (r.get("summary") or {}).get("avg")

        cov = r.get("coverage") or {}
        pct = cov.get("percentComplete")
        if pct is None:
            exp, obs = cov.get("expectedCount"), cov.get("observedCount")
            pct = 100.0 * obs / exp if exp else None

        # A repeated day means the API returned overlapping pages. Prefer the
        # better covered record rather than whichever arrived last.
        prev = rows.get(day)
        if prev and (prev["api_pct"] or 0) >= (pct or 0):
            continue

        rows[day] = {
            "date": day,
            "PM2.5": value,
            "PM2.5_raw": value,
            "api_pct": pct,
            "n_obs": cov.get("observedCount"),
        }

    out = [rows[k] for k in sorted(rows)]
    return apply_coverage(out, min_coverage)


def apply_coverage(rows, min_coverage):
    """Blank out days that are not really full days.

    The API reports percentComplete against an expectedCount of 24, assuming
    hourly reporting. Sensors that report more often than that, and the New
    Delhi sensor reports half-hourly for most of its record, produce
    percentComplete above 100, which is the visible tell that the denominator
    is wrong. The invisible and far more damaging consequence is that a day
    holding 24 of a real 48 readings scores as fully complete, so a mean built
    from half a day of a polluted afternoon enters the series as a daily mean.
    Those are precisely the days that produce physically impossible values.

    So the cadence is taken from the data instead. Within each year, the 90th
    percentile of observation counts is a robust estimate of a full day, and it
    follows a change in reporting interval automatically rather than needing to
    be told. Coverage is then observations divided by that.
    """
    cadence = detect_cadence(rows)
    for r in rows:
        cad = cadence.get(r["date"][:4], 24) or 24
        n = r.get("n_obs")
        r["cadence"] = cad
        r["pct_complete"] = round(100.0 * n / cad, 1) if n is not None else None
        if r["PM2.5"] is None:
            continue
        if r["pct_complete"] is not None and r["pct_complete"] < min_coverage:
            r["PM2.5"] = None
    return rows


def detect_cadence(rows):
    """Readings in a full day, per year, taken from the data itself."""
    by_year = {}
    for r in rows:
        n = r.get("n_obs")
        if n:
            by_year.setdefault(r["date"][:4], []).append(n)
    out = {}
    for y, counts in by_year.items():
        counts.sort()
        out[y] = counts[int(0.9 * (len(counts) - 1))]
    return out


def fetch_daily(key, sensor_id, date_from, date_to, min_coverage, raw=False, quiet=False):
    """Download the daily series one calendar year at a time.

    Why year by year rather than one long paginated request. Pagination stops
    when a page comes back shorter than the page size, which is the normal
    signal for "that was the last page". But if the API ever returns a short
    page mid-range, for example across a stretch where the station reported
    nothing, that signal fires early and the download stops silently, leaving
    you with a truncated series and no error to notice. Requesting one year at
    a time bounds the damage: a year is at most 366 rows, each year is checked
    independently, and a year that comes back empty is reported rather than
    ending the loop. The cost is about twenty requests instead of four, which
    against a limit of sixty a minute is nothing.
    """
    if not quiet:
        print(f"\nPulling daily values for sensor {sensor_id}, {date_from} to {date_to}")
    if raw:
        api_get(f"/sensors/{sensor_id}/days", key,
                {"date_from": date_from, "date_to": date_to, "limit": 3}, raw=True)

    y0, y1 = int(date_from[:4]), int(date_to[:4])
    results, empty_years = [], []

    for year in range(y0, y1 + 1):
        lo = max(date_from, f"{year}-01-01")
        hi = min(date_to, f"{year}-12-31")
        if lo > hi:
            continue
        got = paginate(f"/sensors/{sensor_id}/days", key,
                       {"date_from": lo, "date_to": hi},
                       limit=500, label=f"{year}", quiet=True)
        results.extend(got)
        if not quiet:
            print(f"  {year}: {len(got):>3} days")
        if not got:
            empty_years.append(year)
        time.sleep(SLEEP_BETWEEN_REQUESTS)

    if empty_years and not quiet:
        print(f"\n  NOTE: no data at all for {empty_years}. That is a real hole in"
              f"\n  this station's record, not a download failure. Weigh it before"
              f"\n  choosing this station.")

    rows = parse_daily(results, min_coverage)
    if not quiet and rows:
        cad = detect_cadence(rows)
        odd = {y: c for y, c in sorted(cad.items()) if c != 24}
        if odd:
            print("\n  Reporting cadence found in the data (readings per full day):")
            print("   ", ", ".join(f"{y}:{c}" for y, c in sorted(cad.items())))
            print("  OpenAQ assumes 24. Where these differ, its own percentComplete")
            print("  is too generous, so coverage here is recomputed against these.")
    return rows


# ----------------------------------------------------------------------------
# S3 archive fallback
# ----------------------------------------------------------------------------

def s3_list(prefix, max_keys=1000):
    """List keys under a prefix in the public archive. No credentials needed."""
    import requests

    keys, token = [], None
    while True:
        params = {"list-type": "2", "prefix": prefix, "max-keys": str(max_keys)}
        if token:
            params["continuation-token"] = token
        r = requests.get(ARCHIVE_HOST, params=params, timeout=60)
        if r.status_code >= 400:
            sys.exit(f"S3 listing failed: HTTP {r.status_code}\n{r.text[:300]}")
        ns = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
        root = ET.fromstring(r.text)
        for c in root.findall("s3:Contents", ns):
            k = c.find("s3:Key", ns)
            if k is not None:
                keys.append(k.text)
        truncated = (root.findtext("s3:IsTruncated", default="false", namespaces=ns) == "true")
        token = root.findtext("s3:NextContinuationToken", namespaces=ns)
        if not truncated or not token:
            break
    return keys


def parse_archive_csv(text):
    """Pull (local datetime, value) pairs of PM2.5 out of one archive file.

    Column names are matched flexibly because I could not verify them against a
    real file. If this returns nothing, run with --raw to print the header.
    """
    out = []
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return out
    cols = {c.lower().strip(): c for c in reader.fieldnames}

    def pick(*names):
        for n in names:
            if n in cols:
                return cols[n]
        return None

    c_param = pick("parameter", "parameter_name", "measurand")
    c_value = pick("value", "measurement")
    c_time = pick("datetime", "datetime_local", "date_local", "local", "datetimelocal")

    if not (c_value and c_time):
        return out

    for row in reader:
        if c_param and (row.get(c_param) or "").strip().lower() not in ("pm25", "pm2.5"):
            continue
        try:
            v = float(row[c_value])
        except (TypeError, ValueError):
            continue
        out.append((str(row[c_time])[:10], v))
    return out


def fetch_archive(location_id, date_from, date_to, min_hours=18, raw=False):
    """Rebuild the daily series from the bulk archive, aggregating hourly rows."""
    import requests

    y0, y1 = int(date_from[:4]), int(date_to[:4])
    buckets = {}
    printed_header = False

    for year in range(y0, y1 + 1):
        prefix = f"records/csv.gz/locationid={location_id}/year={year}/"
        keys = s3_list(prefix)
        print(f"  {year}: {len(keys)} files")
        for i, k in enumerate(keys):
            r = requests.get(f"{ARCHIVE_HOST}/{k}", timeout=60)
            if r.status_code >= 400:
                continue
            try:
                text = gzip.decompress(r.content).decode("utf-8", "replace")
            except OSError:
                continue
            if raw and not printed_header:
                print("  first file header:", text.splitlines()[0] if text else "(empty)")
                printed_header = True
            for day, v in parse_archive_csv(text):
                if date_from <= day <= date_to:
                    buckets.setdefault(day, []).append(v)
            if (i + 1) % 100 == 0:
                print(f"    {i + 1}/{len(keys)}")

    rows = []
    for day in sorted(buckets):
        vals = buckets[day]
        # An hourly monitor gives 24 readings a day. Same coverage logic as the
        # API route, expressed in hours because that is what the archive holds.
        keep = len(vals) >= min_hours
        mean = sum(vals) / len(vals)
        rows.append({
            "date": day,
            "PM2.5": mean if keep else None,
            "PM2.5_raw": mean,
            "pct_complete": round(100.0 * len(vals) / 24.0, 1),
            "n_obs": len(vals),
        })
    return rows



# ----------------------------------------------------------------------------
# Comparing candidate stations
# ----------------------------------------------------------------------------

def longest_gap(rows, date_from=None, date_to=None):
    """Longest run of consecutive calendar days with no usable value.

    Computed over the calendar, not over the returned rows. A station that
    simply stops reporting for six months returns no rows at all for that
    stretch, so counting gaps between returned rows would miss the very outage
    that should disqualify it.
    """
    usable = {r["date"] for r in rows if r["PM2.5"] is not None}
    if not usable:
        return None
    days = sorted(r["date"] for r in rows)
    start = date.fromisoformat(date_from or days[0])
    end = date.fromisoformat(date_to or days[-1])

    worst = run = 0
    d = start
    while d <= end:
        run = 0 if d.isoformat() in usable else run + 1
        worst = max(worst, run)
        d += timedelta(days=1)
    return worst


def station_summary(key, location_id, date_from, date_to, min_coverage, threshold=121.0):
    """Everything needed to judge one station, in one row."""
    meta = api_get(f"/locations/{location_id}", key)
    loc = (meta.get("results") or [{}])[0]
    name = (loc.get("name") or "")[:28]
    provider = ((loc.get("provider") or {}).get("name") or "")[:14]

    time.sleep(SLEEP_BETWEEN_REQUESTS)
    sensor_id, _ = sensor_for_location(key, location_id)
    time.sleep(SLEEP_BETWEEN_REQUESTS)

    rows = fetch_daily(key, sensor_id, date_from, date_to, min_coverage, quiet=True)
    if not rows:
        return {"location_id": location_id, "name": name, "provider": provider,
                "empty": True}

    days = sorted(r["date"] for r in rows)
    first, last = days[0], days[-1]
    calendar = (date.fromisoformat(last) - date.fromisoformat(first)).days + 1
    usable = [r for r in rows if r["PM2.5"] is not None]
    vals = [r["PM2.5"] for r in usable]

    return {
        "location_id": location_id, "name": name, "provider": provider,
        "sensor_id": sensor_id, "first": first, "last": last,
        "years": calendar / 365.25,
        "pct_usable": 100.0 * len(usable) / calendar if calendar else 0.0,
        "gap": longest_gap(rows, first, last),
        "n_usable": len(usable),
        "mean": sum(vals) / len(vals) if vals else None,
        "exceed_pct": 100.0 * sum(1 for v in vals if v > threshold) / len(vals) if vals else None,
        "empty": False,
    }


def compare_stations(key, ids, date_from, date_to, min_coverage, threshold=121.0):
    out = []
    for i, lid in enumerate(ids, 1):
        print(f"  [{i}/{len(ids)}] location {lid} ...", flush=True)
        out.append(station_summary(key, lid, date_from, date_to, min_coverage, threshold))
        time.sleep(SLEEP_BETWEEN_REQUESTS)

    print("\n" + "=" * 104)
    print("STATION COMPARISON")
    print("=" * 104)
    print(f"{'loc_id':>7}  {'provider':14}  {'first':10}  {'last':10}  {'yrs':>4}  "
          f"{'usable%':>7}  {'gap':>5}  {'mean':>6}  {'exc%':>5}  name")
    print("-" * 104)
    for r in out:
        if r.get("empty"):
            print(f"{r['location_id']:>7}  {r['provider']:14}  "
                  f"{'no data returned':<48}  {r['name']}")
            continue
        print(f"{r['location_id']:>7}  {r['provider']:14}  {r['first']:10}  {r['last']:10}  "
              f"{r['years']:4.1f}  {r['pct_usable']:7.1f}  {r['gap']:5d}  "
              f"{r['mean']:6.1f}  {r['exceed_pct']:5.1f}  {r['name']}")
    print("-" * 104)
    print("  usable%  share of the calendar with a value passing the coverage rule")
    print("  gap      longest run of consecutive days with no usable value")
    print(f"  exc%     share of usable days above {threshold:.0f}")
    print("\n  Judge on usable% and gap first, span second. A long series with a")
    print("  six month hole is worse than a shorter continuous one, because the")
    print("  hole distorts the seasonal fit rather than merely shortening it.")

    live = [r for r in out if not r.get("empty")]
    if live:
        best = max(live, key=lambda r: (r["pct_usable"] - min(r["gap"], 120) / 4.0))
        print(f"\n  On usable coverage penalised by the longest gap: location "
              f"{best['location_id']}, {best['name']}")
        print("\n  Next:")
        print(f"    python step00_fetch_openaq.py --location-id {best['location_id']} "
              f"--from {best['first']} --out data/delhi.csv")
    return out


# ----------------------------------------------------------------------------
# Output
# ----------------------------------------------------------------------------

def write_csv(rows, out_path, location_id):
    if not rows:
        sys.exit("No rows to write. Nothing was returned for that range.")
    d = os.path.dirname(out_path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date", "PM2.5", "PM2.5_raw",
                                          "pct_complete", "api_pct", "n_obs",
                                          "cadence", "location_id"],
                           extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(dict(r, location_id=location_id))


def report_series(rows, min_coverage):
    days = [r["date"] for r in rows]
    kept = [r for r in rows if r["PM2.5"] is not None]
    dropped = len(rows) - len(kept)

    first, last = date.fromisoformat(days[0]), date.fromisoformat(days[-1])
    calendar = (last - first).days + 1

    print("\n" + "=" * 58)
    print("SERIES")
    print("=" * 58)
    print(f"  Range             : {days[0]} to {days[-1]}")
    print(f"  Calendar days     : {calendar}")
    print(f"  Days returned     : {len(rows)}")
    print(f"  Usable            : {len(kept)}  ({100 * len(kept) / calendar:.1f}% of calendar)")
    print(f"  Dropped, coverage : {dropped} below {min_coverage:.0f}%")
    print(f"  Years             : {calendar / 365.25:.1f}")
    if kept:
        vals = [r["PM2.5"] for r in kept]
        vals_sorted = sorted(vals)
        print(f"  Mean PM2.5        : {sum(vals) / len(vals):.1f}")
        print(f"  Median            : {vals_sorted[len(vals_sorted) // 2]:.1f}")
        print(f"  Max               : {max(vals):.1f}")
        over = sum(1 for v in vals if v > 121)
        print(f"  Days above 121    : {over} ({100 * over / len(vals):.1f}%)")


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------

def _fixture_days():
    """Records shaped like the documented DailyData schema."""
    def rec(day, value, expected, observed):
        return {
            "value": value,
            "summary": {"avg": value, "sd": 5.0},
            "period": {
                "label": "1day", "interval": "24:00:00",
                "datetimeFrom": {"utc": f"{day}T18:30:00Z", "local": f"{day}T00:00:00+05:30"},
                "datetimeTo": {"utc": f"{day}T18:30:00Z", "local": f"{day}T23:59:59+05:30"},
            },
            "coverage": {
                "expectedCount": expected, "observedCount": observed,
                "percentComplete": 100.0 * observed / expected,
                "percentCoverage": 100.0 * observed / expected,
            },
        }
    return [
        rec("2024-01-01", 180.0, 24, 24),   # full day, kept
        rec("2024-01-02", 95.5, 24, 20),    # 83%, kept
        rec("2024-01-03", 300.0, 24, 4),    # 17%, dropped to NaN
        rec("2024-01-05", 60.0, 24, 24),    # a gap at the 4th, on purpose
    ]


def test_parsing(verbose=True):
    ok = True

    rows = parse_daily(_fixture_days(), min_coverage=75.0)
    by_day = {r["date"]: r for r in rows}

    def check(cond, msg):
        nonlocal ok
        if not cond:
            print(f"  FAIL: {msg}")
            ok = False

    check(len(rows) == 4, f"expected 4 rows, got {len(rows)}")
    check(list(by_day) == sorted(by_day), "rows are not date sorted")

    # The local date must win. In UTC these days start at 18:30 the day before,
    # so a UTC parse would label them 2023-12-31 and shift the entire series.
    check("2024-01-01" in by_day, "local date was not used for the day label")

    check(by_day["2024-01-01"]["PM2.5"] == 180.0, "full day was not kept")
    check(by_day["2024-01-02"]["PM2.5"] == 95.5, "83 percent day should be kept")
    check(by_day["2024-01-03"]["PM2.5"] is None, "17 percent day should be NaN")
    check(by_day["2024-01-03"]["PM2.5_raw"] == 300.0, "raw value should survive")
    check("2024-01-04" not in by_day, "a day with no record must not be invented")

    # Duplicates across pages: keep the better covered record.
    dup = _fixture_days() + [dict(_fixture_days()[0], value=999.0,
                                  coverage={"expectedCount": 24, "observedCount": 6,
                                            "percentComplete": 25.0})]
    d2 = {r["date"]: r for r in parse_daily(dup, 75.0)}
    check(d2["2024-01-01"]["PM2.5"] == 180.0,
          "a worse covered duplicate overwrote a better one")

    # A null value with a usable summary average.
    r = _fixture_days()[0]
    r["value"] = None
    check(parse_daily([r], 75.0)[0]["PM2.5"] == 180.0,
          "did not fall back to summary.avg when value was null")

    # Coverage threshold is applied, not ignored.
    strict = {x["date"]: x for x in parse_daily(_fixture_days(), min_coverage=90.0)}
    check(strict["2024-01-02"]["PM2.5"] is None,
          "min_coverage=90 should drop the 83 percent day")

    # Cadence detection: a half-hourly sensor must not be scored against 24.
    def rec48(day, value, observed):
        return {"value": value, "summary": {"avg": value},
                "period": {"datetimeFrom": {"local": f"{day}T00:00:00+05:30"}},
                "coverage": {"expectedCount": 24, "observedCount": observed,
                             "percentComplete": 100.0 * observed / 24}}

    half_hourly = [rec48(f"2019-01-{d:02d}", 100.0, 48) for d in range(1, 21)]
    half_hourly.append(rec48("2019-01-21", 900.0, 24))     # half a day, looks full to the API
    rows2 = parse_daily(half_hourly, min_coverage=75.0)
    by = {r["date"]: r for r in rows2}
    check(by["2019-01-21"]["api_pct"] == 100.0,
          "the API would have called this day 100 percent complete")
    check(by["2019-01-21"]["cadence"] == 48,
          f"cadence should be 48, got {by['2019-01-21']['cadence']}")
    check(by["2019-01-21"]["pct_complete"] == 50.0,
          "24 of a real 48 readings must be scored 50 percent")
    check(by["2019-01-21"]["PM2.5"] is None,
          "the half covered day must be blanked by the coverage rule")
    check(by["2019-01-21"]["PM2.5_raw"] == 900.0, "raw value must survive")
    check(by["2019-01-01"]["PM2.5"] == 100.0, "a full day was wrongly blanked")

    # A genuinely hourly sensor must be unaffected.
    hourly = [rec48(f"2025-01-{d:02d}", 80.0, 24) for d in range(1, 21)]
    rows3 = parse_daily(hourly, min_coverage=75.0)
    check(all(r["PM2.5"] == 80.0 for r in rows3),
          "an hourly sensor must not be penalised by cadence detection")

    # Archive CSV parsing, including a non-PM2.5 row that must be ignored.
    sample = ("location_id,sensors_id,location,datetime,lat,lon,parameter,units,value\n"
              "8118,111,Delhi,2024-01-01T01:00:00+05:30,28.6,77.2,pm25,µg/m³,150.2\n"
              "8118,112,Delhi,2024-01-01T02:00:00+05:30,28.6,77.2,no2,µg/m³,40.0\n"
              "8118,111,Delhi,2024-01-01T03:00:00+05:30,28.6,77.2,pm25,µg/m³,160.8\n")
    pairs = parse_archive_csv(sample)
    check(len(pairs) == 2, f"archive parser took {len(pairs)} rows, expected 2 PM2.5")
    check(all(d == "2024-01-01" for d, _ in pairs), "archive date parsing is wrong")

    if verbose:
        print("  Parsing checks:", "PASSED" if ok else "FAILED")
    return ok


# ----------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Fetch a daily PM2.5 series from OpenAQ.")
    ap.add_argument("--find", action="store_true", help="list nearby PM2.5 stations")
    ap.add_argument("--compare", help="comma separated location ids to evaluate side by side")
    ap.add_argument("--location-id", type=int)
    ap.add_argument("--sensor-id", type=int, help="skip the sensor lookup")
    ap.add_argument("--lat", type=float, default=DEFAULT_LAT)
    ap.add_argument("--lon", type=float, default=DEFAULT_LON)
    ap.add_argument("--radius", type=int, default=DEFAULT_RADIUS, help="metres, max 25000")
    ap.add_argument("--from", dest="date_from", default="2016-01-01")
    ap.add_argument("--to", dest="date_to", default=date.today().isoformat())
    ap.add_argument("--min-coverage", type=float, default=75.0,
                    help="percent of the day that must be observed (default 75)")
    ap.add_argument("--archive", action="store_true",
                    help="use the public S3 archive instead of the API")
    ap.add_argument("--out", default="data/delhi.csv")
    ap.add_argument("--key")
    ap.add_argument("--raw", action="store_true", help="dump the first response")
    ap.add_argument("--test", action="store_true", help="run parsing checks and exit")
    args = ap.parse_args()

    if args.test:
        sys.exit(0 if test_parsing() else 1)

    if args.radius > 25000:
        sys.exit("The API caps radius at 25000 metres. Use a second centre point instead.")

    if args.find:
        key = get_key(args.key)
        report_stations(find_stations(key, args.lat, args.lon, args.radius))
        return

    if args.compare:
        key = get_key(args.key)
        ids = [int(x) for x in args.compare.replace(" ", "").split(",") if x]
        compare_stations(key, ids, args.date_from, args.date_to, args.min_coverage)
        return

    if not args.location_id and not args.sensor_id:
        sys.exit("Give --find, or --location-id, or --sensor-id. See --help.")

    if args.archive:
        if not args.location_id:
            sys.exit("The archive is organised by location id, so --location-id is required.")
        print(f"\nArchive route, location {args.location_id}. No API key needed.")
        rows = fetch_archive(args.location_id, args.date_from, args.date_to, raw=args.raw)
    else:
        key = get_key(args.key)
        sensor_id = args.sensor_id
        if not sensor_id:
            sensor_id, units = sensor_for_location(key, args.location_id)
            print(f"  location {args.location_id} -> pm25 sensor {sensor_id} ({units})")
        rows = fetch_daily(key, sensor_id, args.date_from, args.date_to,
                           args.min_coverage, raw=args.raw)

    report_series(rows, args.min_coverage)
    write_csv(rows, args.out, args.location_id)
    print(f"\n  Wrote {args.out} ({len(rows)} rows).")
    print("\nNext:")
    print(f"    python step01_data_check.py --csv {args.out} --value-col PM2.5")
    print("  Read the verdict block before building anything on this station.\n")


if __name__ == "__main__":
    main()
