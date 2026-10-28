# Question drill

Forty questions in four tiers, with short model answers. Every answer is tagged:

- **[Report §x]** is in the report at that section. Safe to quote.
- **[Recomputed]** is not printed in the report but was recomputed from the repository's own files (`threshold_sweep.csv`) with the report's own definitions. Say "recomputing from my results".
- **[Project notes]** is from the project log or a judgement call, **not** in the report. Say it is from your analysis notes, not that the report states it.

**The formula for every answer:** one sentence (answer first), one number, one honest limit. Then stop.

How to drill: cover the answer, say yours aloud, then compare. Do tiers A and B first, C and D in Phase 2.
Ask me to run "start mock viva" and I will play the examiner and push back.

## Tier A: warm-up (you will almost certainly be asked these)

**A1. In one minute, what did you do and what did you find?**
I forecast hazardous PM2.5 days one to three days ahead at a Delhi monitor with twelve models and judged them as a warning system. ARIMA beat every machine learning regressor at every horizon; the neural networks beat it only at one day ahead. The biggest finding is that the alarm budget moves the hit rate by about 50 points while the model moves it by about 5. [Report abstract, §6.1]

**A2. Why this problem?**
Sustained PM2.5 exposure is linked to cardiopulmonary and all-cause mortality, and a forecast only helps if it arrives before the hazardous day. Existing Delhi machine learning studies score forecasts by R squared, RMSE and MAE, not as a warning system. I also grew up in India, so the question matters to me. [Report §1, §2.3]

**A3. Why 121 µg/m³?**
It is the boundary of the CPCB National Air Quality Index category below 'Severe' for the 24-hour mean, so a policy threshold rather than a round number. [Report §3.1]

**A4. Why this station?**
Every CPCB station serves data only from 19 February 2025, about eighteen months. Location 8118 is the only nearby monitor with the full decade. The cost is that it is an AirNow feed, almost certainly a US diplomatic post monitor, so the results describe one site, not Delhi. [Report §3.1, §5.3]

**A5. What are your three research questions and answers?**
RQ1: ARIMA beats every ML regressor at every horizon (rMAE 0.940 at one day); networks win only at one day. RQ2: neither arm dominates (21 / 11 / 4 across 36 matched comparisons); I prefer forecast-then-threshold. RQ3: the budget sweep moves the hit rate from 0.379 to 0.881; the model, about 5 points. [Report Table 6.1]

**A6. What are hit rate, false alarm rate and alarm budget, in plain words?**
Hit rate is the share of hazardous days caught. False alarm rate is the share of quiet days wrongly flagged. The alarm budget is how many alarms are raised per year, the dial an operator sets. [Report §3.6]

**A7. What was wrong with the data?**
Two things. A clipped instrument ceiling: 1990 appeared three times identically, once on 2 September in the monsoon. And a coverage statistic that divided by 24 readings a day when the sensor was half-hourly until 2024, so half-days looked complete. I took the cadence from the data. [Report §3.2.1]

**A8. Why do you say there is no weekly cycle?**
Three independent tests agree: the periodogram has no peak near seven days; autocorrelation at lag 7 (0.173) sits between lag 6 (0.179) and lag 8 (0.153); and day of week gives a 6.5% spread with ANOVA p = 0.34 and Kruskal-Wallis p = 0.77. A weekly cycle is a traffic signature and the monitor is in a diplomatic enclave. [Report §3.2.2]

## Tier B: core method and results

**B1. Why ARIMA with Fourier terms and not seasonal ARIMA? Why K = 4?**
A seasonal ARIMA takes one seasonal period; with no weekly cycle the only seasonality is annual, which Fourier terms carry compactly. [Report §3.2.2, §3.3.1] On K = 4: BIC kept improving to K = 6, but BIC assumes independent errors and these residuals are autocorrelated, so it over-selects; K = 4 took the clear gain from K = 3 and stayed parsimonious. **[Project notes, not in the report.]** The report does show that giving the GRU four harmonics instead of two improves it. [Report §3.4.1, §5.3]

**B2. Why logarithms?**
The series is strongly right skewed (skewness 2.17, excess kurtosis 8.31), annual Fourier terms explain 69% of the variance of the log, and logs stop a forecast going negative. The back-transform gives a median, exp(m), or a mean, exp(m + s²/2); both are reported. [Report §3.1, §3.3.1]

**B3. Why a rolling origin rather than one train-test split?**
A single split is one draw of history. On one calm block ARIMA scored 0.903 at one day; under the rolling harness the same model scores 0.940. [Report §3.5]

**B4. How do you know there is no leakage?**
The invariant is that at origin t a model may use observations up to day t and nothing else. It is tested: corrupt the series from a chosen date, rerun, and no earlier forecast may change. The label on row t′ is the value at t′ + h, so the training set ends at t − h, which is why I fit one model per horizon. [Report §3.5]

**B5. Why rMAE rather than RMSE or MASE?**
rMAE divides by persistence on identical rows, so 1.000 is persistence and values are directly interpretable. MASE divides by training-period volatility, so it can fall for every model on a calmer block. The Diebold-Mariano test uses absolute loss to match. [Report §3.6, §3.7]

**B6. What does rMAE = 0.940 mean?**
ARIMA's mean absolute error at one day is 94% of persistence's: about 6% better than repeating yesterday. [Report Table 4.1]

**B7. Why does ARIMA beat the machine learning models?**
It matches the forecasting-competition evidence: on a few thousand observations with no exogenous structure, a flexible learner has little to exploit beyond what a classical model already carries (M4). The ML models are also more exposed to the uncleaned tail: ridge goes from 0.997 to 1.118 when the capped values are restored. [Report §2.1, §5.3]

**B8. Why do the networks win only at one day ahead?**
At one day the forecast is dominated by short-range structure, where a nonlinear model has something to exploit. As the horizon lengthens the seasonal component takes over, and the network gets a coarser seasonal signal (two Fourier pairs, not four). A bounded check with four pairs improved the three-day result by 3.96 points. [Report §4.1, §5.3]

**B9. What about the LSTM and the transformer?**
The LSTM beats the GRU at every horizon (by 0.005, 0.008, 0.013) despite a third more parameters. The transformer beats the GRU in 8 of 10 matched seeds at every horizon and has the strongest formal significance at one day, 7 of 10 seeds. Both overturn the arguments I made in advance for preferring the GRU. The transformer is one untuned configuration. [Report §4.1, §3.4.3]

**B10. What did weather do?**
Wind speed and temperature help at one day ahead (the weather GRU beats ARIMA in all ten seeds, 7 of 10 significant) and leave two and three days a tie. The first five seeds had looked like wins; ten seeds overturned that. Gradient boosting improves everywhere; the random forest is worse at three days. [Report §4.1.1]

**B11. What is the answer to RQ2 and why prefer forecast-then-threshold?**
Matched by base algorithm, forecast-then-threshold wins 21 of 36 comparisons, classification 11, four ties, with a median gap of 0.011 of hit rate. I prefer it also because it yields a concentration that can be rethresholded for any future health policy without refitting. [Report §4.2]

## Tier C: hard (the answers that decide the marks)

**C1. Isn't it trivial that a bigger alarm budget gives a higher hit rate?**
Yes, by construction, which is exactly why every model comparison is made at a fixed budget. The finding is not that the first effect exists; it is how large the two effects are: about 50 points for the budget against a few points for the model, and that at three days and 40 alarms a year persistence, which just repeats yesterday, is the best model in the whole study (0.359). [Report §4.3, §5.1]

**C2. Your headline says "about five points". Is that exact?**
It is the report's summary and it is rough. **[Recomputed]** Using the report's own operating-point definition on the sweep file, the spread across the ten forecast-then-threshold models at a fixed budget averages 7.1 points (range 4.3 to 11.5 by horizon and budget). Without the deliberately weak lag-7 seasonal-naive benchmark it is 3.8; for the fitted models alone 2.8. Against 50 points for the budget the conclusion is unchanged. Say: "recomputing from my results".

**C3. Is the left panel of your dial slide cherry-picked?**
It shows four representative models, as the report's Figure 4.5 does. The lag-7 seasonal-naive benchmark would be lower, 0.758 at 100 alarms and one day. **[Recomputed]** It is a deliberately weak reference. [Report Fig 4.5]

**C4. Are the network wins statistically significant?**
At one day, the network is numerically ahead of ARIMA in all ten seeds, and the Diebold-Mariano test reaches p < 0.05 in 4 of 10 (GRU), 5 of 10 (LSTM) and 7 of 10 (transformer). At two and three days, essentially none. Across all 27 tests I ran, with no correction, only six survive a Bonferroni correction, and none of the plain GRU, LSTM or transformer. So I read beyond one day as suggestive. [Report §3.7, §4.1, Table 4.2]

**C5. Why ten seeds, and is the training reproducible?**
Rerunning the identical command with the same seed on the same machine moved the GRU's score nearly as much as switching to a different seed, so a fixed seed does not guarantee a fixed answer. Five seeds were not enough: the weather result at two and three days looked like a win under five and a tie or loss under ten. Ten is a reduction in the problem, not a solution. [Report §5.3]

**C6. Did you tune fairly? Could the ML models do better?**
Trees chose hyperparameters from a small grid at every refit, so the ML results are a lower bound. The GRU's architecture was fixed by inspection. Bounded single-split checks show its three-day setting is the one I can least defend (a 45-day window 2.2 points better, four harmonics 3.96, SGD about 2). I did not rerun the full ten-seed evaluation with them, so Table 4.1 is unchanged. [Report §5.3]

**C7. Isn't the Diebold-Mariano test unreliable for heavy-tailed errors?**
It can be, and the report says so. I used the Harvey-Leybourne-Newbold small-sample correction with absolute-error loss, but did not bootstrap the statistic's distribution, which is a stated limitation. [Report §3.7]

**C8. Is one US-embassy monitor valid?**
It is a reference-grade instrument, but it is one point in the city. I make no claim about Delhi as a whole or other cities; a second, independent station is the first future extension after the weather work. [Report §3.1, §5.3, §6.2]

**C9. The 1000 cleaning ceiling looks arbitrary.**
It is a judgement, and I checked it. Restoring the seven removed days (three of them the clipped 1990) and refitting everything leaves ARIMA essentially unchanged (0.935 against 0.940), because logs and differencing absorb the contamination, while the ML models get worse. So the RQ1 finding strengthens. [Report §5.3]

**C10. Why not combine ARIMA and a neural network, a hybrid or ensemble?**
Zhang (2003) fits a network to ARIMA residuals. I deliberately compared the families side by side, so the comparison says which family suits the series rather than being obscured by a blend. A hybrid is a natural extension. [Report §2.1]

**C11. Doesn't "persistence is best at 40 alarms" mean your models are useless?**
No. ARIMA and the networks earn real, if modest, gains over persistence in accuracy (rMAE 0.832 at three days). At a very tight budget only the most confident days count, and a day already deep inside an episode is the safest to flag, which is exactly what persistence encodes. The recommendation is not to stop modelling; it is that the budget is where the leverage lies. [Report §4.3, §5.1]

**C12. ARIMA's θ is −0.987, almost on the invertibility boundary. Is the model overdifferenced?**
It sits 0.013 inside, a near-cancellation between differencing and the moving average term that is a known signature of a series close to overdifferenced. (1,1,1) still scored lowest of all 24 orders. It crosses the boundary at 3 of 28 refits, each with fewer than 1,700 training days; the optimiser is unconstrained, and those forecasts are scored as usual. [Report §3.3.1, Table 3.4, Fig 3.6]

## Tier D: curveballs and reflection

D4 and D9 are suggested answers: adapt them to what you genuinely think and did.

**D1. What would you do with another three months?**
The six extensions in the report: forecast weather instead of observed; boundary layer height from ERA5; the GRU with four harmonics under the full ten-seed evaluation; a second independent station; weather and the threshold sweep for the LSTM and transformer; a full ten-seed evaluation of the Kolmogorov-Arnold-LSTM. [Report §6.2]

**D2. What would a health authority actually do with this?**
Decide an alarm budget it can justify, then use the best available forecast within it. Because the forecast is a concentration, it can be rethresholded for any future policy without refitting. [Report §5.1, §4.2]

**D3. What is novel here?**
Applying a standard model suite to Delhi is not new. The contribution is evaluating it as a warning system with a varying alarm budget, under a leakage-tested rolling-origin protocol with networks reported as ten-seed ranges, plus two corrected data defects and three priors tested rather than assumed. [Report §2.6, §6]

**D4. What would you do differently?**
Run the seed-variance check earlier (five seeds nearly misled me on weather), set the GRU's Fourier order to match ARIMA from the start (I inherited two pairs from an earlier draft and only tested it afterwards), and test the transformer before the literature review argued against it. [Report §3.4.1, §3.4.3, §5.3]

**D5. Why only PM2.5, and only one city?**
The topic was scoped with my supervisor to one city and one health-relevant pollutant so the evaluation could be done rigorously. PM2.5 is the pollutant with the epidemiological mortality evidence the report cites. **[Project notes for the scoping; the report cites the health evidence in §1.]** Multi-city work is future work.

**D6. Why not a bigger neural network or more data?**
The series is about three thousand usable days, some four thousand counting every evaluation block, which Dr Tian judged enough to try a transformer; the result shows it competitive with the LSTM. More data would mean other stations, which is the future-work extension. [Report §2.2.1, §3.4.3]

**D7. What are the biggest limitations?**
One site and one city; observed, not forecast, weather; the LSTM and transformer were not given weather or the threshold sweep; small tuning grids; uncorrected significance testing with best-seed selection; and network training that is not bit-reproducible. None overturns the central finding, which rests on several independent sources agreeing. [Report §5.3]

**D8. If you could say one thing to the panel?**
A model comparison that does not state the alarm budget it was evaluated at has answered a question nobody who operates the system asked.

**D9. Did you use AI to prepare the report or this talk?**
Answer truthfully and consistently with your declaration in the report and the unit's rules. I cannot answer this for you. Decide your wording now, and check it against the AI-use declaration you submitted.

## Numbers to know cold

Cover this table and recite it. Read the right column aloud.

| What | Number |
|---|---|
| Hazard threshold | 121 µg/m³ (CPCB 'Very Poor' boundary) |
| Usable days; hazardous days | 3,093; 920 (29.7%) |
| Period | 2016-11-09 to 2026-08-27 (9.8 years) |
| Cleaning | 282 of 3,375 days removed (5 below zero, 270 low coverage, 7 above 1000) |
| Coverage defect | 1,085 of 3,467 days below 75% true coverage; 268 with no value |
| Rolling origin | 2,303 origins, 6.8 years, 3-year burn-in, refit every 90 days (networks 180) |
| Single split against rolling | ARIMA 0.903 against 0.940 at one day |
| ARIMA rMAE | 0.940, 0.883, 0.832 at h = 1, 2, 3 |
| Networks at one day | 0.910 to 0.939 (GRU), 0.913 to 0.932 (LSTM), 0.914 to 0.925 (transformer) |
| Seed spread (GRU) | 0.029, 0.028, 0.048; noise floor 0.004 |
| Significance at one day | 4 / 10, 5 / 10, 7 / 10 seeds (GRU, LSTM, transformer); 6 of 27 survive Bonferroni |
| Parameters | GRU 2,329; LSTM 3,097; transformer 3,409; KAN-LSTM 3,288 |
| RQ2 | 21 / 11 / 4 across 36; median gap 0.011 |
| RQ3 | 0.379 to 0.881 (40 to 100 alarms, h = 1): 50 points; model effect about 5 (recomputed: 7 mean) |
| Persistence at h = 3, 40 alarms | 0.359, best in the study |
| Weather | at most 1.2 points of hit rate; 8.2 points of rMAE (gradient boosting, h = 1) |
| ARIMA θ | −0.987, 0.013 inside the boundary; crosses at 3 of 28 refits |
