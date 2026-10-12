"""Build a PDF giving Dr Tian the full detail behind two follow-up
questions: the GRU reproducibility finding, and the Kolmogorov-Arnold
Network scope decision. Unlike the earlier evaluation-criterion PDF,
this one is meant to be read WITH full detail, since the point is for
him to check the handling, not form an unprejudiced opinion from
scratch. No em dashes, matching this project's documented style.

    python3 build_review_items.py
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

OUT = "MTH5000_Review_Items.pdf"

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

story.append(Paragraph("Two Items for Review Before Submission", title))
story.append(Paragraph("A reproducibility finding, and a scope decision", subtitle))
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
story.append(Paragraph("Prepared 12 October 2026", block))
story.append(Spacer(1, 12))

# ---------------------------------------------------------------------------
story.append(Paragraph("1. The GRU Reproducibility Finding", h1))

story.append(Paragraph("What was found", h2))
story.append(Paragraph(
    "The full modelling pipeline was rerun from the cleaned data, under the "
    "exact same code and the same fixed random seeds already used to "
    "produce the report's numbers. Every classical and tree-based model "
    "reproduced its score exactly, bit for bit. The recurrent network "
    "(GRU) did not: its score on rerun moved by nearly as much as the "
    "ordinary gap between two genuinely different seeds, even though "
    "nothing about the data, the code, or the seed had changed.", body))

story.append(Paragraph("What it affected", h2))
story.append(Paragraph(
    "The network, with weather covariates added, had looked under an "
    "initial five seeds like a clear win over ARIMA at both two and three "
    "days ahead. A second, independent batch of five seeds (ten in total) "
    "told a different story at both horizons:", body))
story.append(Paragraph(
    "At two days ahead: 3 of 10 seeds beat ARIMA clearly, 6 are "
    "indistinguishable from it within this project's own measured noise "
    "floor, and 1 is a clear loss.", bullet))
story.append(Paragraph(
    "At three days ahead: 3 of 10 beat ARIMA clearly, 2 are ties, and 5, "
    "a majority, are clear losses, including one seed 0.041 worse than "
    "ARIMA on the same relative error scale used throughout the report.",
    bullet))
story.append(Paragraph(
    "Under the first five seeds alone, both horizons had looked like a "
    "win for the network. That reading did not survive the second, "
    "independent batch of five.", body))

story.append(Paragraph("Likely cause", h2))
story.append(Paragraph(
    "The classical and tree-based models are each fit by a single, "
    "deterministic optimisation. The network is trained over many epochs "
    "of multi-threaded floating-point arithmetic, where small "
    "non-associativity in summation order compounds across epochs. "
    "Nothing else in the suite trains this way, which is consistent with "
    "the network being the only model affected.", body))

story.append(Paragraph("How it was handled", h2))
story.append(Paragraph(
    "The seed count was doubled from five to ten. The network's result is "
    "reported throughout the report as the range across all ten seeds, "
    "never as a single seed's point estimate, the same rule already "
    "applied to its un-augmented version. Every number anywhere in the "
    "report that depended on a tree-based model or the GRU was re-checked "
    "against the fresh run rather than left as previously written. The "
    "finding itself is stated directly in the Limitations chapter, as a "
    "property of the network's training on this hardware, not hidden "
    "behind the improved seed count.", body))

story.append(Paragraph(
    "The question: does this resolution, doubling the sample until the "
    "picture stopped moving and stating the limitation outright, seem "
    "like the right way to have handled this, or is there something you "
    "would want done differently before submission?", body))

# ---------------------------------------------------------------------------
story.append(Paragraph("2. The Kolmogorov-Arnold Network", h1))

story.append(Paragraph(
    "A Kolmogorov-Arnold Network (KAN) was an early stretch-goal "
    "candidate, a more recent neural architecture that replaces a "
    "standard network's fixed activation functions with learned "
    "functions on the edges of the network. It was never formally "
    "decided either way, and no implementation of it exists in this "
    "project's code.", body))

story.append(Paragraph(
    "Adding it properly, rather than as a token gesture, would mean "
    "building a new model class, integrating it into the same "
    "rolling-origin evaluation harness every other model shares, and "
    "holding it to the same standard already applied to the GRU: multiple "
    "seeds, the same significance testing, and the same scrutiny that "
    "surfaced the reproducibility finding above. That is a comparable "
    "amount of work to the GRU's own treatment, not a small addition, and "
    "nineteen days remain to the 31 October deadline.", body))

story.append(Paragraph(
    "The question: given the time remaining, is a Kolmogorov-Arnold "
    "Network comparison worth attempting at reduced scope, or should the "
    "report's model suite be finalised without it?", body))

doc = SimpleDocTemplate(OUT, pagesize=A4,
                        topMargin=22 * mm, bottomMargin=22 * mm,
                        leftMargin=25 * mm, rightMargin=25 * mm)
doc.build(story)
print(f"Wrote {OUT}")
