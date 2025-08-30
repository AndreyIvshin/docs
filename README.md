# Accessibility Issues Remediator
Fixes accessibility issues found `mhtml` files

### Usage
With Python version `3.13` run:
```bash
python -m venv venv && source venv/bin/activate && pip install --upgrade pip
pip install -r requirements.txt
PYTHONPATH=src python src/app.py -m data/1.mhtml 
```
Original `data/1.mhtml` gets converted into `tmp/1.mhtml`

>[!TIP]
>Use `-k` option to NOT purge the 'tmp' directory after the previous run

Run integration test via:
```bash
PYTHONPATH=src:test python test/integration.py
```