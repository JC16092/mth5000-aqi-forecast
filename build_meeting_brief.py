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
    "The modelling is complete and the central result is not the one the proposal "
    "anticipated. Forecast accuracy differs very little between methods, while the "
    "choice of decision threshold changes performance by an order of magnitude more. "
    "At one day ahead, moving from an alarm budget of forty per year to one hundred "
    "raises the hit rate from 0.38 to 0.87. Across every model at a fixed budget of "
    "sixty, the hit rate varies only between 0.52 and 0.57. At three days ahead a "
    "climatological forecast, which uses no recent information whatever, matches the "
    "best model to within four thousandths.", body))
story.append(Paragraph(
    "The recommendation is that the report be built around that finding, with the "
    "model comparison as supporting evidence rather than as the destination. "
    "Sections 2 to 4 describe what was built and why it can be believed; Section 5 "
    "gives the results; Section 6 lists four decisions that require your input.", body))

# ---------------------------------------------------------------- 2
story.append(Paragraph("2. The data", h1))
story.append(Paragraph(
    "Five candidate Delhi stations were compared on coverage rather than on nominal "
    "length of record. Every CPCB station returns measurements only from 19 February "
    "2025, about eighteen months, although the OpenAQ metadata advertises a first "
    "observation in 2016. Four independent stations sharing an identical cutoff is a "
    "systematic limit on what the endpoint serves. Only location 8118 returns the full "
    "record, so it was selected. It is supplied through AirNow and is almost certainly "
    "the United States diplomatic post monitor rather than part of the Indian official "
    "network, which is a limitation to state plainly and is the subject of one of the "
    "questions in Section 6.", body))
story.extend(table([
    ["Property", "Value"],
    ["Source", "OpenAQ location 8118, sensor 23534, provider AirNow"],
    ["Period", "9 November 2016 to 27 August 2026, 9.8 years"],
    ["Usable daily means", "3,093, being 86.4 percent of the calendar"],
    ["Longest gap", "34 consecutive days"],
    ["Days above 121", "920, being 29.7 percent"],
], [125, 245]))

story.append(Paragraph("2.1 Two defects, one of which was silently corrupting the series", h2))
story.append(Paragraph(
    "<b>Physically impossible values.</b> Five negative concentrations, and a maximum "
    "of 1990 which appeared three times identically on unrelated dates, the signature "
    "of a clipped instrument ceiling. One fell on 2 September, in the monsoon, between "
    "neighbouring days of 42 and 178.", body))
story.append(Paragraph(
    "<b>A wrong coverage denominator.</b> OpenAQ reports completeness against an "
    "expected count of 24, assuming hourly reporting. This sensor reported half hourly "
    "from 2016 to 2024 and hourly from 2025. The visible symptom is a completeness "
    "above 100 percent, which is impossible. The damaging one is invisible: a day "
    "holding 24 of a real 48 readings scores as complete, so a mean built from half a "
    "day of a polluted afternoon enters the series as a daily mean. Days at 50 to 75 "
    "percent true coverage produced impossible values about seven times as often as "
    "days above 90 percent. Cadence is now taken from the data itself, using the "
    "ninetieth percentile of observation counts within each year.", body))
story.extend(figure("fig2_coverage.png", 1,
    "The coverage defect. Panel (a): readings per daily mean, with the cadence "
    "estimated from the data each year as the solid line and the fixed denominator of "
    "24 as the dashed line. Panel (b): implausible values by true coverage."))
story.append(Paragraph(
    "Cleaning removed 282 days of 3,375: five negatives, 270 below 50 percent true "
    "coverage, and seven above 1000. The exceedance rate moved only from 30.0 to 27.0 "
    "percent across every candidate rule, so the filter is not selectively removing "
    "the events of interest.", body))

# ---------------------------------------------------------------- 3
story.append(Paragraph("3. A tested assumption that turned out to be false", h1))
story.append(Paragraph(
    "The approved proposal states that daily pollution series carry a weekly cycle "
    "driven by traffic, and the plan treated reconciling a weekly and an annual period "
    "as the central modelling difficulty. Tested three ways on the cleaned series, the "
    "weekly cycle is not present at this station. The periodogram shows the annual "
    "cycle and its harmonics and nothing near seven days. On the deseasonalised "
    "logarithm, lag 7 autocorrelation is 0.173 while lag 6 is 0.179 and lag 8 is 0.153, "
    "so lag 7 lies on the decay curve rather than above it. The day of week effect "
    "spans 6.5 percent with ANOVA p = 0.34.", body))
story.extend(figure("fig3_weekly.png", 2,
    "No weekly cycle. Lags 7, 14 and 21 are circled and sit on the decay curve. Every "
    "day of week interval contains zero."))
story.append(Paragraph(
    "A weekly rhythm in urban particulate concentration is a traffic signature and "
    "station 8118 sits in the diplomatic enclave rather than at a roadside site, so its "
    "absence is coherent rather than missing. The consequence is that the classical "
    "benchmark is ARIMA with annual Fourier terms as exogenous regressors and no weekly "
    "seasonal order. The specification is simpler and now empirically justified. The "
    "benchmark that does assume a weekly cycle is the worst of the seven tried, which "
    "is the quantitative form of the same finding.", body))

# ---------------------------------------------------------------- 4
story.append(Paragraph("4. Why the results can be believed", h1))
story.append(Paragraph(
    "Every model is scored by one shared module on identical days, and every forecast "
    "is produced by one shared loop. A model cannot leak on its own; it can only leak "
    "if the loop permits it, so the loop is what is tested.", body))
story.append(Paragraph(
    "<b>Rolling origin rather than a single split.</b> 2,303 origins from 9 November "
    "2019 to 24 August 2026, spanning 6.8 years, with a three year burn-in, parameters "
    "re-estimated every ninety days and state advanced daily in between. This was not "
    "cosmetic: on a single test block ARIMA scored 0.903 at one day ahead and under "
    "rolling origin it scores 0.940. The single block happened to be calmer than the "
    "training period and was flattering every model.", body))
story.append(Paragraph(
    "<b>An automated leakage test runs before any forecast is produced.</b> The series "
    "is corrupted from a chosen date onward, every model is rerun through the same "
    "loop, and any forecast issued before that date that changes is a failure. It "
    "passes with the state carrying models included, which are the ones that could "
    "plausibly leak.", body))
story.append(Paragraph(
    "<b>One trap specific to supervised learning.</b> At origin t the label on feature "
    "row t prime is the value at t prime plus h, so the training set ends at t minus h, "
    "not at t. A separate model per horizon is required by that arithmetic. The error "
    "would have been three rows per refit and entirely invisible in the output.", body))
story.append(Paragraph(
    "<b>Metrics.</b> Reported separately at each horizon, never averaged. The headline "
    "measure is relative mean absolute error against the persistence forecast on "
    "identical rows, where 1.000 is persistence and below one beats it. Mean absolute "
    "scaled error is reported alongside but reads poorly when test volatility differs "
    "from training volatility, which it does here.", body))

# ---------------------------------------------------------------- 5
story.append(Paragraph("5. Results", h1))

story.append(Paragraph("5.1 Research Question 1: forecast accuracy", h2))
story.extend(table([
    ["Model", "h = 1", "h = 2", "h = 3"],
    ["GRU (range over three seeds)", "0.918 to 0.935", "0.885 to 0.898", "0.840 to 0.879"],
    ["ARIMA with Fourier terms", "0.940", "0.883", "0.832"],
    ["Random forest, change target", "0.962", "0.918", "0.898"],
    ["Gradient boosting, change target", "0.978", "0.937", "0.881"],
    ["Ridge regression", "0.997", "0.952", "0.897"],
    ["Persistence", "1.000", "1.000", "1.000"],
    ["Climatology", "1.415", "1.060", "0.947"],
    ["Seasonal naive, lag 7", "1.759", "1.325", "1.168"],
], [175, 82, 82, 82]))
story.append(Paragraph(
    "The recurrent network is the best model at one day ahead, beating ARIMA under "
    "every initialisation seed tried. ARIMA is the best at two and three days, also "
    "under every seed. So the machine learning wins at the shortest horizon and the "
    "classical model wins as the horizon lengthens. That is consistent with the "
    "mechanism: the network exploits short range nonlinear structure, while at longer "
    "horizons the seasonal component dominates and the Fourier terms carry it more "
    "cleanly. The tree models beat persistence but not ARIMA at any horizon, and "
    "modelling the change rather than the level improves them, because trees cannot "
    "extrapolate beyond the targets they were trained on and this series drifts "
    "downward across the decade.", body))
story.append(Paragraph(
    "The network is reported as a range because the spread across seeds is 0.017 at one "
    "day, 0.013 at two and 0.039 at three. At three days that spread exceeds the gap "
    "between the network and five of the other models. A single seed neural network "
    "number is not a result.", body))
story.append(Paragraph(
    "<b>The first version of this result was wrong and is worth reporting as such.</b> "
    "With fixed hyperparameters, gradient boosting scored 1.152 at one day ahead, worse "
    "than persistence. A check on validation showed the configuration was overfitting: "
    "400 boosting iterations over 31 leaf nodes gave 1.085, while four leaf nodes over "
    "200 iterations gave 0.970. Capacity is now selected at every refit from a small "
    "explicit grid, scored on the last fifth of the training window held out in time "
    "order. Gradient boosting improved to 1.007 at h = 1 and 0.886 at h = 3, and the "
    "conclusion survived. A negative result about a model class is worth nothing until "
    "it has been shown not to be a negative result about one's own hyperparameters.", body))

story.append(Paragraph("5.2 Research Question 3: the decision threshold", h2))
story.append(Paragraph(
    "Holding the event fixed at the health threshold and sweeping the decision "
    "threshold gives, at one day ahead, the best hit rate available within a given "
    "budget of alarms per year:", body))
story.extend(table([
    ["Alarms per year", "40", "60", "80", "100"],
    ["Best hit rate available", "0.377", "0.567", "0.727", "0.873"],
], [130, 60, 60, 60]))
story.append(Paragraph(
    "Against that, the hit rate at a fixed budget of sixty alarms per year, by model:", body))
story.extend(table([
    ["Model", "h = 1", "h = 3"],
    ["Gradient boosting", "0.573", "0.535"],
    ["Logistic classifier", "0.571", "0.493"],
    ["ARIMA with Fourier terms", "0.567", "0.533"],
    ["Persistence", "0.558", "0.524"],
    ["Climatology", "0.521", "0.537"],
], [175, 80, 80]))
story.append(Paragraph(
    "<b>The spread across alarm budgets is about fifty points of hit rate. The spread "
    "across models is about five.</b> At three days ahead climatology, which uses no "
    "recent information at all, matches the best model. The operational question of "
    "what alarm burden can be justified dominates the modelling question by an order of "
    "magnitude.", body))
story.extend(figure("fig5_warning.png", 3,
    "The trade-off, by horizon. The top row is hit rate against false alarm rate; the "
    "bottom row replaces the false alarm rate with alarms raised per year, which is the "
    "unit an operator budgets in. The curves very nearly coincide, which is the "
    "finding. They have deliberately not been separated for legibility."))

story.append(Paragraph("5.3 Research Question 2: the two arms", h2))
story.append(Paragraph(
    "Neither arm dominates. Forecasting the concentration and then applying a threshold "
    "wins at some combinations of horizon and alarm budget, direct classification at "
    "others, and no pattern in the winners survives inspection. Given a tie on accuracy, "
    "the recommendation is to prefer the forecast then threshold arm on other grounds: "
    "it produces a concentration, which can be rethresholded for any future health "
    "policy without refitting, whereas a classifier is welded to the threshold it was "
    "trained on. That argument should be stated explicitly rather than presenting a coin "
    "flip as a result.", body))

# ---------------------------------------------------------------- 6
story.append(Paragraph("6. Decisions required", h1))
for i, (q, ctx) in enumerate([
    ("The hazardous threshold.",
     "The analysis uses 121 microgrammes per cubic metre, the CPCB breakpoint at which "
     "the category becomes very poor, giving an event rate of 29.7 percent. The severe "
     "breakpoint at 250 would give a far smaller and more extreme event set with "
     "correspondingly wider confidence intervals on every hit rate. Rerunning at 250 is "
     "an afternoon's work if you would prefer it, or a sensitivity analysis if you would "
     "prefer both."),
    ("Acceptability of the station provenance.",
     "Using a United States diplomatic post monitor rather than the Indian official "
     "network is forced by the CPCB truncation in Section 2. Whether that is acceptable, "
     "and how prominently it should be caveated, is a judgement I would rather take from "
     "you. The OpenAQ bulk archive may hold the full CPCB record and is worth an hour of "
     "investigation as a robustness check."),
    ("Which back-transform to report.",
     "The model is fitted on the logarithm. Exponentiating the fitted mean gives the "
     "median of the concentration and under-forecasts by 6.4 at one day and 9.5 at three; "
     "the bias corrected form is unbiased at +1.3. They are indistinguishable on mean "
     "absolute error, the corrected form is better on root mean squared error, and as a "
     "warning system it catches more, 0.932 against 0.900, at 116 alarms per year against "
     "107. A systematic tendency to under-forecast seems the wrong failure mode for a "
     "hazard warning, but the choice should be argued rather than assumed."),
    ("How many seeds to report for the network.",
     "The recurrent network was nearly dropped on the grounds that it was unlikely to "
     "matter, and it turned out to be the best model at one day ahead. Its results vary "
     "with initialisation by up to 0.039 of relative error, so the intention is to run "
     "five seeds and report the range rather than a point. Please confirm that is the "
     "standard you want, since it makes the table harder to read but the claim harder "
     "to dispute."),
], 1):
    story.append(Paragraph(f"<b>{i}. {q}</b> {ctx}", bullet, bulletText="\u2022"))

# ---------------------------------------------------------------- 7
story.append(Paragraph("7. What remains", h1))
story.append(Paragraph(
    "Modelling freezes at the end of September. Remaining: the sensitivity analysis "
    "rerunning the pipeline without the upper cleaning threshold, the optional recurrent "
    "network subject to the question above, and the report itself, with a full draft "
    "intended for you in the first week of October. The pipeline runs end to end from an "
    "empty folder in eight scripts, each with an automated correctness test, so any "
    "change you ask for can be propagated through every result in an afternoon.", body))

doc = SimpleDocTemplate(OUT, pagesize=A4,
                        leftMargin=25*mm, rightMargin=25*mm,
                        topMargin=20*mm, bottomMargin=20*mm,
                        title="MTH5000 Supervision Meeting Brief",
                        author="Jaykumar Vinodbhai Chauhan")
doc.build(story)
print("wrote", OUT)
