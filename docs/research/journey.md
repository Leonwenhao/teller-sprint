# Sentient Arena Cohort 0: The Full Journey

**Author:** Leon Liu (柳文浩), Dolores Research
**Period:** March 22 – April 8, 2026 (18 days)
**Final Result:** #2 on leaderboard (187.823), highest accuracy in the competition (71.5%, 176/246), peak score 192.046

---

## 1. Timeline and Key Milestones

### Week 1: Foundation (March 22–28)

**March 22 — Session 0: Planning**
Accepted into Sentient Arena Cohort 0. Produced GENESIS.md (project plan) and BOTCOIN_AUDIT.md (prior work audit). Chose OpenHands as agent framework based on Sentient's documentation. Designed a four-phase pipeline: Retrieve → Extract → Compute → Validate.

**March 22–23 — Session 1: Setup + First Runs**
Installed Arena CLI, authenticated, ran first tests. 2/5 easy questions pass with MiniMax M2.5. Created first skills file (retrieval_strategy). Realized the benchmark is significantly harder than expected — multi-step questions requiring table parsing, unit conversion, and statistical computation.

**March 23 — Session 2: The Harness Discovery**
Discovered critical distinction between `opencode` and `openhands-sdk` harnesses. openhands-sdk injects skills files into system prompt; opencode does not. Skills + Claude Sonnet = 85% cost reduction ($5/q → $0.45/q). 80% accuracy on 10 test questions. This was the first "harness matters" signal.

**March 25 — Session 3: Gap Fixes**
Implemented 6 targeted fixes based on failure diagnosis: environment config, output formatting, web search capability, "reported in" vs "reported for" distinction, historical grouping verification, document versioning. Both persistent failures fixed. 15/17 real attempts pass (88%). Diagnosed remaining failures: ESF balance sheet terminology confusion, unit conversion errors.

**March 26 — Session 4: Cross-Model Validation**
Tested DeepSeek V3.2 as cheaper alternative (~10-15x cheaper than Sonnet). DeepSeek: 16/19 (84%). Sonnet: 18/18 (100%). Key discovery: opencode harness doesn't inject skills into agent context — only prompt template reaches agent. Merged critical rules into prompt template. This finding foreshadowed the later "prompt template > skills directory" insight.

### Week 2: First Submissions + Plateau (March 30 – April 2)

**March 30 — Session 5: First Full Submission**
Submitted DeepSeek V3.2 to full 246-question benchmark. Score: **132.3 (#2 on early leaderboard).** 144/246 correct (58.5%). Total cost: $29.81. High cost from opencode harness crushed our multiplier.

**March 30 — Session 6: MiniMax M2.5 + openhands-sdk**
Critical rule change discovered: Arena forces MiniMax M2.5 for everyone (model field in arena.yaml is ignored). Submissions are free (Arena uses their API keys). Competition is purely behavioral engineering.

Switched to openhands-sdk + MiniMax M2.5. Full sample test: 13/20 pass (65%). Submitted to Arena. Score: **170.7 (#5 on leaderboard).** 158/246 correct (64.2%). Cost: $12.82. Massive improvement from harness switch alone.

**April 1 — Session 7: The v7 Regression**
Built v7 skills (631 lines) with targeted additions: Theil formula fix, Euclidean norm, HP filter, named formula lookup rule, date range enumeration, batch extraction, ESF balance sheet clarification, "write answer early" reinforcement.

Result: **158.5 score, 148/246 correct — REGRESSION (-10 vs v6 best).** First hard evidence that more instructions = worse performance. Reverted to v6. Confirmed ±5 question variance per run (same config scores 153-158).

**April 2 — Session 8: Local Testing Infrastructure**
Built full 246-question local evaluation pipeline. Downloaded OfficeQA ground truth from Databricks GitHub. Created batch evaluation script with resume support, aggregation script with failure breakdown. Smoke test passed. But local runs took ~16 min/question via OpenRouter (vs ~3 min on Arena infrastructure), making local iteration impractical.

### Week 3: Breakthroughs + Victory (April 3–8)

**April 3–4 — Session 10: The "Less Is More" Revelation**
The turning point of the entire competition.

Commissioned deep research into MiniMax M2.5's architecture:
- 229B total / 10B active params (most aggressive MoE sparsity of any frontier model)
- BFCL tool calling: 76.8% (#1 of all models)
- FinanceAgent: 38.58% (weak — needs domain help)
- Verbosity: 3.7x average output length
- Hallucination rate: 88%

Implication: with only 10B active params, MiniMax has less capacity to filter noise from signal. Long prompts don't just waste tokens — they actively degrade tool orchestration.

Built v13-minimal (28 lines) and v13-core (37 lines). Local tests showed v12's always-fail questions FLIPPING to pass with 37 lines. The "Virgil Abloh 3% rule" applied to LLM prompting: don't retrain the model, add just enough to turn it.

v12A (513 lines) submitted to Arena: 174.5 and 170.1 — another regression. v13-codex (37 lines) submitted: 173.2, but traces showed 4 always-fail questions now passing that no previous config had solved.

**April 4 — Session 11: Deep Research + The Fatal Experiment**
Submitted v13-core to Arena: **168.7 (158 correct, 64.2%).** The 37-line approach flipped some questions but lost too many that needed domain knowledge. MiniMax at 38% FinanceAgent genuinely needs verbose domain context.

Built v12-lean (297 lines) — aggressive cuts to v12, including changing "write answer.txt in EVERY Python block" to "write only final answer." Result: **164.4 (151 correct, 61.4%) — catastrophic regression of -22 answers.** Root cause: without the insurance policy of writing in every code block, agent finishes with empty answer files on hard questions.

**The most important lesson of the entire competition: "write answer.txt in every Python block" is the most load-bearing rule. It's not about prompt style — it's about scoring mechanics. An empty file = 0 points, a rough answer = possible match within 1% tolerance.**

Deployed 3 parallel research agents (Claude, ChatGPT, Gemini) for deep research on MiniMax optimization, EvoSkill, OfficeQA exploitation, and competitor intelligence. All three converged on the same dead ends (goose $0 cost bug, M2.7 switch, progressive-disclosure skills) and the same actionable tweaks.

Built v12+tweaks (548 lines): pure v12 + 4 consensus one-liners. Submitted overnight.

**April 5–6 — Session 12: From Off the Leaderboard to #1**
The single biggest session of the competition.

v12+tweaks results: **167.3 (157 correct) — another regression.** All 4 Codex-recommended tweaks hurt. Deep forensic investigation revealed: **every modification since April 2 was Codex-influenced, and every one regressed.** Codex applied software engineering principles (clean code, DRY, no contradictions) to a behavioral engineering problem. The "contradictions" it fixed were actually insurance policies.

**6-run cross-reference analysis** across all configs:
- 114 questions ALWAYS pass (46.3%) — reliable base
- 43 questions ALWAYS fail (17.5%) — structural gaps
- 89 questions SWING (36.2%) — variance-driven

Always-fail analysis revealed: 5-7 questions need named formulas absent from config, 2-3 need CPI data, 20 are complex multi-file extractions.

Built v12-formulas (542 lines): content swap targeting always-fail questions. Removed low-value patterns, added Expected Shortfall, Arc Elasticity, HHI, Gini, Hazard Rate, Box-Cox, HP filter, ARIMA, plus CPI-U annual averages and retrospective table strategy. Net change: -1 line.

Built v14-alpha (138 lines): designed from scratch with density-first principle. Every line a rule, formula, trap, or data point. Zero tutorials, zero code examples, zero explanatory prose.

v14-alpha on openhands-sdk: **169.0 (155 correct) — best SCORE of the day despite fewer correct.** The speed advantage (166.8s vs 279.7s) improved the multiplier enough to outscore v12. Key insight: latency matters more than we thought.

**THE GOOSE DISCOVERY (10 PM, April 5):**
Leon suggested investigating the goose harness. Technical investigation revealed:
- Goose (by Block Inc.) has auto-compaction at 80% context utilization
- When context fills, older tool outputs are summarized while initial instructions preserved
- This directly addresses our #1 problem: accuracy degradation from 80% early to 60% late
- Goose cost: ~$1.85/run vs ~$13 on openhands-sdk (87% reduction)
- Content delivered via `prompt_template_path` (goose_prompt.j2) instead of skills injection

Built goose_prompt.j2 (84 lines): the entire v14-alpha content compressed into a single Jinja2 template. Iron rules, workflow, unit conversion, fiscal year, 20+ named formulas, table reading, domain traps, multi-file strategy, CPI data, web search.

First goose submission: **186.046 (169 correct, $1.85) — jumped from #9 to #6.**

**Second goose submission (2 AM, April 6):** Same config, clean infrastructure (low load). Mid-run accuracy peaked at 73.7% — highest ever seen. Accuracy held above 71% throughout the entire run (compaction working).

**Final: 192.046 (174 correct, 70.7%, $1.85, 171s avg) — #1 ON THE LEADERBOARD.**

**April 6–7 — Session 13: Defending #1**
Submitted v12-formulas+goose: **173.9 (168 correct) — regression.** Longer skills content hurt even with goose compaction. Confirmed that 84-line prompt + 138-line skills is the optimal density.

Submitted 5 variance-hunting rolls with proven #1 config. All daytime submissions scored 10+ points below the 2 AM run due to infrastructure congestion (200-327s latency vs 171s). Best daytime: 185.6. The #1 score of 192.046 was only achievable on empty infrastructure.

Sentient announced they would rerun all submissions in an "isolated evaluation environment." Concern: would original 192.046 be honored or overwritten? Sent Discord message and email with tar file (dolores_goose_v1.tar.gz) for overnight run.

Submitted official competition report (SUBMISSION_REPORT.md) and detailed research paper (FINAL_REPORT.md).

**April 8 — Demo Day**
Sentient reran submissions. Our tar file scored **187.823 with 176 correct (71.5% accuracy — highest accuracy ever).** Score dropped from 192 to 188 due to higher latency (~290s vs 171s), but accuracy actually improved (+2 answers). Final leaderboard: **#2 (187.823), behind The Big Q (188.108).**

Presented Teller live at Demo Day in San Francisco — the only cohort participant presenting in person. Sentient posted on Twitter. Won $4K cash + $8K compute credits ($2K Daytona, $2K Fireworks, $2K Yotta).

Open-sourced Teller at github.com/Leonwenhao/teller.

---

## 2. Technical Evolution of Teller

### Prompt Architecture Progression

| Date | Config | Lines | Accuracy | Score | Key Change |
|------|--------|-------|----------|-------|------------|
| Mar 30 | opencode + prompt v2 | 138 | 58.5% | 132.3 | Baseline |
| Mar 30 | openhands-sdk + v6 skills | 543 | 64.2% | 170.7 | Skills injection |
| Apr 1 | v7 skills | 631 | 60.2% | 158.5 | More lines = regression |
| Apr 2 | v12 (pure v6 revert) | 543 | 70.3% | 180.9 | Lucky roll on proven config |
| Apr 3 | v12A (surgical cuts) | 513 | ~66% | 174.5 | Every modification hurts |
| Apr 3 | v13-codex (minimal) | 37 | ~66% | 173.2 | 4 always-fails flipped |
| Apr 4 | v13-core (minimal) | 37 | 64.2% | 168.7 | Too lean, lost domain knowledge |
| Apr 4 | v12-lean | 297 | 61.4% | 164.4 | Removing insurance = -22 answers |
| Apr 5 | v12+tweaks | 548 | 63.8% | 167.3 | Codex edits hurt |
| Apr 5 | v14-alpha (openhands) | 138 | 63.0% | 169.0 | Density-first design |
| **Apr 5** | **v14-alpha + goose** | **84+138** | **68.7%** | **186.0** | **Goose discovery** |
| **Apr 6** | **v14-alpha + goose** | **84+138** | **70.7%** | **192.0** | **#1 — clean infra** |
| **Apr 8** | **v14-alpha + goose (rerun)** | **84+138** | **71.5%** | **187.8** | **Highest accuracy ever** |

### The Three Eras

**Era 1: Volume (March 22 – April 2)**
Philosophy: more instructions = better performance. Built up from 138 to 631 lines of skills content. Hit ceiling at v6/v12 (543 lines, ~70% accuracy). Every addition beyond 543 lines regressed.

**Era 2: Compression (April 3–5)**
Philosophy: less is more, Virgil Abloh's 3% rule. Cut from 543 to 37 lines. Discovered that MiniMax M2.5 with 10B active params is sensitive to attention dilution. But 37 lines cut too much — lost domain knowledge the model genuinely needs at 38% FinanceAgent.

**Era 3: Density (April 5–8)**
Philosophy: maximum information per token. Neither volume nor compression — density. 84 lines of pure rules, formulas, traps, and data. Zero tutorials, zero code examples, zero explanatory prose. Combined with goose harness for context management. This was the winning configuration.

### What Failed (and Why)

**Every modification from April 2–5 regressed.** The common thread: Codex (OpenAI's coding agent) was used to analyze and improve the prompt. Codex applied software engineering principles — DRY, no contradictions, clean interfaces — to a behavioral engineering problem.

Specific failures:
- **v12A (surgical improvements):** Codex identified 8 "bugs" in v12. 6 of them were actually load-bearing insurance policies. Fixing them removed safety nets.
- **v12-lean (subtract only):** Removed "write answer.txt in EVERY Python block" — the most load-bearing rule. -22 answers.
- **v12+tweaks (4 consensus additions):** Each tweak was individually sensible but collectively made the prompt 5 lines longer, adding noise to a system at its attention capacity.
- **v7 (targeted additions):** Added Theil formula, HP filter, Euclidean norm, batch extraction. 88 extra lines diluted the signal. -10 answers vs v6.

**The meta-lesson: software engineering principles and behavioral engineering principles are different disciplines.** Clean code values like DRY and single-responsibility can actively harm prompt effectiveness when the "contradictions" are insurance policies and the "redundancy" is reinforcement.

### What Worked (and Why)

1. **The "write answer in every Python block" rule:** Insurance policy worth +22 answers. Ensures partial results are always scored rather than lost to empty files.
2. **Named formula definitions:** Expected Shortfall, HHI, Gini, Arc Elasticity, etc. Targets MiniMax's weak domain knowledge (38% FinanceAgent). Added 8-11 always-fail questions to the solvable set.
3. **Embedded CPI data:** BLS Consumer Price Index annual averages (1938-2020) in the prompt. Eliminates need for web search on inflation-adjusted questions.
4. **Domain traps as explicit rules:** "reported IN" vs "reported FOR," "gross debt" vs "debt held by public," fiscal year pre/post-1976. These aren't suggestions — they're disambiguation rules that prevent specific, documented failure modes.
5. **Retrospective table strategy:** For multi-year questions, search the latest year first for a historical summary table. One table beats searching 12 individual files.

---

## 3. EvoSkill and Manual Application

### What EvoSkill Is

Sentient's EvoSkill framework (github.com/sentient-agi/EvoSkill) auto-discovers agent skills from failed trajectories. Published result: improved OfficeQA accuracy from 60.6% to 67.9% using Claude Opus 4.5.

Core EvoSkill loop:
1. Run agent on benchmark
2. Classify failures by type
3. Auto-generate new skills targeting failure patterns
4. Evaluate with new skills
5. Keep if improved, revert if not
6. Repeat

### How We Applied It Manually

We executed the same loop by hand across 12 sessions and 25+ submissions:

**Step 1 — Submit and classify:** After each Arena submission, we pulled traces and classified every failure into four categories:
- **Retrieval errors** — agent searched wrong file or wrong time period
- **Extraction errors** — agent found right file but read wrong cell/column
- **Computation errors** — agent used wrong formula or wrong precision
- **Behavioral errors** — empty answer file, self-sabotage (overwriting correct answers)

**Step 2 — Cross-submission variance analysis:** We compared pass/fail results across 6 submissions with different configurations. For each of 246 questions, we classified:
- 114 always-pass (46.3%) — reliable base, protect these from regression
- 43 always-fail (17.5%) — structural capability gaps, target these
- 89 swing (36.2%) — variance-driven, not directly addressable

**Step 3 — Targeted skill creation:** The always-fail analysis revealed specific addressable gaps:
- 5-7 questions requiring named financial formulas (Expected Shortfall, HHI, etc.) not in our config
- 2-3 questions requiring CPI inflation data not in the Treasury corpus
- 1 question requiring historical date knowledge (Korean War start)
- ~20 complex multi-file extraction questions needing retrieval strategy

We added formula definitions, CPI data, historical dates, and the retrospective table strategy — targeting the highest-EV failures.

**Step 4 — Regression testing:** Every change was validated against known-passing questions. We tracked regressions obsessively because ±5 question variance per run means improvements must exceed the noise floor to be real.

### Results vs Automated EvoSkill

| Approach | Model | Accuracy | Method |
|----------|-------|----------|--------|
| EvoSkill (automated) | Claude Opus 4.5 | 67.9% | Auto-generated skills |
| **Manual EvoSkill (Teller)** | **MiniMax M2.5 (10B)** | **71.5%** | **Hand-crafted skills** |

We outperformed the automated version with a model 20x smaller. The advantage: human judgment in prioritizing which failures to target and understanding why specific rules are load-bearing (e.g., the "write every block" insurance policy would likely be pruned by an automated system as redundant).

---

## 4. The Goose Breakthrough

### The Problem: Context Bloat

Across all openhands-sdk runs, we documented a systematic accuracy degradation pattern:
- Early questions (3-5 tool calls): ~80% accuracy
- Late questions (15-30 tool calls): ~60% accuracy

As tool outputs accumulated in the conversation history, the model's attention to its original skills instructions was diluted. With only 10B active parameters, MiniMax M2.5 is extremely sensitive to this effect. The skills content went from ~33% of context at the start to ~6% by question 30.

This was an architecture problem, not a prompt problem. No amount of prompt engineering could fix it because the issue was context management, not instruction quality.

### The Discovery (April 5, 10 PM)

Leon suggested investigating the goose harness after noticing it as an option in Arena's harness list. Technical investigation revealed:

**Goose** (github.com/block/goose) is Block Inc.'s open-source AI agent framework, written in Rust. Key architectural difference: **auto-compaction at 80% context utilization.** When the context window reaches 80% capacity, goose automatically summarizes older tool outputs while preserving the initial instruction content at full fidelity.

This directly solved our context bloat problem:
- **Before (openhands-sdk):** Instructions diluted as context fills. Accuracy: 80% → 60%.
- **After (goose):** Instructions preserved throughout. Accuracy: 73% → 71%.

### The Numbers

| Metric | OpenHands SDK | Goose | Delta |
|--------|--------------|-------|-------|
| Mean accuracy | 67.4% (166 correct) | 69.5% (171 correct) | +2.1% |
| Best accuracy | 70.3% (173 correct) | 71.5% (176 correct) | +1.2% |
| Mean cost | $14.50 | $1.82 | -87.4% |
| Mean latency | 198s | 185s | -6.6% |
| Best score | 180.9 | 192.0 | +6.1% |

### Why Cost Dropped 87%

On openhands-sdk, the full skills content (~8,000 tokens) was included in every API call as part of the system prompt. Over a multi-step question with 20+ tool calls, this meant sending 8,000 × 20 = 160,000 tokens of repeated skills content. On goose, the prompt template is sent once and preserved through compaction. Result: dramatically fewer total tokens consumed.

### Prompt Delivery Mechanism

On goose, content is delivered via `prompt_template_path` (a Jinja2 template) rather than skills injection. The prompt template content goes into goose's recipe YAML `prompt` field as a user message. This may actually help because MiniMax's RL training is optimized for following user instructions (vs system prompts which can be overridden during reasoning).

---

## 5. Key Metrics and Results

### Final Competition Results

| Metric | Value |
|--------|-------|
| Final leaderboard rank | #2 (187.823) |
| Peak score | 192.046 (#1 at time of submission) |
| Best accuracy | 71.5% (176/246) — highest in competition |
| Best accuracy (original run) | 70.7% (174/246) |
| Total cost per run | $1.85 |
| Cost per question | $0.0075 |
| Average latency (best run) | 171 seconds |
| Model | MiniMax M2.5 (229B total / 10B active, MoE) |
| Prompt template | 84 lines |
| Skills file | 138 lines |
| Agent harness | Goose (Block Inc.) |
| Total submissions | 25+ |
| Optimization sessions | 12 over 14 days |
| Local test questions run | ~250 individual evaluations |

### Comparison to Frontier Models

| System | Accuracy | Active Params | Cost/Question | Notes |
|--------|----------|--------------|---------------|-------|
| GPT-5.1 Agent (raw PDFs) | 37.4% | ~200B+ | ~$4+ | Databricks baseline |
| Claude Opus 4.5 (raw PDFs) | 43.5% | ~200B+ | ~$4+ | Databricks baseline |
| GPT-5.1 Agent (parsed docs) | 52.8% | ~200B+ | ~$4+ | Databricks baseline |
| Claude Opus 4.5 (parsed docs) | 67.8% | ~200B+ | ~$4+ | Best published result |
| EvoSkill + Opus 4.5 | 67.9% | ~200B+ | ~$3+ | Sentient's framework |
| **Teller (MiniMax M2.5)** | **71.5%** | **10B** | **$0.0075** | **This work** |

### Prompt Length vs. Accuracy

| Config | Lines | Accuracy | Score | Lesson |
|--------|-------|----------|-------|--------|
| v7 skills | 631 | 60.2% | 158.5 | Peak volume, worst result |
| v12+tweaks | 548 | 63.8% | 167.3 | Every tweak hurt |
| v12/v6 (production) | 543 | 70.3% | 180.9 | Best of the volume era |
| v12A (surgical cuts) | 513 | ~66% | 174.5 | Cutting "bugs" = cutting insurance |
| v12-lean | 297 | 61.4% | 164.4 | Removing insurance = catastrophe |
| v14-alpha (density) | 138 | 63.0% | 169.0 | Density > volume (multiplier) |
| **goose_prompt.j2** | **84** | **71.5%** | **192.0** | **Density + compaction = winner** |
| v13-core (minimal) | 37 | 64.2% | 168.7 | Too lean, lost domain knowledge |

### Score Progression Over Time

| Date | Score | Correct | Config | Rank |
|------|-------|---------|--------|------|
| Mar 30 | 132.3 | 144 | opencode + DeepSeek | — |
| Mar 30 | 170.7 | 158 | openhands-sdk + v6 | #5 |
| Apr 1 | 158.5 | 148 | v7 (631 lines) | — |
| Apr 2 | 180.9 | 173 | v12 (543 lines) | #4 |
| Apr 3 | 174.5 | ~163 | v12A (513 lines) | — |
| Apr 4 | 168.7 | 158 | v13-core (37 lines) | — |
| Apr 4 | 164.4 | 151 | v12-lean (297 lines) | — |
| Apr 5 | 169.0 | 155 | v14-alpha (138 lines) | — |
| Apr 5 | 186.0 | 169 | **goose + 84 lines** | #6 |
| **Apr 6** | **192.0** | **174** | **goose + 84 lines** | **#1** |
| **Apr 8** | **187.8** | **176** | **goose + 84 lines (rerun)** | **#2** |

---

## 6. Architecture Decisions and Rationale

### Why MiniMax M2.5

MiniMax M2.5 was not a choice — Arena forces it for all participants. But understanding its profile was critical to our prompt engineering strategy.

**Why it worked in our favor:**
- #1 in tool calling (76.8% BFCL) — means we don't waste tokens teaching tool use
- MoE architecture (229B/10B) — extreme parameter efficiency, but sensitive to prompt noise
- Trained via agent-native RL in 200K+ real-world tool environments — the model already knows how to grep, parse, and compute

**Why it needed help:**
- 38% FinanceAgent — weak domain knowledge for financial document reasoning
- 88% hallucination rate — needs strong guardrails
- 3.7x average verbosity — rapid context consumption, making compaction critical

**Our strategy:** Teach domain knowledge, not tool usage. Every line of prompt addresses a genuine knowledge gap (fiscal year conventions, Treasury terminology, statistical formulas). Zero lines teach the model things it already knows (grep syntax, Python patterns, file reading).

### Why Goose Over OpenHands SDK

| Factor | OpenHands SDK | Goose | Winner |
|--------|-------------|-------|--------|
| Context management | None (accumulative) | Auto-compaction at 80% | Goose |
| Cost per run | ~$14.50 | ~$1.85 | Goose |
| Skills injection | System prompt (repeated every call) | Prompt template (sent once) | Goose |
| Instruction fidelity | Degrades 80% → 60% over run | Holds 73% → 71% | Goose |
| Accuracy | 67.4% mean | 69.5% mean | Goose |

The harness switch was the single highest-impact change in the entire competition — more impactful than any prompt modification.

### Why Behavioral Engineering Over RAG or Fine-Tuning

**RAG was not an option:** The corpus (697 TXT files) is provided as a flat directory. The agent uses grep/sed to search — this IS the retrieval mechanism. There's no vector database, no embedding pipeline, no retrieval infrastructure to optimize. The agent's grep-based retrieval is actually quite effective; most failures are extraction or computation errors, not retrieval errors.

**Fine-tuning was not an option:** Arena forces MiniMax M2.5. No model changes allowed. Even if allowed, fine-tuning a 229B MoE model would exceed any reasonable budget.

**Behavioral engineering was the only lever:** Given fixed model and fixed corpus, the only variables were: (1) how we instruct the agent (prompt/skills), (2) which runtime framework manages the agent (harness), and (3) how we structure the agent's workflow (phases, rules, insurance policies).

This constraint turned out to be the thesis: **the performance gap is behavioral, not capability-based.** The same 10B model went from 58.5% to 71.5% through behavioral changes alone.

---

## 7. Lessons Learned

### Technical Lessons

**1. Prompt density > prompt volume for MoE models.**
An 84-line prompt outperformed a 543-line prompt by 1.2% accuracy and 11 score points. MoE models with low active parameter counts (10B) are sensitive to attention dilution. Every unnecessary token competes with critical instructions for the model's limited attention budget.

**2. Agent harness is a first-order performance variable.**
Switching from OpenHands SDK to Goose added +5 correct answers with zero prompt changes and reduced cost by 87%. Context window management (auto-compaction) is not a nice-to-have — it's essential for multi-step agentic workflows. This finding generalizes beyond this competition.

**3. Insurance policies beat clean code.**
"Write answer.txt in every Python block" sounds redundant. It's not. It's worth +22 answers. In behavioral engineering, "contradictions" can be load-bearing insurance policies. Apply software engineering principles (DRY, single-responsibility) to prompts at your peril.

**4. The self-sabotage failure mode is real and underappreciated.**
Without the "stop after writing final answer" rule, the agent frequently overwrites correct answers during unnecessary verification steps. The model's instinct to double-check is actively harmful when the check produces worse results than the initial computation.

**5. Domain knowledge injection works best as reference data, not tutorials.**
Embedding CPI-U annual averages, formula definitions, and fiscal year conventions directly in the prompt outperformed explaining the concepts. The model can execute formulas — it just needs the correct formula to execute.

**6. Cross-submission variance analysis is essential for distinguishing signal from noise.**
±5 question variance per run means a single A/B test is nearly meaningless. We needed 6+ runs to reliably classify questions as always-pass, always-fail, or swing. Without this analysis, we would have attributed random variance to prompt changes.

**7. Infrastructure conditions affect benchmark results more than expected.**
Our 2 AM submission (171s latency, 192.046 score) and 2 PM submission (290s latency, 187.823 score) used identical configs. The 4.2-point difference is entirely infrastructure. Benchmark results should control for infrastructure load.

### Strategic Lessons

**8. Software engineering principles and behavioral engineering principles are different disciplines.**
Codex (OpenAI's coding agent) analyzed our prompt and identified "bugs" — contradictions, redundancies, dead code. Every "fix" regressed performance. The prompt is not software; it's a behavioral specification. What looks like a bug to a software engineer may be a load-bearing insurance policy.

**9. The harness discovery happened because a human said "let's look at goose."**
Not from systematic search, not from research agents, not from competitor analysis. From Leon's intuition to investigate an option we'd overlooked. Research agents contributed deep understanding of MiniMax's profile and confirmed dead ends, but the breakthrough came from human curiosity.

**10. The competition was won on infrastructure selection, not prompt engineering.**
If we'd stayed on OpenHands SDK with our best prompt, our peak score would have been ~185. The goose switch added ~7 points. All the prompt engineering from Sessions 1-11 combined added ~11 points (132 → 180). The harness switch in one evening added 7 of those equivalent points.

**11. "Highest accuracy" is a more durable claim than "highest score."**
Our final leaderboard position (#2, 187.823) was determined by infrastructure latency on the rerun, not by agent quality. Our accuracy (71.5%, 176/246) was the highest of any team. Score is dependent on evaluation conditions; accuracy is intrinsic to the agent.

**12. Open-sourcing immediately after the competition creates more value than keeping it private.**
Teller as an open-source repo generated: Sentient Twitter promotion, demo day credibility, GitHub visibility, inbound interest, and a portfolio artifact. Keeping it private would have produced none of these.

---

## Appendix: Submission History (Complete)

| Date | ID | Config | Harness | Score | Correct | Accuracy | Cost | Latency |
|------|----|--------|---------|-------|---------|----------|------|---------|
| Mar 30 | ccdf4848 | prompt v3 | opencode | 132.3 | 143 | 58.1% | $36.66 | 229s |
| Mar 30 | 5596c2ac | v4 | opencode | 139.4 | 150 | 61.0% | $38.31 | 197s |
| Mar 30 | 3aff9968 | v5 | opencode | 143.3 | 152 | 61.8% | $33.95 | 209s |
| Mar 30 | 54d3fafd | v6 | openhands-sdk | 161.5 | 153 | 62.2% | $15.91 | 200s |
| Mar 30 | ed9b0955 | v6 | openhands-sdk | 163.5 | 153 | 62.2% | $14.60 | 198s |
| Mar 30 | 3decf80a | v6 | openhands-sdk | 170.7 | 158 | 64.2% | $12.82 | 217s |
| Apr 1 | 1f911bc6 | v7 (631 lines) | openhands-sdk | 158.5 | 148 | 60.2% | $11.53 | 270s |
| Apr 1 | 172ac6b4 | v6 revert | openhands-sdk | 162.3 | 153 | 62.2% | $14.43 | 225s |
| Apr 2 | — | v12 | openhands-sdk | 180.9 | 173 | 70.3% | $19.30 | — |
| Apr 3 | fc8e3f8c | v12A (513) | openhands-sdk | 174.5 | ~163 | ~66% | — | — |
| Apr 3 | 0c85a2b2 | v12A (513) | openhands-sdk | 170.1 | ~160 | ~65% | — | — |
| Apr 3 | 20077bd5 | v13-codex (37) | openhands-sdk | 173.2 | ~162 | ~66% | — | — |
| Apr 4 | a84f586d | v13-core (37) | openhands-sdk | 168.7 | 158 | 64.2% | $14.66 | — |
| Apr 4 | fe3f9621 | v12-lean (297) | openhands-sdk | 164.4 | 151 | 61.4% | $12.80 | — |
| Apr 5 | c4def1c8 | v12+tweaks (548) | openhands-sdk | 167.3 | 157 | 63.8% | $13.66 | — |
| Apr 5 | 3770ec5b | v12 pure | openhands-sdk | 166.0 | 157 | 63.8% | $13.24 | 279.7s |
| Apr 5 | d9c55a1a | v12-formulas | openhands-sdk | 164.4 | 153 | 62.2% | $13.16 | 224.0s |
| Apr 5 | 1b886ece | v12-consolidated | openhands-sdk | 161.5 | 149 | 60.6% | $13.50 | 187.7s |
| Apr 5 | 64ae1545 | v14-alpha | openhands-sdk | 169.0 | 155 | 63.0% | $13.66 | 166.8s |
| Apr 5 | 98960149 | v14-alpha | openhands-sdk | 168.4 | 155 | 63.0% | $13.23 | 186.9s |
| Apr 5 | 9518deb7 | v14-alpha prompt | **goose** | 186.0 | 169 | 68.7% | $1.85 | 177.9s |
| **Apr 6** | **c64ef3b4** | **v14-alpha prompt** | **goose** | **192.0** | **174** | **70.7%** | **$1.85** | **171.0s** |
| Apr 6 | 82e93d12 | v12-formulas+goose | goose | 173.9 | 168 | 68.3% | — | — |
| Apr 6-7 | (5 rolls) | v14-alpha prompt | goose | 156-185 | — | — | ~$1.85 | 200-327s |
| **Apr 8** | **6ae6d76c** | **tar file rerun** | **goose** | **187.8** | **176** | **71.5%** | **~$1.85** | **~290s** |

---

## Appendix: The 84-Line Prompt (goose_prompt.j2)

The winning prompt contains exactly these sections, in this order:

| Section | Lines | Purpose |
|---------|-------|---------|
| Iron rules (3 behavioral rules) | 3 | Write-answer insurance, Python-only math, stop signal |
| Workflow (question classification + execution) | 6 | Task dispatch and phase ordering |
| Unit conversion rules | 6 | #1 error pattern — four places to check units |
| Fiscal year conventions | 3 | Pre/post-1976 disambiguation |
| Named formulas (20+ statistical operations) | 20 | Targets always-fail questions |
| Table reading (hierarchical headers) | 6 | Column path tracing with concrete example |
| Domain traps (terminology, false cognates) | 8 | "reported in" vs "reported for," financial term disambiguation |
| Multi-file strategy | 3 | Retrospective table prioritization |
| Output formatting | 3 | Bare-number formatting rules |
| External reference data (CPI-U, historical dates) | 5 | Eliminates web search dependency |
| Web search fallback | 2 | Wikipedia API for edge cases |
| Instruction variable | 1 | `{{ instruction }}` — the question |
| **Total** | **84** | |

Every line is a rule, formula, trap, or data point. Zero tutorials. Zero code examples. Zero explanatory prose.

---

*This document is source material for blog posts, investor narratives, and press. Raw reference, not polished narrative.*

*Dolores Research, April 2026.*
