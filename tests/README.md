# Automatische Tests

Browser-Tests (Playwright, Chromium) gegen `index.html`. Supabase wird durch `stub.js` simuliert,
dadurch laufen die Tests ohne Internet und ohne echte Daten.

```
pip install playwright
playwright install chromium
python3 tests/run_all.py                       # alle Tests
python3 tests/barrierefreiheit_pruefer.py      # Prüfer: Beschriftungen, Kontrast, Grösse der Tippflächen
```

| Datei | Prüft |
|---|---|
| `test_offline.py` | Hinweisleiste ohne Verbindung, Eingaben bleiben stehen, kein Doppel-Absenden |
| `test_konto.py` | Passwortregeln, Passwort ändern, Konto löschen, Datenschutztext |
| `test_echtzeit.py` | Änderungen anderer Geräte, Schutz vor Überschreiben, Abmelden |
| `test_einkauf_menge_bearbeiten.py` | Menge, Bearbeiten per Antippen, leere Ansichten, letzte Seite, Start ohne Verbindung |
| `test_aufgaben.py` | Zuweisen, Fälligkeit, Wichtigkeit, Wiederholung, Filter |
| `test_einkauf.py` | Kategorien, Suche, «Häufig gekauft», Schutz vor Doppelten |
| `test_termine.py` | Ort, Wiederholung, Wochenansicht, Bearbeiten |
| `test_timer.py` | Pausieren, Fortsetzen, +1 Minute, Nochmal |

Hinweise: Die Tests verwenden das heutige Datum und sind deshalb nicht von festen Daten abhängig.
Nicht abgedeckt: echte Geräte (Samsung/Chrome), Push-Mitteilungen, echte Supabase-Verbindung.
