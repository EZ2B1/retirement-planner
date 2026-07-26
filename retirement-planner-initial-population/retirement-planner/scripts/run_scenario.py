import argparse, yaml
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('--scenario',required=True); a=p.parse_args()
data=yaml.safe_load(Path(a.scenario).read_text(encoding='utf-8'))
print(f"Loaded scenario: {data.get('scenario_name','Unnamed')}")
