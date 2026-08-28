"""Build the supervision meeting brief PDF in the project's house style."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, KeepTogether, Image)
from PIL import Image as PILImage

OUT = "supervisor_meeting_3_prep.pdf"

BLACK = colors.black

title = ParagraphStyle("title", fontName="Times-Bold", fontSize=15, leading=19,
                       alignment=TA_CENTER, spaceAfter=2)
subtitle = ParagraphStyle("subtitle", fontName="Times-Roman", fontSize=11.5,
                          leading=15, alignment=TA_CENTER, spaceAfter=10)
block = ParagraphStyle("block", fontName="Times-Roman", fontSize=10.5, leading=13.5,
                       alignment=TA_CENTER, spaceAfter=1)
h1 = ParagraphStyle("h1", fontName="Times-Bold", fontSize=12, leading=15,
                    spaceBefore=12, spaceAfter=5)
h2 = ParagraphStyle("h2", fontName="Times-Bold", fontSize=11, leading=14,
                    spaceBefore=8, spaceAfter=3)
body = ParagraphStyle("body", fontName="Times-Roman", fontSize=11, leading=14.5,
                      alignment=TA_JUSTIFY, spaceAfter=6)
bullet = ParagraphStyle("bullet", parent=body, leftIndent=12, bulletIndent=2,
                        spaceAfter=3)
note = ParagraphStyle("note", fontName="Times-Roman", fontSize=9.5, leading=12,
                      spaceBefore=2, spaceAfter=8)
cell = ParagraphStyle("cell", fontName="Times-Roman", fontSize=9.5, leading=12)
caption = ParagraphStyle("caption", fontName="Times-Roman", fontSize=9, leading=11.5,
                         alignment=TA_JUSTIFY, spaceBefore=3, spaceAfter=10)
cellb = ParagraphStyle("cellb", fontName="Times-Bold", fontSize=9.5, leading=12)


def table(data, widths, align_right=None, highlight_row=None):
    rows = []
    for i, row in enumerate(data):
        # Bold has to be applied through the paragraph style, not through a
        # TableStyle FONTNAME command, because each cell carries its own style.
        style = cellb if (i == 0 or i == highlight_row) else cell
        rows.append([Paragraph(str(c), style) for c in row])
    t = Table(rows, colWidths=widths, hAlign="LEFT")
    cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, BLACK),
        ("LINEABOVE", (0, 0), (-1, 0), 0.6, BLACK),
        ("LINEBELOW", (0, -1), (-1, -1), 0.6, BLACK),
    ]
    t.setStyle(TableStyle(cmds))
    # Keep the table and the breathing space after it together, so following
    # prose never butts against the closing rule.
    return [t, Spacer(1, 7)]


TEXT_WIDTH = 160 * mm


def figure(path, number, text, width_frac=1.0):
    """A figure and its caption, kept on one page."""
    w, h = PILImage.open(path).size
    width = TEXT_WIDTH * width_frac
    img = Image(path, width=width, height=width * h / w)
    img.hAlign = "CENTER"
    cap = Paragraph(f"<b>Figure {number}.</b> {text}", caption)
    return [KeepTogether([Spacer(1, 4), img, cap])]


story = []

story.append(Paragraph("Supervision Meeting Brief", title))
story.append(Paragraph("Progress report and decisions required", subtitle))
for line in [
    "Jaykumar Vinodbhai Chauhan",
    "Student ID: 34710280",
    "Master of Mathematics",
    "MTH5000 Masters Research Project",
    "Supervisor: Dr Tianhai Tian",
    "School of Mathematics, Monash University",
]:
    story.append(Paragraph(line, block))
story.append(Spacer(1, 4))
story.append(Paragraph("Prepared 20 August 2026", block))
story.append(Spacer(1, 10))

# ---------------------------------------------------------------- 1
story.append(Paragraph("1. Summary", h1))
story.append(Paragraph(
    "The data pipeline is complete. A ten year daily PM2.5 series for Delhi has been "
    "acquired, audited, cleaned and converted into a supervised feature table, and the "
    "code that does so is tested and reproducible. This was the whole of the first "
    "planned week and it is finished ahead of schedule.", body))
story.append(Paragraph(
    "Two problems were found in the source data during the audit, one of which was "
    "silently corrupting the series, and both are documented in Section 3. One "
    "assumption in the approved proposal has been contradicted by the data and the "
    "model specification changes as a result, which is set out in Section 4. Four "
    "decisions require your input and are listed in Section 5.", body))

# ---------------------------------------------------------------- 2
story.append(Paragraph("2. Work completed", h1))

story.append(Paragraph("2.1 Station selection", h2))
story.append(Paragraph(
    "Five candidate monitoring stations within 25 km of central Delhi were compared on "
    "data coverage rather than on nominal length of record. Coverage is the share of the "
    "calendar carrying a usable daily mean, and gap is the longest unbroken run of days "
    "with no usable value.", body))
story.extend(table([
    ["Location", "Provider", "First", "Years", "Coverage", "Gap", "Exceed"],
    ["17, R K Puram", "CPCB", "2025-02-19", "1.5", "85.9%", "11", "21.2%"],
    ["50, Punjabi Bagh", "CPCB", "2025-02-19", "1.5", "85.2%", "11", "20.7%"],
    ["235, Anand Vihar", "CPCB", "2025-02-19", "1.5", "86.8%", "10", "23.9%"],
    ["8118, New Delhi", "AirNow", "2016-11-09", "9.8", "89.4%", "31", "30.0%"],
    ["5404, Pusa", "CPCB", "2025-02-19", "1.5", "76.2%", "10", "15.1%"],
], [95, 52, 62, 34, 52, 30, 45], highlight_row=4))
story.append(Paragraph(
    "The decisive result is in the third column. Every CPCB station returns measurements "
    "only from 19 February 2025, roughly eighteen months, even though the OpenAQ location "
    "metadata advertises a first observation of 5 February 2016. Four independent stations "
    "sharing an identical cutoff is a systematic limit on what the measurements endpoint "
    "serves rather than a coincidence. Only station 8118 returns the full record, so it "
    "was selected.", body))
story.append(Paragraph(
    "This carries a cost that must be stated in the report. Station 8118 is supplied "
    "through AirNow and is almost certainly the United States diplomatic post monitor "
    "rather than part of the Indian official network. The project therefore forecasts at "
    "one well characterised reference site in Delhi, which is common in this literature, "
    "and cites OpenAQ and the United States Department of State rather than CPCB.", body))

story.append(Paragraph("2.2 Two defects in the source data", h2))
story.append(Paragraph(
    "<b>Physically impossible values.</b> The raw series contained five negative "
    "concentrations, to a minimum of -7.3, and a maximum of 1990. The value 1990.0 "
    "appeared three times, identically, on unrelated dates, which is the signature of a "
    "clipped instrument ceiling rather than a measurement. One of the three fell on 2 "
    "September, in the monsoon, between neighbouring days of 42 and 178.", body))
story.append(Paragraph(
    "<b>A wrong coverage denominator.</b> OpenAQ reports the completeness of each daily "
    "aggregate as the observation count divided by an expected count of 24, assuming "
    "hourly reporting. This sensor reported half hourly from 2016 to 2024 and hourly from "
    "2025. The visible symptom is a reported completeness above 100 percent, which is "
    "impossible. The damaging symptom is invisible: a day holding 24 of a real 48 readings "
    "is scored as fully complete, so a mean computed from half a day of a polluted "
    "afternoon enters the series as though it were a genuine daily mean. Days at 50 to 75 "
    "percent true coverage were approximately nine times more likely to exceed 500 than "
    "days above 90 percent, which identifies this as the mechanism producing the "
    "impossible extremes.", body))
story.extend(figure("fig2_coverage.png", 1,
    "The coverage defect. Panel (a) shows the number of readings contributing to each "
    "daily mean, with the cadence estimated from the data each year as the solid line. "
    "The sensor reported roughly half hourly until the end of 2024 and hourly thereafter, "
    "while the denominator used to report completeness stayed at 24 throughout. Panel (b) "
    "shows the rate of physically implausible values by true coverage. Days observed for "
    "more than 90 percent of their length yield such values at roughly one seventh the "
    "rate of days below that, which identifies incomplete days as the mechanism rather "
    "than a coincidence."))
story.append(Paragraph(
    "The correction takes the reporting cadence from the data itself, using the ninetieth "
    "percentile of observation counts within each year, which follows the 2025 change in "
    "reporting interval automatically. Recomputed on that basis, 1,085 of 3,199 observed "
    "days fall below 75 percent coverage rather than the 268 the published figure implies.", body))

story.append(Paragraph("2.3 Cleaning applied", h2))
story.extend(table([
    ["Rule", "Days removed", "Basis"],
    ["Value below zero", "5", "Mass concentration cannot be negative"],
    ["Coverage below 50 percent", "270", "Against the true cadence, not the published one"],
    ["Value above 1000", "7", "Judgement, see Section 5"],
    ["Total", "282 of 3,375", ""],
], [125, 70, 175], highlight_row=4))
story.append(Paragraph(
    "The coverage threshold is set at 50 rather than a stricter value because the longest "
    "gap is the binding constraint. At 60 percent the worst gap rises to 69 days and at 90 "
    "percent to 185 days, either of which would distort the estimation of the annual cycle. "
    "At 50 percent the worst gap is 34 days. The exceedance rate is stable across every "
    "candidate threshold, moving only from 30.0 to 27.0 percent, which confirms the filter "
    "is not selectively removing the events of interest.", body))

story.append(Paragraph("2.4 The resulting dataset", h2))
story.extend(table([
    ["Property", "Value"],
    ["Source", "OpenAQ location 8118, sensor 23534, provider AirNow"],
    ["Period", "9 November 2016 to 27 August 2026, 9.8 years"],
    ["Usable daily means", "3,093, being 86.4 percent of the calendar"],
    ["Longest gap", "34 consecutive days"],
    ["Mean, median, maximum", "102.7, 71.7, 896.0"],
    ["Days above 121", "920, being 29.7 percent"],
], [125, 245]))
story.extend(figure("fig1_series.png", 2,
    "The cleaned daily series. Shading marks the days exceeding the threshold. The "
    "episodic structure is the feature the project exists to forecast: exceedances do not "
    "arrive as isolated days but as multi day winter episodes, which is why persistence of "
    "the event itself is carried as a predictor in the feature table."))
story.append(Paragraph(
    "The maximum of 896 falls on 8 November 2017, within the documented severe episode of "
    "that month. A real event surviving the cleaning while the September and February "
    "spikes do not is a useful check that the rules are discriminating rather than merely "
    "truncating.", body))

story.append(Paragraph("2.5 Feature table", h2))
story.append(Paragraph(
    "3,355 rows, 39 feature columns and 6 target columns. A row indexed by date t is one "
    "forecast origin, and every feature in it is a function of observations up to and "
    "including day t. Features comprise lags at 0, 1, 2, 3 and 7 days, first differences, "
    "rolling mean, standard deviation and maximum over 3, 7, 14 and 30 days, an anomaly "
    "and standardised anomaly against the 30 day norm, exceedance frequency over the last "
    "7 and 30 days, days since the last exceedance, calendar terms, four pairs of annual "
    "Fourier terms and three missingness indicators.", body))
story.append(Paragraph(
    "Targets are the concentration at one, two and three days ahead and the matching "
    "binary exceedance indicators, so both arms of Research Question 2 are answered from a "
    "single table. Class balance is 29.7 percent at all three horizons.", body))
story.append(Paragraph(
    "An automated leakage test accompanies the construction. It rebuilds the table from a "
    "series corrupted from a chosen cut date onward and asserts that every feature row "
    "before that cut is unchanged, then verifies target alignment and the right edge "
    "alignment of the rolling windows. It runs before every build and currently passes.", body))

# ---------------------------------------------------------------- 3
story.append(Paragraph("3. A finding that changes the model specification", h1))
story.append(Paragraph(
    "The approved proposal states that daily pollution series carry a weekly cycle driven "
    "by traffic and industrial activity, and the accompanying plan treats the coexistence "
    "of a weekly and an annual period as the central modelling difficulty, since a seasonal "
    "ARIMA accommodates only one seasonal period. That difficulty was to be the main "
    "question for this meeting.", body))
story.append(Paragraph(
    "Tested on the cleaned series, the weekly cycle is not present at this station. Three "
    "independent tests agree.", body))
story.extend(table([
    ["Test", "Result"],
    ["Periodogram, dominant periods",
     "357.9, 178.9, 188.4, 397.7, 325.4, 60.7 days. The annual cycle and its harmonics. Nothing near 7."],
    ["Autocorrelation of the deseasonalised log series",
     "Lag 6 is 0.179, lag 7 is 0.173, lag 8 is 0.153. Lag 7 lies on the decay curve rather than above it. The same holds at lags 14 and 21."],
    ["Day of week effect on the same residuals",
     "Spread of 6.5 percent between the highest and lowest day. ANOVA F = 1.13, p = 0.34. Kruskal-Wallis p = 0.77."],
], [150, 220]))
story.extend(figure("fig3_weekly.png", 3,
    "No weekly cycle. Panel (a) is the autocorrelation of the deseasonalised logarithm of "
    "concentration; lags 7, 14 and 21 are circled and lie on the decay curve rather than "
    "above it, which is persistence rather than periodicity. The shaded band is the 95 "
    "percent interval for zero. Panel (b) gives the effect of each day of the week on the "
    "same residuals with 95 percent intervals; every interval contains zero."))
story.append(Paragraph(
    "There is a coherent physical reading rather than a null result. A weekly rhythm in "
    "urban particulate concentration is a traffic signature, and station 8118 sits in the "
    "diplomatic enclave rather than at a roadside site such as ITO or Anand Vihar. Its "
    "absence at a site that is not traffic dominated is what one would expect.", body))
story.extend(figure("fig4_annual.png", 4,
    "The annual cycle, by contrast, is unmistakable. Monthly median with the interquartile "
    "range shaded. The median exceeds the hazard threshold in November, December and "
    "January and falls to roughly a sixth of that in the monsoon. This is the structure "
    "the Fourier terms are there to capture, and its strength is the reason the absence in "
    "Figure 3 is credible rather than an artefact of a weak test.", width_frac=0.66))
story.append(Paragraph(
    "<b>Consequence.</b> The classical benchmark becomes ARIMA with annual Fourier terms "
    "as exogenous regressors, with no weekly seasonal order. The specification is simpler, "
    "better identified, and now justified empirically rather than assumed. Two further "
    "points follow. Annual Fourier terms explain 69 percent of the variance of the "
    "logarithm of concentration against considerably less on the raw scale, so the "
    "classical modelling will be done in logs. Four Fourier pairs are used; the Bayesian "
    "information criterion continues to improve to six, but it assumes independent errors "
    "and these residuals are strongly autocorrelated, so it will over-select, and the "
    "order will be treated as a tuning parameter under the rolling origin evaluation "
    "instead.", body))

# ---------------------------------------------------------------- evaluation
story.append(Paragraph("4. Evaluation design", h1))
story.append(Paragraph(
    "The models are the straightforward part of what remains. The evaluation is where the "
    "project can quietly fail, so it is worth setting out now rather than at the end.", body))
story.append(Paragraph(
    "<b>Rolling origin rather than a single split.</b> A model will be fitted on an "
    "expanding window, used to forecast one, two and three days ahead, then refitted with "
    "the origin moved forward. Every forecast is therefore made using only information "
    "that existed at the moment it was issued. This is the fiddliest code in the project "
    "and the easiest place to leak future information into past forecasts, so it will be "
    "built and tested on a short window before being run at length, and it will carry the "
    "same corruption test already used on the feature table: a series is corrupted from a "
    "chosen date onward, and any forecast issued before that date must be unchanged.", body))
story.append(Paragraph(
    "<b>Metrics reported separately at each horizon.</b> Mean absolute error, root mean "
    "squared error, and mean absolute scaled error against the naive forecast. Skill decays "
    "with horizon and averaging across horizons would conceal exactly that.", body))
story.append(Paragraph(
    "<b>The warning system, which is the point.</b> A model with good average error can "
    "still miss the extreme days, and those are the only days anyone acts on. For each "
    "approach the decision threshold will be swept from one extreme to the other, and at "
    "each point the hit rate, the false alarm rate, the precision, and the number of alarms "
    "raised per year will be recorded. That last quantity is what an operator actually "
    "lives with and it is rarely reported. The resulting curve of hit rate against false "
    "alarm rate, with the benchmark operating points marked on it, is the figure the "
    "report is built around.", body))
story.append(Paragraph(
    "<b>Class imbalance handled explicitly.</b> Exceedances are a minority at 29.7 percent "
    "and would be a much smaller minority under the severe threshold. Class weighting and "
    "precision-recall analysis will be used rather than accuracy, and the minority class "
    "will not be resampled, since duplicating days breaks the temporal structure the whole "
    "design depends on.", body))

# ---------------------------------------------------------------- 5
story.append(Paragraph("5. Decisions required", h1))
for i, (q, ctx) in enumerate([
    ("The hazardous threshold.",
     "The scripts currently use 121 microgrammes per cubic metre, the CPCB breakpoint at "
     "which the category becomes very poor, which yields an event rate of 29.7 percent. "
     "The severe breakpoint at 250 would yield a far smaller and more extreme event set "
     "with correspondingly wider confidence intervals on every hit rate. The choice "
     "determines what the warning system is for and it should be settled before modelling "
     "begins."),
    ("Acceptability of the station provenance.",
     "Using a United States diplomatic post monitor rather than the Indian official "
     "network is forced by the CPCB truncation described in Section 2.1. Whether this is "
     "acceptable, and how prominently it should be caveated, is a judgement I would rather "
     "take from you than make alone. A secondary route through the OpenAQ bulk archive "
     "may hold the full CPCB record and is worth an hour of investigation in week 6 as a "
     "robustness check."),
    ("The upper cleaning threshold.",
     "Removing values above 1000 is the weakest assumption in the pipeline. It rests on "
     "seasonal implausibility rather than on a documented instrument limit. The intention "
     "is to rerun the complete analysis without that rule in week 5 and report whether any "
     "conclusion changes, which converts the assumption into a stated robustness check. "
     "Please confirm that is sufficient."),
    ("Scope of the classical comparison.",
     "Given that the two seasonal period problem does not arise, the structural state "
     "space model is no longer required to resolve it. Would you still like it fitted as a "
     "decomposition comparison, or is the effort better spent on the machine learning suite "
     "and the evaluation?"),
], 1):
    story.append(Paragraph(f"<b>{i}. {q}</b> {ctx}", bullet, bulletText="•"))

# ---------------------------------------------------------------- 5
story.append(Paragraph("6. Work remaining", h1))
story.append(Paragraph(
    "Submission is due 22 October 2026. The schedule below front loads the modelling so "
    "that all results are frozen by 30 September, leaving two weeks for writing and one "
    "week of contingency.", body))
story.extend(table([
    ["Week", "Dates", "Work", "Completion criterion"],
    ["1", "20 to 26 Aug", "Data acquisition, cleaning, feature table",
     "Complete, 20 August"],
    ["2", "27 Aug to 2 Sep", "Naive, seasonal naive and climatology benchmarks; ARIMA with Fourier exogenous terms on log concentration",
     "Error metrics at each horizon for every benchmark"],
    ["3", "3 to 9 Sep", "Rolling origin evaluation harness",
     "Benchmarks reproduced under the harness with a passing leakage test"],
    ["4", "10 to 16 Sep", "Penalised regression, random forest, histogram gradient boosting",
     "Research Question 1 answered"],
    ["5", "17 to 23 Sep", "Direct exceedance classification and threshold sweep",
     "Research Questions 2 and 3 answered; hit rate against false alarm rate produced"],
    ["6", "24 to 30 Sep", "Recurrent network; robustness checks; results frozen",
     "No further modelling after 30 September"],
    ["7", "1 to 7 Oct", "First complete draft", "Draft to supervisor"],
    ["8", "8 to 14 Oct", "Revision on supervisor feedback", "Second draft, figures final"],
    ["9", "15 to 21 Oct", "Polish and contingency", "Submission, targeted for 19 October"],
], [26, 62, 152, 130]))

# ---------------------------------------------------------------- 6
story.append(Paragraph("7. Reproducibility", h1))
story.append(Paragraph(
    "Four command line scripts carry the pipeline from an empty folder to the feature "
    "table: acquisition from the OpenAQ interface, a viability and structure check, the "
    "cleaning step, and feature construction. Each accepts a synthetic demonstration mode "
    "and each carries an automated correctness test. The cleaning script alters nothing "
    "unless explicitly instructed, and reports what each rule would remove before it is "
    "applied, so every threshold in Section 2.3 is a recorded decision rather than a "
    "default. Raw and cleaned data are retained under version control so that the analysis "
    "does not depend on the data provider serving identical values at a later date, which "
    "the CPCB finding suggests is not a safe assumption.", body))

doc = SimpleDocTemplate(OUT, pagesize=A4,
                        leftMargin=25*mm, rightMargin=25*mm,
                        topMargin=20*mm, bottomMargin=20*mm,
                        title="MTH5000 Supervision Meeting Brief",
                        author="Jaykumar Vinodbhai Chauhan")
doc.build(story)
print("wrote", OUT)
