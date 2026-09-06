# Proposal: refusal as evidence

**Status: proposal, not adopted.** Nothing in this document describes implemented
behaviour. It argues for a change to the project's objective and lists the amendments to
`AGENTS.md` that adopting it would require. Those amendments are deliberately *not*
applied here; the user decides, and `AGENTS.md` remains authoritative until they do.

## The problem with the current direction

The project currently aims at a small outpatient scheduler: register cases, reserve a
compatible room and doctor, estimate duration, confirm completion from hardware. Each
piece is competently built and none of it is new. Outpatient scheduling is a mature
commercial category, duration regression is a textbook supervised problem, occupancy
sensing is commodity hardware, and an FAQ chatbot is ubiquitous.

Judged as *scheduling software*, this project competes against products with twenty years
and large engineering teams behind them, and loses. The scope is not the problem. The
**objective** is.

## The thesis

> A scheduler in a resource-limited clinic is more valuable as an instrument that measures
> unmet demand than as a tool that optimises a calendar.

Commercial schedulers optimise throughput *given* resources. That objective presumes the
resources are roughly adequate and the difficulty is arranging them. In a resource-limited
setting the resources are **not** adequate, and the question that matters is the opposite
one: how much demand could not be served, and precisely which missing resource caused it.

No commercial scheduler reports that, because in a well-funded hospital nobody asks. In
global health it is the central question, because the actionable output is not a better
calendar — it is evidence for where the next doctor or room should go.

This reframing is what makes the project defensible as innovation. It is a different
objective, not a better implementation of the same one.

## Why this is nearly free to build

`assign_patient` already identifies the binding constraint on every failure:

```python
raise ValueError(f'No available room in {ward}. The case stays waiting.')
raise ValueError(f'No available doctor for {ward}. The case stays waiting.')
```

Those two branches *are* the measurement. The information is computed, formatted into a
sentence, displayed once, and discarded. Nothing records that a ward turned a case away at
14:20 because doctors ran out while a room sat idle.

The expensive part of this proposal is already written. What is missing is the decision to
keep the result.

## Four components

### 1. The refusal ledger

Record every refusal rather than only reporting it. Each entry holds the timestamp, the
ward, the requested date, the binding constraint as a code (`no_room`, `no_doctor`,
`no_compatible_doctor`, `not_today`, `duplicate`), and — critically — **what was still free
at that moment**.

"Refused for lack of a doctor while one room stood idle" is the actionable fact. A plain
refusal count is not.

### 2. Counterfactual capacity replay

From the ledger, answer the question a clinic manager actually has: *how many of these
refusals would one more doctor in this ward have absorbed?*

Because assignment is deterministic first-fit, recorded demand can be replayed exactly
against a modified resource set. The simplicity of the algorithm — which is not itself
innovative — becomes the property that makes exact replay possible. A stochastic or
optimising scheduler would make this considerably harder to do honestly.

The output is a specific, numbered recommendation: *"14 refusals this month; 11 would have
been absorbed by one additional doctor; 3 were room-bound."*

### 3. Uncertainty-aware duration

The current model predicts a point estimate in minutes. Operationally the tail matters more
than the mean: a 30-minute mean with a long tail wrecks an afternoon, while a reliable
40-minute appointment does not.

Predict quantiles instead — empirical ones per (ward, doctor) group are sufficient — and
buffer according to predicted spread rather than a fixed turnaround constant. This also
separates genuine capacity shortfall from shortfall caused by schedule fragility, which the
ledger otherwise cannot distinguish.

### 4. Evidence integrity

The unmet-demand claim is only as trustworthy as the occupancy data beneath it. A room
wrongly auto-released by a motion timeout **fabricates capacity that never existed** and
silently corrupts the ledger.

The sensor discipline already required by `AGENTS.md` — motion is activity, not vacancy;
never release without staff confirmation; explicit `awaiting confirmation` and `unknown`
states — stops being only a safety rule and becomes the guarantee that makes the
measurement admissible. The existing design already serves the new objective.

## The privacy result worth foregrounding

The ledger needs no patient identity whatsoever. Ward, timestamp, and constraint code are
sufficient for every output above.

**The most valuable product of this system requires the least sensitive data it holds.**
That is an unusually strong position for a health information tool, and it should be stated
explicitly rather than left implicit. It also aligns with the existing rule that data
minimisation must be architectural rather than instructed.

## What is genuinely new, stated precisely

Overclaiming would collapse this under questioning, so the boundary is drawn deliberately.

**Already well established, and not claimed as novel:** unmet-need measurement in health
systems research; blocked and abandoned demand in queueing theory; capacity planning by
simulation; quantile regression; human-in-the-loop confirmation.

**What is uncommon and defensible:**

- deriving unmet demand *continuously, as a byproduct of the operational tool*, attributed
  to the specific binding resource — where existing practice relies on retrospective
  surveys and aggregate utilisation statistics;
- counterfactual capacity replay performed with the same deterministic rule that produced
  the refusals, so the counterfactual is exact rather than modelled;
- designing the sensing layer specifically so that it cannot fabricate capacity, because
  fabricated capacity corrupts the measurement.

The honest label is **applied systems innovation in framing and instrumentation**, not
algorithmic novelty. That claim survives scrutiny. "We invented measuring unmet need" does
not.

## How it would be evaluated

All data remains simulated, and every result therefore demonstrates software behaviour
rather than clinical or operational effectiveness.

| Question | Measurement |
| --- | --- |
| Does the ledger capture refusals correctly? | Unit tests over scripted demand with known refusal causes. |
| Is the counterfactual exact? | Replay recorded demand against the original resources and confirm it reproduces the original outcomes exactly. |
| Does uncertainty-aware buffering help? | Simulate one clinic day under mean-based and quantile-based buffering; compare overrun cascades. |
| Can sensing corrupt the ledger? | Replay duplicate, stale, and disconnected event traces; confirm no capacity is invented. |

**The thesis is falsifiable, which is a strength.** If counterfactual replay shows that an
additional doctor would absorb almost no refusals, the finding is null for that dataset —
and reporting that plainly is a better result than a fabricated improvement.

## Explicit non-claims

- No clinical effectiveness, and no claim about real-world waiting times.
- No triage, diagnosis, or inference of clinical severity.
- Simulated data demonstrates software behaviour only.
- Counterfactual replay answers what *this deterministic rule* would have done, not what a
  real clinic would have done.

## Cost

This is an addition, not a rewrite. Registration, assignment, and the hardware plan all
survive unchanged; the ESP32 work is reframed rather than redesigned.

| Increment | Work |
| --- | --- |
| Refusal ledger | Return structured refusals instead of discarding them; store and display. Small — the constraint is already computed. |
| Unmet-demand view | Aggregate the ledger by ward, constraint, and period. |
| Counterfactual replay | Re-run recorded demand against a modified resource set. |
| Quantile durations | Extend `duration_model.py`; no interface change required. |
| Sensing | As already planned, with integrity of the ledger as the stated rationale. |

## Amendments to `AGENTS.md` this would require

Listed for approval; **not applied**.

1. *Purpose and scope* — state the measurement objective alongside the coordination one.
2. *First usable version* — add the refusal ledger and unmet-demand view; they become core
   rather than optional.
3. *Scheduling rules* — require that a refusal record its binding constraint and the
   resources still free at that moment.
4. *Machine learning* — permit quantile or interval estimates, not only point predictions.
5. *ESP32 and room state* — record that the confirmation discipline exists to protect the
   integrity of the measurement, not only patient safety.
6. *Verification* — add counterfactual replay exactness to the required scenarios.

## Recommendation

Adopt components 1 and 2. They carry the entire innovation claim, cost the least, and build
directly on code that already exists. Component 3 strengthens the result and can follow.
Component 4 is already required by the project and needs only its rationale restated.

If only one thing is built from this document, build the refusal ledger. Everything else in
the proposal depends on keeping information the program currently throws away.
