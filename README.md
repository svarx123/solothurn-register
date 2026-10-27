# Registerblick · Solothurn

Alle SHAB-Handelsregistermeldungen mit Kantonsbezug SO im ausgewiesenen Zeitraum: Neueintragungen (HR01), Mutationen (HR02), Löschungen (HR03). Suche, Gemeinde- und Datumsfilter, Original-PDF, optionale persönliche Merkliste mit Supabase Auth.

## Lokal starten

Python 3.11 oder neuer, keine Python-Abhängigkeiten:

```sh
python scripts/import_shab.py --days 14
python -m http.server 8000 --directory dist
```

http://localhost:8000 öffnen. Die Meldungsübersicht ist öffentlich. Anmeldung schützt die persönlichen Favoriten, nicht die öffentlichen SHAB-Daten.

## GitHub Pages

Settings → Pages → Source: GitHub Actions. Der Workflow importiert vor jedem Deployment echte SHAB-Daten. Er läuft bei Push auf main, manuell und werktäglich um 07:23 UTC (08:23 im Winter, 09:23 im Sommer). GitHub-Zeitpläne können verzögert sein. Es werden keine E-Mail-Benachrichtigungen versendet.

Der Import lädt alle Seiten des Zeitraums, filtert den Kanton selbst anhand der XML-Metadaten, lädt SO-Details und gleicht annullierte Meldungen ab. Bei einem Fehler wird kein neuer Datenstand veröffentlicht. Angezeigt wird der tatsächlich importierte Zeitraum. Der tägliche Workflow umfasst die letzten 14 Tage; kein vollständiges historisches Archiv. Gelöschte Firmen werden durch ihre publizierten Löschungsmeldungen erfasst. Annullierte Publikationen werden entfernt.

## Anmeldung einrichten

1. Eigenes Projekt auf https://supabase.com/dashboard anlegen.
2. `supabase/schema.sql` einmal im SQL Editor ausführen. Die Merkliste ist durch Row Level Security auf den jeweiligen Nutzer begrenzt.
3. Unter Authentication → URL Configuration die Site URL und erlaubte Redirect URL auf die tatsächliche GitHub-Pages-Adresse (inklusive Unterverzeichnis und abschließendem Slash) setzen. Für lokale Tests http://localhost:8000/ ergänzen.
4. E-Mail/Passwort aktivieren, E-Mail-Bestätigung aktiv lassen, Mindestpasswortlänge mindestens 8. Für regulären Betrieb einen eigenen SMTP-Dienst konfigurieren; der Testversand ist eingeschränkt.
5. In `dist/config.js` die Projekt-URL und den **öffentlichen publishable key** einsetzen. Niemals `service_role`, Secret Key oder Datenbankpasswort in Browsercode/GitHub speichern.
6. Pushen und Registrierung, E-Mail-Bestätigung, An-/Abmeldung, Passwort-Reset und Merkliste mit zwei getrennten Konten testen.

Bis Supabase konfiguriert ist, ist die Anmeldung ausdrücklich als noch nicht eingerichtet gekennzeichnet. Es werden keine lokalen Schein-Konten angelegt.

## Datenquelle

Offizielles Amtsblattportal: https://amtsblattportal.ch/api/v1/publications/xml

Die Anwendung ist eine unabhängige Übersicht. Maßgeblich ist die offizielle Publikation im verlinkten SHAB-PDF. Der Datenstand und das Publikationsdatum sind sichtbar. Öffentliche Daten werden beim Deployment als JSON bereitgestellt; keine geheimen API-Zugangsdaten erforderlich.
