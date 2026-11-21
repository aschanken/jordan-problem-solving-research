# Lane A: Problem framing, diagnosis, root cause, and quality methods

Scope note: the web-fetch budget (100 per hour, shared) ran out mid-lane. Roughly 14 pages were read in full; items marked `[recalled]` come from training memory and were not re-checked this session. Items marked `[verified]` were read on the cited page this session. I did not invent URLs; where I only have a search-result title, I say so.

## Summary

1. **Diagnosis is where LLM agents measurably fail, and the failure is not lack of exploration.** In a controlled study (arXiv 2611.04473), all seven LLMs rescued a faulty system more often than they diagnosed it. Claude Opus 4.6 rescued 20 of 20 medium organisms but diagnosed 55%. In 91% of sessions the agent had already run a discriminating experiment, yet diagnostic accuracy in those sessions was 0.30. Volume of exploration did not correlate with diagnosis (r = -0.05). [verified]
2. **Predicting what each hypothesis implies is the step that rescues diagnosis.** Models scored 0.88-1.00 when given each candidate's predicted readouts, and 0.51-0.74 when they had to derive the predictions themselves (same paper). This is the strongest empirical support for a mandatory "hypothesis -> prediction -> experiment -> observation -> conclusion" record (Zeller's scientific debugging) over a bare "two candidate causes" line. [verified]
3. **Test the suspected cause in both directions.** In the same study, accuracy was 0.71 when the agent perturbed the true cause both ways, 0.04 one way, 0.00 never. Correlational only. A concrete, cheap rule: "confirm a cause by removing it and by forcing it." [verified]
4. **Coding agents misdiagnose by following the issue text and the stack trace.** An empirical failure taxonomy (arXiv 2509.13941) names "issue misleading" (agent adopts the reporter's proposed fix instead of diagnosing) and "superficial information matching" (patching the surface location). About half of agentic-tool failures contained iteration and validation errors, including misreading reproduction output and declaring success wrongly. [verified]
5. **Structured analytic techniques mostly have weak or null evidence; checklists for diagnosis show small or no effect.** ACH did not improve accuracy in the one controlled test of trained intelligence analysts (Mandel et al. 2018). A diagnostic checklist pilot RCT showed no significant error reduction. Do not make a ritual out of ACH or time-outs and expect gains. [verified]
6. **What did help in the analyst literature was aggregation and coherence repair, not method.** Averaging 50 analysts' coherentized judgments cut error 61%. Agents can run fresh-context copies, so independent-sample aggregation is the one human-debiasing result that transfers cheaply. [verified, Mandel et al.]
7. **The "no single root cause" literature is right for incidents and mostly irrelevant for a bug.** For a reproducible code defect there usually is a minimal causal change. Use root-cause search for bugs; use contributing-factor analysis for process failures and agent-run postmortems. [synthesis, grounded in verified sources below]
8. **5 Whys has no evidence of effectiveness and a documented structural flaw (one causal path).** A commissioned BMJ Quality & Safety critique recommends abandoning it for root cause analysis. A V3 diagnosis module should replace it with a branching cause tree. [verified]
9. **Framing errors are upstream of diagnosis and agents are weak at declining to answer.** Premature closure (committing when clarification or abstention was right) occurs on roughly 70% of unanswerable multiple-choice items at baseline, and an abstention prompt only cut it to about 48% (arXiv 2605.15000, medical domain). Prompts are a partial guardrail. [verified]
10. **TRIZ-style prompting has early, mixed evidence and is not a diagnosis tool.** A 2026 ACL Findings benchmark finds LLMs detect that a contradiction exists more easily than they name the correct trade-off parameter pair. TRIZ belongs, if anywhere, in the design-conflict step of DEEP planning. [verified]
11. **Late-run agent behavior degrades and anchors.** In a multi-round information-seeking benchmark, 65.6% of initially wrong diagnoses stayed wrong and 50.8% of initially right ones deteriorated; requests per round fell 7.5 -> 4.2 -> 1.8 (arXiv 2607.10275, medical). Failed coding-agent runs ran longer with wasted exploration (arXiv 2511.00197). Both support a hard "re-diagnose from scratch" trigger. [verified]

## Findings

### 1. Scientific debugging (Zeller), hypothesis log, TRAFFIC
- **What it is.** Zeller's *Why Programs Fail* treats debugging as the scientific method: observe, form a hypothesis consistent with all observations, predict a further outcome, test by experiment, refine or reject, repeat. A hypothesis that survives and predicts becomes a diagnosis. The book recommends a written log where each entry has hypothesis, prediction, experiment, observation, conclusion, so the debugger always knows where it has been. TRAFFIC is the book's seven-step procedure: Track the problem, Reproduce, Automate, Find origins, Focus, Isolate, Correct. [TRAFFIC expansion recalled; the chapter I read did not mention it.]
- **Source.** Zeller, "Why Programs Fail", chapter on the scientific method, https://www.st.cs.uni-saarland.de/whyprogramsfail/pdf/ScientificMethod.pdf [verified for the five steps and log]. Delta debugging (automatically minimizing a failing input or a failing change by systematic bisection-like narrowing) is in the same book and https://www.st.cs.uni-saarland.de/dd?lang=en (search result only) [recalled for mechanism].
- **Critiques.** Written for human programmers with deterministic reproduction; for a heisenbug or a flaky test, "reproduce" and "automate" become the whole problem. The book itself says a quick 10-minute guess phase is fine for small bugs. [verified]
- **Transfer.** Carries over strongly: the log is an external memory that survives context pressure, and the prediction column is exactly the step LLMs skip (see finding 2 in Summary and "Treating the Symptom" below). Delta debugging maps onto `git bisect` and test minimization, which an agent can run mechanically. Does not carry: humans use the log to fight forgetting; an agent's risk is confabulating observations, so each "observation" entry must paste tool output, not paraphrase.
- **V3 implication.** V3 should replace the one-line diagnosis rule with a compact hypothesis-log schema (hypothesis, what it predicts that the rivals do not, experiment command, verbatim observation, verdict) in an on-demand `diagnose` module, because the cited study shows models fail at deriving per-hypothesis predictions. Harness code could validate that the log file exists and that observation fields are non-empty before allowing an edit on a DEEP bug fix.

### 2. LLM diagnosis failure: "Treating the Symptom, Missing the Cause"
- **What it is.** A controlled study with 420 sessions (7 models x 60 synthetic regulatory-network organisms, invented gene names so priors cannot help). Agents run up to 31 perturbation experiments, predict an unseen outcome, commit a diagnosis, then try a rescue. Ground truth lets the authors compute which experiments were discriminating.
- **Source.** Workshop paper, arXiv https://arxiv.org/pdf/2611.04473 and https://neurips.cc/virtual/2026/169435 [verified]. Key numbers: cause identifiable in 53 of 60 organisms; discriminating experiments chosen 24.1% of the time vs 19.2% under random choice; full-log probe accuracy 0.88-1.00 with supplied candidate predictions, 0.51-0.74 without; both-direction perturbation of the true cause 0.71 vs 0.04 vs 0.00.
- **Critiques.** Synthetic biology setting, workshop paper, correlational on the both-directions finding (authors say so). Not a coding benchmark, so transfer is by analogy.
- **Transfer.** The failure mode (fix the symptom without knowing the cause) is the dominant risk for a coding agent whose verifier is "tests pass." Passing tests can reward a rescue that never diagnosed. Also relevant: agents integrate evidence well when the comparison is explicit, and poorly across a long trajectory.
- **V3 implication.** V3 should require, for bug-fix tasks classified STANDARD or above, that the agent state for each candidate cause the observable outcome it predicts for the next experiment, and run an experiment where predictions differ, because explicit candidate-prediction comparison is the intervention the study shows works. Belongs in an on-demand module, with the eval suite measuring "diagnosis correct" separately from "tests pass" (seed bugs with known causes and a decoy easy patch).

### 3. Empirical taxonomy of coding-agent failures
- **What it is.** Manual analysis of 150 failed SWE-bench-Verified issues (342 failure instances) into 3 phases, 9 categories, 25 subcategories (Location, Repair, Iteration and Validation).
- **Source.** arXiv https://arxiv.org/html/2509.13941v1 [verified]. Numbers: Agentless 51.3% of failures had a localization error; agentic tools about half had iteration and validation errors; flawed reasoning about 65% of root causes, knowledge deficiency about 25%, environment friction about 10%; failed agentic runs used about 3.5x more steps. An Expert agent consulted before and during fixes resolved 24 of 108 previously failed issues (22.2%) vs 7 for the baseline rerun.
- **Critiques.** Backbone was Claude 3.5 Sonnet (old), evaluation only on previously failed issues, no variance reported (authors list these). Models are now stronger; proportions may shift.
- **Transfer.** Directly actionable: "issue misleading" means the issue's proposed fix is a hypothesis, not a diagnosis. "Reproduction output misreading" means a verifier whose output the agent interprets itself can be wrong.
- **V3 implication.** V3 should add to the kernel a one-sentence rule "treat any fix proposed in the task text as an unverified hypothesis; reproduce the failure first and show the failing output" because that failure category is named and common. Kernel (one line), plus an eval case where the issue text points to a wrong fix.

### 4. Code-agent trajectories and early abandonment
- **What it is.** Empirical comparison of successful vs failed trajectories of several agents.
- **Source.** arXiv https://arxiv.org/html/2511.00197v1 [verified]. Failed trajectories were longer and more variable (about 57% longer for one agent on Lite, about 83% for OpenHands on Verified); on Verified, failing runs spent about as much effort on wrong files as right ones; most failures still found the correct file, so the error is in finer-grained reasoning; patches succeeded without matching the gold function.
- **Critiques.** Descriptive, not causal; selection effects (hard tasks produce long runs regardless).
- **Transfer.** Supports a trajectory monitor. JORDAN already has "two consecutive worsening attempts -> stop." This adds a cheap structural signal: step count versus a per-tier budget.
- **V3 implication.** V3 should put a step/token budget per tier in a hook that forces the "rebuild the diagnosis from the original symptom" action when exceeded, because long runs are the strongest failure correlate found. Harness code.

### 5. Debugger tools and fault localization at the ceiling
- **What it is.** A large controlled study seeding 610 single-line faults in 144 LeetCode programs; 65,376 episodes across three agents and tool conditions.
- **Source.** arXiv https://arxiv.org/pdf/2610.36015 [verified]. Without tools agents localized 98.2-99.9% of faults. Encouraging debugger use cost 14.7-27.0x tokens and 3.4-5.0x money for gains of at most 2.1 points; optional use gained about 1.3-1.5 points at far lower cost and agents mostly wrote probe scripts instead of stepping.
- **Critiques.** Short self-contained programs with dense tests; authors say results may not carry to multi-file repositories or vague specs.
- **Transfer.** Do not mandate interactive debuggers. "Run something and read the output" is the active ingredient, which JORDAN already encodes.
- **V3 implication.** Nothing to add to the kernel; V3 should not add a "use a debugger" rule. The eval suite should test repository-scale bugs where this study is silent.

### 6. Reproduction and issue-test generation
- **What it is.** Work on generating a failing reproduction test from an issue before patching (SWT-Bench, Otter, others), and a study of old regression tests as a resolution signal.
- **Source.** Search results only, titles not read in full: https://arxiv.org/html/2406.12952v3 (SWT-Bench), https://arxiv.org/pdf/2502.05368 (Otter), https://arxiv.org/html/2510.18270v1 (regression tests and issue resolution). I could not read these before the budget ran out. [uncertain on all numbers]
- **Critiques.** Reproduction tests generated by the same model share its misunderstanding of the issue (recalled, not verified).
- **Transfer.** Matches JORDAN's "wire the verifier first." The caveat is that a self-written reproducer can encode the wrong diagnosis.
- **V3 implication.** V3 should have the reproducer written, or at least reviewed, by a context that did not form the patch hypothesis, because a verifier authored by the diagnoser inherits its framing. Orchestration layer. Lane owners on AI testing may have the numbers.

### 7. 5 Whys and its critique
- **What it is.** Ask "why" iteratively (about five times) from a symptom to a "root cause," associated with Toyota (Ohno).
- **Source.** BMJ Quality & Safety 2016 commentary "The problem with 5 whys", https://qualitysafety.bmj.com/content/qhc/early/2016/09/02/bmjqs-2016-005849.full.pdf [verified]; Allspaw, "Each necessary, but only jointly sufficient", https://kitchensoap.com/2012/02/10/each-necessary-but-only-jointly-sufficient/ [verified]; O'Reilly "The infinite hows", https://oreilly.com/ideas/the-infinite-hows (search result only).
- **Critiques (verified).** No evidence of effectiveness; commentary, not an experiment. It forces one causal path while a causal tree for the same wrong-patient medication case showed over 75 causes and 30 pathways; a two-path 5 Whys covers 2 of 30. It privileges the most distal cause as the intervention point when a proximate forcing function may be cheaper. Allspaw: it assumes a symptom has one sufficient cause; the better question is "how", not "why."
- **Transfer.** The agent version of 5 Whys is a single linear chain of self-explanation, which is precisely the fluent confabulation LLMs produce.
- **V3 implication.** V3 should specify diagnosis as a branching cause tree with a stop rule "stop at the cause you can change and verify," and should ask "how did this become possible" for process failures, because the one-chain method is documented as covering a few percent of causal paths. On-demand module.

### 8. "No root cause" literature (Cook, Allspaw, Dekker) and blameless postmortems
- **What it is.** Cook's *How Complex Systems Fail* (18 short points) argues that catastrophe requires multiple failures, each necessary and only jointly sufficient, that post-accident attribution to a "root cause" is fundamentally wrong, and that hindsight bias distorts reconstruction. Allspaw and others turned this into blameless postmortem practice: reconstruct how each decision made sense at the time, list contributing factors, not a single cause or person.
- **Source.** https://how.complexsystems.fail/ (search result; text recalled, not re-read this session), Allspaw above [verified for "each necessary but only jointly sufficient" and the attribution to Cook, and to Hollnagel/Woods/Dekker/Cook for "Accidents emerge from a confluence of conditions"]; Dekker is only referenced there. https://surfingcomplexity.blog/2025/05/19/not-causal-chains-but-interactions-and-adaptations/ (search result, not read).
- **Critiques.** These arguments are about socio-technical systems with adaptive humans. They do not say a deterministic function has no cause; applying "no root cause" to a null-pointer bug is a category error. Also they provide no efficient search procedure, only a stance on interpretation. [synthesis]
- **Transfer.** Transfers to agent-run postmortems and to multi-agent failures (a bad brief, a missing hook and a weak verifier combine). Does not transfer to single-bug fixing.
- **V3 implication.** V3 should split diagnosis into two modes: "defect mode" (search for the minimal causal change, verify by removing it) and "incident mode" (contributing-factor list with the human decisions and system conditions that allowed it), because they use opposing stopping rules. The existing AAR output should use incident mode. On-demand module.

### 9. Strong inference and multiple working hypotheses
- **What it is.** Platt (1964, *Science*): devise alternative hypotheses, devise a crucial experiment that excludes at least one, run it, repeat on the survivors. Chamberlin (1890): hold several working hypotheses at once to avoid parental affection for a single theory.
- **Source.** Not opened this session. [recalled]
- **Critiques.** Critics note that strong inference suits fields where hypotheses are cleanly exclusive; many real faults involve interacting causes (consistent with Cook above). [recalled]
- **Transfer.** JORDAN's "two candidate causes, cheapest discriminating test" is already a compressed strong inference. The empirical data above show the compression drops the part that matters (predicted outcomes, not just a candidate list).
- **V3 implication.** Nothing new beyond finding 1; keep "cheapest discriminating test" but add "name what each hypothesis predicts."

### 10. Analysis of Competing Hypotheses and evidence on structured analytic techniques
- **What it is.** Heuer's ACH builds a matrix of hypotheses versus evidence, scores each evidence item as consistent or inconsistent with each hypothesis, and favors the hypothesis with the least inconsistent evidence (diagnosticity, not confirmation). [recalled]
- **Source.** Mandel, Karvetski, Dhami (2018), Judgment and Decision Making 13(6), https://dlab.sauder.ubc.ca/sjdm/journal/18/18803/jdm18803.html and the Cambridge version [verified]. 50 UK analysts. ACH did not improve probability accuracy: mean absolute error 0.26 vs 0.21 for controls (p = .14, d = 0.43 favoring control). ACH users rated information usefulness far better aligned with true cue value (r = .68 vs .17). Coherentizing judgments reduced error 35%; averaging all 50 reduced it 61%, mostly from the first small group. Also: https://www.cambridge.org/core/journals/judgment-and-decision-making/article/boosting-intelligence-analysts-judgment-accuracy-what-works-what-fails/1530E9DAE8F42B2E8FC2B5FE374DB50F (search result, "what works, what fails", abstract not read this session).
- **Critiques.** One study, one task, not significant (p = .14) so absence of evidence of harm, not evidence of harm. But ACH does help with evidence weighting, which is exactly diagnostic reasoning.
- **Transfer.** The "evidence usefulness" benefit is real and transfers: score each observation by whether it discriminates between hypotheses. The aggregation result transfers to agents: independent fresh-context samples averaged beat any single sample, and agents can produce them cheaply.
- **V3 implication.** V3 should offer, for ambiguous high-cost diagnoses only, N independent fresh-context diagnoses with the orchestrator comparing hypotheses and pooling, not an ACH matrix, because the aggregation effect has direct evidence and the matrix method does not improve accuracy. Orchestration layer; the eval suite should include an ablation (single vs pooled diagnosis).

### 11. Differential diagnosis, diagnostic error, checklists and time-outs
- **What it is.** Medicine's name for hypothesis-driven diagnosis: generate a differential, find the "can't miss" diagnoses, test to discriminate. Known biases: anchoring, premature closure, search satisficing. Proposed countermeasures include a "diagnostic time-out" (pause and ask what else, what could be missed) and differential checklists.
- **Source.** Ely and Graber 2015 pilot RCT, https://www.degruyterbrill.com/document/doi/10.1515/dx-2015-0008/html [verified]: 14 physicians, 100 patients; error 11.2% checklist vs 17.8% usual care, p = 0.46; checklist physicians considered 6.5 vs 3.4 diagnoses; only one diagnosis was corrected by the checklist; not powered (about 230 per arm needed). Chew et al. 2017, https://pmc.ncbi.nlm.nih.gov/articles/PMC5707798 [verified]: 88 students, overall score no difference (18.65 vs 18.15 median, p = 0.159); a first-half gain disappeared in the second half, attributed to time cost. A time-out RCT is registered at https://clinicaltrials.gov/study/NCT01868659 (search result, results not read).
- **Critiques.** Evidence base thin and underpowered. Widening the differential does not by itself change decisions.
- **Transfer.** Humans: checklist costs time and cognitive load. Agents: a checklist costs tokens but no fatigue, and an agent can run it in a fresh context. A caution from the LLM evidence below: the problem is stopping early and anchoring, which a list does not obviously fix.
- **V3 implication.** V3 should not ship a generic "consider alternatives" checklist as a kernel rule; it should gate on a concrete trigger (first fix failed, or fix confidence lower than evidence) and verify by an outcome, because the checklist evidence shows breadth without accuracy gain. Eval suite should measure breadth vs correctness explicitly.

### 12. LLM premature closure, anchoring, and information-seeking
- **What it is.** Two 2026 medical-domain studies of the same failure modes in LLMs.
- **Source.** arXiv https://arxiv.org/pdf/2605.15000 [verified]: five frontier models; at baseline about 70% commit to an answer on questions with the correct option removed, about 48% with an abstention prompt; in open-ended questions premature closure ranged 20.7% to 44.6% at baseline and fell 4.2-7.9 points with a safety prompt; adversarial cases remained 50.8% at best. arXiv 2607.10275 (via https://www.alphaxiv.org/abs/2607.10275) [verified]: 32 models, best 68.1%; differential diagnosis was the weakest component (43.6% average); information requests per round fell 7.5, 4.2, 1.8; 65.6% of initially wrong diagnoses stayed wrong; 50.8% of initially correct ones deteriorated.
- **Critiques.** Medical question settings, LLM judges (a hematologist-validated judge in the second, kappa 0.804). Not coding.
- **Transfer.** The behaviors map: stop gathering data early, fail to revise an initial diagnosis, keep a wrong anchor. Prompts are a "partial guardrail" per the authors.
- **V3 implication.** V3 should enforce "revise the diagnosis" mechanically: after a failed fix attempt, the next step is to restate the symptom from raw output without reading the prior hypothesis, because anchoring persists in most wrong cases. Harness code (a hook that clears or hides the previous hypothesis block and asks for a fresh one) plus an eval.

### 13. Kepner-Tregoe IS / IS NOT problem analysis
- **What it is.** Specify the problem on four dimensions (what, where, when, extent), writing what IS affected and the comparable thing that IS NOT. For each IS entry find the distinction from the IS NOT, then ask what changed in that distinction. Each candidate cause must explain every IS and IS NOT fact; the one that needs the fewest assumptions is tested.
- **Source.** I could not retrieve a primary description. KT site page I opened did not describe the method; search results included https://kepner-tregoe.com/app/uploads/2024/07/PA-Application-Guide_22July2024.pdf and https://kepner-tregoe.com/wp-content/uploads/2025/08/Updated-ATS-Process-Cards.pdf (not read). Mechanism above is [recalled].
- **Critiques.** [recalled] effective for deterministic production faults, laborious when facts are sparse; no controlled evidence found.
- **Transfer.** Excellent fit for coding: IS/IS NOT is exactly "which inputs fail and which similar ones pass, which commit, which environment." It forces comparison of failing and passing cases, which agents skip. Change analysis is `git log` between last-good and first-bad.
- **V3 implication.** V3 should include IS/IS-NOT as the first step of the `diagnose` module: record one passing near-neighbor for every failing case before hypothesizing, and use bisection where a good revision exists, because a discriminating contrast is the cheapest test. On-demand module.

### 14. Agans's nine rules; bisection; rubber duck; observability
- **What it is.** Agans's rules: understand the system, make it fail, quit thinking and look, divide and conquer, change one thing at a time, keep an audit trail, check the plug, get a fresh view, if you did not fix it it is not fixed. [recalled]
- **Source.** Search result https://courses.cs.washington.edu/courses/cse466/15au/pdfs/lectures/DebuggingRules.pdf (not read). [recalled]
- **Critiques.** Folk wisdom without controlled evidence, but "quit thinking and look" is borne out by the finding that agent exploration without discrimination does not help.
- **Transfer.** "Change one thing at a time," "keep an audit trail," and "if you didn't fix it, it isn't fixed" all map to the existing micro-loop. "Get a fresh view" maps to fresh-context refuters, which JORDAN already has. Rubber-duck is the agent's own written hypothesis log.
- **V3 implication.** Nothing new beyond finding 1 and 13; v2 already covers these.

### 15. Toyota Kata, A3, PDCA, jidoka, poka-yoke, genchi genbutsu
- **What it is.** PDCA/PDSA (Shewhart, Deming) is a cycle with a prediction in Plan and a comparison of outcome to prediction in Study. Rother's improvement kata: understand direction, grasp the current condition, set the next target condition, run one experiment at a time toward it, record the result. Jidoka stops the line on abnormality; andon signals; poka-yoke makes the error impossible or immediately visible; genchi genbutsu is go and see the real place. [recalled]
- **Source.** Evidence on Toyota Kata effectiveness: Lodgaard et al. 2023 case study, https://sintef.brage.unit.no/sintef-xmlui/bitstream/11250/3096409/4/Lodgaard_2023_Toyota_Kata_AAM.pdf [verified]: single action-research case, team-reported 40% lead-time reduction with no baseline or control, claims of high effectiveness rest largely on Rother's book. A3 as mentoring and standard work: [recalled, not re-read].
- **Critiques.** Evidence for Kata is anecdotal and case-based (verified above).
- **Transfer.** Two parts carry well. First, "single-factor experiments toward a target condition" is the same as hypothesis testing by one change at a time; v2 already has it. Second, poka-yoke and jidoka are harness enforcement: block the wrong action rather than ask the agent to remember. JORDAN's prior internal review reached the same conclusion. A3 as a coaching conversation maps to the intake interrogation of operator intent.
- **V3 implication.** V3 should state that every recurring agent failure found in an AAR becomes a poka-yoke (a hook, a lint, a schema), not a prompt sentence, because prompt reminders have partial effects (see finding 12) while a forcing function does not rely on recall. Harness code.

### 16. FMEA, fault tree analysis, Ishikawa, 8D, change analysis, causal factor charting
- **What it is.** FMEA ranks failure modes by severity, occurrence and detection (risk priority number); fault tree analysis works top-down from a hazard with AND/OR gates to find minimal cut sets; Ishikawa groups candidate causes; 8D is a staged team procedure (containment, root cause, escape point, permanent fix, prevention); change analysis compares working vs broken; causal factor charting sequences events and conditions. [recalled; I did not open sources this session]
- **Critiques.** FMEA RPN multiplies ordinal scores and is widely criticized for that (recalled). 8D and Ishikawa are checklists for team discipline, with no outcome evidence found this session.
- **Transfer.** Two ingredients stand out for agents. 8D's separation of **containment** (stop the bleeding) from **root-cause fix**, and its **escape point** question ("why was this not caught earlier"), which converts each bug into a missing check. Fault tree cut sets help when a failure needs several conditions together.
- **V3 implication.** V3 should add an "escape point" line to the report for any fixed bug: which check should have caught this, and add it as a regression test, because it makes each fix improve the verifier. Kernel line or module; JORDAN already says "compound or decay," so this is mostly a concrete form of it.

### 17. Polya, IDEAL, issue trees, the day-one answer, Minto
- **What it is.** Polya: understand the problem, devise a plan, carry out, look back; heuristics include "solve a simpler related problem," "work backward," "can you check the result." Issue trees break a question into mutually exclusive, collectively exhaustive branches; the day-one answer states a hypothesis immediately and the work tries to falsify it; Minto's pyramid presents the answer first. [recalled; sources not opened]
- **Critiques.** Day-one answers invite confirmation bias unless the work is designed to disprove them. [recalled]
- **Transfer.** The day-one answer is the discipline of a falsifiable guess, which is the opposite of premature closure only if paired with a refutation test. Agents are strong at producing a plausible day-one answer and weak at disconfirming it (finding 12), so the pairing must be enforced.
- **V3 implication.** V3 should require that a day-one hypothesis come with the test that would falsify it and that the falsifying test run before the patch is written, because plausible reasoning correlated only moderately (R = 0.56) with correct conclusions in the cited benchmark. Kernel (one line) in the plan step.

### 18. Problem framing: reframing, "Are your lights on?", wicked and tame problems, Stacey, SSM, Ackoff
- **What it is.** Wedell-Wedellsborg: generate several reframings before solving, with moves such as looking at bright spots (where the problem is absent), looking at the user's own contribution, questioning the stated goal. Gause and Weinberg: "a problem is a difference between things as desired and things as perceived," and who owns the difference. Rittel and Webber: wicked problems have no definitive formulation and each attempt is a one-shot; Checkland's SSM uses rich pictures and the CATWOE checklist; Ackoff distinguished resolving, solving and dissolving. [recalled; Wedell-Wedellsborg and Rittel-Webber sources found by search, not read: https://www.aspeninstitute.org/wp-content/uploads/2026/06/Are-You-Solving-the-Right-Problems_-Thomas-Wedell-Wedellsborg.pdf, https://nautilus.org/gps/solving/ten-criteria-for-wicked-problems/]
- **Critiques.** All advocacy-level evidence; no controlled trials found. Wicked-problem language is regularly misapplied to ordinary hard problems.
- **Transfer.** An agent given a task text has an unverified frame by default. The cheapest reframe is the "bright spot": find a case where the symptom is absent, which is IS/IS NOT again. The Gause-Weinberg question "whose difference is this" is the intake interrogation JORDAN already has.
- **V3 implication.** V3 should add to intake a "frame check" of two sentences: the problem as the operator stated it, and one alternative frame (including "no change needed" or "wrong layer"), because the failure taxonomy shows agents adopt the issue's framing. On-demand (STANDARD and above), orchestration layer for intake.

### 19. Cynefin since 2020
- **What it is.** Snowden's framework now has liminal states between domains (notably complex to complicated), a managed-confusion "aporia" move, a 2021 revision, and an EU Joint Research Centre field guide for crisis decisions.
- **Source.** https://cynefin.io/wiki/Cynefin [verified for liminal states, aporia, the 2021 revision and field guide]; https://publications.jrc.ec.europa.eu/repository/handle/JRC123629 (search result, not read) and https://cynefin.io/wiki/Field_guide_to_managing_complexity_(and_chaos)_in_times_of_crisis (search result, not read).
- **Critiques.** The wiki itself calls it "a framework, not a method." No outcome studies found. [verified for the quote; absence of studies is a search result]
- **Transfer.** The useful operational idea is "probe-sense-respond" for complex situations: run a safe-to-fail experiment, then classify. The complex-to-complicated transition is exactly what an exploration phase ends with. This lines up with v2's "start low and promote at surprise."
- **V3 implication.** V3 should treat the exploratory spike (a cheap, reversible, time-boxed probe) as an explicit step before classification when the domain is unfamiliar, and record what moved the task from complex to complicated, because v2's classifier scores familiarity without a way to improve it. On-demand module.

### 20. TRIZ at depth and LLMs
- **What it is.** TRIZ (Altshuller) separates a technical contradiction (improving A worsens B) from a physical contradiction (one parameter must be both high and low), uses the contradiction matrix to point to inventive principles, defines an "ideal final result" (the function delivered with no cost or harm), and ARIZ as an algorithmic sequence of reformulations. [recalled]
- **Source.** Wang and Uzzi, "Inventive Problem Solving with LLMs: A Benchmark for TRIZ Reasoning", Findings of ACL 2026, https://aclanthology.org/2026.findings-acl.1798/ [verified]: LLMs find it easier to detect that a contradiction exists than to name the trade-off parameter pair; principle prediction improves when the model uses TRIZ structure explicitly. Also AutoTRIZ https://arxiv.org/html/2403.13002v2 and TRIZ-GPT https://arxiv.org/pdf/2408.05897 (search results, not read; earlier work "small and rarely used patent text" per the benchmark paper).
- **Critiques.** TRIZ validity itself has little controlled evidence; LLM studies measure agreement with human labels, not problem-solving outcomes.
- **Transfer.** Contradiction framing is useful at design time ("the fix for X breaks Y"), and the "ideal final result" is the same move as writing acceptance criteria before a plan. Not for diagnosis.
- **V3 implication.** V3 should offer a "name the contradiction" line in the competing-COA module (what two requirements conflict, and which one gives), because forcing the conflict into the open helps pick between COAs; do not claim TRIZ improves agent outcomes since no downstream result was found. On-demand module, eval suite should test it before it graduates.

### 21. Apollo RCA, Ishikawa-style cause mapping, and other methods
- **What it is.** Apollo root cause analysis (Gano) builds a cause-and-effect chart where every effect has at least two causes (an action and a condition) and each box is tied to evidence. [recalled; sources not read this session]
- **Critiques.** Same chart-vs-reality concerns as Cook; its useful rule is the evidence-per-box requirement.
- **Transfer.** "Every causal claim cites evidence or is marked as an assumption" is the provenance principle already in JORDAN.
- **V3 implication.** Nothing new; v2 covers provenance. The module can cite Apollo as the model for a cause tree with evidence tags.

## Contradictions with JORDAN v2

1. **One line for diagnosis is under-specified.** "Name at least two candidate causes and run the cheapest test that tells them apart" omits predicting each candidate's outcome, which is the step where models fail (0.88-1.00 vs 0.51-0.74).
2. **Verifier = "tests pass" can be satisfied by a symptom rescue.** The cited study found rescue without diagnosis across all seven models. V3 needs a separate diagnosis check.
3. **"Reproduce before fixing" is in v2 but the reproducer may be authored by the diagnosing context.** Failure taxonomy shows reproduction misreading and insufficient verification as major failure classes.
4. **Prompt-only debiasing is weaker than v2's kernel language implies.** The abstention prompt left most adversarial cases still failing; checklist trials show breadth without accuracy gain.
5. **The root-cause model in v2 (single root, "the cause") fits defects but not incidents or multi-agent failures.**

## Hype and weak evidence

- ACH: popular, one controlled test, no accuracy gain. Treat as a way to weigh evidence, not as an accuracy booster.
- 5 Whys: no evidence of effectiveness; documented structural flaw.
- Toyota Kata effectiveness claims: single-case, team-reported, no baseline.
- Diagnostic time-outs and checklists: small and underpowered trials, no demonstrated error reduction.
- TRIZ for LLMs: benchmarks of label agreement, not outcome improvements.
- Cynefin, wicked problems, SSM, reframing: advocacy-level; no outcome evidence found.
- Numbers in the medical LLM papers are medical benchmarks; I did not find a coding-specific replication.

## Gaps

- Could not read primary pages for Polya, IDEAL, Minto/McKinsey, 8D, FMEA, Ishikawa, FTA, Apollo, Platt, Chamberlin, Agans, Gause-Weinberg, Stacey, Checkland, Ackoff, Kepner-Tregoe (method description), Dekker's own writings, Cook's original text, A3, poka-yoke, jidoka. All are [recalled].
- Did not read SWT-Bench, Otter, SWE-Doctor, DistDebug-Bench or regression-tests papers; names appear only as search results.
- No evidence found on LLM prompts that use Polya, IDEAL, KT or issue trees specifically (searches returned none; not exhaustive).
- Did not find any head-to-head test of scientific-debugging prompting vs baseline on real repository bugs in 2025-2026; a likely eval gap. An early 2023 paper "Explainable Automated Debugging via LLM-driven Scientific Debugging" (https://arxiv.org/pdf/2304.02195) appears relevant but I did not read it.
- Allspaw and Cook were read secondhand; Dekker not read.

## Sources

- https://arxiv.org/pdf/2611.04473
- https://neurips.cc/virtual/2026/169435
- https://arxiv.org/html/2509.13941v1
- https://arxiv.org/html/2511.00197v1
- https://arxiv.org/pdf/2610.36015
- https://arxiv.org/pdf/2605.15000
- https://www.alphaxiv.org/abs/2607.10275
- https://aclanthology.org/2026.findings-acl.1798/
- https://qualitysafety.bmj.com/content/qhc/early/2016/09/02/bmjqs-2016-005849.full.pdf
- https://kitchensoap.com/2012/02/10/each-necessary-but-only-jointly-sufficient/
- https://dlab.sauder.ubc.ca/sjdm/journal/18/18803/jdm18803.html
- https://www.cambridge.org/core/journals/judgment-and-decision-making/article/boosting-intelligence-analysts-judgment-accuracy-what-works-what-fails/1530E9DAE8F42B2E8FC2B5FE374DB50F
- https://www.degruyterbrill.com/document/doi/10.1515/dx-2015-0008/html
- https://pmc.ncbi.nlm.nih.gov/articles/PMC5707798
- https://clinicaltrials.gov/study/NCT01868659
- https://cynefin.io/wiki/Cynefin
- https://publications.jrc.ec.europa.eu/repository/handle/JRC123629
- https://www.st.cs.uni-saarland.de/whyprogramsfail/pdf/ScientificMethod.pdf
- https://www.st.cs.uni-saarland.de/dd?lang=en
- https://sintef.brage.unit.no/sintef-xmlui/bitstream/11250/3096409/4/Lodgaard_2023_Toyota_Kata_AAM.pdf
- https://how.complexsystems.fail/
- https://surfingcomplexity.blog/2025/05/19/not-causal-chains-but-interactions-and-adaptations/
- https://oreilly.com/ideas/the-infinite-hows
- https://courses.cs.washington.edu/courses/cse466/15au/pdfs/lectures/DebuggingRules.pdf
- https://arxiv.org/html/2406.12952v3
- https://arxiv.org/pdf/2502.05368
- https://arxiv.org/html/2510.18270v1
- https://arxiv.org/pdf/2304.02195
- https://arxiv.org/html/2403.13002v2
- https://arxiv.org/pdf/2408.05897
- https://kepner-tregoe.com/app/uploads/2024/07/PA-Application-Guide_22July2024.pdf
- https://www.aspeninstitute.org/wp-content/uploads/2026/06/Are-You-Solving-the-Right-Problems_-Thomas-Wedell-Wedellsborg.pdf
- https://nautilus.org/gps/solving/ten-criteria-for-wicked-problems/
