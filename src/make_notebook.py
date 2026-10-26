"""Build an executed notebook from the same real-data pipeline, no fabricated outputs."""
import contextlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    blocks = [
        ('markdown', '# Demand forecasting - Week 1/2\nReal UCI daily rental data. Proposed project, pending Group 4 confirmation. No inventory/retail performance claim. Run from this notebook folder or the project root.\n'),
        ('code', "from pathlib import Path\nimport sys\nROOT = Path.cwd()\nif ROOT.name == 'notebooks':\n    ROOT = ROOT.parent\nassert (ROOT / 'src' / 'pipeline.py').exists(), 'Open from project root or notebooks folder'\nsys.path.insert(0, str(ROOT / 'src'))\nfrom pipeline import main\nmain()\n"),
        ('markdown', '## Exploratory analysis\nFull-data descriptive summaries only; baseline choice uses validation MAE.\n![EDA](../reports/figures/eda.png)\n'),
        ('code', "import json\nresults = json.loads((ROOT / 'reports' / 'results.json').read_text(encoding='utf-8'))\nprint(json.dumps(results['splits'], indent=2))\nprint('Selected baseline:', results['selected_by_validation_MAE'])\n"),
        ('markdown', '## Held-out rolling one-day forecasts\nLater observations enter only subsequent days. Not a fixed-origin multi-day prediction.\n![Holdout](../reports/figures/holdout.png)\n'),
        ('code', "import pandas as pd\nprint(pd.read_csv(ROOT / 'reports' / 'baseline-comparison.csv').to_string(index=False))\n"),
        ('markdown', '## Limits and next phase\nBike rentals are a public forecasting benchmark, not retail sales or inventory records. Stock/lead times are unavailable. Use explicit scenarios only; obtain real operational inputs and team approval before inventory backtesting. Advanced models/dashboard/API and official submission remain later work. Source attribution and full assumptions are in ../README.md.\n')]
    cells = []
    namespace = {'ROOT': ROOT}
    # Generate from the project root, preserving the caller working directory.
    import os
    previous = Path.cwd()
    try:
        os.chdir(ROOT)
        count = 0
        for kind, source in blocks:
            cell = {'cell_type': kind, 'metadata': {}, 'source': source.splitlines(keepends=True)}
            if kind == 'code':
                count += 1
                stream = io.StringIO()
                with contextlib.redirect_stdout(stream):
                    exec(compile(source, f'notebook-cell-{count}', 'exec'), namespace)
                cell.update(execution_count=count, outputs=[{'output_type': 'stream', 'name': 'stdout', 'text': stream.getvalue().splitlines(keepends=True)}])
            cells.append(cell)
    finally:
        os.chdir(previous)
    notebook = {'nbformat': 4, 'nbformat_minor': 4, 'metadata': {'kernelspec': {'name': 'python3', 'language': 'python', 'display_name': 'Python 3'}}, 'cells': cells}
    destination = ROOT / 'notebooks' / '01-demand-analysis.ipynb'
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(notebook, indent=2), encoding='utf-8')
    print('Executed notebook saved:', destination)


if __name__ == '__main__':
    main()
