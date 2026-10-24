"""Writes SUMMARY.md: every step of every evidence file, with its result, so a reviewer can check the README's claims against the runs.

Usage (from the spike evidence folder): python3 tools/summarise_evidence.py > SUMMARY.md
A step is "ok" (it succeeded), "REFUSED" (it failed with the error shown; many are the expected refusal the scenario is proving) or "fact" (a recorded observation).
"""
import glob
import json
import os
import re

def clean(text: str, limit: int = 150) -> str:
	text = re.sub(r"<[^>]+>", "", str(text)).replace("\n", " ").replace("|", "/")
	return text if len(text) <= limit else text[: limit - 1] + "…"

def brief(step: dict) -> str:
	skip = {"step", "ok", "error", "trace", "result"}
	facts = {k: v for k, v in step.items() if k not in skip}
	if "result" in step and step["result"] is not None:
		facts["result"] = step["result"]
	return clean(json.dumps(facts, default=str, ensure_ascii=False), 190) if facts else ""

print("# Spike evidence summary\n")
print("Generated from the JSON files in this folder by `tools/summarise_evidence.py`. Result column: **ok** = the step succeeded; **REFUSED** = it failed with the error shown (usually the refusal the scenario is proving); **fact** = a recorded observation. Environment of each file is on its first line.\n")
for path in sorted(glob.glob("*.json")):
	data = json.load(open(path))
	if "steps" not in data:
		print(f"## {path}\n\nNot a step file (a description or comparison output): see the file.\n")
		continue
	env = data.get("environment", {})
	print(f"## {path}\n\nsite `{env.get('site')}` · Frappe {env.get('frappe')} · ERPNext {env.get('erpnext')} · {env.get('date')} · {len(data['steps'])} steps\n")
	print("| Step | Result | Detail |\n|---|---|---|")
	for step in data["steps"]:
		result = "REFUSED" if step.get("ok") is False else ("ok" if step.get("ok") else "fact")
		detail = clean(step["error"], 190) if result == "REFUSED" else brief(step)
		print(f"| {step['step']} | {result} | {detail} |")
	print()
