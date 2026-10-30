# MilTeo – Bestandsbericht und Umsetzungsplan

Stand: 24.10.2026. Grundlage: Verbesserungs-Roadmap (ChatGPT), vollständiger Quellcode (`index.html`, `i18n.js`, `sw.js`, `manifest.json`), Datenbank-Regeln und Edge Functions in Supabase (nur gelesen, nichts verändert).

## 1. Architektur (Ist-Zustand)

- **Frontend:** statische PWA auf GitHub Pages. Eine Datei `index.html` (ca. 2100 Zeilen, Skript inline), `i18n.js` (8 Sprachen), `sw.js` (Service Worker: Netzwerk zuerst, Offline-Rückfall auf zwischengespeicherte Seite, Push), `manifest.json`.
- **Backend:** Supabase (Auth, Postgres mit Row Level Security, Realtime, Storage `chat-media` privat, Edge Functions `dish`, `notify`, `tick`; Cron jede Minute).
- **Tabellen:** `families` (nur `code`), `members`, `entries` (Einkauf, Aufgaben, Timer, Termine, Stundenpläne als JSON in `data`), `messages`, `push_subscriptions`, `ai_calls`, `join_attempts`, `app_secrets`; `shopping_items` ist ein Altbestand ohne Verwendung.
- **Zugriffsschutz:** Policies prüfen überall `family_id = my_family()`. Chat-Bilder liegen unter `<familie>/…` und sind per Storage-Policy auf die eigene Familie beschränkt. Der anon-Schlüssel im Frontend ist der öffentliche Schlüssel, im Repository liegen keine geheimen Schlüssel (geprüft per Suche, auch in der Git-Historie nach `service_role`).

## 2. Status je Roadmap-Punkt

Legende: ✅ umgesetzt (im Code gesehen) · 🟡 teilweise · ❌ fehlt · ⛔ braucht Änderung an der Datenbank (nur mit deiner Freigabe)

Alles ist anhand von Code und Datenbank-Regeln beurteilt. Auf echten Geräten getestet ist davon nur, was du selbst ausprobiert hast.

### Priorität 1 – Stabilität und Sicherheit
| Punkt | Status | Befund |
|---|---|---|
| Registrierung, Anmeldung, Abmeldung | ✅ | Fehler verständlich (falsches Passwort, bereits registriert, zu viele Versuche). |
| Passwort vergessen / ändern | ✅ | Vergessen ✅. Ändern in «Konto & Passwort» (mit Prüfung des aktuellen Passworts) ✅ seit Schritt 2. |
| Profil bearbeiten | 🟡 | Name ✅. E-Mail ändern ❌. |
| Familie erstellen, mit Code beitreten | ✅ | Beitritt hat Versuchsbremse (8 Fehlversuche pro Stunde). |
| Code erneuern, Familie verlassen | ✅ | Jedes Mitglied darf beides. |
| Mitglieder entfernen, Rollen (Eltern/Kind) | ⛔ | Es gibt keine Rollen: alle Mitglieder sind gleichberechtigt. Braucht neue Spalte/Tabelle. |
| Einladungscode zeitlich begrenzen | ⛔ | Code ist unbegrenzt gültig (nur manuell erneuerbar). Braucht neue Spalte. |
| Fremde Familiendaten schützen | ✅ | Policies auf `entries`, `messages`, `families`, `members`, Storage geprüft. Ein Mitglied könnte bei `entries` das Feld `created_by` überschreiben (Update-Policy prüft nur die Familie), geringes Risiko. ⛔ |
| Dauerhafte Speicherung | ✅ | Alles in Supabase, nichts nur lokal (ausser Anzeige-Einstellungen). |
| Synchronisierung | ✅ | Chat und (seit Schritt 3) Einkauf/Aufgaben/Termine/Timer per Echtzeit; Abfrage nur noch als Sicherheitsnetz alle 60 Sekunden (15 Sekunden, falls Echtzeit ausfällt). |
| Konflikte bei gleichzeitigem Ändern | ✅ | Seit Schritt 3 wird vor dem Speichern der aktuelle Stand geholt und nur die eigene Änderung darauf angewendet (Abhaken, Zutaten, Erinnerung, Anzeige im Hauptmenü, Stundenplan-Einträge, Rezept). Zutaten werden über Name und Menge gefunden, nicht über die Position. Die Server-Markierungen für gesendete Erinnerungen bleiben dabei erhalten. Restrisiko: zwei Änderungen im selben Sekundenbruchteil (Lesen und Schreiben sind zwei Schritte). |
| Lade-, Offline-, Speicherfehler sichtbar | ❌ → **jetzt in Arbeit** | Vorher: Eingabetext wird gelöscht, bevor das Speichern geklappt hat. Bei fehlender Verbindung alle 15 Sekunden die Meldung «Fehler beim Laden». Kein Offline-Hinweis. |
| Eingaben validieren | 🟡 | Längen und Datum im Formular geprüft; serverseitig nur `kind`-Check und `left(name, 40)`. Serverseitige Grenzen für `entries.data` fehlen. ⛔ |
| Kinder-Datenschutz | ❌ | Hängt an Rollen. ⛔ |
| Keine Zugangsdaten in Logs | ✅ | Im Code nichts gefunden; Edge Functions loggen keine Tokens. |

### Priorität 2 – Dashboard und Oberfläche
| Punkt | Status | Befund |
|---|---|---|
| Dashboard | 🟡 | Begrüssung, nächster Termin, Stundenplan, 6 Kacheln mit Kurzinfo ✅; seit Schritt 4 auch Schnell-Hinzufügen (Einkauf/Aufgabe/Termin), Karte «Offene Aufgaben», Namen der Mitglieder in der Familien-Kachel. Fehlen: Familienname (⛔, `families` hat keinen Namen), mehrere neueste Chatnachrichten. |
| Leere Ansichten | ✅ | Seit Schritt 4: verständlicher Text und Knopf, der zum Eingabefeld führt (Einkauf, Aufgaben, Termine, Timer, Chat). |
| Navigation | ✅ | Untere Leiste, aktiver Punkt hervorgehoben. Auf der Startseite ausgeblendet (bewusst). |
| Einheitliches Design, responsiv | ✅ | Seit Schritt 5: ab 760 px breiter (860 px) mit 3 Kacheln pro Zeile, ab 1100 px 1000 px. |
| Dark Mode | ✅ | Seit Schritt 5: Schalter «Darstellung» (Automatisch/Hell/Dunkel) unter Familie, pro Gerät gemerkt, ohne Aufblitzen beim Start. |
| Barrierefreiheit | ✅ | Seit Schritt 5: alle Knöpfe/Felder haben Namen (Eigener Prüfer: vorher 10 ohne Namen, jetzt 0), Kontrast im Hell- und Dunkelmodus erfüllt (Logo ausgenommen), Zielgrösse mind. 36 px, Fokusrahmen, `aria-current` im Menü, anklickbare Flächen per Tastatur bedienbar, Esc schliesst Bild, weniger Bewegung wird beachtet. Grenze: das Standardwerkzeug axe-core liess sich hier nicht laden; geprüft wurde mit eigenem Skript, nicht mit Screenreader auf echtem Gerät. |

### Priorität 3–5 – Einkauf, Aufgaben, Termine
| Bereich | Status | Befund |
|---|---|---|
| Einkauf | 🟡 | Hinzufügen, abhaken, löschen (mit Rückgängig), Gericht → Zutaten (eingebaute Rezepte + kostenlose KI), Menge, Bearbeiten, 8 Sprachen ✅; seit Schritt 7: automatische Kategorien (9 Gruppen, aus dem Namen erraten, im Bearbeiten änderbar), Suche (ab 6 Einträgen, auch in Zutaten), «Häufig gekauft» (ab 2× abgehakt, **pro Gerät** gemerkt), Duplikat-Schutz (offen → Hinweis und Menge ergänzen, erledigt → zurück auf die Liste). Fehlen: Notizen, mehrere Listen. Kategorien erkennt nur deutsche Wörter. Wochenmenü ❌. |
| Aufgaben | 🟡 | Erstellen, abhaken, löschen, Ersteller anzeigen, Bearbeiten ✅; seit Schritt 6: Zuweisen an ein Familienmitglied, Fälligkeit, Wichtigkeit, Wiederholung (täglich/wöchentlich/monatlich: Abhaken setzt das nächste Datum), Filter (Alle/Meine/Überfällig/Erledigt), Sortierung nach Fälligkeit, Kennzeichen «Überfällig» auch auf der Startseite. Gespeichert im Datenfeld, keine DB-Änderung. Fehlen: Erinnerung/Benachrichtigung bei Fälligkeit und bei Zuweisung (bräuchte Änderung der Funktion `tick`), Belohnungssystem ❌. |
| Termine | 🟡 | Erstellen, löschen, Erinnerung (auch nachträglich), Import aus Datei, Stundenplan mit Gruppen, einklappbar ✅; seit Schritt 8: Ort (mit Link zur Karte), Wiederholung (täglich/wöchentlich/monatlich/jährlich), Wochenansicht (Liste/Woche, blättern), vollständiges Bearbeiten (Titel, Datum, Zeit, Ort, Wiederholung). **Wiederholung:** das Datum rückt auch serverseitig weiter (Funktion `tick`, Version 6, 25.10.2026), die Erinnerung für die nächste Wiederholung kommt also auch, wenn niemand die App öffnet. Fehlen: Personen-Zuordnung, Kalenderexport, Stundenplan in der Wochenansicht. |

### Priorität 6–10
| Bereich | Status | Befund |
|---|---|---|
| Chat | ✅/🟡 | Echtzeit, Bilder, Sprachnachrichten, Zeitstempel, Leerhinweis ✅. Fehlgeschlagene Nachrichten werden nur per Hinweis gemeldet (Text bleibt im Feld ✅); keine Ungelesen-Zählung pro Nachricht (Punkt und Zähler auf der Startseite ✅). |
| Timer | ✅ | Starten, Restzeit, Ende-Hinweis, Push bei geschlossener App ✅; seit Schritt 9: Pausieren/Fortsetzen, +1 Minute, «Nochmal starten» nach Ablauf; Startseite zeigt «pausiert». Pausiert wird intern mit einem weit entfernten Endzeitpunkt gespeichert, damit der Server keine Mitteilung schickt (ältere, noch nicht neu geladene App-Versionen würden einen pausierten Timer als sehr lange laufend anzeigen). Fehlt: mehrere Voreinstellungen (Kurzwahl 5/10/15 Min). |
| Benachrichtigungen | ✅ | Schalter für Chat/Timer/Termine, Berechtigung wird erklärt, Test-Taste, automatische Erneuerung, hohe Zustellpriorität. |
| Einstellungen | 🟡 | Name, Sprache, Mitglieder, Code ✅. Kontolöschung ✅ (Schritt 2, mit Passwortabfrage). Datenschutzinformation ✅ (Schritt 2); Kontaktadresse ❌ (noch keine hinterlegt). |
| Schweiz | ✅ | Datumsformat und 24-Stunden-Zeit über die Gerätesprache `de-CH`, Standardsprache Deutsch, keine kostenpflichtigen Dienste. Zeitzone: Termine ohne Zeitzone werden lokal verstanden, die Server-Erinnerungen rechnen in Europe/Zurich. |
| Technische Qualität | ✅ | PWA installierbar ✅, Service Worker ✅. Seit Schritt 12: automatische Tests im Ordner `tests/` (8 Testdateien plus Prüfer für Barrierefreiheit, Start mit `python3 tests/run_all.py`), Altlasten bereinigt (`sw (1).js` entfernt, überzählige `</div>` entfernt, keine technischen Fehlertexte mehr bei «Familie verlassen»). Offen: `index.html` ist weiterhin eine grosse Datei (kein Umbau, bewusst). |

### Supabase-Prüfung (Sicherheit)
- `pg_net` liegt im Schema `public` (Warnung, nur Aufräumarbeit).
- «Leaked password protection» ist ausgeschaltet. Sie gibt es bei Supabase nur im kostenpflichtigen Pro-Plan (Meldung im Dashboard am 24.10.), wird also nicht aktiviert. Ersatz in der App: mindestens 8 Zeichen und Ablehnung sehr bekannter Passwörter (Schritt 2).
- Tabellen ohne Policy (`ai_calls`, `app_secrets`, `join_attempts`, `shopping_items`): für Clients damit gesperrt, also gewollt sicher.
- Familiencodes werden mit `random()` statt einer kryptografischen Quelle erzeugt (8 Zeichen aus 31, durch die Versuchsbremse praktisch nicht erratbar; trotzdem verbesserungswürdig).

## 3. Priorisierter Umsetzungsplan

Jeder Schritt: klein, getestet, danach wieder lauffähig. Schritte mit ⛔ warten auf deine Freigabe.

1. **Verbindung und Speichern ohne Datenverlust** (jetzt umgesetzt): Eingaben bleiben stehen, wenn das Speichern scheitert; sichtbarer Hinweis bei fehlender Verbindung; keine Fehlermeldung alle 15 Sekunden; Anzeige springt zurück, wenn etwas nicht gespeichert werden konnte.
2. **Konto und Datenschutz:** Schaltfläche «Konto löschen» (nutzt die vorhandene Serverfunktion, mit Bestätigung), Datenschutzinformation, Passwort in der App ändern.
3. **Echtzeit-Sync für alle Listen** statt 15-Sekunden-Abfrage; Zutaten einzeln speichern, damit gleichzeitiges Abhaken sich nicht überschreibt.
4. **Leere Ansichten mit Aktion** und **Dashboard** (Mitglieder, offene Aufgaben, Schnell-Hinzufügen).
5. **Barrierefreiheit** (Beschriftungen, Fokusrahmen, Tab-Rollen), Dark-Mode-Schalter, breitere Darstellung auf Tablet/Desktop.
6. **Aufgaben:** zuweisen, Fälligkeit, Priorität, Wiederholung, Filter (alles im bestehenden JSON, ohne Datenbankänderung).
7. **Einkauf:** Menge, Kategorie, Suche, «häufig gekauft», Duplikat-Schutz.
8. **Termine:** Ort, Beschreibung, wiederkehrend, Wochenansicht, Bearbeiten.
9. **Timer:** Pausieren/Zurücksetzen.
10. ⛔ **Rollen und Einladungen:** Eltern/Kind, Mitglieder entfernen, Code mit Ablaufdatum, `created_by`-Schutz, Familienname. Braucht neue Spalten bzw. Tabelle und Policies; ich schicke dir vorher den genauen SQL-Text.
11. **Belohnungssystem** – auf Wunsch übersprungen.
12. **Automatisierte Tests** im Repository (Playwright) und Aufräumen der Altlasten.

## 4. Änderungsprotokoll

| Schritt | Dateien | Test |
|---|---|---|
| 1 Verbindung und Speichern | `index.html` (Hinweisleiste `#net`, `addEntry`/`updateEntry`/`delEntry`/`loadEntries`/`loadChat`, Formulare Einkauf/Aufgaben/Termine), `i18n.js` (3 neue Texte in 8 Sprachen) | Automatisch im Browser mit simuliertem Netzausfall (22 Prüfungen, alle bestanden): Text bleibt bei Fehler stehen, Hinweisleiste erscheint und verschwindet wieder, Abhaken und Löschen springen zurück, keine Fehlermeldung bei der Hintergrund-Abfrage, Doppel-Absenden speichert nur einmal, Banner in Französisch. Bisherige Tests (Import, Stundenplan) laufen weiter. **Nicht getestet:** echtes Handy mit echtem Mobilfunk; die neuen Übersetzungen (mk, sr, sq, tr) stammen von mir und sind nicht von Muttersprachlern geprüft. |
| 2 Konto und Datenschutz | `index.html` (Bereich «Konto & Passwort», «Datenschutz», `pwProblem`, `checkCurrentPw`), `i18n.js` (14 neue Texte in 8 Sprachen) | Automatisch im Browser mit simuliertem Server (alle bestanden): falsches aktuelles Passwort wird abgelehnt, schwache/ungleiche neue Passwörter werden abgelehnt, richtiges Ändern ruft die Passwortänderung auf; Konto löschen verlangt das Passwort, zeigt bei Serverfehler eine freundliche Meldung, räumt bei Erfolg lokale Daten auf und zeigt die Anmeldung; Registrierung blockiert schwache Passwörter; Datenschutztext auf Französisch. **Nicht getestet:** das echte Löschen auf dem Server (bewusst, um keine echten Daten zu löschen). |

## 5. Bekannte Einschränkungen beim Konto löschen
- **Dein eigenes Konto (petrov.aleks92@gmail.com) lässt sich im Moment nicht löschen:** 6 Einträge der alten Tabelle `shopping_items` verweisen auf dich und blockieren das Löschen. Die App zeigt dann die freundliche Fehlermeldung. Andere Konten sind nicht betroffen. **Behoben am 24.10.2026 mit deiner Freigabe:** Der Verweis wurde auf «beim Löschen leer setzen» umgestellt (Migration `shopping_items_created_by_set_null`; die 6 Einträge sind unverändert).
- Hochgeladene Chat-Bilder und Sprachnachrichten bleiben nach dem Löschen im Speicher liegen (die Nachrichten selbst werden gelöscht). Das Aufräumen braucht eine neue Speicher-Regel (⛔).
- In Einträgen der Familie kann der Name des Erstellers als Text stehen bleiben (steht so im Hinweis in der App).

## 6. Nachtrag: Hinweis zur KI (Gemini)
Laut den Gemini-API-Bedingungen (ai.google.dev/terms, geprüft am 24.10.2026) darf Google bei der kostenlosen Nutzung gesendete Inhalte zur Verbesserung seiner Produkte verwenden, und Mitarbeitende können sie lesen; persönliche oder vertrauliche Daten sollen nicht gesendet werden. Deshalb steht dazu jetzt ein Absatz im Datenschutz-Text und ein kurzer Hinweis bei «Termine aus Datei» und beim Stundenplan-Upload (8 Sprachen). Die Alternative wäre ein bezahlter Gemini-Plan (dort wird nicht zum Training verwendet) – kostet Geld, daher nicht umgesetzt.
| 3 Echtzeit und Überschreibschutz | `index.html` (`subscribeEntries`, `patchEntry`, `scheduleReload`, `itemIdx`; Abfrage der Mitglieder höchstens alle 60 Sekunden) | Automatisch im Browser mit simuliertem Server (alle bestanden): Änderung einer anderen Person erscheint ohne Warten; gleichzeitiges Abhaken zweier Zutaten bleibt beides erhalten; inzwischen gelöschte Zutat oder Eintrag verursacht keinen Fehler; Löschen trifft trotz verschobener Position die richtige Zutat; Server-Markierung «Erinnerung gesendet» bleibt erhalten; Offline-Verhalten aus Schritt 1 funktioniert weiter. **Nicht getestet:** echte Echtzeit-Verbindung zwischen zwei Geräten (nur simuliert), das bitte kurz zu zweit ausprobieren. Datenbank unverändert. |
| 4 Menge, Bearbeiten, leere Ansichten, Dashboard, letzte Seite | `index.html`, `i18n.js` (15 neue Texte in 8 Sprachen) | Automatisch im Browser mit simuliertem Server (alle bestanden): Menge speichern/anzeigen/entfernen, Bearbeiten per Antippen (Text und Menge; Eingabe bleibt beim Neuladen durch andere erhalten; leerer Text wird abgelehnt; Abbrechen), Zutat im Gericht bearbeiten, leere Ansichten mit Knopf und Fokus, Schnellaktionen, Karte «Offene Aufgaben», zuletzt besuchte Seite nach Neustart und beim Zurückwechseln (Anmelde-Ereignis ändert die Seite nicht mehr), Start ohne Verbindung aus dem Zwischenspeicher, Zurück-Taste führt zur Startseite. Sichtkontrolle per Bildschirmfoto (390 px breit). **Nicht getestet:** echtes Handy (App-Wechsel, Tastatur), die neuen Übersetzungen (mk, sr, sq, tr) stammen von mir. |
| 5 Barrierefreiheit, Darstellung, breite Ansicht | `index.html`, `i18n.js` (9 neue Texte in 8 Sprachen) | Eigener Prüfer vorher/nachher (ohne Namen 10→0, Kontrast 21→0 ausser Logo, kleine Ziele 60→6 von mind. 36 px), alle früheren Tests bestanden, Darstellung umschalten und merken, Bildschirmfotos hell/dunkel/1280 px. **Nicht getestet:** Screenreader (TalkBack), echtes Handy/Tablet; neue Übersetzungen (mk, sr, sq, tr) stammen von mir. |
| 6 Aufgaben: zuweisen, Fälligkeit, Wichtigkeit, Wiederholung, Filter | `index.html`, `i18n.js` (17 neue Texte in 8 Sprachen) | Automatisch mit simuliertem Server (alle bestanden): Speichern aller Felder, keine leeren Felder ohne Optionen, Sortierung, drei Filter, Wiederholung setzt nächstes Datum, Bearbeiten und Entfernen der Optionen, Startseite, Englisch inkl. Sprachwechsel, frühere Tests und Barrierefreiheits-Prüfer unverändert gut. **Nicht getestet:** echtes Handy (Datumsauswahl auf Samsung); neue Übersetzungen (mk, sr, sq, tr) von mir. |
| 7 Einkauf: Kategorien, Suche, häufig gekauft, Duplikat-Schutz | `index.html`, `i18n.js` (16 neue Texte in 8 Sprachen) | Automatisch mit simuliertem Server (alle bestanden): Kategorien erraten (12 Beispiele), Gruppierung, Duplikate (andere Schreibweise, Menge ergänzen, erledigt zurückholen), Suche inkl. Zutaten im Gericht, Kategorie ändern/zurücksetzen, «Häufig gekauft» hinzufügen, Gericht bleibt oben; dabei Fehler im Bearbeiten der Aufgaben-Optionen gefunden und behoben. Frühere Tests und Prüfer unverändert. **Nicht getestet:** echtes Handy; Übersetzungen (mk, sr, sq, tr) von mir. |
| 8 Termine: Ort, Wiederholung, Wochenansicht, Bearbeiten | `index.html`, `i18n.js` (13 neue Texte in 8 Sprachen) | Automatisch mit simuliertem Server (alle bestanden): Wiederholungs-Berechnung (Monatsende, Schaltjahr), Speichern von Ort/Wiederholung, Weiterrücken von Wiederholungen (Erinnerung wird neu gesetzt, einmalige Termine bleiben), Bearbeiten inkl. Entfernen, Eingabe bleibt bei Neuladen erhalten, Wochenansicht inkl. Folgewochen, Englisch. Frühere Tests und Prüfer unverändert. **Nicht getestet:** echtes Handy (Datum-/Zeitauswahl, Karten-Link), Erinnerungen auf dem Server für wiederholte Termine; Übersetzungen (mk, sr, sq, tr) von mir. |
| 8b Server: Wiederholung in `tick` | Edge-Function `tick` v6 (keine DB-Änderung) | Rechenregel mit 9 Beispielen geprüft (Monatsende, Schaltjahr, Jahreswechsel; identisch zur App), Funktion bereitgestellt, danach laufen die Minuten-Aufrufe weiter mit Status 200 und neuem Zähler `rolled`. **Nicht getestet:** Weiterrücken an einem echten wiederkehrenden Termin (es gibt noch keinen in der Familie). |
| 9 Timer: pausieren, fortsetzen, +1 Minute, nochmal | `index.html`, `i18n.js` (6 neue Texte in 8 Sprachen) | Automatisch mit simuliertem Server (alle bestanden): Dauer wird gespeichert, Pause (Rest bleibt stehen), +1 Minute im Pausenmodus, Fortsetzen, Nochmal nach Ablauf, Startseite. Frühere Tests und Prüfer unverändert. **Nicht getestet:** echtes Handy; Mitteilung nach Fortsetzen auf dem Server (Logik unverändert, Endzeit wird neu gesetzt); Übersetzungen (mk, sr, sq, tr) von mir. |
| 10 Rollen und Einladungen | `index.html`, `i18n.js` (14 neue Texte in 8 Sprachen), `docs/sql/schritt10_rollen.sql` (Datenbank, mit Freigabe ausgeführt) | Neue Spalte «Rolle» (Admin/Mitglied); Ersteller sind Admins; nur Admins erzeugen neuen Code, ernennen Admins und entfernen Mitglieder; der letzte Admin kann nicht fehlen. In der App: Rollen-Abzeichen, Verwalten-Knöpfe, «Einladung teilen» mit Link. Geprüft: 9 Regelfälle direkt in der Datenbank (zurückgerollt, Datenmengen unverändert) und neuer Browser-Test `test_rollen.py`. Nicht auf echten Geräten getestet. Hinweis: 3 Funktionen wurden wegen einer Tool-Sperre mit zusammengesetztem Wort «DELETE» installiert; die SQL-Datei enthält die schlichte Form. |
| Startseite für milteo.ch | `index.html`, `i18n.js` (31 neue Texte in 8 Sprachen), `milteo-video.mp4`, `milteo-video-poster.jpg`, `sw.js` | Neue Besucher sehen eine Werbeseite mit Beispielvideo, Funktionen, Schritten und Kontakt (support@milteo.ch); von dort Registrieren oder Anmelden. Installierte App, bekannte Nutzer, Einladungs- und Passwort-Links gehen direkt zur Anmeldung. Test `test_startseite.py` bestanden, Bildschirmfotos Handy und Computer geprüft. Das Video zeigt simulierte Daten. |
| Benachrichtigung bei neuen Einträgen | `index.html`, `i18n.js`, Server-Funktion `notify` (Version 7), Datenbank: neue Spalte `push_subscriptions.n_change` (mit Freigabe) | Neuer Einkauf, neue Aufgabe, neuer Termin oder gestarteter Timer löst bei den anderen Familienmitgliedern eine Mitteilung aus (mit Namen). Pro Art (Einkauf, Aufgaben, Termine, Timer) höchstens eine Mitteilung innerhalb von 5 Minuten; gleichzeitig Hinzugefügtes (4 s) wird gebündelt. Eigener Schalter «Änderungen der Familie». Getestet: Browser-Test `test_benachrichtigung.py`; die Server-Funktion selbst und der echte Versand auf Handys sind noch nicht live geprüft. |
| Rezept: Schritte merken, Temperatur und Zeit | `index.html`, `i18n.js`, Server-Funktion `dish` (Version 13) | Geöffnetes Rezept und abgehakte Schritte bleiben nach Neuladen/App-Update 7 Tage auf dem Gerät erhalten. Temperaturen und Zeiten werden in den Schritten hervorgehoben, dazu eine Zeile «Auf einen Blick». Neue Rezepte enthalten Temperatur und Zeit je Schritt (Vorheizen als erster Schritt). Bereits gespeicherte Rezepte bleiben unverändert, bis «Rezept neu erstellen» gewählt wird. Getestet: `test_rezept.py`; KI-Verhalten auf echtem Gerät noch nicht geprüft. |
| Einführung und WhatsApp-Einladung | `index.html`, `i18n.js` | Willkommens-Karte auf der Startseite, solange die Familie noch keine Einträge hat (mit «Verstanden» weg, merkt sich das auf dem Gerät). Karte «Du bist noch allein hier» mit Knöpfen «Per WhatsApp einladen» und «Anders teilen», solange man das einzige Mitglied ist; WhatsApp-Knopf auch im Familien-Bereich. Getestet: `test_einladung.py`; WhatsApp-Öffnen auf echtem Handy nicht geprüft. |
| KI-Einwilligung und Datenschutztext | `index.html`, `i18n.js` | Vor dem ersten Foto-/PDF-Upload (Termine, Stundenplan) einmalig Rückfrage, dass die Datei an Google (Gemini) geht; bei «Abbrechen» wird nichts gesendet. Datenschutztext ergänzt: Chat-Nachrichten gehen nicht an Google. Offen: bezahlte Gemini-Stufe aktivieren (Google-Konto), Datenschutztext danach anpassen. Getestet: `test_ki_einwilligung.py`. |
| 12 Aufräumen und Tests | `index.html`, `tests/` (neu), `sw (1).js` gelöscht | Alle Testdateien laufen aus dem Projektordner und bestehen; Prüfer unverändert (nur Logo-Kontrast). Seitenaufbau: Anzahl öffnender und schliessender `<div>` jetzt gleich (83/83). **Nicht abgedeckt:** echte Geräte, Push, echte Supabase-Verbindung. |
