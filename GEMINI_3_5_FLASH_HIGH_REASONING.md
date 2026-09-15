# Gemini 3.5 Flash: high reasoning in Gemini CLI

Checked against Google's documentation and current upstream CLI source on 2026-09-15.

## What to expect

Gemini 3.5 Flash supports `minimal`, `low`, `medium`, and `high` thinking.
`HIGH` is the highest supported level.

The Gemini API defaults to `medium`, but the current Gemini CLI source already
configures the main Gemini 3.5 Flash chat model to inherit `HIGH`. Your installed
CLI version and existing user, project, or administrator settings can differ.
If your session already uses `HIGH`, explicitly setting it will not increase
reasoning further.

## Request HIGH explicitly

On Windows, edit:

```text
%USERPROFILE%\.gemini\settings.json
```

Merge the following configuration into the existing file. Preserve your other
settings. If `modelConfigs.overrides` already exists, append the rule to its
existing array instead of replacing the array or adding duplicate JSON keys.

```json
{
  "modelConfigs": {
    "overrides": [
      {
        "match": {
          "model": "gemini-3.5-flash"
        },
        "modelConfig": {
          "generateContentConfig": {
            "thinkingConfig": {
              "thinkingLevel": "HIGH"
            }
          }
        }
      }
    ]
  }
}
```

Do not combine `thinkingLevel` with a legacy `thinkingBudget` setting for the
same model request.

Restart Gemini from your reporting folder:

```powershell
gemini --model gemini-3.5-flash
```

This configures the requested thinking level; it does not confirm the effective
settings of an existing work-PC session. Administrator or more specific
configuration overrides may take precedence.

## Sources

- [Gemini CLI default model configurations](https://github.com/google-gemini/gemini-cli/blob/main/packages/core/src/config/defaultModelConfigs.ts)
- [Gemini CLI model configuration overrides](https://geminicli.com/docs/cli/generation-settings/)
- [Gemini CLI settings files and precedence](https://geminicli.com/docs/reference/configuration/)
- [Gemini 3.5 Flash supported thinking levels](https://ai.google.dev/gemini-api/docs/whats-new-gemini-3.5)
