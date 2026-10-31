# Assist AI Router — Deutsch

Version **1.0.3** · LiteLLM **1.106.4** · Home Assistant **2026.8+**

## In fünf Schritten zu Assist

1. App installieren, starten und **Weboberfläche öffnen** wählen. Es ist keine weitere LiteLLM-Installation nötig.
2. Unter **Anbieter** eine Vorlage auswählen. Schlüssel im Formular eintragen, Modell prüfen und speichern. Danach **Verbindung testen**. Der Test sendet eine kurze echte Anfrage.
3. Ein zweites unabhängiges Anbieterprofil hinzufügen. Die nummerierte Liste am Griff ⠿ per Drag-and-drop oder mit ↑/↓ sortieren. Im Preset **Feste Priorität** ist das oberste Profil zuerst an der Reihe.
4. **Assist verbinden → Verbindungsdaten anzeigen → LiteLLM in Home Assistant hinzufügen**. URL und Router-Schlüssel in das offizielle Formular übernehmen. Der Router-Schlüssel ist unabhängig von deinen Anbieter-Keys.
5. Im LiteLLM-Eintrag **Konversationsagent hinzufügen**, Modell **assist-auto** auswählen und bei Bedarf Assist-Werkzeuge aktivieren. Entitäten freigeben und den Agenten unter **Einstellungen → Sprachassistenten** zuweisen.

Home Assistant erreicht die API über den internen App-Hostnamen auf Port 8000. Der Assistent liest diesen Hostnamen vom Supervisor. `/v1/models` stellt `assist-auto`, eigene Regel-Aliase und `provider:<Profil-ID>` bereit. Profile mit `provider:` sind zum gezielten Testen gedacht und haben keinen Anbieter-Fallback. Für Assist normalerweise `assist-auto` wählen.

## Anbieter und Secrets

Auf den Anbieterkarten in **Übersicht** und **Anbieter** kannst du mit **Pausieren/Fortsetzen** ein Profil vorübergehend aus dem Routing nehmen. Die Pause bleibt bis zum manuellen Fortsetzen bestehen, auch nach Neustarts. Schlüssel, Reihenfolge, Regeln und Verbrauch bleiben erhalten. Neue Anfragen überspringen das Profil; laufende Anfragen können noch abschließen. Bestehende Limits und Abkühlzeiten gelten beim Fortsetzen weiterhin.

Die Ingress-Oberfläche ist der komfortable Editor. **Speichern** schreibt über `/addons/self/options` in dieselbe Konfiguration wie Home Assistants App-Konfigurationsseite. Erfolgreich gespeicherte Werte werden sofort übernommen. Änderungen über die HA-Konfigurationsseite werden beim Aktualisieren der Router-Oberfläche oder einem App-Neustart geladen. Gleichzeitige Änderungen lösen einen Konflikt aus, statt eine neuere Konfiguration still zu überschreiben; die Supervisor-API bietet allerdings keinen atomaren Compare-and-Swap zwischen verschiedenen Editoren.

### Modelle direkt beim Anbieter laden

Trage im Anbieterformular den API-Schlüssel und bei Bedarf die API-Basis-URL ein. Beim Öffnen mit gespeicherten Zugangsdaten wird die Modellliste automatisch geladen; neue Schlüssel-/URL-Eingaben aktualisieren sie beim Verlassen des Feldes. Die Vorschläge stehen direkt im Feld **LLM-Modell**, ohne separaten Ladebutton oder zweite Auswahl. Mit ▾ alle Modelle öffnen oder im Feld suchen. Der LiteLLM-Präfix wird automatisch ergänzt; du brauchst vorher noch keinen Modellnamen. Neue direkt eingegebene Schlüssel funktionieren bereits vor dem Speichern, ohne das Profil oder den Schlüssel dabei zu speichern. Bereits gespeicherte Schlüssel und `!secret`-Verweise werden serverseitig verwendet. Ein **neuer** `!secret`-Verweis muss zuerst im Profil gespeichert werden; dafür kannst du zunächst einen SDK-Vorschlag als Modell verwenden. Beim Wechsel des Anbieters oder API-Ziels muss ein gespeicherter Schlüssel neu eingegeben oder das geänderte Profil ausdrücklich gespeichert werden.

Direkte Adapter sind für Gemini, Groq, Cerebras, OpenRouter, Mistral, Hugging Face, SambaNova, Together AI, NVIDIA NIM, OpenAI, Anthropic, DeepSeek, xAI, Cohere, Ollama und eigene OpenAI-kompatible Modelllisten vorhanden. Ohne passenden Listen-Endpunkt, etwa für Azure-Deployments oder kontospezifische Cloudflare-Konfigurationen, bleiben **SDK-Modellvorschläge** und manuelle Eingabe verfügbar. Anbieterantworten werden als solche gekennzeichnet; eine Modellliste bestätigt weder kostenlose Nutzung noch individuelle Freigabe oder Tool-Unterstützung. Einige APIs liefern auch andere Modellarten als Chatmodelle. Gemini/Cohere werden auf bekannte Chat-Funktionen gefiltert. Größere paginierte Antworten werden begrenzt und gegebenenfalls als Teilliste markiert.

Die Abfrage startet beim Öffnen des Anbieterfensters oder nach abgeschlossener Änderung der Zugangsdaten. Sie lädt Metadaten, erzeugt keinen Prompt und verändert keine Token-Zähler; providerseitige Limits für Metadatenabfragen können trotzdem gelten. Zugangsdaten stehen ausschließlich in Request-Headern zum eingestellten Anbieter. Weiterleitungen werden nicht verfolgt; Anbieterfehler werden ohne Schlüssel oder Antworttext angezeigt.

Das Schlüsselfeld zeigt `!`, `!s`, `!se` bis `!secret name` unmaskiert, solange die Eingabe dem Secret-Präfix folgt; bei Abweichungen wird sofort wieder maskiert.

Du kannst einen Schlüssel direkt im Formular eingeben oder einen **bereits vorhandenen** Verweis wie `!secret groq_api_key` verwenden. Der Supervisor löst Secrets auf. Beim späteren Bearbeiten bleibt der Verweis erhalten; der aufgelöste Secret-Wert wird nicht an den Browser zurückgegeben. Beim Öffnen wird der Originaleintrag über einen eigenen Ingress-Endpunkt ins Feld geladen. Direkte Schlüssel lassen sich mit dem Augen-Symbol im Schlüsselfeld einsehen; Secret-Verweise sind empfohlen. Ein leeres Schlüsselfeld beim Bearbeiten behält den gespeicherten Wert bei. **Gespeicherten Schlüssel entfernen** löscht ihn ausdrücklich. Neue Einträge in Home Assistants `secrets.yaml` kann diese App nicht erstellen. Direkte Formulareingabe erfordert überhaupt keine Textdatei.

Vorlagen decken Google AI Studio, Groq, Cerebras, OpenRouter, Mistral, Hugging Face, GitHub Models, SambaNova, Together AI, Fireworks AI, Cohere, Cloudflare, NVIDIA NIM, OpenAI, Anthropic, DeepSeek, xAI, Perplexity, Azure, Ollama und eigene OpenAI-kompatible Endpunkte ab. Modellnamen sind bearbeitbare Beispiele. SDK-Vorschläge aus dem Katalog der gepinnten LiteLLM-Version ergänzen das Modellfeld, wenn die direkte Abfrage nicht verfügbar ist; dieser Katalog bestätigt keine Verfügbarkeit in deinem Konto. Nicht alle Vorlagen sind gratis. Bei einigen Anbietern sind Konto-ID, Deployment-URL oder API-Version zusätzlich nötig.

Markiere **kostenlose Nutzung bestätigt** nur für ein tatsächlich kostenloses Modell/Kontingent. Die App überprüft deinen Tarif nicht und kann Rechnungen eines Anbieters nicht unterbinden. Kostenpflichtig markierte Profile sind standardmäßig gesperrt. Lokale Modelle brauchen eine erreichbare URL und müssen für Gerätesteuerung Tool-Aufrufe unterstützen. Ein „Verbindungstest erfolgreich“ bestätigt die Textverbindung; die tatsächliche Werkzeugqualität hängt vom Modell ab.

## Routing

| Preset | Verhalten |
| --- | --- |
| Feste Priorität | Profile in deiner Reihenfolge ausprobieren |
| Kontingente schonen | Kleinster verbrauchter Anteil der bekannten Limits zuerst; unbekanntes Kontingent nachrangig |
| Gleichmäßig verteilen | Startpunkt pro Anfrage drehen; aktuelle Limits weiter beachten |
| Lokal zuerst | Lokale Profile zuerst, danach erlaubte Cloud-Profile |

Eigene Regeln treffen anhand des Modellalias und optional vorhandener Tools eine Anbieterauswahl. Die **erste passende Regel** gilt. Die Auswahl bildet eine Grenze: außerhalb dieser Profile findet kein Fallback statt. Das Preset sortiert innerhalb dieser Grenze. Ein eigener Alias, z. B. `assist-fast`, erscheint im Modellmenü der LiteLLM-Integration. `*` trifft alle Routing-Aliase. Die expliziten `provider:`-Aliase umgehen die Regel-Auswahl und verwenden genau ein Profil; Kostenfreigaben und Fähigkeiten gelten trotzdem.

Bei 429, Authentifizierungsfehlern, nicht verfügbaren Modellen, Netzwerkfehlern und 5xx versucht der Router das nächste geeignete Profil. Anbieter-Cooldowns und `Retry-After` verhindern sofortige Wiederholungen. Gemeinsame Kontingentgruppen teilen 429-Cooldowns. Andere fehlerhafte Anfragen werden nicht beliebig erneut gesendet. Kontextfehler können auf ein anderes Profil ausweichen; Nachrichten werden nicht gekürzt und Assist-Werkzeuge nicht entfernt. Zeitbudget und maximale Versuche begrenzen die Suche. Die HTTP-Timeouts werden an LiteLLM weitergereicht; Netzwerkphasen können die Gesamtdauer beeinflussen.

## Kontingente und Verbrauch

RPM, TPM, Tagesanfragen, Tages-/Monatstokens, Kontextfenster und ein Monatsbudget lassen sich pro Profil einstellen. **0 bedeutet keine lokale Begrenzung / unbekannt**, kein unbegrenztes Gratis-Kontingent. Eine Sicherheitsreserve bleibt frei. Vor dem Aufruf reserviert SQLite unter einer Sperre die voraussichtlichen Tokens, sodass parallele Anfragen sich nicht dasselbe lokale Kontingent zusagen.

Die Eingabeschätzung zählt konservativ UTF-8-Bytes einschließlich Werkzeugschemas plus Protokollreserve und maximaler Ausgabe. Sie ist bewusst keine exakte Tokenisierung und kann große Assist-Kontexte früh aus einer kleinen Quote ausschließen. Anbieterangaben ersetzen die Schätzung nach erfolgreicher Antwort. Ohne Verbrauchsangaben bleibt sie als **≈** markiert. Fehlgeschlagene und bei einem Neustart unterbrochene Versuche behalten die Reservierung vorsichtshalber. Der Request-Zähler enthält auch fehlgeschlagene Versuche.

Anbieter, Basis-URL und Schlüssel bilden automatisch eine gemeinsame Zählergruppe. Für gemeinsame Projekt-/Kontolimits über mehrere Schlüssel hinweg denselben Namen unter **Kontingentgruppe** vergeben und identische Limits eintragen. Zählergrenzen sind **UTC**; Minute = rollende 60 Sekunden, Tag/Monat = Kalendertag/-monat. Anders getaktete Anbieterquoten werden durch den jeweiligen 429-Cooldown ergänzt. Außerhalb dieser App verbrauchtes Kontingent ist unbekannt.

Das Dashboard zeigt lokal erfassten Verbrauch und verlinkt echte Anbieterportale. Es behauptet keinen verifizierten Restguthabenstand. In **Verbrauch** siehst du Eingabe-/Ausgabe-/Gesamttokens, Dauer, Anfrage-ID und alle Versuche eines Fallbacks. CSV enthält auch geschätzte USD-Kosten aus manuell angegebenen Preisen. Die Tabelle zeigt die letzten 100 Versuche, die Datenbank hält die eingestellte Historie; aktuelle Monatszähler bleiben mindestens bis Monatsende erhalten. Es werden keine Prompts, Antworten oder ausführbaren Tool-Argumente gespeichert.

## MCP und Integrationen

Für die HACS-Integration **MCP Assist von mike-nott** gibt es unter **Assist verbinden** einen eigenen auswählbaren Einrichtungsweg. Er öffnet das HACS-Repository und das richtige Integrationsformular und zeigt eine angepasste Router-URL **ohne `/v1`**, den Router-Schlüssel, `assist-auto` und einen Timeout-Vorschlag. In MCP Assist wählst du **OpenAI** als kompatiblen Servertyp und ersetzt die vorbelegte Cloud-Adresse durch die Router-Adresse. Siehe die [vollständige MCP-Assist-Anleitung](MCP_ASSIST.md) einschließlich Entitätsfreigaben, Gratis-Kontingent-Einstellungen und Fehlerbehebung. MCP Assist kann anstelle des nativen LiteLLM-Konversationsagenten verwendet werden.

Die **native LiteLLM-Integration** ist die Assist-Anbindung. MCP ist optional: der HA-MCP-Client bindet externe Werkzeuge ein, der HA-MCP-Server stellt Home Assistant externen Clients bereit. **Assist verbinden** öffnet dafür die offiziellen Formulare. Die App vergibt keine Entitätenrechte und verändert keine Dateien oder `.storage`-Einträge. OAuth und Werkzeugfreigaben erfolgen in Home Assistant.

## Betrieb und Updates

Die Verwaltung lauscht auf Ingress-Port 8099 und akzeptiert im Produktivbetrieb ausschließlich den Supervisor-Ingress-Peer `172.30.32.2`. Dieser Port wird nicht am Host veröffentlicht. Der KI-Endpunkt auf 8000 verlangt einen zufällig erzeugten Router-Schlüssel; er enthält keine Verwaltungsrouten. Ein Host-Port ist optional und standardmäßig deaktiviert. Direkter Zugriff über ein unverschlüsseltes fremdes Netzwerk sollte über einen eigenen HTTPS-Reverse-Proxy erfolgen. Die Ingress-Verwaltung ist für vertrauenswürdige HA-Benutzer gedacht.

SQLite, Konfiguration und Router-Schlüssel liegen in `/data` und gehören in dein App-Backup. Backups können Zugangsdaten enthalten. Das Image basiert auf dem exakten offiziellen LiteLLM-Release-Tag mit dessen eingefrorenen Abhängigkeiten; die App prüft die installierte SDK-Version beim Start. Das vollständige Upstream-Image ist entsprechend größer als eine reine SDK-Installation. Keine Telemetrie, keine automatischen kostenpflichtigen Healthchecks, kein Redis/Postgres erforderlich.

**Auf neue stabile Version prüfen** fragt GitHub erst nach Klick ab und cached das Ergebnis eine Stunde. Die App installiert dabei nichts. Upgrades erhalten eine neue getestete App-Version. Ab v1.0.0 gilt semantische Versionierung (`MAJOR.MINOR.PATCH`) statt der bisherigen Datums-Versionen.

Wenn alle erlaubten Anbieter erschöpft oder ausgefallen sind, antwortet der Router mit HTTP 503 und `no_provider_available`. Unbegrenzte Cloud-Antworten sind damit nicht garantiert. Für die höchste Verfügbarkeit ergänze ein lokal laufendes, Assist-taugliches Modell.

## Vor einem stabilen Release prüfen

Die Softwaretests ersetzen keinen Praxistest auf Home Assistant OS: amd64/aarch64 installieren; Ingress und Schutzmodus prüfen; Speichern mit echtem `!secret` inklusive Neustart prüfen; native LiteLLM-Einrichtung und Assist-Gerätesteuerung mit Tool-Aufrufen testen; echte 429/Retry-After-Szenarien mehrerer Anbieter und Backup-Wiederherstellung prüfen. Visuelle Browserprüfung und reale Anbieter-/HA-Tests sind gesondert zu protokollieren.

## Quellen

* [Home Assistant LiteLLM](https://www.home-assistant.io/integrations/litellm/)
* [App-Optionen und Secrets](https://contributors.home-assistant.io/apps/guides/options/)
* [Supervisor-App-API](https://contributors.home-assistant.io/apps/supervisor-api/apps/)
* [LiteLLM-Routing](https://docs.litellm.ai/docs/routing)
* [Gepinntes LiteLLM-Release](https://github.com/BerriAI/litellm/releases/tag/v1.106.4)

## API-Tarife und Regelbeispiele

Die [deutsche README](../README.md) enthält konkrete Alias-/Tool-/Auffangregeln sowie eine datierte Tabelle offizieller Tarif-/Limitquellen. Die Anbieteransicht unterscheidet dokumentierte Beispiele von OpenRouter-/DeepSeek-Kontodaten. Geldbeträge sind keine Tokenlimits; unbekannte Werte bleiben unbekannt. Beispiel-Limits werden nur per Klick ins Formular übernommen.
