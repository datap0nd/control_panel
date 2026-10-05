# ASAP direct-download protocol note: Gemini CLI prompt

Use this to get a sanitized description of the ASAP direct-download scripts so
the same backend download can be built into Metronome Flows. Open Gemini CLI on
the work PC and paste the prompt below. Skim the note before sharing it, even
after Gemini's own sanitization check. Section 5 matters most: if it comes back
marked [UNSURE], say so when sharing the note.

```text
I need a sanitized protocol note about the ASAP direct-download scripts in
%USERPROFILE%\Documents\Project (asap_direct_client.py, download_ff8_input.py,
download_global_ff8_input.py, download_global_s26fe_input.py and templates\).
An engineer will use it to build the same backend download into Metronome,
where users type filter values into a Flow and Metronome builds the request.
Describe the protocol (structure and field names), not secret values.

GROUND RULES
- Read-only. Do not edit the scripts, anything in the Metronome folder,
  governance.db or any Flow. Do not run a Metronome Flow.
- You may run ONE of the scripts once, unchanged, only to confirm something
  you cannot read from the code. Tag every statement: [FROM CODE],
  [OBSERVED] (seen in that run) or [UNSURE].
- Write the note to your scratch workspace as asap_direct_protocol.md and
  also print it here in full.

NEVER INCLUDE (replace with placeholders)
- Hostnames, full URLs, IP addresses. Write paths only, e.g. POST /mstr/servlet/mstrWeb.
- Cookie values, tokens, session ids, mstrWeb/rb values, passwords,
  usernames, email addresses.
- Report data rows or cell values.
- Any 32-character MicroStrategy GUID. Replace each with a named placeholder,
  the same GUID always becoming the same placeholder: {REPORT_ID},
  {REPORT_OBJECT_ID}, {PROMPT_REGION}, {ATTR_REGION}, {ELEMENT_1}, ...
Filter names and the filter values the scripts select (MIDDLE EAST, Z8,
week numbers) may stay.

THE NOTE MUST COVER

1. Sign-in and session
   - How the client gets an authenticated session (browser SSO? which
     credentials file? which browser profile folder?) and what it hands to
     the HTTP client: cookie NAMES and header NAMES only.
   - How it detects an expired session or a sign-in page.

2. Request sequence. For every request, in order:
   - method and path
   - every query/form field name, marked as one of: fixed constant (give the
     value if not secret, e.g. evt=4001, objectType=8), per-report ID
     (placeholder), per-run value (e.g. the prompt XML), or copied from an
     earlier response (say which response and exactly how it is extracted)
   - required headers (names, plus values when not secret)
   - what the response looks like and what the client reads from it (which
     inputs of <form id="pageStateForm">, how a "wait page" is recognised)
   - which requests are mandatory and which are optional

3. Polling and export
   - The evt=5005 loop: interval, what means still running / done / failed,
     and the timeout.
   - Full parameter sets for the Excel export (evt=3012) and the CSV export
     (evt=3131), including any "export report title" / "filter details"
     options and what each parameter does.
   - How the final file is recognised (content-type, content-disposition,
     other headers), its encoding, and any oddities.

4. The prompt-answer XML (promptsAnswerXML)
   - The full FF8 Input template with GUIDs replaced by placeholders, keeping
     every tag and attribute exactly.
   - Annotate which part is each filter (Region, Series, week range) and what
     each tag/attribute means where you can tell (mi, in, oi, pa, did, ia, lcl...).
   - How two selected values for one filter are written, and how
     "no filter / all" is written.
   - What update_week_range() changes: which elements, the week format
     (e.g. 202629), and the week numbering (ISO? Sunday-start?).

5. Typing filter values (MOST IMPORTANT)
   Users will type values such as "MIDDLE EAST" instead of picking IDs.
   - In the XML, is a selected value written as an element ID that contains
     the display name (shape like h<DisplayName>;<ATTRIBUTE_GUID>), or as an
     opaque code/GUID that must be looked up? Show the shape with placeholders.
   - If it must be looked up: where did the scripts get those IDs, and which
     request returns them?
   - If you run a script: what happens with a misspelled value - an error, an
     empty file, or an UNFILTERED file? Only test this if it is quick and
     read-only; otherwise mark it [UNSURE].

6. Where each ID comes from
   - How were REPORT_ID, REPORT_OBJECT_ID and each prompt/attribute GUID found
     (HAR capture, page source, portal menu, REST call)?
   - Can they be read from the report page as it opens in the portal, before
     RUN is pressed? From where exactly (frame URL, form field, inline script,
     menu tree)?
   - What objectType=8 means here, how REPORT_OBJECT_ID relates to the ASAP
     menu entry, and how REPORT_ID relates to the report tab
     (e.g. "Export Wizard").

7. Differences between the three report scripts
   - Do they differ only in IDs, filters and template, or does any report need
     a different request sequence or export type?

8. Timings and failures seen while building the scripts (wait-page loops,
   expired sessions, server errors), described without data.

Before finishing, search your note for: http, any hostname, @, any
32-character hex string, "Cookie:", "token", "password". Fix anything found,
then end the note with the line: "Sanitization check passed."
```
