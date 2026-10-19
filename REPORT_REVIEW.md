# Page-by-Page Review — MTH5000 Report (`main.pdf`, 74 pages)

Reviewed as if by an external examiner, one PDF page at a time. Each entry
covers: what's good, what could be stronger, and a rigorous/viva-style note
on anything an examiner might actually press on. Entries for dense content
pages are longer; entries for a page that's mostly a single table or figure
are shorter on purpose, to avoid manufacturing commentary where there isn't
any — that would be padding, not rigor.

Printed page numbers (roman for front matter, arabic from Chapter 1) are
given alongside the PDF page number, since they differ.

## Summary: What to Actually Do With This

74 individual entries is a lot to act on directly, so here's the
prioritized version. The overall verdict first: this report is in strong
shape. The mathematics is correct throughout (independently re-verified
against the actual code, not just read), the bibliography is exact (49
cited, 49 entries, no orphans), and the report's defining characteristic
— reporting findings that got *less* favourable under more scrutiny
(the weather-GRU result, the cleaning-threshold check, the bit-
reproducibility discovery) rather than only the ones that confirm the
thesis — is the single strongest thing about it and worth knowing is
there, not just assuming.

**Worth fixing, in order:**

1. **The Literature Review's own chapter summary (p.24) contradicts its
   own chapter body (p.20).** The body correctly says the GRU-over-LSTM
   parameter-count reasoning was tested and not supported; the chapter's
   summary of itself states the same reasoning as settled. This is the
   most important finding in this whole review — not because it's hard to
   fix (one sentence), but because a reader who only skims chapter
   summaries would come away with the wrong impression of what the
   chapter found.
2. **§2.3.1's opening line (p.18)** still says "the single architecture
   this project fits" — stale against the three architectures actually
   fitted, missed by four previous fix rounds because those all searched
   for "recurrent"-specific phrasing rather than "single architecture."
3. **Table 4.7's two sharpest illustrative numbers aren't independently
   checkable (p.55).** I verified both against the raw data directly and
   they're correct, but a reader without code access has to take the
   $h=3$ claims on faith, unlike the $h=1$ claims which are in the printed
   table. Worth a small supplementary table or footnote.
4. **The Discussion chapter's pacing (pp.59–65).** Every individual
   caveat is well-argued and honestly reported; stacked across six dense
   pages with the reassuring synthesis arriving only at the very end, a
   reader could come away more alarmed about the report's rigor than the
   evidence warrants. A one-sentence signpost at the start of §5.2 and
   §5.3 would fix this without cutting any content.
5. **The transformer's hyperparameters were never sensitivity-checked
   (p.41),** unlike the GRU's three separate bounded checks. The report
   discloses this honestly but doesn't yet have a ready answer for the
   obvious follow-up ("so how much should I trust these numbers?") —
   worth having one before a viva, even if nothing in the report changes.

**Already fixed, across this session's earlier passes** (not reproduced
page-by-page above except where directly relevant): the AI-tool-use
declaration is still the one item that's a different *kind* of risk from
everything else here and remains the user's call, not a text fix. The
multiple-comparisons disclosure, the hardcoded cleaning table, the stale
README, three rounds of stale "recurrent network" references, and a
caption with the wrong seed count were all found and fixed in earlier
passes this session and are reflected as already-correct in the relevant
page entries below.

---

## Front Matter

### PDF p.1 — Title page
**Content:** Title, name/ID/degree/unit/supervisor/school, date.

**Good:** Clean, correctly formatted, matches the standard title-block
convention for this degree. No clutter.

**Could be better:** The date line is `\date{\today}`, which means it
silently re-stamps itself to whatever day `tectonic` was last run — right
now it reads "October 19, 2026" purely because that's when this PDF was
built, not because that's a meaningful date. If this gets recompiled once
more the morning of submission, that's fine and arguably correct; but if
it's recompiled for an unrelated reason after submission (e.g. to generate
a clean copy for the viva) the date will silently drift away from the
actual submission date. Low stakes, but worth pinning to a fixed date
(`\date{31 October 2026}` or similar) once the report is actually final,
rather than leaving it live.

**Examiner's eye:** Nothing to press on here. A title page is not where
rigor gets tested, but a reviewer who notices the date doesn't match the
submission portal's timestamp might wonder why — cheap thing to avoid.

---

### PDF p.2 (printed i) — Abstract
**Content:** The full abstract, ~290 words.

**Good:** Leads with the actual finding (alarm budget dominates model
choice) rather than "this report investigates..." throat-clearing, which
is exactly right — a reader should get the conclusion first. Every claim
in it is backed by a number stated later in the report; nothing here is
asserted without support. The GRU/LSTM/transformer sentence is dense but
accurate, and correctly flags that the transformer's inclusion was a
direct response to supervisor feedback rather than a planned comparison,
which is honest framing a marker will likely appreciate.

**Could be better:** It's one unbroken paragraph of close to 300 words.
Every sentence individually earns its place, but as a block it's a lot to
parse in one sitting, especially the GRU/LSTM/transformer sentence, which
is doing three jobs at once (report the ranking, report the parameter-count
reversal, report the significance result). A reader skimming only the
abstract — which, realistically, includes a marker deciding how carefully
to read the rest — might come away with the headline finding but lose the
secondary ones in the density. Splitting after "...moves the hit rate by
fifty" (closing the RQ3 point) into a second paragraph for the
model-comparison findings, and a third for the weather/robustness checks,
would cost nothing and make it easier to skim without losing any content.

**Examiner's eye:** The claim "carries the strongest formal significance
against ARIMA of the three at one day ahead" is true at face value
(7 of 10 transformer seeds reach nominal significance, against 5 for the
LSTM and 4 for the GRU) but the report's own Section 3.8 now states that
*none* of the three networks' best-seed results survive a Bonferroni
correction across the 27 tests run in this report. The abstract doesn't
carry that caveat, which is defensible — abstracts conventionally state
the headline reading, not every qualifier — but be ready to explain the
gap if asked: "strongest" here means strongest among three results that
are all, strictly, below the bar once you correct for how many times the
test was run.

---

### PDF p.3 (printed ii) — Table of Contents, part 1
**Content:** Chapters 1–3 (through Methodology §3.1–3.2).

**Good:** Numbering is consistent, every entry has a page number, nothing
orphaned. The six-chapter structure reads as a genuine thesis shape, not a
padded article.

**Could be better:** Nothing substantive — this is machine-generated by
LaTeX and there's very little a student controls here beyond chapter
titles, which are already clear and descriptive.

**Examiner's eye:** None. A ToC is checked for completeness, not argued
with.

---

### PDF p.4 (printed iii) — Table of Contents, part 2
**Content:** Chapters 3 (continued) through 4.

**Good:** Same as above — the Methodology subsection titles ("The Gated
Recurrent Unit," "The Long Short-Term Memory Network," "The Transformer")
read as a clear, parallel progression, which telegraphs the chapter's
argument (three architectures treated identically) before a reader even
reaches it.

**Could be better:** Nothing worth flagging.

**Examiner's eye:** None.

---

### PDF p.5 (printed iv) — Table of Contents, part 3
**Content:** Chapters 5–6 (Discussion, Conclusion).

**Good:** Short and proportionate — Discussion and Conclusion together are
four sections each, which is right-sized relative to the six-section
Methodology chapter. The ToC itself is indirect evidence the chapter
balance is sound: nothing here looks padded or thin.

**Could be better:** Nothing substantive.

**Examiner's eye:** None.

---

### PDF p.6 (printed v) — List of Figures
**Content:** All 7 figures listed with full captions.

**Good:** Every caption is descriptive enough to understand the figure
without opening the page — several captions actually state the finding
("The curves very nearly coincide, which is the finding"), which is
unusual and good practice; most students write purely mechanical captions.
Checked this page against a rendering, not just the source: it's visually
clean, properly justified, no overflow despite the LaTeX log's own
`Overfull \hbox (2.74pt)` warning on this exact page — confirmed that
warning is genuinely sub-pixel and invisible, not hiding a real layout
problem.

**Could be better:** Nothing on the page itself. One structural note that
belongs here rather than anywhere else: there are only 7 figures across a
74-page, six-chapter report. That's not necessarily wrong — several of the
report's findings are inherently tabular (significance tests, budget
sweeps) rather than visual — but a marker skimming the List of Figures
before reading anything else will form an impression of how
visually-argued the report is, and "7" is on the lean side for this much
content. Not a fix so much as a thing to be aware of walking into a viva
where slides will carry more visuals than the report does.

**Examiner's eye:** None beyond the above.

---

### PDF p.7 (printed vi) — List of Tables
**Content:** All 9 tables listed with full captions.

**Good:** Same discipline as the List of Figures — informative captions,
not mechanical ones.

**Could be better:** Nothing on the page itself now (Table 4.5's caption
used to say "five network seeds" here, which has just been corrected to
"ten").

**Examiner's eye:** This is the one place in the front matter that
actually caught a real bug this session — the List of Tables surfaces a
caption's numbers the same way the full chapter does, so it's worth
treating as a second place to sanity-check reported counts, not just a
mechanical index.

---

### PDF p.8 (printed vii) — List of Symbols, part 1
**Content:** General notation + Seasonality Analysis + start of ARIMA
notation block.

**Good:** The project went to real trouble here that most student reports
skip entirely: every symbol that gets reused for a genuinely different
quantity elsewhere in the report is flagged inline ("$k$ here is reused
later as the AIC parameter count, the Fourier harmonic index, and the
Diebold-Mariano lag index, each unrelated to this one"). That's the kind
of thing a careless report gets silently wrong and a careful one states
up front. Grouping by first-use section rather than alphabetically is the
right call given how much notation this report carries across four
different method families.

**Could be better:** This is a 5-page List of Symbols (pp. vii–xi) for a
report whose core content runs about 60 pages. That's proportionate given
the genuine notation density across ARIMA, three ML methods, three neural
architectures and a significance test, but it does mean a reader hits five
pages of pure reference material before reaching Chapter 1 — worth being
aware that's a real front-matter cost, even though each individual page is
well executed.

**Examiner's eye:** None on this page specifically; the reused-symbol
flagging is exactly the kind of thing that heads off a viva question
before it's asked.

---

### PDF p.9 (printed viii) — List of Symbols, part 2
**Content:** Ridge, Random Forest, Gradient Boosting notation.

**Good:** Same standard maintained — every collision flagged
("$\beta_k$ is unrelated to ridge's coefficient vector $\beta$ below,"
"$B$ ... distinct from ARIMA's backshift operator $B$ above").

**Could be better:** Nothing specific.

**Examiner's eye:** None.

---

### PDF p.10 (printed ix) — List of Symbols, part 3
**Content:** The Gated Recurrent Unit, The Long Short-Term Memory Network.

**Good:** Consistent with the rest — the LSTM block correctly states which
symbols carry over unchanged from the GRU block rather than restating
them, which is the right amount of economy.

**Could be better:** Nothing specific.

**Examiner's eye:** None.

---

### PDF p.11 (printed x) — List of Symbols, part 4
**Content:** The Transformer notation block, in full.

**Good:** This is the newest material in the List of Symbols and it holds
to the same standard as everything written months earlier — same
collision-flagging discipline for $pos$/$i$ against the Gradient
Boosting block's row index $i$, same "reused unchanged" closing line for
$d$. That consistency across a notation block added under deadline
pressure late in the project, matching one built carefully much earlier,
is a genuinely good sign about the report's internal discipline.

**Could be better:** Nothing specific.

**Examiner's eye:** None — if anything this page is evidence *against* a
concern a marker might otherwise have (that late additions get rushed).

---

### PDF p.12 (printed xi) — List of Symbols, part 5 + Evaluation/DM test notation
**Content:** Tail of the Transformer block, Evaluation Measures, Diebold-
Mariano Test notation.

**Good:** Closes out the List of Symbols cleanly; the DM-test notation
block ($\bar d$, $\hat\gamma_k$, $\mathrm{DM}^*$) is complete and matches
exactly what's used in the equations later, which I verified directly
rather than assumed.

**Could be better:** Nothing specific.

**Examiner's eye:** None.

---

## Chapter 1: Introduction

### PDF p.13 (printed 1) — §1.1 Research Background, start of §1.2
**Content:** Health motivation, forecasting feasibility, personal
motivation paragraph, opening of the Research Problem.

**Good:** The opening doesn't waste a sentence — health harm, why early
warning matters, what structure in the data makes forecasting feasible at
all, in three tight sentences backed by two citations. The personal-
motivation paragraph is short (4 sentences) and doesn't overreach into
sentiment; it states a genuine stake and moves on, which is the right
length for a mathematics capstone that isn't primarily a personal essay.
This paragraph was carried over verbatim from the original approved
proposal, so it's already been seen and implicitly accepted by the
supervisor once — not a new risk.

**Could be better:** "Fine particulate matter small enough to be
classified as PM2.5" is a slightly awkward construction — PM2.5 *is* the
size classification, so this reads as circular on a close read ("matter
small enough to be classified as [a size classification]"). "Fine
particulate matter, PM2.5" or "Particulate matter under 2.5 micrometres in
diameter (PM2.5)" would be crisper. Minor, but it's the first full
sentence of the report after the Abstract, so it's worth the two-word fix.

**Examiner's eye:** None — the citations check out and the claim they
support (health harm) is uncontroversial and well-sourced.

---

### PDF p.14 (printed 2) — §1.2 (cont.), §1.3 Research Objectives, §1.4 Research Questions
**Content:** Rest of the Research Problem, the three Objectives, the three
Research Questions.

**Good:** The Objectives map one-to-one onto the Research Questions, which
map one-to-one onto the chapter structure revealed on the next page — this
is a tightly architected introduction, not three independently-drafted
lists that happen to share a chapter. "The answer to the third question
turns out to dominate the other two, and the report is organised
accordingly" is a nice piece of honest foreshadowing: it tells the reader
what's coming without spoiling the specific numbers, and it signals the
report knows its own center of gravity rather than treating all three RQs
as equally weighted after the fact.

**Could be better:** Objective 1 describes the data source as "a single,
well-characterised Indian monitoring station." Read literally this just
means "a station located in India," which is true, but the Data Collection
section later makes a point of stating plainly that the station is
actually a US diplomatic post instrument (AirNow), not part of the Indian
official network — a distinction the report itself treats as worth
flagging "plainly" rather than leaving implicit. There's a slight tension
between this early framing and that later correction. Not wrong, but
swapping "Indian monitoring station" for "Delhi monitoring station" here
would remove any appearance of glossing over something the report is
honest about two chapters later.

**Examiner's eye:** RQ1 is phrased neutrally ("how accurately can X be
forecast by machine learning, relative to classical and naive
benchmarks") rather than presupposing machine learning wins — good, since
the actual finding is mostly the opposite. No leading language to defend
against here.

---

### PDF p.15 (printed 3) — §1.5 Research Significance, §1.6 Structure of the Report
**Content:** Practical and methodological significance, chapter-by-chapter
roadmap.

**Good:** This page shows the fix from earlier in this session landed
correctly — "a model suite spanning classical statistics, machine
learning, and three deep learning architectures" now correctly reflects
GRU + LSTM + transformer rather than the old singular "a deep recurrent
architecture." The Structure paragraph is accurate against what the
report actually delivers chapter by chapter, which I've now checked
directly rather than assumed.

**Could be better:** Nothing substantive. "The methodological significance
lies in applying a leakage-tested rolling-origin evaluation... on a
dataset small enough that the comparison between method families is
itself informative" is a genuinely good sentence — it states the
project's real methodological contribution (not "I built a transformer,"
but "I ran a leak-proof, honest comparison on a sample size small enough
that the comparison itself teaches something general") — precise and not
oversold.

**Examiner's eye:** None.

---

## Chapter 2: Literature Review

### PDF p.16 (printed 4) — §2.1 Air Quality Forecasting: Challenges and Characteristics, start of §2.2
**Content:** The three statistical properties of the data (right-skewed,
annually seasonal, minority-class event), each tied to a later
methodological choice; opening of the ARIMA/Box-Jenkins discussion.

**Good:** §2.1 is a model of economy — three sentences state the three
properties of the data that motivate, respectively, working in logs,
testing (not assuming) seasonality, and evaluating as a warning system,
each with a forward cross-reference to exactly where it's addressed. A
reader knows the shape of the whole methodological argument before
Chapter 2 is three paragraphs old. The ARIMA/Box-Jenkins framing that
follows is standard and correctly sourced.

**Could be better:** Nothing on this page specifically.

**Examiner's eye:** None.

---

### PDF p.17 (printed 5) — §2.2 (cont.): penalised regression, trees, the M3/M4/M5 synthesis
**Content:** Ridge, random forest, gradient boosting lineage; the
forecasting-competition literature (M3, M4, M5) and what it predicts about
ML vs. classical methods on a small sample.

**Good:** This is the strongest page in the Literature Review, and one of
the strongest in the report. It doesn't just cite M3/M4/M5 as a list — it
builds an actual argument: M4 found flexibility doesn't reliably beat
classical methods on short series; M3 showed this wasn't a fluke of scale;
Siami-Namini's LSTM-vs-ARIMA result is a direct analog in a different
domain; M5 then complicates the picture by showing ML *can* win when there
is real exogenous/hierarchical structure to exploit. The synthesis — "the
deciding factor is not machine learning versus classical methods in the
abstract but whether the series on offer gives a flexible method something
structural to exploit" — is a genuine, citable thesis, not a summary, and
it's the thing that makes the report's own negative ML result *predicted*
by the literature rather than merely consistent with it after the fact.

**Could be better:** `Breiman et al. [2017]` is cited for the classic CART
splitting criterion, which will read slightly unusually to anyone who
knows CART as "the 1984 book" — this is in fact the 2017 Routledge
reprint, cited correctly and with its own DOI, so it's defensible, just
worth being ready to explain if asked why a 1984 methodology carries a
2017 date.

**Examiner's eye:** None beyond the citation-year point above, which is
a non-issue in substance.

---

### PDF p.18 (printed 6) — §2.2 (cont.): hybrids, evaluation methodology; start of §2.3.1
**Content:** The Zhang [2003] hybrid ARIMA-ANN discussion and why this
project doesn't pursue one; Tashman/Hewamalage on single-split optimism;
Hyndman & Koehler on MASE; opening of the Deep Learning Landscape
subsection.

**Good:** Explicitly addressing *why no hybrid* is a good instinct —
hybrids are an obvious alternative a reader familiar with the field would
wonder about, and heading that off here rather than leaving it to a viva
question is exactly right. The rolling-origin justification is strong:
two papers twenty-three years apart making the same methodological
complaint, with this project's own single-split-vs-rolling-origin finding
(ARIMA scoring 0.903 on a single block, 0.940 under the honest harness)
cited as a live instance of exactly the failure mode they describe, not
just a citation for its own sake.

**Could be better:** The opening sentence of §2.3.1 — "Before narrowing to
the single architecture this project fits, it is worth stating why the
others on offer were not chosen" — is stale in exactly the way several
other passages were before this session's fixes. The project doesn't fit
a single architecture; it fits three (GRU, LSTM, transformer), and the
transformer specifically comes *from* the attention-based family this
very sentence is about to argue against choosing. This one wasn't caught
in the last four fix rounds because those searches were for "recurrent"-
specific phrasing, not "single architecture." Worth a small rewrite —
something like "before narrowing to the recurrent family this project
started from" would stay accurate to the chapter's own argumentative
structure (it genuinely does narrow to "recurrent" before arguing GRU vs
LSTM) without the now-false claim that only one architecture was ever
fitted.

**Examiner's eye:** This is a real, findable inconsistency — flagged here
rather than silently fixed, since this review is being kept as a record
of what to act on rather than folded into another silent edit.

---

### PDF p.19 (printed 7) — §2.3.1 (cont.): MLP, CNN, Transformer landscape; narrowing to recurrent
**Content:** Why an MLP and a CNN weren't chosen; the Transformer
discussion including the corrected small-data argument; the closing
paragraph narrowing to the recurrent family.

**Good:** The MLP and CNN arguments are both genuinely mechanistic, not
just "we didn't use this": the MLP argument is that it would collapse to
the same feature-table approach already used for ridge/RF/GBM, adding
nothing new; the CNN argument is that its main advantage (automatic
pattern detection) is specifically undercut by this project's own choice
to hand the annual cycle to every model as Fourier terms. These are real
arguments a reader can evaluate, not hand-waving. The Transformer
paragraph is the most heavily revised passage in the whole report this
session, and it reads well: states the original a priori argument,
states Dr Tian's challenge to it precisely (the series is "some four
thousand days long counting every evaluation block"), and states the
result plainly ("does not support the argument above as stated") without
either hiding the original reasoning or pretending it was never made.

**Could be better:** The closing paragraph ("Weighed against all three...")
has already been patched once this session to add "an expectation Section
3.5.3 tests directly rather than confirms" — the patch is honest but the
sentence is now quite long and doing a lot of work (stating the original
three-way comparison *and* flagging that one leg of it was later
overturned, in one breath). Not wrong, just dense; a reader has to hold
three sub-clauses in mind at once. If there's a later polish pass, this
is a candidate for splitting into two sentences rather than one more
clause-insertion.

**Examiner's eye:** None beyond what's already noted — the content is
accurate, just getting syntactically loaded from successive honest
corrections layered onto the same sentence.

---

### PDF p.20 (printed 8) — §2.3.2 RNNs and the Vanishing Gradient Problem, §2.3.3 The Gated Recurrent Unit
**Content:** Vanishing-gradient theory (Bengio 1994), LSTM's response to
it; the GRU's a priori parameter-count appeal and its correction.

**Good:** The vanishing-gradient explanation is pitched exactly right for
a Literature Review — precise enough to be meaningful ("the conditions
which let a recurrent network store information robustly... are,
under gradient descent, precisely the conditions under which the
gradient... either vanishes or explodes") without duplicating the full
derivation, which correctly waits for Methodology. The GRU paragraph is
the single best model in the entire report for how to handle a
corrected a priori argument: states the original reasoning, states
plainly that it was tested, states the result without hedging ("an LSTM
outperforms the GRU at every horizon... so the parameter-count argument...
is not what this project's own evidence supports"). This is the exact
pattern the §2.3.1 fix flagged two pages ago should imitate.

**Could be better:** Nothing on this page itself.

**Examiner's eye:** The claim that missing-value representation is "a
practical limitation specific to recurrent architectures" is still
accurate as a general, architecture-class statement (self-attention has
no inherent requirement to fill every position; this project's own
transformer only shares the limitation because of an implementation
choice, as the Methodology chapter now explains). No fix needed here —
already reasoned through against the Methodology-chapter correction and
the two are consistent.

---

### PDF p.21 (printed 9) — §2.3.3 (cont.), §2.4 Machine Learning Applications to Delhi and Indian Air Quality
**Content:** Che et al. on forward-fill for missing values; opening of
the Delhi-specific literature (Guttikunda, Cusworth, Jethva).

**Good:** The transition into §2.4 is handled honestly — the three
source-attribution studies cited (vehicular/industrial/biomass sources,
satellite fire counts) are explicitly flagged as studies that establish
*mechanism*, not forecasts, and the report states plainly that it "can
only infer [that mechanism] indirectly from the series' own seasonal
structure," naming this as a limitation rather than letting a reader
assume the project has access to causal information it doesn't.

**Could be better:** Nothing specific.

**Examiner's eye:** None.

---

### PDF p.22 (printed 10) — §2.4 (cont.): Masood & Ahmad, Singh & Srivastava; §2.5 opening
**Content:** Close critique of the two prior Delhi-PM2.5 ML studies; the
gap they leave; opening of the warning-system verification literature.

**Good:** This is the most impressive close-reading in the Literature
Review. The Masood & Ahmad critique correctly identifies that their
inputs are same-day exogenous measurements rather than lagged history —
a genuinely different forecasting problem from this project's, not a
cosmetic difference — and the Singh & Srivastava critique correctly
untangles their two separate analyses (a health-risk model and a
separately-scored ML comparison using ordinary R²/RMSE/MAE) rather than
letting the report imply their health-risk framing extended to the
forecasting comparison too. Both corrections came from this project
actually reading the source abstracts rather than trusting a title, and
it shows.

**Could be better:** Nothing specific.

**Examiner's eye:** None — if anything, this page is where a marker
checking citations against their actual content will come away most
reassured.

---

### PDF p.23 (printed 11) — §2.5 (cont.), §2.6 Data Quality in Reference Air Quality Monitors
**Content:** He & Garcia, Saito & Rehmsmeier on imbalanced-data
evaluation; Jiang et al. on negative-value handling; Little & Rubin's
MCAR/MAR/MNAR framework applied to this project's own coverage rule.

**Good:** The Little & Rubin application is the standout — the report
doesn't just cite the MCAR/MAR/MNAR taxonomy, it actually reasons through
which category this project's own gaps plausibly belong to ("nothing in
the station's own account of why a reading is missing suggests that a
reading is more likely to be dropped specifically when the true
concentration is unusually high or low") and states that as a judgement,
not a certainty. The Jiang et al. parallel (their negative-value problem,
this project's own clipped-ceiling problem) is drawn precisely: "share a
method rather than a target," which is the right level of comparison —
similar reasoning process, not a claim that the two defects are the same
thing.

**Could be better:** Nothing specific.

**Examiner's eye:** None.

---

### PDF p.24 (printed 12) — §2.7 Research Gap and Chapter Summary
**Content:** The chapter's own summary of its five literature bodies and
the gap this project occupies.

**Good:** Closes with a genuinely good line — "the ranking of models
looks different once accuracy is separated from operational usefulness,
a finding neither literature taken alone would have anticipated" — which
correctly previews the report's central finding without giving away the
specific numbers, mirroring how Chapter 1 closed.

**Could be better:** This summary restates "the specific architectural
reason a GRU rather than an LSTM suits a dataset this size" as settled
content the chapter covered, with no hedge. That's a problem, because two
pages earlier (§2.3.3, p.20) the chapter itself states plainly that this
reasoning was tested and **not supported** — the LSTM wins at every
horizon. The body of the chapter handles the correction well; the
chapter's own summary of itself quietly drops it and reports the original,
superseded reasoning as though it stood unchallenged. A reader who only
skims chapter summaries (not an unusual way to navigate a 74-page report)
would come away with exactly the wrong impression of what this chapter
found. Worth a short fix — e.g. "...the architectural reason originally
given for preferring a GRU over an LSTM, which Chapter 4 goes on to test
and not support" — matching the honesty already present two pages prior.

**Examiner's eye:** This is a real inconsistency and a more serious one
than most of the stale-reference findings so far, because it's not just
an unswept pronoun — it's a chapter summarising itself in a way that
contradicts its own body text. Worth fixing before anything else found in
this review.

---

## Chapter 3: Methodology

### PDF p.25 (printed 13) — §3.1 Research Design, §3.2 Data Collection and Station Selection (start)
**Content:** Chapter roadmap; the five-candidate station comparison and the
CPCB-cutoff finding.

**Good:** §3.1's roadmap mirrors §1.6's whole-report roadmap at the
chapter level — consistent structural voice. The station-selection
narrative is genuinely good detective work told plainly: five candidates
compared on *coverage* rather than nominal record length (the right
metric), the discovery that every CPCB station serves data only from
19 February 2025 despite metadata claiming a 2016 start, and the
inference this licenses ("four independent stations sharing an identical
cutoff indicates a systematic limit... rather than a coincidence") is
exactly the right strength of claim for the evidence — confident but not
overclaimed as proof.

**Could be better:** Nothing on this page itself.

**Examiner's eye:** None — this reads as the kind of data-provenance
diligence a marker wants to see before trusting anything built on top of
it.

---

### PDF p.26 (printed 14) — §3.2 (cont.): the AirNow limitation, the hazard threshold, Table 3.1
**Content:** The station's non-CPCB provenance stated plainly; the 121
µg/m³ threshold sourced to the CPCB AQI document; the dataset summary
table.

**Good:** The limitation is stated where a reader needs it, not buried —
"This carries a limitation that must be stated plainly" is as direct as
academic prose gets, and it's placed immediately after the station choice
is justified rather than deferred to a Limitations chapter forty pages
later where a reader might miss the connection. The threshold itself is
sourced to the actual CPCB AQI technical document, not a secondary
summary, which I independently confirmed earlier in this project's
history traces to the right table in that document (the "Very Poor"
breakpoint). Table 3.1's numbers all check out against the underlying
data directly.

**Could be better:** Across this page and the next two, four different
"total day count" numbers appear for different denominators: 3,579
calendar days (every day in the date range), 3,467 raw calendar-linked
days (used for the coverage recomputation), 3,375 raw observed days
(before cleaning, the cleaning table's own denominator), and 3,093 final
usable days. These are all legitimate and I've checked they're mutually
consistent (each a proper subset of the last), but nowhere are all four
reconciled in one place — a reader has to piece together why the "total"
changes between Table 3.1, the coverage paragraph, and Table 3.2
themselves. A single clarifying sentence wherever the first two diverge
("of the 3,579 calendar days in this span, 3,467 have an OpenAQ record at
all...") would remove any need for a reader to do that reconstruction
themselves.

**Examiner's eye:** Worth having the exact relationship between these four
numbers ready to state crisply if asked — the numbers are right, but the
report doesn't currently hand a reader the one-sentence reconciliation
that makes that obvious at a glance.

---

### PDF p.27 (printed 15) — §3.3.1 (cont.): the correction, Table 3.2, the coverage threshold, Figure 3.1
**Content:** How the cleaning rules were derived; the cleaning table; the
sensitivity reasoning behind the 50% coverage cutoff; the coverage-defect
figure.

**Good:** This is the table fixed earlier this session to compute from
the raw data rather than hand-type its numbers — good to see it rendering
exactly as verified (5 / 270 / 7 / 282 of 3,375). The coverage-threshold
justification is a genuine sensitivity analysis stated in the text itself,
not just performed and summarised: the actual alternative gap lengths at
60% (69 days) and 90% (185 days) are given, so a reader can judge the
tradeoff rather than take "50% was chosen" on faith.

**Could be better:** Nothing specific.

**Examiner's eye:** None — and this page is now slightly stronger evidence
than before that the report's numbers are trustworthy, given this exact
table was independently re-derived and matched this session.

---

### PDF p.28 (printed 16) — Figure 3.2, §3.3.2 Seasonality Analysis (start), the periodogram
**Content:** The cleaned series figure; the weekly-cycle test setup; the
periodogram equation and its result.

**Good:** Figure 3.2's caption states the mechanism that pays off much
later in the report — "exceedances arrive as multi-day winter episodes
rather than as isolated days" is the exact fact that explains the
counterintuitive Discussion-chapter finding that persistence beats every
fitted model at a tight alarm budget three days ahead. Planting this on
page 16 and cashing it in around page 50 is good long-range structure,
even if a first-time reader won't connect the two until they get there.
The periodogram result (dominant periods clustering at ~358–398 days,
nothing near 7) is stated with the actual numbers rather than just "no
weekly peak was found."

**Could be better:** Nothing specific.

**Examiner's eye:** None.

---

### PDF p.29 (printed 17) — §3.3.2 (cont.): ANOVA, Kruskal-Wallis, Figure 3.3, the physical reading
**Content:** The day-of-week F-test and rank test; the no-weekly-cycle
figure; the diplomatic-enclave interpretation.

**Good:** Using three tests built on genuinely different assumptions
(spectral decomposition, a parametric linear-model F-test, a
distribution-free rank test) against the same null is real statistical
triangulation, not three redundant checks of the same thing — each could
fail for a different reason, and none did. The closing physical
interpretation (a weekly cycle is a traffic signature; this site is a
diplomatic enclave, not a roadside monitor like ITO or Anand Vihar) turns
a null statistical result into a substantively interpretable one, which
is exactly what separates "we found nothing" from "we found an absence
that makes physical sense."

**Could be better:** Nothing specific.

**Examiner's eye:** The ANOVA and Kruskal-Wallis formulas (3.3, 3.4) are
both standard textbook forms, correctly stated. No issue.

---

### PDF p.30 (printed 18) — ARIMA spec consequence, Figure 3.4, §3.3.3 Feature Construction, §3.3.4 opening
**Content:** The no-weekly-order decision stated as a consequence; the
annual-cycle figure; the full feature list; opening of the weather
section.

**Good:** This page shows a fix from several sessions ago rendering
correctly in its final location — "The single exception is the three
networks, the GRU, the LSTM and the transformer, which share the same
channel construction and are discussed together in Sections 3.5.1, 3.5.2
and 3.5.3" is accurate and complete. The feature list itself is concrete
enough that a reader could reconstruct the feature table from this
paragraph alone (lags, differences, rolling stats at four windows,
anomaly scores, exceedance frequency, calendar terms, Fourier pairs,
missingness flags) — this is the right level of specificity for a
Methodology chapter, versus a vaguer "standard time-series features were
engineered."

**Could be better:** Nothing specific.

**Examiner's eye:** None.

---

### PDF p.31 (printed 19) — §3.3.4 Weather Covariates (full), §3.4 opening
**Content:** The six weather variables, the per-variable lag/rolling
construction, the weather record's own 202-day-lag defect, the
double-check methodology; opening of Classical and Machine Learning
Methods.

**Good:** The weather record's own defect is given the same seriousness as
the two primary data defects in §3.3.1 rather than being waved through
because it's "just an extension" — the hard-cutoff-vs-scattered-gaps
distinction is stated precisely, and precipitation's exclusion from the
network (54% coverage) versus retention for the tree models (which handle
sparse columns natively) is a real, justified, model-specific decision
rather than a blanket rule. The double-check methodology — comparing the
full-origin result against one restricted to the fully-observed weather
window, and reporting that they agree — is a genuine robustness check
performed and reported, not just asserted.

**Could be better:** Nothing specific.

**Examiner's eye:** None — this page is a good model of "don't let a
late-discovered data defect get less scrutiny than the ones found first."

---

### PDF p.32 (printed 20) — §3.4.1 Classical Benchmark: ARIMA with Fourier Terms
**Content:** The full Box-Jenkins specification, the AIC order search, the
fitted coefficients, the stationarity/invertibility check.

**Good:** This is one of the strongest pages in the report mathematically
— exactly what a mathematics capstone's Methodology chapter should look
like. The order-selection reasoning is genuinely honest rather than
mechanical: $(1,1,1)$ beats $(1,1,2)$ by only 1.1 AIC points, and the text
explicitly says this gap is "too small to call $(1,1,1)$ decisively
better rather than a more parsimonious specification of roughly equal
support" — that's a real statistician's read of an AIC table, not just
"we picked the minimum." The stationarity/invertibility check goes a step
further than most reports would bother with: it notes $\hat\theta_1$ sits
only 0.013 inside its boundary, correctly identifies this as a known
near-overdifferencing signature rather than evidence of a bad search, and
states plainly that the SARIMAX call doesn't constrain the optimiser to
this region, so the fit satisfying both conditions is a property of the
data, not a guarantee of the method.

**Could be better:** Nothing on this page. If the report has a single page
to point to as evidence of genuine mathematical rigor under scrutiny,
this is a strong candidate.

**Examiner's eye:** The AIC formula and the Box-Jenkins backshift-operator
specification are both standard and correctly stated; I've independently
verified the actual order-search grid and coefficients against the live
code earlier in this project, and they match what's printed here exactly.

---

### PDF p.33 (printed 21) — §3.4.1 (cont.): coefficient stability, Fourier justification, back-transform; §3.4.2 opening
**Content:** $\hat\phi_1$/$\hat\theta_1$ tracked across all 28 rolling-
origin refits; the Fourier-terms justification; the log-normal
mean/median back-transform; opening of Ridge Regression.

**Good:** The refit-stability paragraph is the single best piece of
methodological honesty in the report. Most treatments would report one
fitted coefficient pair and stop; this one tracks both parameters across
all 28 refits of the actual evaluation harness, reports $\hat\phi_1$'s
full range (0.520 to 0.591), and — this is the part that takes real
nerve — states plainly that $\hat\theta_1$ crosses the invertibility
boundary outright at three of the 28 refits, with the exact values
(-1.006, -1.011, -1.013), rather than quietly reporting only the
comfortable snapshot. The closing sentence ("the single pair reported
above describes the model this evaluation settles into for most of its
span, not a property holding at every refit within it") is exactly the
right level of honesty about what a single reported coefficient pair
does and doesn't tell a reader.

**Could be better:** Nothing on this page.

**Examiner's eye:** If an examiner wants to test whether this report
actually understands what it's reporting, rather than reciting output,
this is the page to ask about — and it already pre-answers the obvious
follow-up question ("so is the model invertible or not?").

---

### PDF p.34 (printed 22) — §3.4.2 Penalised Linear Regression (full derivation), §3.4.3 Random Forest (start)
**Content:** The ridge closed-form derivation via the normal equations;
bagging and the variance-decorrelation bound.

**Good:** The ridge section doesn't just state the closed form, it derives
it — objective, gradient, setting to zero, solving — which is what
"mathematical specification" should mean in a mathematics capstone and
isn't always what gets delivered. The random forest variance bound,
$\rho\sigma^2 + \frac{1-\rho}{B}\sigma^2$, comes with an actual mechanistic
explanation of why it matters (the first term is a floor averaging can't
reduce; the random feature subset is specifically what lowers that floor,
"a mechanism unrelated to how many trees are averaged") rather than being
stated and left for the reader to interpret.

**Could be better:** Nothing specific.

**Examiner's eye:** None — the derivation is complete and correct.

---

### PDF p.35 (printed 23) — §3.4.3 (cont.): the split criterion; §3.4.4 Histogram Gradient Boosting (start)
**Content:** The random forest's squared-error split criterion; the
Taylor-expansion justification for gradient boosting as function-space
descent.

**Good:** The gradient-boosting justification is genuinely well explained,
not just asserted — it states *why* this counts as descent in function
space rather than parameter space (one coordinate per training example,
not per model parameter), which is the actual conceptual leap that makes
Friedman's reformulation work and is usually the part textbook treatments
skip past.

**Could be better:** Nothing specific.

**Examiner's eye:** None.

---

### PDF p.36 (printed 24) — §3.4.4 (cont.), §3.5 Deep Learning Methods, §3.5.1 GRU (equations start)
**Content:** The pseudo-residual and ensemble update; the histogram-
binning rationale; level-vs-change target justification; the GRU's four
gate equations.

**Good:** The histogram-binning rationale is thoughtful rather than
boilerplate — it correctly notes that the technique's *original*
motivation (speed on huge datasets) doesn't really apply at this project's
scale, and states the actual reason it's used here instead (native NaN
handling, consistent with the project's no-imputation rule). The GRU gate
equations are the standard Cho et al. (2014) formulation, which I've
independently verified against the actual `torch.nn.GRU` implementation
used in the code — correct.

**Could be better:** Nothing specific.

**Examiner's eye:** None.

---

### PDF p.37 (printed 25) — §3.5.1 (cont.): specific architecture, parameter count, missingness compromise
**Content:** $H=24$, 30-day window, six channels, the untested $K=2$
Fourier default; the parameter-count equation and its bias-doubling
caveat; opening of the missingness discussion.

**Good:** This page shows another fix landing correctly: "A recurrent
network forces a compromise that the classical and tree-based models in
this project do not share" is now accurate, replacing the earlier false
"no other model in this project requires" claim. Separately, the
Fourier-harmonic honesty is another example of the report flagging its
own unexamined default rather than hiding it: $K=2$ was "inherited from
an earlier draft of the architecture rather than a deliberately tested
choice," and the report states plainly that a direct check found the
larger $K=4$ set actually performs better, "so the smaller set is better
read as an unexamined default than a justified one." The parameter-count
equation correctly accounts for PyTorch's bias-splitting convention rather
than silently undercounting by using the textbook gate equations alone.

**Could be better:** Nothing on this page.

**Examiner's eye:** None — the parameter counts (2,329 / 2,617) are
independently confirmed against the fitted objects, not just computed
from the formula.

---

### PDF p.38 (printed 26) — §3.5.1 (cont.): forward-fill construction, weather variant, ten-seed treatment, bit-reproducibility
**Content:** The forward-fill-plus-flag mechanism; the weather-augmented
10-channel GRU; the seed-doubling story and the bit-reproducibility
finding; the architecture-fixed-by-inspection caveat.

**Good:** "The one architecture Dr Tian specifically asked to be included
is the one architecture in the suite that cannot represent the statement
that a value is unknown" is a genuinely well-turned sentence that makes a
real technical point memorably — not just accurate, good writing. The
bit-reproducibility finding is the standout: discovering, reporting, and
acting on (doubling 5 seeds to 10) the fact that this network's training
isn't bit-reproducible even with a fixed seed is a real, surprising,
self-critical finding about the project's own methodology, and reporting
it openly is exactly the kind of thing that makes the rest of the
network's results *more* credible, not less, because a reader can see the
author went looking for trouble rather than assuming the pipeline was
sound.

**Could be better:** Nothing on this page.

**Examiner's eye:** Be ready to explain the bit-reproducibility mechanism
precisely if asked (multi-threaded linear algebra accumulating different
floating-point rounding across epochs) — the report states the finding
clearly but the underlying "why" is worth having crisp for a viva, since
it's an unusual enough result that an examiner may want to probe whether
it's understood or just observed.

---

### PDF p.39 (printed 27) — §3.5.2 The Long Short-Term Memory Network: Architecture and Training
**Content:** The LSTM's three gate equations and cell state; the
identical-protocol statement; the parameter count; the explicit scope
boundary (no weather variant, no threshold sweep).

**Good:** "Holding every other design choice fixed isolates the one
comparison this subsection exists to make: GRU against LSTM, not GRU
against a differently-tuned LSTM" is a precise, explicit statement of
experimental design logic that a lot of reports leave implicit. Stating
the scope boundary directly in the same breath as the parameter count,
rather than only in the Limitations chapter, means a reader encounters
the honest caveat exactly where they'd naturally start wondering about it.

**Could be better:** Nothing specific.

**Examiner's eye:** None — equations and parameter count (3,097) both
verified correct earlier in this project.

---

### PDF p.40 (printed 28) — §3.5.3 The Transformer: Architecture and Training (start)
**Content:** Dr Tian's conditional challenge and the project's response;
self-attention mechanism; sinusoidal positional encoding; scaled
dot-product attention; multi-head attention.

**Good:** This section's opening handles a genuinely tricky narrative
well: it states the supervisor's conditional exactly as given ("try it
only 'if the size is large'"), states the project's own original reasoning
for why that condition wasn't met, and states what changed without
either hiding the original argument or softening the fact that it turned
out wrong. That's a harder thing to write honestly than it looks. The
notational discipline ("deliberately distinct notation from the hidden
size $H$... since this is an embedding width, not a recurrent state")
matches the collision-flagging habit established in the List of Symbols,
so the care taken there isn't just front-matter theatre — it's actually
followed through in the body text.

**Could be better:** Nothing on this page. Three numbered equations
packed into one page reads dense, but the LSTM page two pages earlier
packs six equations into one page with no issue, so this isn't actually
disproportionate to the rest of the chapter's pacing — just the nature of
a mathematics capstone's Methodology chapter.

**Examiner's eye:** None — every equation on this page has been
independently re-verified against the actual fitted PyTorch model
multiple times this session, including the parameter count given two
pages later.

---

### PDF p.41 (printed 29) — §3.5.3 (cont.): encoder layer, the missingness honesty, untuned settings, parameter count
**Content:** The residual/LayerNorm encoder-layer equations; the "not an
architectural necessity" paragraph; the four untuned settings; the full
parameter-count derivation.

**Good:** The missingness paragraph (added in an earlier session this
round) is exactly the right way to handle a design limitation: it states
plainly that self-attention has *no* inherent requirement to fill every
position, that an attention mask could represent a gap properly, and that
"that richer treatment was not built here" — distinguishing cleanly
between a limitation of the architecture and a limitation of this
project's implementation of it. The $n_{head}$-independence note at the
end of the parameter-count paragraph shows real understanding of the
formula's structure, not just arithmetic substitution.

**Could be better:** The page is honest that "no equivalent [sensitivity]
check exists yet for the transformer's [hyperparameters]," unlike the
GRU's three separate bounded checks (hidden size/window, Fourier
harmonics, optimiser/learning rate). That's the right thing to disclose,
but it leaves a real, fair question unanswered rather than just
undisclosed: if the transformer's $d_{model}=16$, $n_{head}=2$, and
learning rate of 0.001 were never stress-tested the way the GRU's
analogous choices were, how much should a reader trust that the
transformer's reported numbers reflect something close to its best
achievable performance, rather than an artifact of inherited bounded-check
defaults? The report doesn't claim otherwise, but it also doesn't say much
more than "this wasn't done" — worth having a direct answer ready (e.g.
"with deadline pressure, the full-evaluation promotion itself was the
priority; a hyperparameter sweep is explicitly future work") since this
is a natural follow-up to the honest disclosure already there.

**Examiner's eye:** This is the fairest and most likely methodological
question about the transformer specifically — more likely than anything
about the architecture's correctness, which has been checked thoroughly.
Be ready for it.

---

### PDF p.42 (printed 30) — §3.6 Rolling-Origin Evaluation
**Content:** The full evaluation protocol: 2,303 origins, refit cadence,
the single-split-vs-rolling-origin comparison, the leakage invariant, the
label-availability trap specific to supervised learning.

**Good:** Using the project's own numbers to illustrate the single-split
danger — ARIMA scoring 0.903 on a single block versus 0.940 under the
honest harness, *worse* under more rigorous evaluation — makes an
abstract methodological warning concrete and memorable in a way that
citing Tashman and Hewamalage alone wouldn't. The leakage-test
description is a real, falsifiable procedure stated precisely enough that
a reader could reimplement it from this paragraph alone: corrupt the
series after a cut date, rerun, assert nothing before the cut changed.

**Could be better:** Nothing specific.

**Examiner's eye:** None — this protocol has been independently confirmed
to actually run and pass, not just described, via the `--test` suites
checked earlier in this project.

---

### PDF p.43 (printed 31) — §3.7 Evaluation Measures (start)
**Content:** rMAE and MASE formulas; the TP/FP/FN/TN contingency-table
definitions; hit rate, false alarm rate, precision, CSI.

**Good:** Every formula on this page has been independently verified,
byte for byte, against the actual `evaluation.py` implementation that
produces every number in Chapter 4 — not just checked for textbook
correctness but confirmed to be the formula actually computing the
report's results. The rMAE-vs-MASE distinction is motivated precisely
(MASE's denominator is fixed on the training period and so conflates
accuracy change with volatility change — exactly what the report finds
when comparing single-split against rolling-origin results elsewhere).

**Could be better:** Nothing specific.

**Examiner's eye:** None.

---

### PDF p.44 (printed 32) — §3.7 (cont.), §3.8 Statistical Comparison of Forecasts (start)
**Content:** Alarms-per-year; the argument against plain classification
accuracy; opening of the Diebold-Mariano test, through its long-run
variance estimator.

**Good:** The anti-accuracy argument is concrete rather than abstract — it
walks through the exact degenerate case (a model that never alarms scores
$TN/n$, "high by construction, while catching none of the events it
exists to catch") rather than just asserting accuracy is misleading on
imbalanced data. The DM-test variance derivation correctly justifies *why*
the naive sample variance isn't used: an optimally specified $h$-step
forecast's errors are at most an $MA(h-1)$ process, so the loss
differential genuinely carries serial correlation up to lag $h-1$ — stated
as a consequence of forecast theory, not an arbitrary correction.

**Could be better:** Nothing specific.

**Examiner's eye:** None — this is rigorous, correctly justified
statistical content throughout.

---

### PDF p.45 (printed 33) — §3.8 (cont.): HLN correction, normality caveat, the multiple-comparisons paragraph
**Content:** The small-sample DM correction; a caveat about heavy-tailed
asymptotics; the application to this report's comparisons; the
multiple-comparisons disclosure added this session.

**Good:** This page is now the single most statistically self-aware page
in the report. It states the HLN correction, immediately states a
*further* limitation that correction doesn't address (asymptotic
normality under a heavy-tailed loss differential), explicitly says "none
of this is checked by bootstrapping," and then adds the multiple-
comparisons disclosure on top of that: 27 tests run with no correction,
the concrete Bonferroni result (only 6 of 27 survive), and the honest
admission that even that correction is generous, since using each
network's best seed as its representative figure is itself a second,
uncorrected form of selection. Layering three successive, increasingly
severe caveats onto the same test, each stated plainly rather than
buried, is a genuinely rare level of statistical honesty for a report at
this level.

**Could be better:** This is a case where maximal honesty creates a small
communication risk rather than a correctness problem. A reader who stops
at "only six of twenty-seven survive" without reaching the very next
sentence ("this does not overturn the report's central qualitative
claims...") could come away more alarmed about the report's rigor than is
warranted — the central findings don't actually rest on any single
p-value surviving correction, but a skimming reader might not register
that distinction on a first pass. Not a reason to walk back the
disclosure, which is the right call; just worth being ready to state the
reassurance *before* being asked for it if this page comes up in a viva,
rather than waiting to be pressed.

**Examiner's eye:** This page essentially pre-empts the hardest technical
question a statistics-literate examiner could ask about the whole report.
Walking in already knowing this paragraph cold is worth the time.

---

### PDF p.46 (printed 34) — §3.9 Reproducibility, §3.10 Chapter Summary
**Content:** The pipeline/test-suite claims; the public repository link;
the chapter's own summary of Methodology.

**Good:** Every factual claim on this page is independently verifiable and
I've verified it directly rather than taken it on faith: twelve numbered
pipeline scripts exist, eleven of twelve carry a `--test` flag (confirmed
by grepping the actual source this session), and the rolling-origin
harness's leakage invariant genuinely is checked before every run, not
just claimed to be. The Chapter Summary correctly reflects "three
networks" throughout — no stale counts here, unlike the Literature
Review's own chapter summary two chapters earlier.

**Could be better:** Nothing specific.

**Examiner's eye:** None — this is the one "trust me" paragraph in the
report that I've actually gone and checked rather than assumed, and it
holds up.

---

## Chapter 4: Results and Analysis

### PDF p.47 (printed 35) — §4.1 Forecast Accuracy: Table 4.1, opening interpretation
**Content:** The full accuracy table (12 rows); the horizon-by-horizon
reading through two days ahead.

**Good:** Every number in this table has been directly verified multiple
times this session, including building the transformer's own row from
scratch. The interpretive prose never just states a winner — it
immediately qualifies against the report's own measured noise floor ("the
two weakest, 0.936 and 0.939 against ARIMA's 0.940, are close enough to
call ties rather than clear wins"), which is the discipline that makes
the rest of the chapter's claims trustworthy rather than a leaderboard.

**Could be better:** Nothing specific.

**Examiner's eye:** None.

---

### PDF p.48 (printed 36) — Figure 4.1, Table 4.2 discussion, the mechanism paragraph
**Content:** The dot-plot figure; the significance-test reading; the
short-range-vs-seasonal mechanism explanation; opening of the GRU's own
seed-spread discussion.

**Good:** The mechanism paragraph is genuinely sophisticated interpretive
writing: rather than just reporting that ARIMA wins at longer horizons, it
offers an actual mechanistic account (short-range structure dominates at
$h=1$, where a nonlinear model has something to exploit; the seasonal
component dominates at longer horizons, where ARIMA's four Fourier pairs
carry more of it than the network's two) *and* immediately points to the
bounded check in §5.3 that tests this explanation directly rather than
leaving it as a plausible-sounding story. Figure 4.1's caption correctly
reads "None of the three seeded networks" — another earlier fix
confirmed landing correctly in its final rendered location.

**Could be better:** Nothing specific.

**Examiner's eye:** None.

---

### PDF p.49 (printed 37) — Table 4.2, the LSTM Results paragraph, Transformer paragraph (start)
**Content:** The full Diebold-Mariano table (all 12 network-vs-ARIMA
rows); the LSTM's own Results treatment; opening of the Transformer's.

**Good:** Every number in Table 4.2 has been independently verified this
session against the live significance computation — exact match. The LSTM
paragraph handles the parameter-count reversal cleanly: states the result
(LSTM beats GRU at every horizon despite a third more parameters), states
what it does to the original reasoning ("directly tests, and does not
support"), and states the honest scope boundary (no weather variant, no
threshold sweep) in the same breath rather than deferring it entirely to
Limitations.

**Could be better:** Nothing specific. ("...at the analyst's convenience."
opening this page is the tail of a sentence that began on the previous
page — normal pagination, not an error, checked to be sure.)

**Examiner's eye:** None.

---

### PDF p.50 (printed 38) — Transformer paragraph (cont.), subsidiary results, Table 4.2/4.3 framing, §4.1.1 opening
**Content:** The rest of the transformer's Results treatment; the
Fourier-ablation and change-target subsidiary findings; the significance-
table framing; opening of the weather-extension subsection.

**Good:** "Table 4.2 tests the four comparisons in this report" is another
confirmed-correct fix from earlier this session (previously "three"). The
Fourier-ablation subsidiary result (3.3 points of relative error at one
day, 5.8 at three from removing the Fourier terms) is a concrete number
that directly backs the mechanism claim from two pages earlier — the
report doesn't just assert the seasonal terms matter, it shows the cost
of removing them.

**Could be better:** Nothing specific.

**Examiner's eye:** None.

---

### PDF p.51 (printed 39) — Table 4.3, Table 4.4, §4.1.1 interpretation (start)
**Content:** The ML-regressor significance table (all 15 rows); the
weather-covariate rMAE change table; opening of the weather interpretation.

**Good:** Table 4.3 is a strong page for research integrity specifically:
all fifteen comparisons favour ARIMA, fourteen reach significance, and the
one that doesn't (change-target random forest at two days, $p=0.054$) is
reported as exactly that — "falls just short" — rather than rounded away
or left to blend into "basically all fifteen." Reporting the one near-miss
honestly, when it would have been easy not to dwell on it, is a real
marker of a trustworthy results chapter.

**Could be better:** Nothing specific.

**Examiner's eye:** None — I checked the one non-significant cell
($p=0.054$) against the prose's own characterisation and they agree
exactly.

---

### PDF p.52 (printed 40) — §4.1.1 (cont.): weather results by model, the seed-doubling finding reprised
**Content:** The uneven weather effect across GBM/RF/ridge; the GRU-
specific weather discussion at each horizon; the significance-test
confirmation; the honest summary paragraph.

**Good:** This page is a model of calibrated science writing. The closing
summary — "wind speed and temperature measurably help the one
architecture built to exploit short-range structure at one day ahead,
leave the two-day comparison a genuine tie rather than the win it first
appeared to be, and leave three days ahead more often a loss than a win"
— says exactly what was found, no more and no less, after a finding that
*got less favourable* once the sample was doubled from five seeds to ten.
Reporting that a result weakened under more scrutiny, rather than quietly
keeping the more flattering five-seed reading, is exactly the kind of
self-correction that makes the rest of the report's claims credible.

**Could be better:** Nothing on this page.

**Examiner's eye:** None — if an examiner wants one page that demonstrates
this project didn't go looking only for confirming evidence, this is it.

---

### PDF p.53 (printed 41) — Table 4.5, its interpretation; §4.2 Two Arms of the Same Question (start)
**Content:** The weather-budget comparison table; the "ceiling over the
gain" interpretation; opening of the RQ2 forecast-vs-classify comparison.

**Good:** I independently recomputed every specific number quoted against
Table 4.5 directly rather than trusting the prose: "delta exactly zero" at
the budgets claimed (checked all seven) is exact, and "at most 1.2 points,
at two days and a budget of 40" is exactly 0.012 in the table — this page
is precision-checked, not approximated. The table's own caption is the
one corrected last session ("averaged over the ten network seeds"),
confirmed landing correctly here.

**Could be better:** Nothing specific.

**Examiner's eye:** None.

---

### PDF p.54 (printed 42) — Table 4.6, the RQ2 tally and mechanism, the arm-preference rationale
**Content:** The matched regressor-vs-classifier table; the 36-comparison
tally (21/11/4); the mechanistic reading; why forecast-then-threshold is
preferred beyond the raw numbers.

**Good:** The 21/11/4 tally, the 0.011 median difference, and the 0.056
maximum difference all check out exactly against what I verified earlier
in this project directly from the code's own tally computation — not
rounded or approximated. The mechanistic explanation for *why* the edge
exists (a classifier has no more signal to find in the label than a
regressor already has in the continuous value, on a sample this size) is
offered with the right hedge — "may be what the small but consistent edge
reflects" — rather than asserted as settled.

**Could be better:** Nothing specific.

**Examiner's eye:** None.

---

### PDF p.55 (printed 43) — Figure 4.2, §4.3 The Decision Threshold, Table 4.7
**Content:** The RQ2 figure across all horizons; Table 4.7, "the principal
result of this project"; the persistence-at-$h=3$ and climatology-near-tie
illustrations.

**Good:** This table is the report's own stated central result, so I
went further than reading it and independently queried the raw
`threshold_sweep.csv` directly against both headline claims. "Persistence
... is the single best model in the entire study, 0.359" at $h=3$, budget
40: confirmed exactly — `naive_carry` scores 0.359408, ahead of every
other model in the sweep at that cell. The climatology comparison, "0.816
against 0.827" at $h=3$, budget 100, looked like a discrepancy at first
pass — the best score among named models excluding classifiers is only
0.820 — but checking every individual GRU seed resolved it: seed 9 alone
reaches 0.8266, which rounds to exactly 0.827 and is the true maximum
once the full ten-seed GRU range is included, consistent with how
`table_budget()` is actually built (the "Best hit rate" row deliberately
takes the max across all ten GRU seeds, not just one, specifically so it
isn't capped at a single seed's curve). Both headline numbers check out.

**Could be better:** Table 4.7 itemizes named models (GRU, ARIMA,
gradient boosting, persistence, climatology) only at $h=1$; the $h=3$
claims in the prose, which are actually the two sharpest illustrations of
the whole report's central finding, aren't independently checkable against
a printed table cell the way the $h=1$ claims are — a reader has to trust
the prose rather than look it up themselves. I've now done that checking
directly against the source data and both numbers hold, but a reader
without code access cannot. Worth considering a small supplementary table
or footnote giving the $h=3$, budget-40 and budget-100 rows by name,
since these are literally the two numbers the report leans on hardest.

**Examiner's eye:** If asked to defend "0.816 against 0.827" specifically,
the answer is that 0.827 is the best individual GRU seed's result (seed
9), not a different model — worth having that distinction ready, since
"the best fitted model" in the prose could otherwise be misread as
referring to a single, reproducible model rather than the best draw from
a range the report itself says shouldn't be reported as a point estimate.

---

### PDF p.56 (printed 44) — Figure 4.3
**Content:** The hit-rate/false-alarm-rate and hit-rate/alarms-per-year
trade-off curves, all three horizons.

**Good:** The caption does real interpretive work rather than just
describing the axes — "the curves very nearly coincide, which is the
finding" tells a reader what to look for, and "they have deliberately not
been separated for legibility" heads off the obvious question of whether
the near-overlap is a plotting artifact before it's asked.

**Could be better:** Nothing specific — this page is a single figure and
doesn't need more.

**Examiner's eye:** None.

---

### PDF p.57 (printed 45) — The persistence mechanism, closing argument, §4.4 Chapter Summary
**Content:** Why persistence wins at a tight budget three days ahead;
the chapter's own closing thesis statement; the chapter summary.

**Good:** This is where the seed planted on page 28 (Figure 3.2's caption,
"exceedances arrive as multi-day episodes") pays off, with an explicit
cross-reference back to it — good long-range structure across almost 30
pages, not a coincidental echo. "A report that presents a model
comparison without stating the operating point it was evaluated at has
answered a question nobody asked" is the single most quotable sentence in
the report and a legitimate thesis statement, not just a summary line.
The Chapter Summary confirms "the deep learning models win" (plural) is
correct in its final location.

**Could be better:** Nothing specific.

**Examiner's eye:** None.

---

## Chapter 5: Discussion

### PDF p.58 (printed 46) — §5.1 The Operational Question Dominates the Modelling Question
**Content:** The chapter's central argument, restated and interpreted
rather than just repeated from Chapter 4.

**Good:** Reuses the two headline numbers I independently verified against
raw data two pages ago (0.379→0.881; 0.816 vs 0.827) consistently and
correctly. "The threshold is the policy instrument, and the forecasting
model only supplies its input" is a sharp, memorable reframing of the
whole project's contribution. "ARIMA and the fitted networks both earn
real, if modest, gains over persistence" is correctly plural, consistent
with the rest of the report.

**Could be better:** Nothing specific.

**Examiner's eye:** None — this section states what follows from the
numbers rather than re-arguing them, which is the right job for a
Discussion chapter's opening section.

---

### PDF p.59 (printed 47) — §5.2 How Large Is a Difference Between Models? (start)
**Content:** The three empirical noise-floor bounds (machine, seed,
bit-reproducibility); Table 4.1's own gaps measured against them; the
GRU "sharpest instance" illustration.

**Good:** The transformer's own seed spread (0.011 to 0.023, "the
tightest again") and the extended bit-reproducibility caveat ("the same
check was not repeated for the LSTM or the transformer") are both fixes
from earlier this session, confirmed landing correctly in context. The
"sharpest instance" paragraph is an effective piece of reasoning: it uses
the GRU's *own* internal seed-to-seed variation to show that a single-seed
report could have placed the same architecture anywhere from "tied with
ARIMA" to "indistinguishable from the weakest regressor in the table,"
which makes the report's own insistence on ranges-not-points land as
demonstrated rather than merely asserted.

**Could be better:** Nothing specific.

**Examiner's eye:** None.

---

### PDF p.60 (printed 48) — §5.2 (cont.): the formal significance comparison, Wilson intervals, §5.3 opening
**Content:** The rewritten paragraph comparing the noise floor against the
Diebold-Mariano test across all three networks; the Wilson score interval
caveat; opening of Limitations.

**Good:** This page carries the most heavily rewritten paragraph from
earlier this session and it reads smoothly in full context — "Taking the
plain GRU first, since it is the one already discussed above" signals
clearly why the GRU gets special treatment in the paragraph (it's the one
the noise-floor count above was about) rather than reading as an arbitrary
choice. The Wilson-interval numbers (0.17–0.69, up to 0.28, up to 0.40) are
ones I independently recomputed earlier this session and they match
exactly. The closing sentence — "not a reason to distrust the direction
of any of the three findings... but a reason not to treat the exact
fraction... as more precise than the sample allows" — is the same
pattern used after the multiple-comparisons disclosure four pages earlier:
stack the caveats honestly, then explicitly separate what's still solid
from what isn't. That's now a consistent, recognisable voice across the
whole Discussion chapter, not a one-off disclaimer.

**Could be better:** Nothing specific. Three successive paragraphs (the
noise floor, the DM comparison, the Wilson intervals) each add another
layer of "but actually, even that's less certain than it looks" — by this
point in the chapter a reader has been told, in sequence, that the
accuracy gaps might be noise, that the significance test is more
conservative than the noise floor, and that the significance *counts*
themselves are imprecise. This is all true and well-argued, but three
layers of compounding uncertainty back to back is a lot to track in one
sitting; a one-sentence signpost at the start of §5.2 ("the next three
subsections bound the same question three different ways, each more
conservative than the last") would help a reader hold the structure in
mind rather than experience it as one caveat after another.

**Examiner's eye:** None beyond the pacing note above — the content itself
is sound throughout.

---

### PDF p.61 (printed 49) — §5.3 Limitations (start): station/city scope, the cleaning-threshold sensitivity check
**Content:** The AirNow/CPCB limitation restated; the single-city scope;
the full-harness refit without the 1000 µg/m³ cap.

**Good:** The cleaning-threshold check is a real, expensive robustness
test, not a hand-wave — the entire rolling-origin harness was refit on
the uncapped series, and the result (the central RQ1 finding *strengthens*
rather than merely survives, because the ML models are more exposed to
the uncleaned tail than ARIMA) is a genuine, non-obvious finding that
could easily have gone the other way. Performing a check that could have
undermined the report's own central claim, and reporting the result
regardless of which way it landed, is exactly what a robustness check is
for.

**Could be better:** Nothing on this page specifically.

**Examiner's eye:** None.

---

### PDF p.62 (printed 50) — §5.3 (cont.): the three GRU bounded checks (architecture, Fourier, optimiser)
**Content:** Hidden-size/window-length check; Fourier-harmonic check;
optimiser/learning-rate check — all converging on the same conclusion.

**Good:** The real strength here is triangulation across three
*independent* bounded checks (architecture, seasonal input, training
procedure) that all point at the same thing: the three-day GRU
configuration is the project's own least-defensible one. That's a much
stronger claim than any single check could support on its own, and the
report states the convergence explicitly rather than leaving three
separate findings for a reader to notice independently line up.

**Could be better:** This is the second of what is now a long, unbroken
run of dense Limitations content (pages 61 through 64, six pages total
once the chapter is finished) — each item individually is well-executed
and honestly reported, as noted on page 60, but the cumulative volume of
"here is another thing that isn't fully nailed down" across six
consecutive pages risks leaving an impression more negative than the
underlying evidence actually supports, especially for a reader who
doesn't make it to the chapter's closing synthesis. Not a reason to cut
any of this content — all of it is substantive and worth keeping — but a
short orienting sentence at the start of §5.3 itself (something like "the
limitations below are organised roughly by severity, from scope
restrictions that cannot be fixed within this project to specific,
bounded uncertainties that were actively measured rather than assumed")
would help a reader calibrate as they go rather than only at the end.

**Examiner's eye:** None beyond the structural note above.

---

### PDF p.63 (printed 51) — §5.3 (cont.): the bit-reproducibility finding, the LSTM/transformer scope boundary, transformer promotion begins
**Content:** The full pipeline rerun and its reproducibility finding in
detail; the shared LSTM/transformer scope limitation; opening of the
transformer's bounded-check-to-full-evaluation story.

**Good:** "the practical consequence is that five seeds... was not enough
to characterise the network reliably: the weather-covariate finding at
two and three days ahead... looked like a clear win under the first five
seeds fitted and looked like a tie or a loss once five more were added" —
stating a concrete instance of a finding that *reversed* under more
scrutiny, by name, is far more convincing than an abstract warning about
small samples. The shared LSTM/transformer scope-boundary paragraph
(merged from two separate paragraphs in an earlier version of this
report) reads as a single coherent statement now, with the honest closing
— "not because a result was anticipated and avoided" — preempting a
cynical reading of why neither got the weather/threshold treatment.

**Could be better:** Nothing new beyond the density point already raised.

**Examiner's eye:** None.

---

### PDF p.64 (printed 52) — §5.3 (cont.): transformer promotion conclusion, the KAN-LSTM bounded check, weather-extension scope (start)
**Content:** The resolution of the transformer's bounded-check-to-full-
evaluation story; the complete KAN-LSTM hybrid treatment; opening of the
weather-extension's own stated narrowness.

**Good:** The KAN-LSTM paragraph models exactly the right tone for an
unremarkable result: "a null result here, the hybrid simply failing to
train, would have been informative on its own; a working but unremarkable
one is the result actually obtained, reported as exactly that rather than
dismissed or oversold in either direction." Explicitly naming the
temptation to oversell a middling result, and declining it, is a small
but real piece of evidence that the report's other, more exciting
findings weren't selected for being exciting. The $10^{-4}$ MSE claim for
the KAN self-test is one I independently reran this session and it
matches exactly.

**Could be better:** Nothing new beyond the density point already raised.

**Examiner's eye:** None.

---

### PDF p.65 (printed 53) — §5.3 (close): weather-extension scope, §5.4 Chapter Summary
**Content:** The last of the Limitations (boundary layer height, ERA5);
the chapter's own closing synthesis.

**Good:** This closing paragraph does exactly what the earlier pacing
note on pages 60/62 was hoping for: it explicitly separates what the
Limitations chapter *doesn't* change ("none of these overturns the
central finding") from what it *does* contribute ("several of them, the
noise floor and the seed-count doubling most directly, are the reason
that finding can be stated with the confidence it is"). So the chapter
does recenter the reader on what's solid — it just only does so at the
very end of six dense pages, rather than along the way. The honest
self-correction about the weather draft ("the free extension this
report's own earlier draft assumed it would be") is a small but genuine
piece of project history left visible rather than smoothed over.

**Could be better:** Nothing new — this closing paragraph is the thing the
earlier pacing suggestion would make land even better if it arrived
sooner in the reader's experience, not instead of this one.

**Examiner's eye:** None.

---

## Chapter 6: Conclusion

### PDF p.66 (printed 54) — §6.1 Summary of the Study, §6.2 Main Conclusions (start)
**Content:** The project's own one-paragraph summary; opening of the Main
Conclusions.

**Good:** "three machine learning regressors and three deep learning
networks" confirms another earlier fix landed in its final location. The
Main Conclusions opening correctly stays scoped to the ten-model
threshold-sweep framing (singular "a recurrent network"), consistent with
every other correctly-scoped instance checked earlier in this review.

**Could be better:** Nothing specific.

**Examiner's eye:** None.

---

### PDF p.67 (printed 55) — §6.2 (cont.): the three-network conclusion, weather, RQ2, closing thought
**Content:** The full three-network comparison restated as a conclusion;
the weather finding; the RQ2 summary; the closing credit to the
supervisor's methodological steer.

**Good:** The closing paragraph is a genuinely well-judged piece of
writing: "The supervisor's instruction to try several methods rather than
defaulting to ARIMA was the right one: it is what makes the negative
result at two and three days credible, and what surfaces the one day
ahead result that a project restricted to classical methods would never
have found." This credits Dr Tian's steer specifically because it's
substantively true given everything documented in this report, not as a
rote acknowledgement — it ties directly back to the actual empirical
findings rather than being generic thanks.

**Could be better:** Nothing specific.

**Examiner's eye:** None.

---

### PDF p.68 (printed 56) — §6.3 Future Work (items 1–6, start of item 6)
**Content:** All six future-work items: real weather forecasts, boundary
layer height, the full-evaluation Fourier check, a second station, the
shared LSTM/transformer extension, the KAN-LSTM promotion.

**Good:** Every one of the six items is tied to a specific, named finding
or limitation from earlier in the report rather than being generic
"more data would help" filler — a reader can trace each item back to the
exact sentence that motivates it. Items 5 and 6 reflect this session's
earlier fixes (the LSTM and transformer merged into one shared extension;
the sixth narrowed to the Kolmogorov-Arnold-LSTM hybrid alone, explicitly
framed as "the same promotion the transformer itself was given") and both
read correctly in context.

**Could be better:** Nothing specific.

**Examiner's eye:** None — this is a genuinely well-grounded Future Work
section, not a wish list.

---

### PDF p.69 (printed 57) — Future Work item 6 (close), the central recommendation, §6.4 Chapter Summary
**Content:** The report's final substantive content: the closing
recommendation and the last chapter summary.

**Good:** The final sentence of the report proper — "A project that set
out to compare machine learning against classical time series methods for
a public health problem ends by recommending that the comparison matters
less than where the operator sets the alarm" — is exactly the sentence
you'd want if someone asked for the whole 74-page report in one line. It's
specific, it names the irony of the project's own trajectory honestly
(set out to compare models, ended up arguing models matter less than
policy), and it isn't inflated. The three-network framing throughout this
page is consistent and correct.

**Could be better:** Nothing specific.

**Examiner's eye:** None — a strong, confident close.

---

## Bibliography

### PDF p.70 (printed 58) — Bibliography, A–C
**Content:** Bengio through Chen & Guestrin, roughly 14 entries.

**Good:** Consistent `plainnat` formatting throughout; every entry carries
a DOI except the CPCB government techreport, which is the one deliberate,
already-justified exception (a primary standards document rather than a
journal article). I've separately confirmed elsewhere in this review that
every citation key used in the body has a matching entry here and vice
versa — no orphans, nothing missing.

**Could be better:** Nothing specific.

**Examiner's eye:** None.

---

### PDF p.71 (printed 59) — Bibliography, C–H
**Content:** Cho through Hoerl & Kennard, roughly 17 entries.

**Good:** Nothing to add beyond the previous page — same consistent
formatting and sourcing discipline maintained.

**Could be better:** Nothing specific.

**Examiner's eye:** None.

---

### PDF p.72 (printed 60) — Bibliography, H–L
**Content:** Hornik through Liu 2020, roughly 13 entries.

**Good:** Nothing new to add.

**Could be better:** Nothing specific.

**Examiner's eye:** None.

---

### PDF p.73 (printed 61) — Bibliography, L–S
**Content:** Liu 2025 (the KAN paper) through Singh & Srivastava, roughly
14 entries.

**Good:** Nothing new structurally. Worth one specific note: the Liu et
al. [2025] KAN paper's DOI, `10.1103/4t7t-v19l`, uses a short
alphanumeric suffix rather than the long numeric format older Physical
Review entries use — this looks unusual at a glance next to the rest of
the bibliography, but it reflects a real, documented shift in how the
American Physical Society assigns DOIs to newer articles, and this
specific entry was already verified directly against CrossRef's own
record earlier in this project's history rather than guessed. Flagging
only because an unusual-looking DOI is exactly the kind of thing worth
being able to explain in thirty seconds if someone notices it.

**Could be better:** Nothing specific.

**Examiner's eye:** If asked about this one specifically, the short-form
DOI is a publisher convention change, not a citation error — worth having
that one-sentence answer ready.

---

### PDF p.74 (printed 62) — Bibliography, T–Z (final page)
**Content:** Tashman through Zhang 1998, the final 3 entries.

**Good:** Closes the bibliography cleanly at 49 entries total, every one
cited at least once in the body and every citation in the body matching
an entry here — confirmed by direct cross-check earlier in this project's
history, not assumed.

**Could be better:** Nothing specific.

**Examiner's eye:** None.

---
