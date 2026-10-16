"""Build a PDF summarising what was actually done in response to Dr
Tian's second review email: the GRU sensitivity check, the LSTM
comparison, and the two bounded architecture checks. Unlike the earlier
evaluation-criterion PDF, this one reports real results, since the
point is to show him what was found, not to ask an unprejudiced
question. No em dashes, matching this project's documented style.

    python3 build_tian_response.py
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

OUT = "MTH5000_Response_to_Second_Review.pdf"

title = ParagraphStyle("title", fontName="Times-Bold", fontSize=15, leading=19,
                       alignment=TA_CENTER, spaceAfter=2)
subtitle = ParagraphStyle("subtitle", fontName="Times-Roman", fontSize=11.5,
                          leading=15, alignment=TA_CENTER, spaceAfter=10)
block = ParagraphStyle("block", fontName="Times-Roman", fontSize=10.5, leading=13.5,
                       alignment=TA_CENTER, spaceAfter=1)
h1 = ParagraphStyle("h1", fontName="Times-Bold", fontSize=12.5, leading=16,
                    spaceBefore=14, spaceAfter=5)
h2 = ParagraphStyle("h2", fontName="Times-Bold", fontSize=11, leading=14,
                    spaceBefore=9, spaceAfter=3)
body = ParagraphStyle("body", fontName="Times-Roman", fontSize=11, leading=15,
                      alignment=TA_JUSTIFY, spaceAfter=7)
bullet = ParagraphStyle("bullet", parent=body, leftIndent=12, spaceAfter=4)

story = []

story.append(Paragraph("Response to Your Second Review", title))
story.append(Paragraph(
    "GRU sensitivity, the LSTM comparison, and two bounded architecture checks",
    subtitle))
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
story.append(Paragraph("Prepared 16 October 2026", block))
story.append(Spacer(1, 12))

story.append(Paragraph(
    "Thank you for the detailed reply. This summarises what was actually "
    "done in response to each point, and what it found.", body))

story.append(Paragraph("1. GRU Sensitivity to Optimiser and Learning Rate", h1))
story.append(Paragraph(
    "Checked directly with a bounded sensitivity sweep, the same design "
    "already used for the GRU's hidden-size and sequence-length check. "
    "At one and two days ahead the default setting, Adam at a learning "
    "rate of 0.01, is at or near the best configuration tried. At three "
    "days ahead it is not: switching to SGD with momentum improves the "
    "mean error by about two points, with a tighter spread across seeds "
    "as well. This is the third separate sensitivity check, after "
    "architecture and Fourier harmonics, to flag three days ahead "
    "specifically as the GRU's weakest-tuned configuration, now stated "
    "together in the report's Limitations.", body))
story.append(Paragraph(
    "One part of the question does not apply to this architecture: a "
    "GRU's gate activations are fixed by the architecture itself, "
    "sigmoid and tanh, not a tunable choice the way a plain feed-forward "
    "layer's activation is, so “activation function” was not a "
    "free parameter to sweep.", body))

story.append(Paragraph("2. The LSTM Comparison", h1))
story.append(Paragraph(
    "This is the result that matters most. An LSTM was built and fitted "
    "under the exact same protocol as the GRU, the same channels, the "
    "same window, the same training setup, the same ten random seeds, "
    "and carried through the full rolling-origin evaluation rather than "
    "a bounded check.", body))
story.append(Paragraph(
    "The LSTM beats the GRU at every horizon: by 0.005 of relative error "
    "at one day ahead, 0.008 at two, and 0.013 at three, despite "
    "carrying roughly a third more parameters, 3,097 against 2,329. "
    "That result tests directly, and does not support, the reasoning "
    "the report originally gave for choosing the smaller architecture, "
    "that fewer parameters should matter more on a series this size. "
    "The report's Literature Review has been corrected to say so "
    "plainly rather than leave the original reasoning standing.", body))
story.append(Paragraph(
    "Against ARIMA, the LSTM's own picture closely mirrors the GRU's: a "
    "clear win at one day ahead (ahead in all ten seeds, reaching formal "
    "significance in five of them), a near-tie at two days, and a "
    "narrow ARIMA win at three days, with no seed reaching significance "
    "at either of the longer horizons.", body))

story.append(Paragraph("3. Two Further Architectures, as Bounded Checks", h1))
story.append(Paragraph(
    "Both were run as a single-split, three-seed check, the same bounded "
    "design already used elsewhere in this report for a first look at a "
    "question, rather than the full ten-seed treatment given to the GRU "
    "and the LSTM. Building either one to that full standard would be a "
    "comparable amount of work to the LSTM's own treatment.", body))
story.append(Paragraph("A small transformer encoder.", h2))
story.append(Paragraph(
    "Your suggestion was conditional on data size, a transformer if the "
    "data is large; this project's data, about three thousand daily "
    "observations, is not, and the report's own Literature Review argues "
    "against a transformer on that basis. On the bounded check it does "
    "not beat ARIMA at any horizon, consistent with that argument. It is, "
    "however, more competitive with the GRU on this same comparison than "
    "the argument predicts, ahead of it at one and three days "
    "specifically.", body))
story.append(Paragraph("A Kolmogorov-Arnold Network, as a KAN-LSTM hybrid.", h2))
story.append(Paragraph(
    "Built exactly as you described it, an LSTM backbone with its usual "
    "linear output layer replaced by a Kolmogorov-Arnold layer. No "
    "maintained library exists for this the way one does for a GRU or "
    "LSTM, so the layer was implemented from the published construction "
    "and checked in isolation, confirming it can learn a nonlinear "
    "target, before being fitted on real data at all. It trained stably "
    "across all three seeds, with no divergence, which was a real risk "
    "going in. On the bounded check it is competitive with the other "
    "architectures without a dramatic win or loss in either direction, "
    "the worst of the four at one day ahead, the best at two.", body))

story.append(Paragraph("What Changed in the Report", h1))
story.append(Paragraph(
    "A new Methodology subsection gives the LSTM's full architecture "
    "and training details; its results sit alongside the GRU's "
    "throughout the Results chapter and its own row in the significance "
    "table. The GRU optimiser finding, the LSTM's results, and both "
    "bounded checks are stated in Limitations, and Future Work now "
    "includes completing the LSTM's own weather and threshold-sweep "
    "treatment and extending the two bounded checks to the full ten-seed "
    "evaluation. The report now compiles to 70 pages.", body))

doc = SimpleDocTemplate(OUT, pagesize=A4,
                        topMargin=22 * mm, bottomMargin=22 * mm,
                        leftMargin=25 * mm, rightMargin=25 * mm)
doc.build(story)
print(f"Wrote {OUT}")
