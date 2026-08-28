# Reference sources and links: MTH5000 proposal

All ten works cited in the proposal, with direct links. As a Monash student you have institutional access to the paywalled ones through the Monash library (library.monash.edu). Search the title or paste the DOI into the library search rather than paying anything.

## Core EKC literature

**Grossman, G. M. & Krueger, A. B. (1991).** Environmental impacts of a North American free trade agreement. NBER Working Paper No. 3914.
- https://www.nber.org/papers/w3914 · DOI: 10.3386/w3914
- The original EKC paper. NBER working papers are often freely downloadable.

**Farooq, U., Bhanja, N., Rather, S. R. & Dar, A. B. (2024).** From pollution to prosperity: using inverted N-shaped environmental Kuznets curve to predict India's environmental improvement milestones. *Journal of Cleaner Production*, 434, 140175.
- https://doi.org/10.1016/j.jclepro.2023.140175
- Paywalled (Elsevier). Use library access. Key India-specific finding: inverted-N shape, India still in degradation phase, income thresholds around USD 342 and USD 3,071.

**Al-Mulali, U., Ridwan, I. L., Aslan, A. & Raboshuk, A. (2025).** Evaluating environmental policies' impact on India's environmental Kuznets curve. *Air Quality, Atmosphere and Health*, 18(12), 4109–4122.
- https://doi.org/10.1007/s11869-025-01869-3
- Paywalled (Springer). Use library access. Shows policy interventions shift the curve.

## The econometric critique (most important for your methodology)

**Wagner, M. (2008).** The carbon Kuznets curve: a cloudy picture emitted by bad econometrics? *Resource and Energy Economics*, 30(3), 388–408.
- https://doi.org/10.1016/j.reseneeco.2007.11.001
- Paywalled (Elsevier). A free working-paper version usually exists via IHS Economics Series / RePEc. Search the title on ideas.repec.org.

**Wagner, M. (2015).** The environmental Kuznets curve, cointegration and nonlinearity. *Journal of Applied Econometrics*, 30(6), 948–967.
- https://doi.org/10.1002/jae.2421
- Paywalled (Wiley). Read these two before you write your methodology chapter; they are the reason your specification is set up the way it is.

## Panel econometric methods

**Levin, A., Lin, C. F. & Chu, C. S. J. (2002).** Unit root tests in panel data. *Journal of Econometrics*, 108(1), 1–24.
- https://doi.org/10.1016/S0304-4076(01)00098-7

**Im, K. S., Pesaran, M. H. & Shin, Y. (2003).** Testing for unit roots in heterogeneous panels. *Journal of Econometrics*, 115(1), 53–74.
- https://doi.org/10.1016/S0304-4076(03)00092-7

**Pesaran, M. H. (2007).** A simple panel unit root test in the presence of cross-section dependence. *Journal of Applied Econometrics*, 22(2), 265–312.
- https://doi.org/10.1002/jae.951
- This is the CIPS test you'll actually use. A free Cambridge working-paper version circulates widely.

**Hausman, J. A. (1978).** Specification tests in econometrics. *Econometrica*, 46(6), 1251–1271.
- https://doi.org/10.2307/1913827 · JSTOR. Free through Monash library.

## Pollution data source

**van Donkelaar, A., Hammer, M. S., Bindle, L., et al. (2021).** Monthly global estimates of fine particulate matter and their uncertainty. *Environmental Science & Technology*, 55(22), 15287–15300.
- https://doi.org/10.1021/acs.est.1c05309
- **Open access** (CC BY-NC-ND). Free to read. This is the paper you cite for your PM2.5 data.

---

# Data sources: where you actually get the data

**Satellite PM2.5 (primary pollution data)**
- ACAG, Washington University: https://sites.wustl.edu/acag/surface-pm2-5/
- Also mirrored at NASA SEDAC and https://www.satpm.org
- Free. Download as NetCDF (.nc) or ArcGIS ASCII. Look for the V5.GL series, annual files.

**CPCB ground-station data (validation only)**
- OpenAQ API: https://openaq.org, with docs at https://docs.openaq.org (free API key required)
- CPCB daily AQI bulletins: https://cpcb.nic.in/AQI_Bulletin.php
- CPCB real-time API via data.gov.in: https://www.data.gov.in/resource/real-time-air-quality-index-various-locations

**State GSDP and population**
- RBI Handbook of Statistics on Indian States: https://rbi.org.in → Publications → Annual
- RBI Database on Indian Economy: https://data.rbi.org.in
- MOSPI: https://mospi.gov.in
- Census of India (2001, 2011 + projections): https://censusindia.gov.in

---

**Suggested reading order:** Grossman & Krueger first (what the EKC is), then the two India papers (what's already known and disputed), then Wagner (why most of it may be wrong), then the methods papers as you need them while coding. van Donkelaar only when you start handling the satellite files.
