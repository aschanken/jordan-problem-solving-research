# Lane B: Decision science, expert cognition and high-reliability operations

Provenance note. About 30 searches were run and about 15 pages were read. Page reading was cut short when the shared fetch budget ran out (HTTP 403, "100 per hour, shared by every agent"). Anything marked [verified] was read on the cited page this session. [recalled] means from training memory and unchecked. Several PubMed pages returned only boilerplate, so some well-known numbers (Haynes 2009, Tetlock) are [recalled]; a search snippet confirmed the source exists but not its figures.

## Summary (what matters most for V3)

1. **The RPD/Klein evidence undercuts "always generate 2-3 COAs" as a default.** Experts in time-pressured domains usually generate one workable option, mentally test it, and go. The Army tested this as the Recognition Planning Model (RPM), and participants estimated about 30% less planning time. That figure is a perception, not a measurement. Kahneman and Klein agree this only holds in high-validity environments. Software work mixes both kinds of environment. V3 should make multi-COA conditional on low validity or irreversibility, and not default it to "DEEP".
2. **Multi-COA is best supported when options are generated independently and cheaply, then compared on a small number of criteria.** The supporting evidence is the aggregation literature (independent judgments beat discussion) and set-based design. It is not supported as an in-one-context debate between personas.
3. **Premortem is the best-supported item in JORDAN v2, but the evidence is thin and old.** The original prospective-hindsight result is a lab study of about 30% more reasons generated [recalled]. Field evidence is descriptive only. The persona-lens count (4 or 5) has no evidence behind it.
4. **Human approval gates decay.** Anthropic's own data says users accept 93% of permission prompts [verified]. Their classifier-based answer has a 17% false-negative rate on real overeager actions [verified]. An always-on human gate for DEEP is only safe if approvals are rare, high-signal, and carry specific evidence. Otherwise the gate becomes theater (Bainbridge's monitoring irony).
5. **Handoff structure has real, measured effect.** I-PASS: medical errors fell 23% and preventable adverse events 30% across 9 hospitals [verified]. The mechanism is a fixed, read-back-able structure (illness severity, patient summary, action list, situation awareness and contingency, synthesis by receiver). V3's handoff files and worker briefs should use a fixed schema with receiver synthesis.
6. **Checklists work when they are short, owned, and enforced, and fail when they are imposed as ritual.** The Ontario study found no measurable change in outcomes after mandated WHO checklists [verified at title/abstract level via search]. Read-do versus do-confirm distinction (Degani and Wiener) maps to what a hook should enforce versus what a model should self-confirm.
7. **Independent-then-aggregate beats discuss-then-decide.** Nominal groups out-generate brainstorming groups roughly two to one, driven by production blocking [verified]. Forecasting teams that shared and critiqued did beat independent forecasters in Tetlock's tournament, so structured sharing helps once individuals have committed estimates [verified]. For an AI lead, this means: fan out independent fresh-context workers first, then compare.
8. **Authentic dissent beats role-played devil's advocacy (Nemeth).** A refuter instructed to attack is the analogue of a devil's advocate. The evidence suggests a refuter that holds its own independently derived answer is more valuable than one told to object [verified via an interview; primary papers not read].
9. **Safety science says the recovery ladder's monotonic escalation is sound, but the premise "each rung is safe" is not.** Reason, Rasmussen, Vaughan, Hollnagel all describe drift: local adaptations that each look safe but erode margins. V3 needs a drift detector (rising count of overrides, skipped gates, relaxed acceptance criteria), not only per-task gates.
10. **Lessons-learned stores mostly fail to change behavior.** Surveys of lessons-learned programs list the same failure modes: nobody owns the lesson, retrieval is not at the point of decision, and lessons stay at single-loop (fix the symptom) level. V3's experience store must inject lessons at decision time and test whether they change outcomes.
11. **Span of control (about 3 to 7, optimal about 5 in ICS doctrine [recalled]) is a human limit, not an agent limit, but the analogous agent limit is lead context, not attention.** Cap concurrent workers by the lead's ability to read and arbitrate their reports.

## Findings

### 1. Recognition-Primed Decision (RPD) and the Recognition Planning Model (RPM)

**What it is.** Klein's field studies of fireground commanders found that experienced decision-makers typically recognize a situation as a type (with expected cues, goals and typical action), pick the first workable action, and run a quick mental simulation to see whether it will fail. They only move to another option if the simulation finds a flaw. This is satisficing in Simon's sense. The RPM took this into planning: instead of MDMP's compare-several-COAs step, a staff develops one COA, wargames it for flaws, and modifies or replaces it.
**Source.** Ross, Klein, Thunholm, Schmitt, Baxter, "The Recognition-Primed Decision Model," Military Review, July-August 2004 (https://apps.dtic.mil/sti/tr/pdf/ADA521492.pdf) [verified]. Fireground text: USDA Forest Service reprint stating that about 80 percent of decisions were made in under a minute and commanders evaluated one option at a time (https://www.fs.usda.gov/t-d/pubs/htmlpubs/htm95512855/page13.htm) [verified]. The widely quoted "about 80% recognition, about 12% option comparison" split was not found on the pages read; the Forest Service page explicitly gives no percentage [verified], so treat that split as [recalled].
**Critiques and failure modes.** The Army test was a 2-week experiment with an ad hoc brigade staff, 2 days of training and 5 days of exercise, using observations, questionnaires and interviews. The 30% time saving was participants' estimate, not a stopwatch result. Participants worried about rushed mission analysis, and one colonel said it justified more research, not replacing MDMP [all verified]. The 20% tempo gain cited in the same article came from Swedish Army research, not the US test [verified]. Recognition requires expertise in a stable environment (see Finding 2); novices have no patterns to match.
**Transfer.** An LLM agent has strong pattern recognition from training, so RPD resembles its default behavior (generate the first plausible fix). That is a risk as much as a strength: the agent's "recognition" is not validated by feedback in this repo. What carries over is the structure: one candidate, then an explicit simulation or check for flaws, then escalate to alternatives only when the check fails. What does not carry over: the commander's calibrated confidence. An agent's felt confidence is not evidence.
**V3 implication.** V3 should make single-COA-plus-adversarial-check the default for STANDARD and DEEP, and require 2-3 COAs only when a trigger fires (first COA fails its flaw check, the change is one-way or irreversible, or the problem is novel with no verifier). This belongs in the on-demand COA module as a trigger rule, with the trigger list also written into the classifier. Testable: compare cost and success on a task set under always-3-COA versus triggered-COA.

### 2. Kahneman and Klein, "Conditions for intuitive expertise: a failure to disagree"

**What it is.** The two opposing traditions (heuristics and biases; naturalistic decision making) jointly conclude that intuitive judgment is trustworthy when (a) the environment has stable, learnable regularities (high validity) and (b) the person had adequate practice with feedback. Subjective confidence is not a reliable indicator of accuracy.
**Source.** American Psychologist, 2009, https://pubmed.ncbi.nlm.nih.gov/19739881/ [verified by summary of abstract only; page fetch returned a paraphrase].
**Critiques.** The framework is qualitative; it does not give thresholds for "high validity."
**Transfer.** For a coding agent, high-validity sub-areas exist (compile errors, type errors, well-tested library APIs: fast, unambiguous feedback). Low-validity areas include architecture choices, requirement interpretation and "will this scale." The classifier can use validity as a feature: is there a fast, trustworthy verifier?
**V3 implication.** V3 should add "verifier validity" to CLASSIFY, as a question: "is there a fast, unambiguous check?" If yes, trust the first plan and let the check catch errors. If no, require independent review before executing. Kernel (one line) plus eval suite (measure whether classification by verifier validity predicts rework).

### 3. Premortem (prospective hindsight) evidence

**What it is.** Participants imagine the project has already failed, then write reasons why. Mitchell, Russo and Pennington (1989) found that this framing generates more and more specific reasons than forecasting "what might go wrong" [recalled; the commonly cited increase is about 30%, unchecked here]. Klein adapted it into the premortem.
**Source.** Original: Mitchell, Russo, Pennington, Journal of Behavioral Decision Making, 1989 [recalled; not opened]. A 2022 field application: https://par.nsf.gov/servlets/purl/10435109 [verified]: six-person team, 1.5 hours, 17 and 13 unique failures and 15 to 18 solutions per session, with no control condition and no follow-up on whether risks materialized. The paper itself cites Veinott et al. 2010 and Peabody and Veinott 2017 for the comparative claims [verified that it cites them; those papers not read].
**Critiques.** The field evidence is descriptive and self-judged. The 2022 authors say premortems "do not provide guarantees of completeness" and recommend predefined risk taxonomies for high-hazard systems [verified]. Nothing found supports a specific persona count.
**Transfer.** Cheap for an agent. The main value in human teams is licensing dissent and removing the social cost of pessimism; agents do not have that social cost, so the value is mostly the prospective-hindsight prompt and enumeration. A single fresh-context model asked "this failed; write the cause" probably covers most of the value. Personas are a diversity heuristic whose benefit over simple resampling is untested.
**V3 implication.** V3 should keep premortem but (a) run it as N independent fresh-context samples with a fixed prompt rather than one context role-playing several personas, (b) merge and de-duplicate, and (c) convert findings into checks the harness can run (the compile-to-watchdog step in v2 is the right idea). Orchestration layer plus eval: test whether persona lenses add distinct failure modes versus resampled generic premortem.

### 4. Sensemaking (Weick) and the data-frame model (Klein)

**What it is.** Weick: people act to make sense of ambiguous situations, building plausible accounts retrospectively; sensemaking fails when a frame is held too long. Klein's data-frame model: people have a frame (story) that selects and shapes data, and data that does not fit prompts frame elaboration, questioning or replacement. [recalled; no source opened this session]
**Critique.** Descriptive, not prescriptive; hard to test.
**Transfer.** Direct analogue of agent failure: anchoring on a first diagnosis and reading all later output through it. Klein's practical point is to track "what would make me abandon this frame?" up front.
**V3 implication.** V3 should require every plan and every diagnosis to state one observable "frame-breaker" (an observation that would mean the premise is wrong). v2 has "plan abandonment on contradicted premise" but no mechanism to name the trigger in advance. Kernel line plus schema field in the plan. Testable by checking whether agents abandon failed approaches earlier.

### 5. Bounded rationality, satisficing, cost of deliberation, reversibility

**What it is.** Simon: search stops at the first option meeting an aspiration level. Gigerenzer: simple heuristics can match or beat complex models in uncertain settings. Optimal stopping and value of information: stop deliberating when the expected improvement is less than its cost. Bezos's one-way and two-way doors: deliberate heavily only on irreversible decisions. Real options: pay a small amount to keep an option open. [all recalled; no sources opened]
**Critiques.** Aspiration levels are set subjectively. "Reversible" is often misjudged: code merges are reversible, data migrations and published artifacts often are not.
**Transfer.** Best fit with v2's two-doubts rule. Reversibility is already in CLASSIFY. What is missing is an explicit deliberation budget tied to value of information.
**V3 implication.** V3 should size planning effort by (reversibility, blast radius), and give each plan phase a token or step budget with an advisory when exceeded. Kernel plus harness (budget counters). Testable: planning-token share versus outcome on tasks of differing reversibility.

### 6. Set-based concurrent engineering and Cynefin safe-to-fail probes

**What it is.** Toyota-style set-based design carries several design alternatives forward and narrows as constraints are learned, deciding at the last responsible moment. Cynefin (Snowden) recommends small safe-to-fail probes in complex domains where cause and effect are only clear in hindsight. [recalled]
**Critique.** Set-based work costs more up front; it pays off when change is expensive later. Cynefin has little rigorous empirical testing; some regard it as a sense-making aid only.
**Transfer.** This is the best theoretical home for "competing COAs" in an agent: spike two approaches cheaply in isolated worktrees and let a verifier cut. Doing it as prose COA documents is weaker than doing it as running code.
**V3 implication.** V3 should turn DEEP's competing COAs into competing cheap spikes (prototype branches evaluated by the same acceptance command) wherever a verifier exists, and fall back to paper COAs only where it does not. COA module plus orchestration layer. Testable: spike-selected versus paper-selected success rate.

### 7. Forecasting, calibration and reference classes (Tetlock)

**What it is.** In the IARPA tournament, three levers raised accuracy (lower Brier score is better): training, teaming and tracking top performers. Training covered reference classes, averaging multiple estimates, extrapolation, and avoiding overconfidence, confirmation bias and base-rate neglect; it took about 45 minutes per module. Teams beat independent forecasters (0.22 versus 0.31 on one table cell); top 2% "superforecasters" put in elite teams stayed ahead (0.07 versus 0.16) [all verified].
**Source.** Mellers et al., "Identifying and Cultivating Superforecasters..." (Psychological Science, 2015) and "Developing expert political judgment" (Judgment and Decision Making), https://escholarship.org/content/qt4rg4n9vr/qt4rg4n9vr_noSplash_4ff67e56b3dac616e0163b75090705e6.pdf [verified for the numbers above]. CHAMPS-KNOW is from Tetlock and Gardner's book, not from this paper; the page I read does not mention it [verified absence; content [recalled]].
**Critiques.** Forecasting questions are short-horizon, well-defined geopolitical events; the transfer to engineering estimates is untested. Teaming gains depended on the training in giving and receiving critique.
**Transfer.** Agent estimates (will this change break tests, how many files affected) can be scored by actually running things. That gives the feedback that human forecasters get from resolved questions, which is the condition for calibration.
**V3 implication.** V3 should log every material prediction the agent makes ("this approach should pass test X", "blast radius is files A, B") with a stated probability bucket, and score it against the outcome. This feeds the experience store and gives the first calibration data. Harness (logging) plus eval suite. It also enforces the "no unearned numbers" rule in the right direction: buckets with later resolution.

### 8. Noise, decision hygiene, mediating assessments, Delphi

**What it is.** Kahneman, Sibony and Sunstein's Noise recommends: independent judgments before discussion, structured decomposition of a decision into separately rated assessments (the mediating assessments protocol, MAP), and delayed holistic judgment. Delphi is the older version: anonymous rounds with feedback. [recalled; protocol description at https://www.theuncertaintyproject.org/tools/the-mediating-assessments-protocol and the Behavioral Scientist interview were surfaced by search but not read]
**Critiques.** Evidence is mostly from hiring and rating studies and the authors' own audits; there is limited controlled evidence for large decisions. Structured rating can crowd out valid intuition when validity is high.
**Transfer.** Very direct. An agent comparing COAs should score each on pre-declared criteria independently (separate fresh contexts) before any holistic pick, and the picker should see scores without the arguments that produced them.
**V3 implication.** V3 should score COAs by separate scorer instances against a fixed rubric and then choose, instead of one context writing and judging its own COAs. Orchestration layer. Testable: agreement between independent scorers (noise) and correlation of score with downstream outcome.

### 9. Group decision failure: groupthink, dissent, brainstorming, aggregation

**What it is.** Janis's groupthink (cohesive groups suppress dissent) is a theory with mixed empirical support [recalled]. Nemeth's work finds that authentic minority dissent stimulates broader thinking even when wrong, while assigned devil's advocacy does not, and may entrench the original view [verified via the Behavioral Scientist interview, https://behavioralscientist.org/stop-playing-devils-advocate-and-other-advice-for-better-decision-making/; primary papers not opened]. The interview also reports that first-ballot majority predicts jury verdicts about 90% of the time [verified as her statement]. Diehl and Stroebe (1987): real brainstorming groups produce fewer ideas than pooled individuals; production blocking (waiting your turn) explains most of it; speaking-freely individuals produced about 106 ideas versus about 55 when forced to wait [verified, https://www.uni-muenster.de/imperia/md/content/psyifp/aeechterhoff/wintersemester2011-12/seminarthemenfelderdersozialpsychologie/08_diehl_stoebe_productivityloss-brainstorming_jpsp1987.pdf].
**LLM analogue.** Search turned up 2025 papers on multi-agent debate, notably "Debate or Vote: Which Yields Better Decisions in Multi-Agent Large Language Models?" (https://arxiv.org/abs/2508.17536v1) and "Talk Isn't Always Cheap" (https://arxiv.org/pdf/2509.05396v2) [titles verified from search results; contents NOT read because the fetch budget ended; the claim that majority voting accounts for most debate gains is [uncertain], to be checked by the AI lanes]. Also "Large Language Models Cannot Self-Correct Reasoning Yet" (https://arxiv.org/pdf/2310.01798) [title only].
**Transfer.** LLM copies share training and often the same prompt, so their errors correlate; independence is weaker than in human panels, and the first answer in the context anchors the rest (a machine form of blocking and conformity). Independence has to be engineered: fresh contexts, different prompts or model families, no sight of each other's output until after commitment.
**V3 implication.** V3 should ban in-context "panel discussion" patterns for decisions and require: independent fresh-context generation, then commit, then reveal. The refuter should be given the artifact plus the criteria and asked to produce its own verdict, not told to find faults. Orchestration layer plus eval (compare against majority-of-N baseline).

### 10. High-reliability organizations (Weick and Sutcliffe)

**What it is.** Five principles: preoccupation with failure, reluctance to simplify, sensitivity to operations, commitment to resilience, deference to expertise. [recalled; lists confirmed present across search results such as https://psnet.ahrq.gov/primers/primer/31/high-reliability but not opened]
**Critiques.** Evidence is largely case study; healthcare "HRO" programs have shown mixed results, and the label is often applied without measurement [recalled, uncertain].
**Transfer.** "Deference to expertise" suggests routing a decision to the agent or tool with the verifier, not the highest-ranking model. "Sensitivity to operations" means the lead should read raw worker output, not only worker summaries. "Reluctance to simplify" maps to refusing to accept a one-line "done" without quoted evidence.
**V3 implication.** V3 should have the lead spot-check raw artifacts for a sample of worker reports, with sampling rate rising when workers report unusually clean results. Orchestration layer.

### 11. Crew resource management and checklists

**What it is.** CRM: sterile cockpit (no non-essential talk below 10,000 ft), challenge-and-response, graded assertiveness ("probe, alert, challenge, emergency action"), and explicit authority gradients [recalled]. Degani and Wiener (1993, Human Factors) distinguish read-do (do each item as you read it, good for time-pressured sequences) from do-confirm (do from memory, then confirm against the list, good for experienced crews and routine tasks), and give design guidelines; they note nonuse or improper use of checklists is a frequent contributing factor in accidents [verified abstract at https://ntrs.nasa.gov/citations/19930068509].
**Evidence on surgical checklists.** The WHO checklist study (Haynes et al., NEJM 2009) reported a fall in death and complications [verified that the study exists via PubMed result https://pubmed.ncbi.nlm.nih.gov/19144931/; figures recalled as about 1.5% to 0.8% mortality and 11% to 7% complications, unchecked]. A population study of Ontario hospitals after mandated checklists found no significant improvement in outcomes (Urbach et al., NEJM 2014, https://pubmed.ncbi.nlm.nih.gov/24620866/) [title verified, results not read in full]. The usual explanation is that benefit depends on implementation quality and team engagement, not on the paper list.
**Transfer.** Checklists for agents are cheap to make mandatory in code, so the failure mode is not nonuse but empty compliance: the agent ticks boxes it did not execute. A do-confirm list where each item requires an artifact (command output) resists this. Read-do suits fixed procedures (deploy, release); do-confirm suits ordinary coding, where the agent knows the procedure.
**V3 implication.** V3 should express every checklist item as a command with captured output or a harness-verifiable fact, never as a statement to be asserted. Harness (hooks and schema). Test: rate of false "done" claims with versus without artifact-bound items.

### 12. Incident Command System (ICS) and span of control

**What it is.** ICS features: unity of command (one boss per person), common terminology, management by objectives, modular organization, manageable span of control (3 to 7 reports, 5 optimal), incident action plans for each operational period, and formal transfer-of-command briefings [recalled]. The FEMA ICS pages I tried returned "File not found" and could not be read, so these features are unverified here. Sources surfaced by search but unread: https://emilms.fema.gov/is_0200c/groups/53.html, https://training.fema.gov:443/EMIWeb/IS/IS700b/Handouts/National_Incident_Management System_Third Edition_October_2017.pdf.
**Critique.** The 3-to-7 range is a doctrinal rule of thumb; I did not find empirical derivation. Span of control research in management does not support a universal number.
**Transfer.** For agents the binding constraint is the lead's context: each worker report costs tokens to read and arbitrate. "Unity of command" maps to one owner per file or subtask (no two workers editing the same area), and transfer-of-command briefing maps to the handoff file when a lead hits its context limit.
**V3 implication.** V3 should set a default concurrent-worker cap (start at about 5, to be tuned empirically) and treat a worker report as a unit with a fixed length budget. Orchestration layer. Mark the number as a starting hypothesis, not a result.

### 13. Handoffs: SBAR and I-PASS

**What it is.** I-PASS is a structured handoff: Illness severity, Patient summary, Action list, Situation awareness and contingency planning, Synthesis by receiver (read-back). SBAR (Situation, Background, Assessment, Recommendation) is a shorter communication format [recalled].
**Evidence.** Across 10,740 admissions at nine hospitals, I-PASS was associated with medical errors down 23% (24.5 to 18.8 per 100 admissions, P<0.001), preventable adverse events down 30% (4.7 to 3.3 per 100, P<0.001), no change in nonpreventable events, six of nine sites individually significant, and no change in oral handoff duration (2.4 vs 2.5 minutes) [verified, https://pubmed.ncbi.nlm.nih.gov/25372088/ (Starmer et al., NEJM 2014)].
**Critiques.** The study was before-after without concurrent controls at all sites (recalled), and it was bundled with training and culture change, so the structure is not isolated as the cause.
**Transfer.** Strong. Handoffs between lead and worker, and between sessions, are where context is lost. The effective features are: fixed fields, an explicit contingency ("if X happens, do Y"), and receiver synthesis.
**V3 implication.** V3 should require the worker to restate the task, constraints and acceptance command in its own words as its first output (receiver synthesis) and have the harness diff that against the brief before work proceeds. Harness plus brief schema. Add "illness severity" analogue (risk tier) and "contingency" fields to the handoff file template.

### 14. Safety science: Swiss cheese, Rasmussen, STAMP/STPA, Safety-II and ETTO, normalization of deviance

**What it is.** Reason: accidents need holes in several defense layers to line up, and latent conditions matter as much as active errors. Rasmussen: systems drift toward the boundary of acceptable performance under pressure for efficiency, and behavior is skill-, rule- or knowledge-based. Vaughan: normalization of deviance, where repeated acceptable-seeming deviations reset the norm (Challenger). Hollnagel's ETTO: people constantly trade thoroughness for efficiency, and this is also why things usually go right; Safety-II studies how things go right. [all recalled]
STPA (Leveson) treats accidents as control problems and analyzes four unsafe control action (UCA) types: not providing a needed action, providing an unsafe one, wrong timing or order, and wrong duration [verified, https://ptolemy.berkeley.edu/projects/cps/Unsafe_Control_Actions.html]. Search also surfaced recent STAMP/STPA papers applied to AI systems (https://arxiv.org/pdf/2512.17600, https://arxiv.org/pdf/2410.22526) [titles only].
**Critiques.** STPA is labor-intensive, and quality depends on the analyst. Swiss cheese is criticized as linear and hindsight-friendly. Safety-II evidence is mostly qualitative.
**Transfer.** The agent system is literally a control structure (lead controls workers, workers control tools). STPA's four UCA types give a compact review for each command the lead can issue: dispatch not done, dispatch wrongly done, done too early or late, continued too long. ETTO predicts an agent will shave verification under token or time pressure, which matches v2's "process theater" observation. Drift predicts gradual relaxation of gates across sessions.
**V3 implication.** V3 should (a) run a one-off STPA-style pass over the orchestration layer's control actions (dispatch, approve, merge, escalate) to find unsafe-control-action scenarios, and (b) add drift metrics (gate skips, overrides, loosened acceptance criteria per week). Eval suite and harness.

### 15. Automation, human oversight and approval fatigue

**What it is.** Bainbridge's "Ironies of Automation" (1983): designers leave operators the tasks they cannot automate; monitoring for rare abnormalities is "humanly impossible" for sustained periods; skills decay without practice, yet the operator must take over in the hardest cases [all verified at https://gwern.net/doc/sociology/technology/1983-bainbridge.pdf]. Sheridan and Parasuraman's levels of automation, and automation surprise, are [recalled].
Anthropic's auto-mode write-up states that manual prompts cause approval fatigue ("users accept 93% of them anyway"), that its action classifier has a 0.4% false-positive and 17% false-negative rate on real overeager actions, and that the system halts and escalates to a human after 3 consecutive or 20 total denials [all verified, https://anthropic.com/engineering/claude-code-auto-mode]. Its own conclusion: not a replacement for careful human review on high-stakes infrastructure.
**Transfer.** This is the strongest evidence in the lane for the "human approval gate" design question. An approval that people accept 93% of the time carries little information; an always-on gate for DEEP will, over time, be rubber-stamped. The remedy in the human-factors literature is to make approvals rare, concrete, and different in kind: show the exact diff or action, state what is irreversible, and require an active input (not a default yes) for the few high-risk cases.
**V3 implication.** V3 should (a) restrict human approval to a small set of defined irreversible or high-blast-radius action classes enforced in hooks, (b) present each approval request as BLUF plus the exact action, evidence and rollback, (c) track the human's accept rate and treat a rate above a threshold on a gate as a signal to tighten or remove that gate, and (d) use the denial-ceiling pattern (3 consecutive or 20 total, then escalate) for agent-side loops. Harness plus eval.

### 16. Learning loops: Argyris, deliberate practice, lessons-learned failure

**What it is.** Argyris and Schon: single-loop learning corrects actions within existing governing assumptions; double-loop questions the assumptions and goals themselves. Defensive routines block the latter. Deliberate practice (Ericsson) requires specific goals, immediate feedback and repetition at the edge of ability. [recalled]
Search results surfaced practitioner and survey literature on why lessons-learned programs fail (for example https://www.igi-global.com/chapter/why-do-lessons-learned-often-fail/286314 and https://www.igi-global.com/chapter/common-pitfalls-and-shortcomings-of-lessons-learned-programs/117335 [titles only; not read]). The usual findings [recalled, uncertain]: lessons are written as general advice, stored where no one looks at decision time, have no owner, and rarely change the process.
**Transfer.** An experience store of prose lessons is the same artifact. An agent with a "lessons" file will read it only if the harness injects it, and may follow it only superficially.
**V3 implication.** V3 should convert a lesson into one of three enforceable forms: a hook or check, a test, or a classifier rule, and only otherwise keep it as prose with an expiry and an owner. Harness plus eval. Test: does each retained lesson reduce a repeat failure on a replay set?

## Verdict on JORDAN v2's four named design elements

| Element | Evidence verdict | Why |
|---|---|---|
| 2-3 competing COAs for DEEP | **Partly undercut as a default; supported as conditional.** | RPD/RPM evidence says experts rarely compare, and one option plus a flaw check is faster. Support exists when options are generated independently and when spikes can be tested (set-based design, aggregation of independent judgments). Do it on triggers, not by tier. |
| Multi-persona premortem | **Supported in principle (prospective hindsight), unsupported in detail.** | Original effect is lab-based; field evidence is descriptive; no evidence on persona count; independent resampling is probably equivalent. |
| Human approval gate (always-on for DEEP) | **Undercut as designed.** | 93% accept rate [verified], Bainbridge monitoring irony [verified]. A gate that is always on and mostly approved decays. Keep only for defined irreversible actions with concrete evidence. |
| Monotonic recovery ladder | **Supported with a caveat.** | Escalating, never retreating matches anti-repetition advice and the denial-ceiling pattern. It does not address drift, and it assumes each rung's outcome is independently verified. |

What the handoff, checklist, span-of-control and fatigue literatures imply for an AI lead agent: (1) use fixed-schema handoffs with receiver restatement; (2) bind each checklist item to a command output; (3) cap concurrent workers by the lead's reading capacity, starting near 5 and measuring; (4) count approvals and retire gates people stop reading; (5) give the single human a short list of irreversible-action approvals, not a stream.

## Contradictions with JORDAN v2

- **Tier-triggered COAs** (DEEP means 3 COAs) conflicts with RPD/RPM and Kahneman-Klein, which say to match deliberation to environment validity and reversibility, not to a tier label.
- **"DEEP always escalated to a human"** conflicts with the approval-fatigue evidence. The gate should be on action classes, not on pipeline tier.
- **Premortem personas compiled into watchdogs** is good, but personas in one context are not independent. This conflicts with the independence-before-discussion finding.
- **Fused risk = max(risk, premortem severity)** uses two signals that are not independent if from the same model; the "independent verification" claim in v2 is weaker than stated unless fresh contexts or different models produce them.
- **12 phases for STANDARD/DEEP** adds handoff points; I-PASS evidence suggests each handoff needs structure and receiver synthesis, otherwise each phase is a place to lose information.
- **Experience store as a learning mechanism** conflicts with the lessons-learned literature unless lessons become enforcement.

## Hype and weak evidence

- Groupthink: popular, with a mixed empirical record [recalled].
- "Expert intuition is magic" and "System 1/System 2 explains everything": Kahneman and Klein's own paper restricts when intuition is valid.
- The Army RPM 30% time saving: participant estimate only [verified].
- Premortem as a proven method: effect evidence is lab-based; field reports are descriptive [verified].
- WHO surgical checklist as a universal fix: contradicted by the Ontario result [verified at title level].
- ICS span of control 3 to 7: doctrine, not derived from experiment.
- HRO principles: case-study evidence, not controlled outcomes.
- Devil's advocacy: the role-played version appears to be the weaker form (Nemeth), though I read only an interview.
- Multi-agent LLM debate: 2025 papers question its gains over voting; contents not read.

## Gaps

- Could not open: Mitchell/Russo/Pennington 1989, Veinott 2010, the full Urbach 2014 and Haynes 2009 abstracts (PubMed pages returned only boilerplate), the FEMA ICS pages (404), the multi-agent debate papers (fetch budget exhausted), and Klein's 1998 and 2008 books.
- No source found for the "80% recognition, 12% comparing" statistic; the Forest Service reprint gives no percentage.
- No primary source read for Reason, Rasmussen, Vaughan, Sheridan, Parasuraman, Argyris, Weick and Sutcliffe, Janis, Gigerenzer, Simon, Delphi, or Noise; they are [recalled].
- Did not find evidence on I-PASS or checklists for software or AI-agent handoffs; transfer is by analogy.
- Did not find direct evidence on optimal numbers of concurrent LLM workers.
- Cynefin, reference class forecasting and real options: no new sources sought beyond memory.

## Sources

- https://pubmed.ncbi.nlm.nih.gov/19739881/ (Kahneman and Klein 2009)
- https://apps.dtic.mil/sti/tr/pdf/ADA521492.pdf (Ross, Klein et al., Military Review 2004)
- https://www.fs.usda.gov/t-d/pubs/htmlpubs/htm95512855/page13.htm (fireground summary)
- https://par.nsf.gov/servlets/purl/10435109 (2022 premortem field application)
- https://pubmed.ncbi.nlm.nih.gov/24620866/ (Urbach et al. 2014, Ontario checklists; search result)
- https://pubmed.ncbi.nlm.nih.gov/19144931/ (Haynes et al. 2009; search result)
- https://pubmed.ncbi.nlm.nih.gov/25372088/ (Starmer et al. 2014, I-PASS)
- https://ntrs.nasa.gov/citations/19930068509 (Degani and Wiener 1993)
- https://behavioralscientist.org/stop-playing-devils-advocate-and-other-advice-for-better-decision-making/ (Nemeth interview)
- https://www.uni-muenster.de/imperia/md/content/psyifp/aeechterhoff/wintersemester2011-12/seminarthemenfelderdersozialpsychologie/08_diehl_stoebe_productivityloss-brainstorming_jpsp1987.pdf (Diehl and Stroebe 1987)
- https://escholarship.org/content/qt4rg4n9vr/qt4rg4n9vr_noSplash_4ff67e56b3dac616e0163b75090705e6.pdf (Mellers et al.)
- https://gwern.net/doc/sociology/technology/1983-bainbridge.pdf (Bainbridge 1983)
- https://anthropic.com/engineering/claude-code-auto-mode (Anthropic auto mode)
- https://ptolemy.berkeley.edu/projects/cps/Unsafe_Control_Actions.html (STPA UCA types)
- Search-result only, not read: https://arxiv.org/abs/2508.17536v1, https://arxiv.org/pdf/2509.05396v2, https://arxiv.org/pdf/2310.01798, https://arxiv.org/pdf/2503.13657 (MAST, "Why do multi-agent LLM systems fail"), https://arxiv.org/pdf/2512.17600, https://arxiv.org/pdf/2410.22526, https://www.theuncertaintyproject.org/tools/the-mediating-assessments-protocol, https://psnet.ahrq.gov/primers/primer/31/high-reliability, https://emilms.fema.gov/is_0200c/groups/53.html, https://www.igi-global.com/chapter/why-do-lessons-learned-often-fail/286314, https://www.igi-global.com/chapter/common-pitfalls-and-shortcomings-of-lessons-learned-programs/117335
