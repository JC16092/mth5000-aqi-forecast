# Software setup guide: MTH5000 project

Everything here is free and open source, and runs on a normal laptop. No app or website is being built: the outputs are a written report, static figures, and reproducible code.

## The shape of the pipeline

The project has two halves that want different tools.

1. **Geospatial prep (Python).** Turn gridded satellite PM2.5 files into one number per state per year.
2. **Econometrics (R).** Run the panel tests and regressions on that table.

The handover between them is a single CSV, of roughly the form `state, year, pm25, gsdp_per_capita, population`. Once that file exists, the Python half is finished and never needs to run again.

If you would rather stay in one language, all-R is workable (`terra` and `sf` replace the Python geospatial stack). All-Python is the weaker option, because panel unit-root testing is poorly supported there.

---

## Part 1, Python (data preparation)

Install Python 3.11 or newer, then:

```bash
pip install xarray netCDF4 rioxarray geopandas rasterstats pandas numpy matplotlib
```

What each is for:

| Package | Purpose |
|---|---|
| `xarray`, `netCDF4` | Read the satellite PM2.5 `.nc` files |
| `rioxarray` | Attach coordinate reference info to the grids |
| `geopandas` | Load Indian state boundary shapefiles |
| `rasterstats` | Average grid cells within each state polygon |
| `pandas`, `numpy` | Assemble and clean the panel |
| `matplotlib` | Maps and exploratory plots |

If `geopandas` gives you trouble installing via pip (it sometimes does, because of its C dependencies), use conda instead:

```bash
conda install -c conda-forge geopandas rasterstats xarray netcdf4 rioxarray
```

### Rough shape of the Python step

1. Read one annual satellite file into an `xarray` DataArray.
2. Load the state boundaries into a `geopandas` GeoDataFrame.
3. Use `rasterstats.zonal_stats` to compute the mean PM2.5 inside each state polygon, weighted by the gridded population raster.
4. Repeat over all years, concatenate, write to CSV.

---

## Part 2, R (estimation)

Install R and RStudio, then:

```r
install.packages(c("plm", "lmtest", "sandwich", "tidyverse", "sf", "modelsummary"))
```

`plm` is the important one, it contains every test named in your methodology:

| Function | What it does | Where it appears in your proposal |
|---|---|---|
| `pcdtest()` | Pesaran CD test for cross-sectional dependence | Step 2 |
| `cipstest()` | Pesaran CIPS second-generation panel unit root test | Step 2 |
| `plm(..., model = "within")` | Fixed-effects panel regression | Step 3 |
| `vcovSCC()` | Driscoll-Kraay standard errors | Step 3 |
| `phtest()` | Hausman test, fixed vs random effects | Step 3 |

`modelsummary` turns model objects into publication-quality tables you can drop straight into the report. `sf` lets you draw the choropleth maps in R if you prefer that to Python.

---

## Data you still need to download

Beyond the sources already listed in the proposal:

**Indian state boundaries (shapefiles).** Required to aggregate the satellite grid to states.
- GADM: https://gadm.org/download_country.html (select India, level 1 = states)
- Alternative: Natural Earth, https://www.naturalearthdata.com

**Gridded population.** Required for the population-weighting step.
- NASA SEDAC, Gridded Population of the World (GPW v4): https://sedac.ciesin.columbia.edu/data/collection/gpw-v4
- Free, but requires a NASA Earthdata login.

Note: if population weighting proves fiddly, simple area-weighted averaging is an acceptable fallback. Just say which one you used and why. Worth confirming the preference with Dr Tian.

---

## Figures to produce

All static, for the report. No interactivity needed.

1. PM2.5 over time for a handful of contrasting states (rich vs poor, north vs south).
2. The central scatter: GSDP per capita against PM2.5, with the fitted quadratic and its turning point marked.
3. Choropleth maps of India: one shaded by PM2.5, one by income per capita, side by side.
4. Coefficient plot with confidence intervals, and the turning point estimate with its interval.
5. Diagnostic plots, residuals, and a plot showing whether the 2020 COVID year sits as an outlier.

---

## Suggested working order

1. Install Python side, download one year of satellite data, get it to open. Do not proceed until this works.
2. Download shapefiles, aggregate that one year to states, sanity-check the numbers against known values (Delhi should be very high; Kerala and the north-east much lower). If the ranking looks wrong, something is broken.
3. Loop over all years, build the pollution panel.
4. Assemble GSDP and population separately, merge, export CSV.
5. Move to R and begin estimation.

Step 2 is the one to be careful with. If the state-level numbers do not match intuition, stop and debug, because every later result depends on that aggregation being right.

## Version control

Worth using git from the start, even solo, since it makes it possible to undo a bad change without losing work. A private GitHub repository is free.
