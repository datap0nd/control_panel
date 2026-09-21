# Power BI to standalone HTML: Gemini CLI prompt

Use this for a one-page pilot before attempting an entire report. Put a copy of
the Power BI Project (PBIP/PBIR) in `source/`, reference screenshots in
`reference/`, and any approved local CSV/JSON snapshot in `data/`. Open Gemini
CLI from their parent folder and paste the prompt below.

Do not include data or metadata that your organization does not permit the
configured AI provider to process. Do not publish the generated HTML until all
embedded data is approved for public access.

```text
Build a standalone HTML replacement for the Power BI report in ./source.

Goal: one interactive report that can run with a local data file during
development, plus a command that generates a single, self-contained HTML
snapshot with the data embedded. The snapshot must work offline with its charts
and filters intact.

Hard boundaries:
- Do not connect to Fabric, Power BI Service, a gateway, an API, or an MCP server.
- Treat the PBIP/PBIR files as read-only descriptions of the report, not as a
  source of data.
- Do not modify the PBIP project, upload files, publish anything, or push to
  GitHub.
- Use only approved local files in ./data for real values. Never invent values
  and present them as real.
- Assume every value embedded in the final HTML can be inspected by anyone who
  receives it.

Work in this order:

1. Inspect ./source and ./reference. Inventory the pages, visuals, fields,
   measures, slicers, filters, and visual interactions. For each finding,
   identify the source file or screenshot that supports it. Mark anything you
   cannot determine as unknown; do not guess.

2. Choose one representative page for the first implementation. Explain what
   local data it needs to preserve all of that page's filter choices, not just
   the currently visible chart values. Flag measures such as distinct counts,
   averages, and time-based calculations that need special care. If no usable
   data exists in ./data, define the required CSV/JSON format and use clearly
   labelled synthetic test data until real data is supplied.

3. Build the page in a separate ./html-app folder. Keep the data-loading,
   calculations/filtering, and chart rendering code separate. Match the
   reference layout and recreate the meaningful interactions. Prefer Apache
   ECharts where appropriate. Do not hard-code KPI results or chart values.

4. Provide two commands:
   - a development command that runs the interactive report using a local data
     file;
   - a snapshot command that writes ./dist/report.html with its data, CSS,
     JavaScript, fonts, and chart library bundled locally. The finished HTML
     must make zero network requests when opened.

5. Add tests for calculations and filters. Compare available reference totals
   with Power BI values and report every mismatch. Test the generated HTML in
   a browser, including offline mode, several filter combinations, and a
   check for network requests.

Before coding, give me a short inventory, the proposed data format, and the
main fidelity risks. Then implement the first page. At the end, tell me exactly
what matches, what differs, what still needs real data, and the commands to
run.
```

The snapshot needs enough data for every permitted filter combination. A copy
of the currently displayed chart values is not sufficient.
