<!-- header:begin (generated from project metadata) -->
<h1 align="center">Assist AI Router</h1>

<p align="center">
  <img src="https://raw.githubusercontent.com/seb5594/Home-Assistant-Assist-AI-Router-App/dev/assist_ai_router/logo.png" alt="Assist AI Router" width="160" height="160">
</p>

---

<p align="center">
  <a href="https://paypal.me/seb5594"><img src="https://img.shields.io/static/v1?label=Support&amp;message=PayPal&amp;color=0070BA&amp;logo=paypal&amp;logoColor=white&amp;style=for-the-badge" alt="PayPal" height="40"></a>
  <a href="https://buymeacoffee.com/seb5594"><img src="https://img.shields.io/static/v1?label=Support&amp;message=Buy%20Me%20a%20Coffee&amp;color=FFDD00&amp;logo=buy-me-a-coffee&amp;logoColor=black&amp;style=for-the-badge" alt="Buy Me a Coffee" height="40"></a><br>
  <a href="https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fseb5594%2FHome-Assistant-Apps"><img src="https://img.shields.io/static/v1?label=Home%20Assistant&amp;message=Add%20app%20repository&amp;color=18BCF2&amp;logo=homeassistant&amp;logoColor=white&amp;style=for-the-badge" alt="Home Assistant" height="28"></a>
  <img src="https://img.shields.io/static/v1?label=home%20assistant&amp;message=%E2%89%A5%202026.8.0&amp;color=1877A5&amp;style=for-the-badge" alt="home assistant" height="28">
  <a href="https://github.com/seb5594/Home-Assistant-Assist-AI-Router-App/releases/tag/v1.0.2"><img src="https://img.shields.io/static/v1?label=version&amp;message=1.0.2&amp;color=1877A5&amp;style=for-the-badge" alt="version" height="28"></a>
  <img src="https://img.shields.io/static/v1?label=image%20pulls&amp;message=20&amp;color=1877A5&amp;style=for-the-badge" alt="image pulls" height="28"><br>
  <img src="https://img.shields.io/static/v1?label=arch%20%26%20size&amp;message=amd64%201235.7%20%C2%B7%20aarch64%201242.6%20MiB&amp;color=157F71&amp;style=flat" alt="arch &amp; size" height="20">
  <img src="https://img.shields.io/static/v1?label=stage&amp;message=stable&amp;color=2F855A&amp;style=flat" alt="stage" height="20">
  <img src="https://img.shields.io/static/v1?label=ingress&amp;message=enabled&amp;color=7C3AED&amp;style=flat" alt="ingress" height="20"><br>
  <a href="https://github.com/seb5594/Home-Assistant-Apps/issues"><img src="https://img.shields.io/github/issues/seb5594/Home-Assistant-Assist-AI-Router-App?label=issues&amp;style=flat" alt="issues" height="20"></a>
  <img src="https://img.shields.io/static/v1?label=runtime%20tests&amp;message=4%20passed&amp;color=2F855A&amp;style=flat" alt="runtime tests" height="20">
  <a href="https://github.com/seb5594/Home-Assistant-Assist-AI-Router-App/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/seb5594/Home-Assistant-Assist-AI-Router-App/ci.yml?branch=dev&amp;label=checks&amp;style=flat" alt="checks" height="20"></a>
  <a href="https://github.com/seb5594/Home-Assistant-Apps#license"><img src="https://img.shields.io/github/license/seb5594/Home-Assistant-Assist-AI-Router-App?label=license&amp;style=flat" alt="license" height="20"></a>
</p>
<!-- header:end -->

**Mehrere KI-Anbieter. Ein Zugang für Home Assistant Assist.**

[English](README.en.md) · [Konfiguration im Detail](assist_ai_router/DOCS.md) · [MCP Assist](assist_ai_router/MCP_ASSIST.md) · [Changelog](assist_ai_router/CHANGELOG.md)

Assist AI Router bündelt verschiedene KI-Anbieter und lokale Modelle hinter einem authentifizierten, OpenAI-kompatiblen Endpunkt für Home Assistant Assist. Die App nutzt das enthaltene **LiteLLM SDK** für Modellanfragen und ergänzt eine eigene Routinglogik, Verbrauchserfassung und Ingress-Oberfläche. Anbieter, Modelle, Schlüssel, Prioritäten und Limits verwaltest du im Browser. Speichern übernimmt Änderungen in die App-Konfiguration und wendet sie sofort an.

**App v1.0.2 · LiteLLM 1.106.4 · Home Assistant ab 2026.8 · amd64 / aarch64.** Ab dieser Ausgabe gilt das Versionsschema `MAJOR.MINOR.PATCH`. Frühere Datums-Releases bleiben im Changelog erhalten.

## Funktionen

- Bis zu **100 Anbieterprofile**, jeweils mit Modell, Schlüssel, Endpunkt und Limits; mehrere Profile desselben Anbieters sind möglich.
- **Nummerierte Liste untereinander** in Übersicht und Anbieteransicht, per Ziehgriff ⠿ oder ↑/↓ sortierbar. Änderungen werden sofort gespeichert.
- **Pausieren/Fortsetzen**, ohne Zugangsdaten, Position, Regeln oder Verbrauch zu verlieren.
- Automatische Modellvorschläge direkt im Feld **LLM-Modell**, ergänzt durch SDK-Vorschläge und manuelle Eingabe.
- Vier Routing-Presets, eigene Alias-/Tool-Regeln, Ausweichanbieter und persistente Abkühlzeiten.
- Lokale Kontingentkontrolle mit Reservierungen für parallele Anfragen, gemeinsamen Kontingentgruppen und Sicherheitsreserve.
- Eingabe-/Ausgabe-/Gesamttokens, Status, Dauer und Request-ID pro API-Versuch sowie CSV-Export.
- Geführte Einrichtung der nativen **LiteLLM-Integration** oder von **MCP Assist aus HACS**.
- Deutsche und englische Oberfläche sowie eine festgelegte LiteLLM-Version mit Image-Digest und optionalem Versionscheck.

Die App bildet die hier beschriebenen Funktionen ab. Sie ist keine Oberfläche für sämtliche Einstellungen des vollständigen LiteLLM-Proxys: Teams, virtuelle LiteLLM-Schlüssel, externe Abrechnung und alle SDK-/Proxyparameter sind nicht als App-Optionen verfügbar.

## Installation und Schnellstart

1. Öffne das [Home-Assistant-App-Repository](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fseb5594%2FHome-Assistant-Apps) oder füge `https://github.com/seb5594/Home-Assistant-Apps` im App-Store als Repository hinzu. Du benötigst eine HA-Installation mit Supervisor/App-Unterstützung.
2. Installiere und starte **Assist AI Router** und öffne die Weboberfläche. LiteLLM ist enthalten; kein separater Proxy muss installiert werden.
3. Wähle unter **Anbieter** eine Vorlage, vergib einen Profilnamen und trage Schlüssel oder vorhandenen `!secret`-Verweis ein. Für eigene/lokale Server ist eine erreichbare API-Basis-URL nötig.
4. Wähle ein **LLM-Modell** aus den Vorschlägen oder gib den vollständigen Modellnamen mit LiteLLM-Präfix ein. Speichere und teste.
5. Ergänze weitere unabhängige Anbieter, sortiere die Profile und wähle unter **Routing** ein Preset. Standard ist **Feste Priorität**.
6. Folge **Assist verbinden** und verwende für normale Assist-Nutzung **`assist-auto`**.

**Verbindung testen** sendet eine kurze echte Modellanfrage. Dabei können Tokens, Anfragenkontingent und gegebenenfalls Kosten anfallen. Eine erfolgreiche Textantwort beweist nicht die Qualität der Tool-Aufrufe oder Gerätesteuerung.

## Anbieter und Modelle

### 21 Vorlagen

| Vorlage | LiteLLM-Präfix | Direkte Modellabfrage |
| --- | --- | --- |
| Google AI Studio / Gemini | `gemini/` | Ja |
| Groq | `groq/` | Ja |
| Cerebras | `cerebras/` | Ja |
| OpenRouter | `openrouter/` | Ja |
| Mistral / La Plateforme | `mistral/` | Ja |
| Hugging Face Inference | `huggingface/` | Ja |
| GitHub Models | `github/` | SDK / manuell |
| SambaNova | `sambanova/` | Ja |
| Together AI | `together_ai/` | Ja |
| Fireworks AI | `fireworks_ai/` | SDK / manuell |
| Cohere | `cohere_chat/` | Ja |
| Cloudflare Workers AI | `cloudflare/` | SDK / manuell |
| NVIDIA NIM | `nvidia_nim/` | Ja |
| OpenAI | `openai/` | Ja |
| Anthropic | `anthropic/` | Ja |
| DeepSeek | `deepseek/` | Ja |
| xAI | `xai/` | Ja |
| Perplexity | `perplexity/` | SDK / manuell |
| Azure OpenAI | `azure/` | SDK / manuell; Deployment/API-Version beachten |
| Ollama | `ollama_chat/` | Ja, am lokalen Server |
| OpenAI-kompatibel / vLLM / llama.cpp | `openai/` | Wenn der Server einen Modellendpunkt anbietet |

Vorlagen garantieren keine Gratisnutzung. Konto, Modell, Endpunkt, API-Version und Tool-Fähigkeiten müssen passen. Manche Anbieter erfordern eigene Konto-/Deployment-URLs. Mehrere Modelle desselben Schlüssels werden als getrennte Profile eingerichtet.

### Automatische Modellliste im Eingabefeld

Beim Öffnen des Anbieterfensters lädt die App mit gespeicherten Zugangsdaten Modelle vom Anbieter. Nach einer neuen Schlüssel-/URL-Eingabe startet die Aktualisierung beim Verlassen des Feldes. Offene Modellendpunkte und lokale Server können ohne Schlüssel abgefragt werden. Es gibt keinen separaten Ladebutton und keine zweite Modellauswahl.

Die Ergebnisse stehen als Vorschläge **direkt im Feld LLM-Modell**. Mit ▾ direkt am Modellfeld öffnest du alle geladenen Modelle, auch wenn bereits ein anderer Modellname gespeichert ist. Tippen filtert die Liste; ↑/↓ und Enter wählen einen Eintrag. Escape schließt die Liste. LiteLLM-Präfixe werden ergänzt; die App ersetzt einen bestehenden Modellwert nicht ungefragt. Manuelle Eingaben bleiben möglich.

Modellabfragen lesen Metadaten, erzeugen keinen Prompt und ändern die Tokenzähler nicht. Anbieter können solche Abfragen begrenzen. Antwortgröße, Laufzeit und Pagination sind begrenzt; Teillisten werden markiert. Scheitert die Abfrage, bleiben verfügbare SDK-Vorschläge und manuelle Eingabe. Ein gelistetes Modell garantiert weder Gratiszugang noch Kontoberechtigung noch Chat-/Tool-Unterstützung.

Neue wörtliche Schlüssel funktionieren vor dem Speichern. Neue `!secret`-Verweise müssen zuerst zusammen mit einem Modellnamen gespeichert werden, damit Supervisor sie auflösen kann. Gespeicherte Schlüssel werden bei einer Änderung des Zielendpunkts erst nach erneuter Schlüsseleingabe oder ausdrücklichem Speichern der geänderten Konfiguration genutzt.

### API-Tarife, Kontodaten und belegbare Limitbeispiele

Im Anbieterfenster zeigt **API-Tarif und Kontingente** dokumentierte Tarifoptionen und bei unterstützten offiziellen Endpunkten Live-Kontodaten. Stand: **30.10.2026**. Die Tarifoptionen sind keine Erkennung deines Kontos. Ein Chat-Webseiten-Abo enthält nicht automatisch API-Nutzung.

| Anbieter | Dokumentierte Information | Quelle |
| --- | --- | --- |
| Google AI Studio | Free-/Paid-Tarife: RPM, TPM und RPD hängen von Projekt und Modell ab; aktuelle Werte in AI Studio prüfen. | [Docs](https://ai.google.dev/gemini-api/docs/rate-limits) |
| Groq | Free-Beispiele für gpt-oss-20b/120b: 30 RPM, 1.000 RPD, 8.000 TPM, 200.000 Tokens/Tag. Organisationslimits können abweichen. | [Docs](https://console.groq.com/docs/rate-limits) |
| Cerebras | Trial-Beispiele für gpt-oss-120b/qwen-3.8-27b: 5 RPM, 30.000 ungecachte TPM, 1.000.000 Tokens/Tag. Zusätzlich gelten Stunden-/Gesamttokenlimits. Trial-Credits verfallen; kein dauerhaft kostenloser Tarif. | [Docs](https://inference-docs.cerebras.ai/support/rate-limits) |
| OpenRouter | Die Schlüssel-API kann Free-Tier-Status, Credit-Limit und tägliche Gratis-Modellanfragen liefern. Kein universelles Tokenlimit. | [Docs](https://openrouter.ai/docs/api_reference/limits) |
| Mistral / La Plateforme | Limits hängen von Organisation, Modell und Tarif ab. Limits-Seite prüfen; ein Endkunden-Abo legt kein API-Kontingent fest. | [Docs](https://docs.mistral.ai/admin/billing-usage/usage-limits) |
| Hugging Face Inference | Dokumentierte Monatscredits: Free 0,10 USD (Änderungen möglich), PRO 2 USD, Organisationen 2 USD je Sitz. Geldbeträge sind keine festen Tokenmengen und kein geprüfter Reststand. | [Docs](https://huggingface.co/docs/inference-providers/pricing) |
| SambaNova | Credits und aktuellen Tarif im Konto prüfen. Die Free-Tarifseite verlangt gekaufte Credits vor API-Nutzung; kein Gratis-Tokenbudget angenommen. | [Docs](https://cloud.sambanova.ai/plans) |
| Cohere | Trial: 1.000 API-Aufrufe/Monat; bestimmte Chatmodelle 20 RPM. Monatsanfragen sind weder Tokens noch Tageskontingente. | [Docs](https://docs.cohere.com/docs/rate-limits) |
| Cloudflare Workers AI | 10.000 Neurons/Tag als freie Zuteilung; keine universelle Umrechnung in Tokens. Einige Modelle benötigen bezahlten Zugang. | [Docs](https://developers.cloudflare.com/workers-ai/platform/pricing/) |
| NVIDIA NIM | Developer-Zugang dient dem Prototyping. Kein zuverlässig dokumentiertes universelles Tokenkontingent wird voreingetragen. | [Docs](https://docs.api.nvidia.com/nim/docs/product) |
| DeepSeek | Der Guthabenendpunkt zeigt verfügbare, gewährte und gekaufte Geldbeträge, keinen Abotarif oder festen Tokenbestand. | [Docs](https://api-docs.deepseek.com/api/get-user-balance/) |

Für weitere Vorlagen bleibt der Tarif unbekannt, wenn der normale API-Schlüssel keinen unterstützten Kontoendpunkt bietet. Eigene Proxy-URLs werden nicht zur Kontoabfrage an einen anderen Host umgeleitet. Keine Login-Seiten werden gescrapt und keine Probe-Prompts zur Tariferkennung erzeugt.

OpenRouter kann den Free-Tier-Status, das verbleibende Schlüssel-Ausgabelimit und gegebenenfalls tägliche Gratis-Modellanfragen liefern. DeepSeek liefert verfügbare, gewährte und gekaufte Geldbeträge. Diese Kontodaten sind bis zu fünf Minuten zwischengespeichert und von den lokalen Router-Zählern getrennt. Geld wird nicht in Tokens umgerechnet. Lokale Limits und Kostenfreigaben ändern sich nicht automatisch. Bei passenden Groq-/Cerebras-Modellen kannst du ein **dokumentiertes Limitbeispiel** ins Formular übernehmen, mit deinem Konto abgleichen und speichern. Zusätzliche Stunden- und andere nicht abgebildete Limits werden weiterhin vom Anbieter durchgesetzt.

## Reihenfolge, Pausen und Schlüssel

Positionsnummern zeigen die **gespeicherte Profilreihenfolge**, einschließlich pausierter Profile. Am Griff ⠿ vor/hinter ein Profil ziehen oder die Pfeil-Buttons verwenden. Die Reihenfolge bestimmt das Preset **Feste Priorität**; andere Presets können sie umsortieren. Auch in der Übersicht sind die Profile untereinander angeordnet.

**Pausieren** schließt ein Profil für neue Modellanfragen aus. Bereits laufende Aufrufe können abschließen. Pausen bleiben über Neustarts bestehen und enden nur durch **Fortsetzen**. Schlüssel, Regeln, Position und Verbrauch bleiben erhalten; Fortsetzen setzt keine Kontingente oder Abkühlzeiten zurück. Modell-Metadaten können beim Bearbeiten eines pausierten Profils weiterhin geladen werden.

Wörtliche API-Schlüssel sind zunächst maskiert und lassen sich über Anzeigen/Verbergen einsehen. Beginnt die Eingabe mit `!`, bleibt sie sichtbar, solange sie zu `!secret` passt: `!`, `!s`, `!se`, `!sec`, `!secr`, `!secre`, `!secret` und anschließend `!secret name`. Bei einer Abweichung wie `!sx` oder `!secretX` wird sofort wieder maskiert.

`!secret name` verweist auf ein **vorhandenes** HA-Secret. Die App kann keine neuen Einträge in der Secrets-Datei anlegen. Direkte Schlüsseleingabe benötigt keine Textdatei. Beim Öffnen eines Profils wird der ursprünglich gespeicherte Eintrag über einen eigenen Ingress-Endpunkt geladen. Bei `!secret` bleibt ausschließlich der Verweis sichtbar; aufgelöste Secret-Werte werden nicht an den Browser zurückgegeben. Direkte Schlüssel sind zunächst maskiert und lassen sich mit Anzeigen/Verbergen einsehen. Secrets sind empfohlen. Beim Bearbeiten das Feld leer lassen, um den bisherigen Schlüssel zu behalten; **Gespeicherten Schlüssel entfernen** löscht ihn ausdrücklich.

Webänderungen werden über Supervisor in den App-Optionen gespeichert, einschließlich der rohen Secret-Verweise. Änderungen im HA-Reiter **Konfiguration** werden beim Aktualisieren der Einstellungen oder Neustart eingelesen. Eine Revisionsprüfung verhindert, dass eine veraltete Webansicht neuere Änderungen unbemerkt ersetzt. Bei Konflikten aktualisieren und erneut bearbeiten; parallele Änderungen in mehreren Oberflächen vermeiden.

## Routing und Fallbacks

| Preset | Auswahl |
| --- | --- |
| Feste Priorität | Geeignete Profile in gespeicherter Reihenfolge |
| Kontingente schonen | Nach dem höchsten verbrauchten Anteil bekannter Limits; ohne bekannte Limits wird 1,0 angesetzt |
| Anfragen verteilen | Dreht den Startpunkt pro Anfrage weiter |
| Lokal zuerst | Lokale Profile vor erlaubten Cloud-Profilen; Reihenfolge innerhalb der Gruppen bleibt bestehen |

Vor einem Versuch prüft der Router Aktivierung, Kostenfreigabe, Tool-/Bildfähigkeiten, Kontextfenster, lokale Limits und Abkühlzeiten. Ohne globale Freigabe kostenpflichtiger Profile kommen nur als kostenlos bestätigt oder lokal markierte Profile infrage. Diese Angaben sind manuelle Freigaben, keine Tarifprüfung oder Garantie gegen Anbieterabrechnungen.

**Eigene Regeln** wählen per Modellalias und optionaler Tool-Bedingung eine erlaubte Profilmenge. Die erste passende Regel gewinnt. Das Routing-Preset sortiert innerhalb dieser Menge; Fallbacks verlassen sie nicht. `*` ist eine Auffangregel für Routing-Aliase. Die Reihenfolge der IDs in einer Regel definiert keine eigene Priorität.

**`assist-auto`** ist der Standardzugang. Eigene Regelaliase erscheinen ebenfalls in `/v1/models`. **`provider:<profil-id>`** verwendet genau ein aktives Profil ohne Ausweichanbieter, aber weiterhin mit Kosten-/Fähigkeits-/Limitprüfung. Für Ausfallsicherheit einen Routingalias verwenden.

429, Authentifizierungsfehler, fehlende Modelle, Netzwerk-/Timeout- und Serverfehler können einen Fallback auslösen. `Retry-After` verlängert Abkühlzeiten; gemeinsame Kontingentgruppen teilen 429-Sperren. Allgemein abgelehnte Anfragen werden nicht beliebig wiederholt. Kontextfehler können zum nächsten geeigneten Modell führen. Nachrichten und Werkzeuge werden nicht abgeschnitten.

**Beispiele:** Für „Gratis zuerst“ unabhängige Konten als überprüft kostenlos bestätigen, Limits eintragen und Feste Priorität wählen. Für „Lokal bevorzugen“ einen Tool-fähigen lokalen Server ergänzen und Lokal zuerst wählen. Für getrennte Assist-Anforderungen einen Alias wie `assist-home` mit Tool-Bedingung und passenden Profilen anlegen.

Versuche und Zeitbudgets sind begrenzt. Sind alle erlaubten Anbieter erschöpft oder nicht erreichbar, liefert die API **HTTP 503 / `no_provider_available`**. Ein lokales Modell kann die Verfügbarkeit verbessern; unbegrenzte Antworten sind nicht garantiert.

### Konkrete Regeln zum Nachbauen in der Weboberfläche

Angenommene globale Profilreihenfolge: **1. Lokal**, **2. Groq**, **3. Gemini**. Wähle zunächst **Feste Priorität**. Trage Regeln über **Routing → Eigene Regeln** ein; Profilnamen stehen hier für deine tatsächlich eingerichteten Profile.

| Reihenfolge | Regelname | Alias | Werkzeuge erforderlich | Erlaubte Profile | Ergebnis |
| --- | --- | --- | --- | --- | --- |
| 1 | Assist mit Geräten | `assist-auto` | Ja | Lokal, Groq | Tool-Anfragen versuchen Lokal, danach Groq. |
| 2 | Assist Text | `assist-auto` | Nein | Groq, Gemini | Anfragen ohne Tools versuchen Groq, danach Gemini. |
| 3 | Privat lokal | `assist-private` | Nein | Lokal | Nur der lokale Server; kein Cloud-Fallback bei Ausfall. |
| 4 | Cloud Text | `assist-cloud` | Nein | Groq, Gemini | Eigenes auswählbares Modell für Cloud-Anfragen mit Fallback. |

„Werkzeuge erforderlich: Nein“ bedeutet **keine Bedingung**, nicht „Werkzeuge verboten“. Deshalb steht die Tool-Regel vor der allgemeinen `assist-auto`-Regel. Die private Profilmenge verhindert Cloud-Fallbacks. Kostenfreigaben gelten zusätzlich zu diesen Regeln.

Eine optionale **Auffangregel** mit Alias `*`, ohne Tool-Bedingung und erlaubten Profilen Groq/Gemini gehört ganz ans Ende. Sie wirkt nur auf bereits bekannte Routing-Aliase und legt keine beliebigen neuen Modellnamen an. Eine davor passende Regel wird durch sie nicht erweitert. Direkte `provider:`-Modelle umgehen die Regelauswahl.

Die Auswahlreihenfolge der Checkboxen erzeugt keine zusätzliche Priorität. Im Beispiel geht Groq vor Gemini, weil die globale Liste so sortiert ist. Andere Routing-Presets können die Startposition ändern. Regeln prüfen keine Prompttexte, Uhrzeiten oder Wörter; unterstützt sind Alias, Tool-Bedingung und Profilmenge.

## Verbrauch und Kontingente

Die Anzeige erfasst **lokal beobachteten Verbrauch dieses Routers**, keine universell verifizierten Anbieter-Guthaben. Nutzung durch andere Apps ist unbekannt. Die Anbieterportale sind verlinkt.

| Profiloption | Bedeutung |
| --- | --- |
| RPM / TPM | Anfragen/Tokens im rollierenden 60-Sekunden-Fenster |
| Anfragen/Tag, Tokens/Tag, Tokens/Monat | Lokale Limits; Tages-/Monatswechsel um 00:00 UTC |
| Kontextfenster | Konservative Eingabeschätzung plus maximales Ausgabebudget |
| Eingabe-/Ausgabepreise | Manuelle USD je eine Million Tokens |
| Monatliches Budget | Lokale Kostengrenze auf Basis der eingetragenen Preise |
| Kontingentgruppe | Gemeinsamer Zähler mehrerer Profile desselben Kontos/Projekts |

**0 bedeutet unbekannt bzw. keine lokale Begrenzung.** Budgets benötigen passende Preise. Anbieterpräfix, Basis-URL und Schlüssel bilden standardmäßig die gemeinsame Zählergruppe. Für verschiedene Schlüssel desselben Kontolimits dieselbe ausdrückliche Kontingentgruppe und identische Limits verwenden.

SQLite reserviert vor jedem API-Versuch geschätzte Eingabe plus maximale Ausgabe unter einer Sperre. So können parallele Anfragen dieselbe lokale Restmenge nicht mehrfach verplanen. Die Schätzung nutzt UTF-8-Bytes inklusive Werkzeuge plus Protokollreserve und ist keine exakte Tokenisierung. Anbieterwerte ersetzen die Reservierung nach erfolgreichen Antworten, sofern vorhanden. Fehlende Werte bleiben mit **≈** als geschätzt markiert. Fehlgeschlagene/unterbrochene Versuche behalten konservative Reservierungen; Anfragenzähler enthalten auch Fehler.

**Verbrauch** zeigt die letzten 100 tatsächlichen API-Versuche mit Profil, Request-ID, Zeit, Tokens, Dauer und Ergebnis. Fallbacks derselben Routeranfrage teilen die Request-ID. Ein Dialog mit mehreren Tool-Schritten kann mehrere Routeranfragen und IDs erzeugen. CSV enthält zusätzlich geschätzte Kosten. Prompts, Antworten und ausführbare Tool-Argumente werden nicht in der Verbrauchsdatenbank gespeichert.

## Home Assistant Assist verbinden

### Native LiteLLM-Integration

1. Öffne **Assist verbinden → LiteLLM → Verbindungsdaten anzeigen**.
2. Kopiere Basis-URL und **Router-Schlüssel** in das verlinkte HA-Integrationsformular. Der Router-Schlüssel ist unabhängig von den Anbieterschlüsseln.
3. Öffne den LiteLLM-Eintrag und füge einen Konversationsagenten für **`assist-auto`** oder deinen Regelalias hinzu.
4. Aktiviere bei Bedarf **Home Assistant steuern**, gib die benötigten Entitäten frei und wähle den Agenten im Sprachassistenten.

Die App liefert die interne Adresse aus Supervisor auf Port 8000. Die native [LiteLLM-Integration](https://www.home-assistant.io/integrations/litellm/) verbindet Assist mit diesem Endpunkt. Geräteaktionen führt der Konversationsagent über die freigegebenen HA-Werkzeuge aus.

### MCP Assist aus HACS

Wähle unter **Assist verbinden** alternativ **MCP Assist**. Die UI öffnet das HACS-Projekt und Integrationsformular und zeigt Kopierdaten. Download und HA-Neustart erfolgen durch dich.

Wähle den Servertyp **OpenAI**, die Router-URL **ohne abschließendes `/v1`**, den Router-Schlüssel und `assist-auto`. MCP Assist ergänzt die API-Pfade. Sein Timeout sollte über dem Router-Gesamtbudget liegen; die UI schlägt fünf zusätzliche Sekunden vor. MCP-Port 8090 ist nicht Router-Port 8000.

Die [MCP-Assist-Anleitung](assist_ai_router/MCP_ASSIST.md) beschreibt Freigaben, Einrichtung und Fehlerbehebung für die geprüfte 0.17.2-Anbindung. [MCP Assist](https://github.com/mike-nott/mcp-assist) ist ein alternativer Konversationsagent. Die separat verlinkten nativen HA-MCP-Client/-Server-Integrationen sind dafür nicht pauschal nötig. Die App installiert nichts im Hintergrund und verändert keine HA-`.storage`-Dateien.

## Allgemeine Einstellungen und Betrieb

| Einstellung | Standard | Wirkung |
| --- | --- | --- |
| Ausgabetokens | 512 | Obergrenze pro Modellaufruf, auch bei größeren Clientwerten |
| Gesamtbudget | 45 s | Zeitbudget einer Routeranfrage |
| Budget je Versuch | 12 s | An LiteLLM weitergereichter Timeout pro Anbieter |
| Max. Versuche | 4 | Höchstzahl tatsächlicher Anbieteraufrufe je Anfrage |
| Abkühlzeit | 60 s | Basis für passende Fehler; `Retry-After` kann verlängern |
| Reserve | 5 % | Nicht verplanter Anteil eingetragener lokaler Limits |
| Historie | 30 Tage | Aufbewahrung; der laufende Monat bleibt für Monatszähler erhalten |
| Kostenpflichtige Profile | Aus | Freigabe zusätzlich zu kostenlos/lokal markierten Profilen |
| Eigene Gateway-URL | Leer | Überschreibt die angezeigte Adresse, richtet keinen Netzwerkzugang ein |

Es gibt keine regelmäßigen kostenpflichtigen Modelltests. Statusanzeigen stammen aus früheren Tests/Anfragen und lokalen Sperren; „Verbunden“ ist kein kontinuierlicher Live-Gesundheitscheck. Sichtbare Statusdaten aktualisieren sich alle 15 Sekunden, außer bei geöffnetem Dialog, Speichern und Ziehen.

- **Ingress 8099:** Verwaltung über Supervisor-Ingress, ohne veröffentlichte Host-Port-Zuordnung.
- **API 8000:** `/v1/models` und `/v1/chat/completions` mit Bearer-Router-Schlüssel; `/health` als einfacher Erreichbarkeitstest. Keine Verwaltungsrouten auf diesem Port. Hostfreigabe ist optional und standardmäßig aus.
- **Streaming:** Anbieterantworten werden vollständig gepuffert und anschließend als SSE ausgegeben. Es gibt keine tokenweise Live-Ausgabe; ein Fallback erfolgt nicht mitten in einem bereits übertragenen Tool-Aufruf.
- **Backups:** Optionen, Router-Schlüssel und SQLite liegen unter `/data`. App-Daten sichern; Backups können Zugangsdaten enthalten.
- **Netzwerk:** Cloudanfragen übertragen Prompt/Kontext an den gewählten Anbieter. Lokale Server müssen aus der App erreichbar sein. Für Zugriffe über nicht vertrauenswürdige Netze einen passenden HTTPS-Zugang einrichten.
- **Schlüssel:** Die normale Einstellungsantwort enthält keine Schlüssel. Nur das geöffnete Profil lädt den ursprünglichen Eintrag; aufgelöste Secrets werden niemals ausgeliefert. Modellabfragen senden Zugangsdaten in Headern an das konfigurierte Ziel; Weiterleitungen sind gesperrt und fremde Fehlertexte werden nicht ausgegeben. LiteLLM-Telemetrie ist deaktiviert.

LiteLLM bleibt auf **1.106.4** mit Image-Digest festgelegt; beim Start wird die SDK-Version geprüft. **Versionsprüfung** fragt GitHub erst nach Klick ab, cached eine Stunde und installiert nichts. Eine neue Upstream-Version ersetzt die geprüfte Abhängigkeit nicht automatisch.

## Fehlerbehebung

| Beobachtung | Vorgehen |
| --- | --- |
| Keine Modellvorschläge | Schlüssel/URL vervollständigen, Feld verlassen, Modellfeld leeren oder tippen, Statushinweis prüfen; manuelle Eingabe nutzen. |
| Neuer Secret-Verweis kann nicht aufgelöst werden | Profil mit `!secret name` und manuellem/SDK-Modell speichern, dann erneut öffnen. |
| Kostenpflichtig gesperrt | Überprüfte Gratisnutzung bestätigen, lokales Profil markieren oder kostenpflichtige Profile ausdrücklich erlauben. |
| Limit früher als erwartet | Reserve, konservative Schätzung, fehlgeschlagene Versuche und geteilte Kontingente berücksichtigen. |
| Abkühlzeit nach Fortsetzen | Pause löscht keine Rate-Limit-Sperren; angezeigten Zeitpunkt abwarten. |
| Abweichende Reihenfolge | Routing-Preset, Regeln, Fähigkeiten, lokale Sperren und direkte `provider:`-Aliase prüfen. |
| HA erreicht Router nicht | Interne Adresse aus der Einrichtung verwenden; Ingress ist nicht die Modell-API. |
| MCP Assist 404/401 | Servertyp OpenAI, URL ohne `/v1`, Router-Schlüssel statt Anbieterschlüssel prüfen. |
| Alle Anbieter scheitern | Kontolimits, Netzwerk und Freigaben prüfen; unabhängige Anbieter/lokalen Fallback ergänzen. |

## Entwicklung und weitere Informationen

[Konfiguration im Detail](assist_ai_router/DOCS.md) · [MCP Assist](assist_ai_router/MCP_ASSIST.md) · [Entwicklung und Abnahme](CONTRIBUTING.md) · [Changelog](assist_ai_router/CHANGELOG.md) · [Weitere Home Assistant Apps](https://github.com/seb5594/Home-Assistant-Apps)

Automatisierte Tests prüfen Routing, Secrets, HTTP-Zugänge, Metadatenabfragen und die SDK-Anbindung. Die Abnahme mit echtem Home Assistant, Anbieter-Konten, Geräteaktionen, Browsern und Backup-Wiederherstellung ist zusätzlich nötig.

Der UI-Footer verlinkt das Projekt und weitere Apps und enthält **Support my work ☕** sowie „Application developed by seb5594 (Sebastian Schmidt) - Made with ♥ in Germany“ mit rotem Herz.

Die MIT-Lizenz gilt für diesen Projektcode. LiteLLM und andere Drittkomponenten behalten ihre jeweiligen Lizenzen. Autor: **seb5594 (Sebastian Schmidt)**.

<!-- support:begin (generated, shared text) -->
## Say thanks

All my projects are built in my spare time, just for the fun of it. Still, they take a lot of time and care, and many of the smart home gadgets I buy end up here because I want to make them cloud-free and smart-home ready. Every bit of support means a lot to me.

If my work helped you or turned out to be useful, show your appreciation with a hot drink for my next sleepless night.

[![PayPal](https://img.shields.io/static/v1?label=Support&message=PayPal&color=0070BA&logo=paypal&logoColor=white&style=for-the-badge)](https://paypal.me/seb5594) [![Buy Me a Coffee](https://img.shields.io/static/v1?label=Support&message=Buy%20Me%20a%20Coffee&color=FFDD00&logo=buy-me-a-coffee&logoColor=black&style=for-the-badge)](https://buymeacoffee.com/seb5594)
<!-- support:end -->

<!-- license:begin (generated from the license file) -->
## License

[![license](https://img.shields.io/static/v1?label=license&message=MIT&color=5B6770&style=flat)](LICENSE)

Published under the [MIT License](LICENSE).
<!-- license:end -->
