# AI-assisted arm, run 1

Accepted tests from the AI session go here. Full procedure: `docs/EXPERIMENT.md`, Step 3.

1. `python tools\prepare_ai_run.py --run run1` builds the isolated workspace `..\SEF_ai_workspace\run1\`.
2. Open a **new** AI session in that workspace (never in this project folder) and send the prompts in its `PROMPTS.md`.
3. Copy proposed files here, run them, and review every test against the specification.
4. Tag every kept test with its prompt id: `# source: P-001` or `# source: P-001 (edited)`.
5. Log each prompt with `python tools\log_prompt.py add ...` and your time in `logs/time_log.csv` (`arm` = `ai/run1`).
