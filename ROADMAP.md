# Weiterentwicklung / Roadmap

Die erste Version bleibt experimentell, bis die realen HA-Abnahmeschritte in CONTRIBUTING.md dokumentiert sind. Diese Liste beschreibt geplante Erweiterungen, keine bereits verfügbaren Funktionen.

| Priorität | Deutsch | English |
| --- | --- | --- |
| 1 | Echte HA-OS-Abnahme: native LiteLLM-Einrichtung, Secrets-Neustart, Assist-Tools und Mehranbieter-429 | Real HA OS acceptance: native LiteLLM setup, secret persistence, Assist tools and multi-provider 429s |
| 1 | Browserprüfung auf Mobilgerät/Desktop mit Tastatur und Screenreader | Mobile/desktop browser checks, keyboard navigation and screen-reader review |
| 1 | aarch64-Laufzeittest auf nativer Hardware oder mit geprüfter Emulation | aarch64 runtime checks on native hardware or verified emulation |
| 2 | Anbieteradapter für verifizierbare Kontingent-APIs und Reset-Zeitpunkte; lokale Schätzungen weiterhin getrennt kennzeichnen | Provider adapters for verifiable quota APIs/reset times, clearly distinguished from local estimates |
| 2 | Kontingent-Simulator: vorab prüfen, welche Route für einen Beispielkontext verfügbar wäre, ohne Provider-Anfrage | Quota simulator: preview routing for an example context without sending a provider request |
| 2 | Zeitabhängige Regeln, Latenz-Historie und ein kontrollierter Schalter zum Wiederprüfen nach Schlüsselwechsel | Time-based rules, latency history and controlled re-checks after credential changes |
| 2 | Optionale Home-Assistant-Sensoren für verfügbare Routen, Verbrauch und bevorstehende Erschöpfung | Optional HA sensors for available routes, usage and approaching exhaustion |
| 3 | Profile ohne Schlüssel exportieren/importieren; Migrationen und wiederherstellbare Konfigurationsrevisionen | Import/export profiles without keys, migrations and recoverable configuration revisions |
| 3 | Automatische Einrichtungsabläufe nur auf Basis offizieller Discovery-/Config-Flow-Unterstützung mit sichtbarer Rechtewahl | Automatic setup only through supported discovery/config flows with visible permission selection |

Für durchgängige Verfügbarkeit ist ein lokales Tool-fähiges Modell die wirksamste Ergänzung zu begrenzten Gratis-APIs. Zusätzliche Schlüssel desselben Kontos sind häufig kein unabhängiges Kontingent; gemeinsame Limits sollten als Kontingentgruppe modelliert werden.

A local tool-capable model is the strongest addition to limited free cloud quotas. Extra keys under the same account often do not provide independent allowance; represent shared limits with a quota group.
