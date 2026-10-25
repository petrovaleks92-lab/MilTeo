"""Startet alle automatischen Tests von Milteo (Browser-Tests mit simuliertem Server).

Einmalig:  pip install playwright && playwright install chromium
Start:     python3 tests/run_all.py

Jeder Test meldet PASS/FAIL und am Ende «ALLES BESTANDEN». Es wird nichts im Internet
angesprochen: Supabase wird durch tests/stub.js ersetzt.
"""
import os, subprocess, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
failed = []
for f in sorted(glob.glob(os.path.join(HERE, 'test_*.py'))):
    name = os.path.basename(f)
    r = subprocess.run([sys.executable, f], capture_output=True, text=True, timeout=600)
    out = r.stdout + r.stderr
    ok = r.returncode == 0 and 'FAIL' not in out and 'Traceback' not in out and 'ALLES BESTANDEN' in out
    print(('OK     ' if ok else 'FEHLER ') + name)
    if not ok:
        failed.append(name)
        print('\n'.join(out.strip().splitlines()[-15:]))
print()
print('Alle Tests bestanden.' if not failed else 'Fehlgeschlagen: ' + ', '.join(failed))
sys.exit(1 if failed else 0)
