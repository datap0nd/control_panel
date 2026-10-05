# ASAP catalog survey: Gemini CLI prompt

Use this to find out how many ASAP reports could be downloaded through the
MicroStrategy backend and which filter types to support first. It asks for
counts and filter types, not IDs. Open Gemini CLI on the work PC and paste the
prompt below. It is independent of the protocol note in
`ASAP_DIRECT_PROTOCOL_PROMPT.md`, so either can run first. Gemini stops after a
10-report pilot and waits for your OK before surveying the rest.

```text
I need a read-only SURVEY of the ASAP portal: counts and filter types across
every report my account can see, so we know how many reports could be
downloaded through the MicroStrategy backend and which filter types to
support first. This is a survey, not an inventory: numbers and types, not IDs.

GROUND RULES
- Read-only. Never press RUN, never export, never change a saved report,
  subscription or setting. Do not edit anything in the Metronome folder,
  governance.db or any Flow, and do not run a Metronome Flow.
- Read filter (prompt) definitions without running reports. If the only way
  to see a report's filters would run it (for example, creating an instance
  of a report that has no prompts), skip it and count it as "filters
  unknown". Ask me before using any method that runs reports.
- Go easy on the portal: one report at a time, at least 3 seconds between
  reports, no parallel requests. If the portal slows down or errors repeat,
  stop and tell me.
- Start with a PILOT of 10 reports from different menus. Show me the pilot
  summary, the method you used and the time per report, then wait for my OK
  before surveying the rest.
- Keep progress in your scratch workspace (asap_survey_progress.json) so the
  survey can resume after an interruption. Write the final summary there as
  asap_catalog_survey.md and print it here in full.

NEVER INCLUDE
- Hostnames, URLs, IP addresses.
- Cookie values, tokens, session ids, passwords, usernames, email addresses.
- Any MicroStrategy GUID or object ID.
- Filter option lists or selected values (no regions, accounts, shops,
  products), and no report data rows or cell values.
Top-level menu names and report names may appear only where asked below.

HOW TO FIND THE REPORTS
Start from the portal menu as my account sees it (the same tree the visible
header menu shows) and visit every leaf. Resolve shortcuts to what they
point at. Say how you walked it (visible menu, menuInfo.do, REST folders...).

CLASSIFY EVERY MENU ITEM
- MicroStrategy report (grid / Export Wizard style)
- MicroStrategy document or dossier
- HTML dashboard or page with download links
- Other, or could not tell (say why)
Also count each report's tabs / export views (e.g. "Export Wizard").

FOR EVERY MICROSTRATEGY REPORT, RECORD ITS FILTER TYPES (types only)
Use MicroStrategy's prompt types when you can read them (ELEMENTS, VALUE,
OBJECTS, EXPRESSION, LEVEL, ...), plus:
- VALUE: the data type (date, number, text)
- ELEMENTS: whether the portal shows it as a dropdown, a multi-select list or
  a "type to search" list, and whether it is required
- OBJECTS: whether it picks attributes (dimensions) or metrics (measures)
- which filter is the week/period filter and how it is shown (week range
  slider, two dropdowns, date picker, ...)
If you can only see the rendered page, describe each control instead
(dropdown, search list, slider, date picker, checkbox list) and tag it
[FROM PAGE].

THE SUMMARY MUST CONTAIN
1. Totals: menu items visited, counts per classification, shortcuts
   resolved, and items that failed to open, by reason.
2. Counts per top-level menu (menu name and numbers only).
3. Filter types: for each type, how many reports use it and how many of
   those have it required.
4. Coverage buckets, as numbers of MicroStrategy reports that use ONLY:
   a) element lists plus a week/period range (the same kinds as FF8 Input)
   b) a) plus attribute/metric pickers (OBJECTS)
   c) at least one other type, broken down by which type(s)
   d) no filters at all
   e) filters unknown
5. Week/period filters: how many reports have one, broken down by how it is
   shown and its format (e.g. YYYYWW).
6. Reports in bucket c): up to 50 report names, each with the unusual
   type(s) it needs.
7. Method, total time, average time per report, and anything that made the
   survey unreliable.

Before finishing, search the summary for: http, any hostname, @, any
32-character hex string, "token", "password". Fix anything found, then end
with the line: "Sanitization check passed."
```
