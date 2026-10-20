# Decisions and freeze points

The code and the results refer to design decisions as D1 to D62 and to sections of the working plan as "plan §x".
The plan is the author's private working document; this file is the public record. It lists each decision with its
date (all in October 2026), what was decided and why, the git tags that froze the lexicon and the prompts, and what
each cited plan section covers. The order matters: it shows what was fixed before which result.

## Freeze points

| Tag | Commit | Date | What it froze | Before |
|---|---|---|---|---|
| `e1-frozen` | `e26c2b9b` | 14 Oct | Lexicon v1 and the planted label set, after the calibration on the discovery seed (no threshold moved) | E1 |
| `lexicon-v2` | `5383c2a0` | 14 Oct | Lexicon v2 (D42): jump and peak locations on count features judged on the gaps between observed values | any confirmation run |
| `prompts-v3-x3` | `cf1ee6b9` | 15 Oct | The writer's prompts v3 and the extractor's prompts x3 | E3 |

The prompts' hashes are tested (`llm/prompts/frozen*.json`), so a changed prompt fails the tests. Extractor x4 was
frozen on 15 Oct, after the first text-level E2 run, in the same way (D48, D51).

The order of the work:

1. 13 Oct: the synthetic DGP frozen (D11); the EBM setting rechecked on fresh seeds (D18); the bootstrap bands
   validated by a null check with a rule fixed before the run (D23).
2. 14 Oct: the lexicon calibrated on the discovery seed by a rule fixed before the run and frozen as v1; E1 on the
   discovery seed; plan-level E2; the writer pilot; lexicon v2 (D42).
3. 15 Oct: the round-trip pilot; prompts v3 and extractor x3 frozen; E3 with Haiku and Sonnet; text-level E2;
   extractor x4; E1 and plan-level E2 on the confirmation seeds and the plasmode tier, under lexicon v2.
4. 16 Oct: the false-alarm labels; E3 re-scored with labels; the local spot check, designed and priced before it
   ran (D49), with its own frozen prompts.
5. 17 Oct: plasmode text-level E2 (D54); the self-hosted writer (D55).
6. 20 Oct: the LLM critic's prompts frozen after its pilot, then the critic run (D61).

## Decisions

| D | Date | Decision | Why |
|---|---|---|---|
| D1 | 13 Oct | Make the planted truth unambiguous: a sign flip of about 5% of the importance, a wider and higher bump at 36 months, `n_inquiries` at about 4%; an acceptance check before the experiments. | Some planted effects were not recovered even at n = 50,000, so the truth was not one the data could show. |
| D2 | 13 Oct | Facts are always purified (functional ANOVA, `interpret.utils.purify`): main-effect parts move into the main terms. | `interpret` does not purify EBM pairs: the planted pairs carried 28% main-effect parts, spurious pairs 35–86%. |
| D3 | 13 Oct | Bands come from bootstrap refits, for both models. | The EBM's outer-bag bands are too narrow: at n = 5,000 a noise feature got a 3.7% share and "a weak effect" would have passed. |
| D4 | 13 Oct | Simultaneous (sup-t) bands for every rule that scans a curve. | With pointwise bands, a null curve excludes 0 somewhere about half the time (multiple testing). |
| D5 | 13 Oct | Interaction patterns are judged on conditional effects (main effect plus pair). | A purified pair averages to zero over the other feature, so on its own every pair looks like a sign flip. |
| D6 | 13 Oct | The EBM fits at most 5 pairs. | The default fits 27; the spurious ones dilute every other share. With 5, the planted pairs rank first. |
| D7 | 13 Oct | Acceptance is relative to an oracle: a model must recover what the oracle recovers on the same sample. | Even the oracle misses claims near a class edge on 2.5–10% of seeds at n = 50,000 (a sampling floor). |
| D8 | 13 Oct | Both boosted models shrink the planted sign flip (EBM to about 70%, XGB2 to about 45%); reported as a result, not tuned away (settled by D11, D15). | No XGB2 setting helped; changing the truth to suit a model would be circular. |
| D9 | 13 Oct | Noise fitted at n = 5,000 is handled by the bands (D3, D4), not by a model setting. | No smoothing setting removed it. |
| D10 | 13 Oct | Each failed acceptance check is labeled a model miss (the oracle passes) or a data miss (the oracle fails too). | The acceptance check tests the model setting, so it must separate the model's misses from the luck of the draw. |
| D11 | 13 Oct | The synthetic DGP is frozen. | Every change moved another margin; further changes would shape the truth after what the models can find. |
| D12 | 13 Oct | E1 keeps three references apart: T (labels), the oracle (what the sample supports), M (verdicts); errors split into a data and a model layer. | Otherwise agreement mixes data, model and lexicon errors. |
| D13 | 13 Oct | Every share-based claim (strength, share, rank) gets a band and three values: true, false, undecidable. | A share alone cannot tell noise from a weak effect at n = 5,000. |
| D14 | 13 Oct | The gate's guarantee is faithfulness to M; confident errors against T are reported apart. | Bands measure sampling variance, not model bias: a shrunk but stable effect is confidently wrong against T. |
| D15 | 13 Oct | XGB2 stays fitted for prediction (early stopping on validation log loss). | That is how banks fit it; a model tuned to recover the truth is a model nobody runs. |
| D16 | 13 Oct | The lexicon is calibrated on the oracle's verdicts and the null terms of the discovery seed, never on the fitted models. | Calibrating on M would move thresholds until shrunk effects pass, hiding model error in the lexicon. |
| D17 | 13 Oct | Bootstrap refits use Poisson counts as weights, one code path for both models. | Resampled duplicate rows leak into the EBM's internal validation split. |
| D18 | 13 Oct | The EBM setting is rechecked on fresh seeds (4–6) by a rule fixed before the run. | It was chosen on seeds 1–3, which include the confirmation seeds. |
| D19 | 13 Oct | XGB2 is decomposed exactly into step terms, checked against its own leaves; TreeSHAP is only a cross-check. | Every number in the Facts can be reproduced from the model file. |
| D20 | 13 Oct | One purification and centering path for both models (`facts/steps.py`). | Any additive model is summarized the same way, so "strong" means the same for each. |
| D21 | 13 Oct | The Facts store the bootstrap draws with the bands (curves: pointwise and simultaneous; scalars: percentile). | New claim types get bands without refitting. |
| D22 | 13 Oct | Interactions are read as conditional effects: one feature from its 5th to its 95th percentile, the other at its 5th and 95th. | How a credit officer reads an interaction, at values that occur in the data. |
| D23 | 13 Oct | The bands must pass a null check fixed before the run (at least 32 of 36 noise curves covered). | The bands are validated before anything relies on them. |
| D24 | 13 Oct | The binding acceptance run uses the frozen lexicon with three-valued verdicts; E1 does not wait for a pass, and the remaining model misses enter E1 as its model layer. | Point checks fail on tolerance edges; tuning further would shape the setting after the result. |
| D25 | 13 Oct | "Negligible" is judged on significance and size: true needs a share band below 2%, or no detectable effect, an estimated share below 2% and a band below 5%; every word asserting an effect needs a detectable one. | A null term's share is biased upward, while its curve bands cover 0. |
| D26 | 13 Oct | Every acceptance check runs on XGB2 through its exact decomposition, as on the EBM. | The same validation for every model class. |
| D27 | 13 Oct | The XGB2 decomposition is compared with PiML's before the paper says anything about PiML (`piml_check/`). They agree. | A statement about a tool is checked against the tool first. |
| D28 | 13 Oct | What the paper says about PiML is limited to what was measured; tool findings go to the tool's maintainers. | As a validator would raise them. |
| D29 | 14 Oct | "Mostly increases" needs a detected exception, otherwise it is undecidable; "increases" stays certified when no exception is detected. | "Mostly" asserts an exception, so it needs an observed one. |
| D30 | 14 Oct | Undecidable claims are never released as stated: the writer hedges them (`unsettled(...)`) or states a set; every undecidable verdict carries a reason code. | The gate must not release a coin flip. |
| D31 | 14 Oct | E1's metrics for three-valued verdicts: decided rate, accuracy among decided, confident errors (a false claim certified or a true one refuted). | Agreement alone hides abstentions. |
| D32 | 14 Oct | Mutation operators work in the lexicon's units, with controls; caught means not released; M10 (strict against "mostly") has no label and is reported by n. | A mutant must be an error by the lexicon's own rules. |
| D33 | 14 Oct | Sets of values ("weak to moderate", "second or third", "generally decreases") are judged by the band-in-set rule. | The writer can state what a wide band supports. |
| D34 | 14 Oct | After E1 on the discovery seed: strict direction words are judged at the resolution of the model's bands; lexicon v1 is kept and the credit-history case reported. | Both models trace the bump at 36 months, but their bands do not resolve the rise before it. |
| D35 | 14 Oct | The US frame is SR 26-2 / OCC Bulletin 2026-13, with SR 11-7 as its predecessor. | The guidance in force; it leaves generative AI to the bank's own controls. |
| D36 | 14 Oct | Before E3: the gate is reported as a control: P_U with the gate off and on, E_U, the residual by exit state, always next to the exit states and the claim volume. | How a model-risk team judges any control; a gate that releases nothing has E_U = 1. |
| D37 | 14 Oct | Writer Claude Haiku 5.5 (`claude-haiku-5-5`), with a Claude Sonnet 5.5 subset (one draw per cell); Haiku 5.5 as the extractor throughout; the Batch API. | The gate, not the writer, is studied; the extractor is the fixed measuring instrument; cost. |
| D38 | 14 Oct | The API's default sampling settings. | No tuning of the writer. |
| D39 | 14 Oct | No fallback model; a refusal escalates. | Every run ends in a defined exit state. |
| D40 | 14 Oct | The writer answers in a JSON envelope; its DSL lines are parsed with `ast` against a whitelist. | Nothing the LLM writes is executed. |
| D41 | 14 Oct | The two noise features get plausible names for the writer (`months_at_address`, `num_dependents`), mapped back before verification; a naming check against opaque names, by a rule fixed in advance, decided that E3 runs both namings. | "Noise" would give the answer away; any name brings priors, so both are measured. |
| D42 | 14 Oct | After the writer pilot: lexicon v2 judges a jump or peak location on a count feature against the gap between neighboring observed values. E1 and the binding run did not change; plan-level E2 was rerun. | "Risk jumps at 1 delinquency" was certified for XGB2 (cut at 1.0) and refuted for the EBM (cut at 0.5). |
| D43 | 15 Oct | The extractor sees the text, the feature names and descriptions and the word table, never the facts or the plan. | It must read the text as a reader would. |
| D44 | 15 Oct | The round trip verifies claims the text states beyond its plan, counts coverage on the text, and blocks a statement no DSL form expresses if it states a number (flags it otherwise). | What the reader gets is checked, not only the plan. |
| D45 | 15 Oct | The opening sentence may not lead with a minor term (the emphasis rule). | A logically sound text can still mislead by emphasis. |
| D46 | 15 Oct | Repair messages say why a claim failed (prompt v3); the no-progress rule treats a jump or peak on a curve without one as one problem. | The writer can only fix what it understands. |
| D47 | 15 Oct | The paper keeps its global core and ends with a local spot check (adverse-action reasons) on the same models and gate. | Banks need both; the local case reuses the gate. |
| D48 | 15 Oct | The LLM-written mutants are also read with extractor x4; false alarms are measured on E3's released texts with independent readings, labeling only what a reading blocks. | The cost of the gate on LLM-written text had not been measured. |
| D49 | 15 Oct | The local spot check, fixed before it ran: seed 2 at n = 50,000, both models, 54 notices; declined = the riskiest 20%; reference = the unweighted average of the 500 approved applicants closest to the cutoff; a reason is material from 10% of the score gap, at most four reasons. | A design fixed and priced in advance. |
| D50 | 16 Oct | The D42 edge case (3 of 17 plasmode location controls refuted) is reported as a limit, not fixed; the lexicon stays frozen. | A fix after the results would need E1 and E2 rerun on every seed. |
| D51 | 16 Oct | Extractor x4 for the remaining runs, both versions reported side by side: x4 blocks 14.3% of correct texts against 7.7% for x3, and catches 85% of invented features against 36%. | No new paid run, nothing tuned on labeled data. |
| D52 | 17 Oct | The readable handover's merged steps (a gradual rise shown as a few large steps, which invites jump claims) are reported, not fixed. | The prompts and the handover were frozen, and E3 ran on them. |
| D53 | 16 Oct | Three conventions of the local spot check: no principal reason is true against T where T's gap is not positive; a notice must state every principal reason certified under M; local prompts are frozen apart. | Regulation B asks for the principal reasons. |
| D54 | 17 Oct | Plasmode text-level E2: the extractor sees the column codes with the data dictionary's descriptions; one seed. | The texts use plain words, the model column codes. |
| D55 | 17 Oct | A self-hosted open-weight writer (`qwen3.8:27b` through Ollama) as a third E3 writer, with the same extractor. | Banks that host their own models: the facts stay on their hardware. |
| D56 | 19 Oct | An LLM critic (an LLM given the facts and a text, asked to flag errors) is compared with the gate on texts already labeled, in this paper. Run 20 Oct (D61). | The first question model risk asks: why not ask another LLM? |
| D57 | 19 Oct | The released text as a distribution (many draws of one cell) is left to later work. | The paper's question is the gate's effect per draft. |
| D58 | 19 Oct | Four metrics planned for E1 and E3 are computed from results on disk: EBM against XGB2 verdicts, stability across draws, the expressivity gap and Holm-corrected contrasts. Not yet computed. | Promised in the plan's experiment list. |
| D61 | 20 Oct | The critic is another vendor's model: OpenAI's GPT-6 Luna (priced like Claude Haiku 5.5) on every set, GPT-6.1 Sol (priced like Claude Sonnet 5.5) on the labelled LLM mutants and the template texts; reasoning effort medium. It gets the writer's facts (H1), the writer's rules for choosing words and the round trip's coverage and emphasis rules. Prompts c1, frozen after two pilot rounds on the pilot datasets (`llm/prompts/frozen_critic.json`; round 1 judged phrasing against the rules, so round 2 says a true but less precise statement is supported). Scored against the final labels and the author's first-pass labels, and on E3's released texts with labels of its flags. | A critic of the writer's own model family could share its blind spots; the critic gets everything the writer had, so the comparison is with the strongest version of the alternative. The first-pass labels are free of the lexicon's and any LLM's reading. |
| D62 | 20 Oct | The author's labels of the critic's flags on E3's released texts (40 texts sampled from the 300 it blocks) are reported as the author's reading, with each flag's type (`flag_types.csv`): most errors follow the writer's prompt where it states a stricter rule than the lexicon (five rules differ: strict direction, "do not interact", "hardly matters", the growth of an effect, jumps); five are statements the round trip does not check. The prompts and the lexicon stay frozen; the differences are reported, and fixing them is later work. | Relabelling after seeing the result would invite bias; the types show which errors the gate missed and which are readings the lexicon makes differently. |

D59 and D60 concern circulating the draft, not the method.

## Plan sections cited in the code

| Section | Date | Topic |
|---|---|---|
| §0 | | Guiding principles: sound method; practical for banks and fintechs |
| §4.1, §4.4 | | The synthetic tier's DGP; the plasmode tier |
| §5, §5.1–§5.8 | | The pipeline: fact provider, DSL, lexicon, handover, writer, verifier, round trip, gate and stop rules |
| §6, §7, §8 | | Experiments E1–E3; the worked example; the paper's outline |
| §11, §12, §13 | | Risks; open decisions; the definition of done |
| §14, §14.1, §14.2 | 13 Oct | Week-1 results; the DGP strengthened; root causes and decisions D1–D18 |
| §14.3, §14.4 | 13 Oct | Fact providers for both models (D19–D23); the recheck, the bootstrap bands and the null check; the PiML check |
| §14.5 | 13 Oct | Facts for the oracle and T; lexicon v0, the DSL and the verifier; D24–D28 |
| §14.7, §14.8 | 14 Oct | D29–D33 built; the readable handover checked against the exact model |
| §14.9, §14.10 | 14 Oct | The calibration rule, fixed before the run; E1 on the discovery seed and the binding acceptance run (D34) |
| §14.11, §14.12 | 14 Oct | Plan-level E2; SR 26-2 and the gate as a control (D35, D36) |
| §14.14 | 14 Oct | The LLM part specified (D37–D41); the pilot; prompt v2; lexicon v2 (D42) |
| §14.15, §14.16 | 15 Oct | The round trip (D43–D46); E3's results |
| §14.17–§14.20 | 15 Oct | Text-level E2; extractor x4; the labels of the LLM-written errors (D47, D48); confirmation seeds and the plasmode tier (D49) |
| §14.21, §14.22 | 16 Oct | The false-alarm labels (D50, D51); the local spot check (D53) |
| §14.23 | 17 Oct | E3 against T without hedges; plasmode text-level E2 (D54); D52; the figures, tables and worked example; one command for every number (D55 prepared) |
| §14.24 | 19 Oct | The self-hosted writer's full run (run 17 Oct) |
| §14.29 | 20 Oct | The LLM critic: its pilot, prompts c1, the runs and their labels (D56, D61) |
