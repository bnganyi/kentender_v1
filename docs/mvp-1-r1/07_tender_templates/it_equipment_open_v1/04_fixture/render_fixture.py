import json
from pathlib import Path

from jinja2 import Environment, StrictUndefined, select_autoescape


ROOT = Path(__file__).resolve().parents[1]
input_path = ROOT / "04_fixture" / "kebs_input.json"

environment = Environment(
    autoescape=select_autoescape(enabled_extensions=("html",)),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
)
context = json.loads(input_path.read_text(encoding="utf-8"))

outputs = (
    ("invitation_to_tender.html", "kebs_invitation_expected.html"),
    ("complete_tender.html", "kebs_expected.html"),
)

for template_name, output_name in outputs:
    template_path = ROOT / "02_master" / template_name
    output_path = ROOT / "04_fixture" / output_name
    template = environment.from_string(template_path.read_text(encoding="utf-8"))
    output_path.write_text(template.render(**context), encoding="utf-8")
