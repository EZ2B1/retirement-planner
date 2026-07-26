from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def test_required_directories_exist():
    for p in ['src/retirement_planner','docs','data/reference','data/scenarios','tests','workbooks/reference']:
        assert (ROOT/p).exists(), p
