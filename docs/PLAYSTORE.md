# Milteo im Google Play Store

Stand: Vorbereitung. Paketname: `ch.milteo.app` (nach der ersten Veröffentlichung nicht mehr änderbar).

## Ablauf
1. Play-Console-Konto anlegen (einmalig ca. 25 USD, Identitätsprüfung, bei privaten Konten Telefon + Adresse).
2. App «Milteo» in der Console anlegen (Sprache Deutsch, App, kostenlos).
3. App-Paket (.aab) bauen: PWABuilder (pwabuilder.com, URL https://www.milteo.ch → «Package for stores» → Android) oder Bubblewrap mit `docs/android/twa-manifest.json`. Beim Signieren «Play App Signing» wählen.
4. In der Console unter «App-Signatur» den SHA-256-Fingerabdruck kopieren, in `docs/android/assetlinks.json.vorlage` eintragen und als `.well-known/assetlinks.json` im Repo ablegen (sonst erscheint eine Browserleiste in der App). GitHub Pages blendet Ordner mit Punkt aus: Datei `.nojekyll` im Repo-Stamm anlegen.
5. Geschlossener Test: Tester (nach aktuellem Stand ca. 12) per E-Mail einladen, 14 Tage laufen lassen, dann Produktionszugang beantragen.
6. Store-Eintrag ausfüllen (Texte unten), Datenschutz-Link, Datensicherheits-Fragebogen, Inhaltseinstufung, Zielgruppe.
7. Zur Prüfung einreichen.

## Store-Texte (Deutsch)
**App-Name (max. 30):** Milteo Familienplaner

**Kurzbeschreibung (max. 80):** Einkauf, Aufgaben, Termine, Timer und Chat für die ganze Familie.

**Ausführliche Beschreibung:**
Milteo bringt die ganze Familie auf denselben Stand: eine App für Einkaufsliste, Aufgaben, Termine, Timer und Familien-Chat.

• Einkaufsliste: gemeinsam füllen, abhaken, Gericht eingeben und Zutaten per KI erhalten
• Rezepte Schritt für Schritt, mit Temperatur und Zeit
• Aufgaben für Kinder und Eltern, mit Fälligkeit und Wiederholung
• Termine und Stundenplan, auch aus Foto oder PDF
• Timer, die auf allen Handys klingeln
• Chat nur für die Familie
• Mitteilungen, wenn jemand etwas ergänzt
• 8 Sprachen: Deutsch, Mazedonisch, Französisch, Italienisch, Serbisch, Albanisch, Türkisch, Englisch
• Keine Werbung, kein Tracking

Jede Familie testet Milteo 30 Tage mit allen Funktionen.

**Kategorie:** Lifestyle (alternativ Produktivität)
**Kontakt:** support@milteo.ch · https://www.milteo.ch
**Datenschutz-Link:** https://www.milteo.ch (Datenschutz-Abschnitt; besser eine eigene Seite anlegen)

## Grafiken
- App-Icon 512×512: `icon-512.png` (vorhanden)
- Feature-Grafik 1024×500: fehlt
- Handy-Screenshots (mind. 2, besser 4–8): fehlen

## Offen / zu klären
- Abos in der App: Google verlangt für digitale Abos in der Regel Google Play Billing. Bezahl-Funktion deshalb erst nach Klärung einbauen; die erste Version bleibt kostenlos.
- Datenschutz auf eigener Seite, Impressum mit Namen und Adresse.
- Datensicherheits-Fragebogen: gesammelt werden E-Mail, Name, Inhalte der Familie; Kinder-Daten möglich.
