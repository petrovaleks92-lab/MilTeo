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
| Einkauf | 🟡 | Hinzufügen, abhaken, löschen (mit Rückgängig), Gericht → Zutaten (eingebaute Rezepte + kostenlose KI), 8 Sprachen ✅; seit Schritt 4: Menge pro Artikel und Bearbeiten durch Antippen (auch Zutaten im Gericht und Aufgaben). Fehlen: Kategorien, Suche, «häufig gekauft», Notizen, Duplikat-Schutz, mehrere Listen. Wochenmenü ❌. |
| Aufgaben | 🟡 | Erstellen, abhaken, löschen, Ersteller anzeigen, Bearbeiten ✅; seit Schritt 6: Zuweisen an ein Familienmitglied, Fälligkeit, Wichtigkeit, Wiederholung (täglich/wöchentlich/monatlich: Abhaken setzt das nächste Datum), Filter (Alle/Meine/Überfällig/Erledigt), Sortierung nach Fälligkeit, Kennzeichen «Überfällig» auch auf der Startseite. Gespeichert im Datenfeld, keine DB-Änderung. Fehlen: Erinnerung/Benachrichtigung bei Fälligkeit und bei Zuweisung (bräuchte Änderung der Funktion `tick`), Belohnungssystem ❌. |
| Termine | 🟡 | Erstellen, löschen, Erinnerung (auch nachträglich), Import aus Datei, Stundenplan mit Gruppen, einklappbar ✅. Fehlen: Ort/Beschreibung, Personen-Zuordnung, wiederkehrend, Tages-/Wochenansicht, Titel/Datum nachträglich ändern, Kalenderexport. |

### Priorität 6–10
| Bereich | Status | Befund |
|---|---|---|
| Chat | ✅/🟡 | Echtzeit, Bilder, Sprachnachrichten, Zeitstempel, Leerhinweis ✅. Fehlgeschlagene Nachrichten werden nur per Hinweis gemeldet (Text bleibt im Feld ✅); keine Ungelesen-Zählung pro Nachricht (Punkt und Zähler auf der Startseite ✅). |
| Timer | 🟡 | Starten, Restzeit, Ende-Hinweis, Push bei geschlossener App ✅. Pausieren/Zurücksetzen ❌. |
| Benachrichtigungen | ✅ | Schalter für Chat/Timer/Termine, Berechtigung wird erklärt, Test-Taste, automatische Erneuerung, hohe Zustellpriorität. |
| Einstellungen | 🟡 | Name, Sprache, Mitglieder, Code ✅. Kontolöschung ✅ (Schritt 2, mit Passwortabfrage). Datenschutzinformation ✅ (Schritt 2); Kontaktadresse ❌ (noch keine hinterlegt). |
| Schweiz | ✅ | Datumsformat und 24-Stunden-Zeit über die Gerätesprache `de-CH`, Standardsprache Deutsch, keine kostenpflichtigen Dienste. Zeitzone: Termine ohne Zeitzone werden lokal verstanden, die Server-Erinnerungen rechnen in Europe/Zurich. |
| Technische Qualität | 🟡 | PWA installierbar ✅, Service Worker ✅. Kein automatisierter Testlauf im Repository, `index.html` ist gross. Altlasten: `sw (1).js`, überzählige `</div>` bei Zeile 269/270, Anzeige technischer Fehlertexte bei «Familie verlassen». |

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
11. **Belohnungssystem** (nach Rollen).
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
