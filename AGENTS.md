# Project guidance: outpatient scheduling assistant

## Purpose and scope

This directory contains a student final project combining **Tkinter**, **global health innovation**, **machine learning**, and **ESP32 hardware**. Its purpose is to help front-desk staff coordinate waiting cases, doctors, and rooms in one outpatient department.

Read `Proposal.md` for the user's original proposal. The working defaults below reflect the subsequent discussion and can evolve with the user's instructions. Prefer a small, meaningful, explainable application that the student can understand and present.

Keep this project's source, documentation, tests, sample data, and hardware files inside `preview-1-prime`. The sibling `preview-3` contains a separate diabetes demo and is not this project's codebase.

## Working with Claude Code and handoffs

`HANDOFF.md` is the shared session record for Codex and Claude Code. At the start of every session, read its newest session-log entry after reading this file. Use it to understand what the other assistant changed, what was verified, and what remains unfinished. Do not treat an old handoff entry as current without checking the code.

At the end of a session that changes the project, add one newest-first entry to `HANDOFF.md` describing the change, verification, and unfinished work. Keep durable project rules here, lesson progress in `LEARNING.md`, and newcomer run instructions in `README.md`; do not duplicate those documents unnecessarily in the handoff log.

## Teaching and independent rebuilding

The user explicitly wants to learn step by step and be able to recreate the project independently. Treat understanding and a working application as equally important outcomes.

- Build one small, runnable learning increment at a time. Avoid delivering several unexplained modules or the entire application in one turn.
- Before each increment, explain its purpose, the new concepts, and how it connects to what already exists.
- After implementation, explain the important code and trace one concrete example from user action to result. Define unfamiliar terms before relying on them.
- The user explicitly requests detailed explanations and teaching notes throughout Python files. Annotate new syntax, arguments, execution order, and design choices near the relevant code. Explain deeply rather than giving only brief summaries, and preserve the user's own edits and exercises.
- Provide the exact run command, expected behavior, and a short way to verify the change.
- Offer one small modification or reconstruction exercise, with a hint. Give the user an opportunity to try it before advancing; adapt the pace when they ask. Do not make quizzes or explicit approval a requirement for routine edits and fixes.
- Ask about Python/Tkinter experience early, then adjust explanations to the user's demonstrated understanding. Do not presume they know classes, callbacks, databases, or ML terminology.
- Maintain `LEARNING.md` with the roadmap, completed lessons, commands, exercises, and common mistakes as they arise. Clearly separate planned lessons from completed work.
- Keep code readable and explain design decisions. Introduce abstractions and dependencies when their benefit can be demonstrated in the current lesson.
- Eventually include a rebuild exercise from an empty folder using a behavior checklist, without requiring the user to copy the finished source.

## Current state

- Project guidance and the original proposal are present.
- Lesson 1 is preserved in `lessons/lesson_01.py`, including the user's confirmation-popup change.
- Lesson 2 is implemented in `app.py` and `registration.py`: patient name, optional medical information, appointment date, phone, and destination ward; generated ward-based queue IDs; an in-memory registration list and overview table.
- Queue format is `QWWRR`: two ward digits and two random digits (`00`–`99`). Repeated ward prefixes are allowed. Full IDs must be unique across the current session, even across appointment dates. A full ward pool rejects further registration without looping. This format permits 100 tickets per ward per session; persistence is not implemented.
- The user confirmed the date means appointment date and that each ward may contain multiple rooms. Ward codes identify destinations, not rooms. Registration must not assume one patient or one room per ward; room assignment is a later step.
- No appointment dataset, trained duration model, ESP32 connection, or external AI integration has been verified.
- Update this section and `README.md` when working features and run commands exist. Do not describe planned capabilities as completed.

## First usable version

1. Current front-desk entry: patient name, medical information, appointment date, phone number, and destination ward, with an automatically generated queue ID. Arrival time, appointment type, resource requirements, and clinical-staff urgency can be added when implementing scheduling.
2. A waiting queue and a clear view of doctor and room availability.
3. Explainable scheduling suggestions based on staff-assigned urgency, waiting order, estimated duration, and compatible resources.
4. Explicit appointment lifecycle: waiting, scheduled, in progress, completed, and cancelled.
5. Manual room status controls and simulated hardware events, followed by an ESP32 button integration.
6. Appointment-duration estimation, initially using a documented baseline, then a trained model when appropriate data is available.

Build the queue and conflict checks before adding ML or hardware. The app must remain demonstrable without an ESP32, internet connection, or API key.

## Scheduling rules

- Clinical staff supply urgency; the application does not diagnose or infer clinical severity from symptoms.
- Never double-book a doctor, room, or patient. Check complete time intervals, not only start times.
- Respect doctor schedules, required capabilities, room status, and any configured turnaround buffer.
- A free room does not imply a suitable doctor is available, and a scheduled end time does not prove a session has finished.
- When there is no valid assignment, leave the case waiting and explain why.
- Use a deterministic, documented tie-breaker such as arrival time within an urgency group. Show long waits for staff review.
- Keep in-progress sessions fixed. Staff must explicitly apply changes to existing assignments; show the effects of overruns and rescheduling.
- Start with a straightforward scheduling algorithm. Do not claim global optimality without implementing and evaluating it.

## Machine learning

- The initial ML task is **appointment-duration prediction**, not medical triage or diagnosis.
- Use only information available when the prediction is made. Actual end time and completed duration are outcomes, not input features.
- Compare a small regression model against a simple baseline such as median duration per appointment type.
- Separate training and evaluation appropriately for the data, using chronological evaluation when forecasting future appointments. Prevent duplicate or repeated-entity leakage where identifiers allow it.
- Report measured error in minutes and document dataset provenance, size, and limitations. Do not invent accuracy or effectiveness claims.
- Clearly label synthetic records and simulated evaluation. Synthetic-data results demonstrate software behavior, not hospital effectiveness.
- If there is no trained model or insufficient input, use the documented baseline and label the estimate's source in the UI.

## ESP32 and room state

- Start with staff-confirmed session-start/session-finish events from a button; include a software simulator using the same event interface.
- Motion and door events indicate activity, not confirmed room availability. Never release an occupied room solely because motion stops or a door opens.
- Separate observed sensor activity from the operational room state: available, occupied, awaiting confirmation, unavailable, or unknown.
- Handle repeated events, button bounce, disconnections, and stale signals. Missing hardware data must not make a room available automatically.
- Include timestamps and device/room identifiers, show connection status, and retain manual controls.
- Prefer a simple USB serial integration for the first hardware version. Confirm the actual board, sensor, and wiring before writing hardware-specific instructions.

## Optional AI FAQ assistant and privacy

- The external AI FAQ feature is a later extension; core scheduling works locally.
- Limit the first FAQ interface to predefined general hospital topics and approved public information. Local FAQ answers are a valid starting point.
- Do not send patient records, queue IDs, appointment histories, clinical notes, sensor logs, or schedule exports to an external AI service.
- Construct external requests from an allowlist of public FAQ content. Removing names alone is not a sufficient privacy boundary.
- Keep the FAQ component isolated from patient storage and scheduling actions. A prompt saying "do not leak information" is not an access control.
- Keep credentials outside source code and out of logs. Do not claim zero leakage or provider guarantees without verifying the complete implementation and provider terms.
- Use fictional records during development and demonstrations.

## Implementation approach

- Use Python with native Tkinter/ttk for the desktop interface. Keep the first version understandable and dependencies minimal.
- Separate scheduling/domain logic, storage, duration estimation, hardware events, and UI so the important logic is testable without a window.
- Prefer standard-library tools and SQLite for local persistence when needed. Use established ML libraries when introducing a trained model; do not implement training mathematics from scratch solely to avoid a dependency.
- Keep serial reads, network requests, and training off the Tkinter event loop. Update widgets on the UI thread using a queue and `after()`.
- Resolve project resources relative to their files. Avoid hard-coded user paths in application logic.
- Do not add a cloud backend, hospital-system integration, login system, or elaborate architecture before the core demonstration needs it.
- Add run/setup commands only after verifying them. Explain assumptions and non-obvious scheduling decisions in plain language.

## Verification and demonstration

Test scheduling behavior with meaningful scenarios: overlapping intervals, resource incompatibility, unavailable staff, equal-priority cases, cancellations, overruns, manual changes, and no feasible slot.

Test hardware behavior with duplicate, stale, and disconnected events. When ML is added, verify fallback behavior, leakage prevention, and baseline comparison. When an API is added, test the actual outbound payload for prohibited fields.

The intended end-to-end demonstration is: enter fictional cases, assign compatible doctors and rooms, show conflict prevention, start a session, confirm its completion through a simulated or real button, and update the waiting queue. Clearly distinguish simulated, implemented, and future features.
