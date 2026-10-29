# MCP Assist aus HACS mit Assist AI Router verbinden

[English guide](MCP_ASSIST.en.md) · [MCP-Assist-Projekt](https://github.com/mike-nott/mcp-assist)

MCP Assist von **mike-nott** ist ein eigener Konversationsagent mit dynamischer Entitätssuche und MCP-Werkzeugen. Du kannst ihn anstelle des nativen LiteLLM-Konversationsagenten verwenden. Assist AI Router bleibt dabei der Zugang zu deinen Anbietern und übernimmt Prioritäten, Limits und Fallbacks.

## Vorbereitung

* Home Assistant ab 2026.8, HACS und die gestartete Assist-AI-Router-App.
* Mindestens ein aktives, freigegebenes und getestetes Anbieterprofil mit Tool-Unterstützung. Pausierte Profile werden übersprungen.
* In der Router-Weboberfläche **Assist verbinden → MCP Assist (HACS · mike-nott)** auswählen. Dort sind alle Links und die passenden Kopierfelder zusammengefasst.

## 1. Installation über HACS

Öffne [MCP Assist in HACS](https://my.home-assistant.io/redirect/hacs_repository/?owner=mike-nott&repository=mcp-assist&category=integration), lade die Integration herunter und starte Home Assistant neu. Alternativ füge in HACS unter **Benutzerdefinierte Repositorys** die Adresse `https://github.com/mike-nott/mcp-assist` mit Kategorie **Integration** hinzu.

HACS muss vorher installiert sein. Der Router installiert keine Custom-Komponenten im Hintergrund und benötigt keinen Schreibzugriff auf deine Home-Assistant-Dateien.

## 2. Verbindungsdaten übernehmen

Wähle im MCP-Assist-Einrichtungsweg des Routers **Verbindungsdaten anzeigen**. Öffne anschließend [MCP Assist hinzufügen](https://my.home-assistant.io/redirect/config_flow_start/?domain=mcp_assist).

| MCP-Assist-Feld | Wert |
| --- | --- |
| Profilname | Zum Beispiel `Assist AI Router` |
| Servertyp | **OpenAI** |
| Server-URL | Die im Router für MCP Assist angezeigte URL **ohne `/v1`** |
| API-Schlüssel | Dein **Router-Zugangsschlüssel**, kein Anbieter-Key |
| Modell | **assist-auto**, alternativ ein eigener Routing-Regel-Alias |
| Response Time Out | Mindestens das Router-Zeitbudget plus 5 Sekunden; die Oberfläche berechnet einen Vorschlag |

Beispiel: Die native LiteLLM-Integration verwendet `http://<interner-app-host>:8000/v1`; MCP Assist bekommt `http://<interner-app-host>:8000`. MCP Assist ergänzt `/v1/models` und `/v1/chat/completions` selbst. Verwende den vom Supervisor ermittelten Hostnamen aus der Weboberfläche; `localhost` wäre in Home Assistant ein anderer Dienst.

Der Servertyp **OpenAI** wählt hier das OpenAI-kompatible Protokoll und den konfigurierbaren Endpunkt. Er legt nicht fest, welcher Cloud-Anbieter antwortet. Das entscheidet weiterhin der Router. Die in MCP Assist vorbelegte Adresse `https://api.openai.com` muss durch die Router-Adresse ersetzt werden. Die lokalen Typen LM Studio/llama.cpp/vLLM senden im geprüften Quellstand keinen Bearer-Schlüssel und sind deshalb für diesen authentifizierten Router nicht der passende Einrichtungsweg.

Die Modellauswahl wird mit deinem Router-Schlüssel geladen. `assist-auto` behält automatische Fallbacks bei. Ein `provider:<ID>`-Modell legt sich dagegen auf genau ein Profil fest. Anbieter-Keys bleiben ausschließlich im Router beziehungsweise in dessen Supervisor-Secrets; der Router-Schlüssel wird nur in das HA-Formular kopiert und nie in HACS-/Einrichtungslinks eingebettet.

## 3. Werkzeuge und Sprachassistent

Aktiviere in MCP Assist nach Bedarf **Control Home Assistant**. Gib unter **Einstellungen → Sprachassistenten → Entitäten freigeben** die gewünschten Geräte/Entitäten frei. Wähle danach unter [Sprachassistenten](https://my.home-assistant.io/redirect/voice_assistants/) das neue MCP-Assist-Profil als Konversationsagenten deiner Pipeline.

Für MCP Assist als Konversationsagenten ist keine zusätzliche native `mcp`-/`mcp_server`-Integration erforderlich. Die native LiteLLM-Integration kann parallel installiert bleiben; für dieselbe Pipeline wählst du einen der beiden Konversationsagenten. Der MCP-Assist-Port, standardmäßig 8090, gehört zu dessen MCP-Dienst. Er ist nicht der LLM-Endpunkt des Routers auf Port 8000. Für die Verbindung zum Router ist keine zusätzliche öffentliche Portfreigabe nötig.

## 4. Sparsame Startwerte und Funktionstest

Für kleine Gratis-Kontingente eignen sich als Ausgangspunkt 256–512 Antwort-Tokens, eine kurze Historie und wenige Werkzeug-Iterationen, etwa 3–5. Behalte zunächst MCP Assists technische Werkzeuganweisungen bei. Dynamische Entitätssuche kann große vollständige Entitätslisten im Prompt vermeiden; jede weitere Werkzeugrunde erzeugt trotzdem weitere Modellanfragen. Beobachte den tatsächlichen Verbrauch im Router und erhöhe Grenzen bei Bedarf.

Teste zuerst eine reine Statusfrage. Teste anschließend bewusst eine einfache Geräteaktion und prüfe, ob sich das Gerät tatsächlich geändert hat. Der Router führt keine HA-Werkzeuge selbst aus; MCP Assist führt sie in Home Assistant aus und übergibt die Ergebnisse wieder an das Modell. Die Softwaretests decken den HTTP-/Streaming-Vertrag und diese Nachrichtenfolge ab, ersetzen aber keinen Test mit deinem Home Assistant und deinen Modellen.

## Anbieter zwischendurch pausieren

Klicke auf der Anbieterkarte **Pausieren** und später **Fortsetzen**. Das funktioniert in Übersicht und Anbieteransicht. Die Pause bleibt bis zum manuellen Fortsetzen bestehen, auch nach App-Neustarts. Schlüssel, Priorität, Regeln und bisheriger Verbrauch bleiben erhalten. Neue Anfragen, einschließlich MCP-Assist-Anfragen, überspringen das Profil; bereits laufende Anfragen können noch abschließen. Bestehende Abkühlzeiten und Kontingentgrenzen werden beim Fortsetzen nicht zurückgesetzt. Pausierte Profile müssen vor einem Verbindungstest fortgesetzt werden.

## Fehlerbehebung

| Symptom | Prüfen |
| --- | --- |
| HACS-Link funktioniert nicht | HACS installiert? Richtiges HA-Ziel im My-Home-Assistant-Dialog? Alternativ Repository manuell in HACS hinzufügen. |
| MCP Assist lässt sich nicht hinzufügen | Nach dem HACS-Download Home Assistant neu starten. |
| Servertyp OpenAI hat kein URL-Feld | MCP Assist aktualisieren; ältere Quellstände unterstützen den benötigten benutzerdefinierten Endpunkt möglicherweise nicht. |
| 404 oder leere Modellliste | Server-URL ohne `/v1`, ohne `/models` und ohne `/chat/completions` eingetragen? |
| 401 / ungültiger API-Schlüssel | Router-Schlüssel verwenden und interne Router-Adresse statt OpenAI-Cloud-Adresse prüfen. |
| Zeitüberschreitung beim Anbieterwechsel | MCP-Assist-Timeout über das Router-Zeitbudget setzen; Modellgeschwindigkeit und Anzahl der Werkzeugrunden prüfen. |
| Antworten ohne Gerätewirkung | Tool-fähiges Modell, MCP-Assist-Gerätesteuerung und Entitätsfreigaben prüfen; tatsächliche Werkzeugaufrufe kontrollieren. |
| Kein Anbieter verfügbar | Mindestens ein Profil aktiv, passende Tools unterstützt, Gratis-Freigabe gesetzt und Kontingent verfügbar? |

Geprüfter Upstream-Quellstand am **29.10.2026**: MCP Assist **0.17.2**, Commit [`feff8d3`](https://github.com/mike-nott/mcp-assist/tree/feff8d31761fe54a3a7ca2afd1949ad6e69dd019). Maßgeblich sind der [OpenAI-Konfigurationspfad](https://github.com/mike-nott/mcp-assist/blob/feff8d31761fe54a3a7ca2afd1949ad6e69dd019/custom_components/mcp_assist/config_flow.py) und der [OpenAI-kompatible Agent](https://github.com/mike-nott/mcp-assist/blob/feff8d31761fe54a3a7ca2afd1949ad6e69dd019/custom_components/mcp_assist/agent.py). Eine installierte HACS-Version kann davon abweichen.
