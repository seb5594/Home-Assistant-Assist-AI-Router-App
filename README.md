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
  <a href="https://github.com/seb5594/Home-Assistant-Assist-AI-Router-App/releases/tag/v2026-10-27"><img src="https://img.shields.io/static/v1?label=version&amp;message=2026-10-27&amp;color=1877A5&amp;style=for-the-badge" alt="version" height="28"></a>
  <img src="https://img.shields.io/static/v1?label=image%20pulls&amp;message=4&amp;color=1877A5&amp;style=for-the-badge" alt="image pulls" height="28"><br>
  <img src="https://img.shields.io/static/v1?label=arch%20%26%20size&amp;message=amd64%201235.6%20%C2%B7%20aarch64%201242.6%20MiB&amp;color=157F71&amp;style=flat" alt="arch &amp; size" height="20">
  <img src="https://img.shields.io/static/v1?label=stage&amp;message=experimental&amp;color=2F855A&amp;style=flat" alt="stage" height="20">
  <img src="https://img.shields.io/static/v1?label=ingress&amp;message=enabled&amp;color=7C3AED&amp;style=flat" alt="ingress" height="20"><br>
  <a href="https://github.com/seb5594/Home-Assistant-Apps/issues"><img src="https://img.shields.io/github/issues/seb5594/Home-Assistant-Assist-AI-Router-App?label=issues&amp;style=flat" alt="issues" height="20"></a>
  <img src="https://img.shields.io/static/v1?label=runtime%20tests&amp;message=3%20passed&amp;color=2F855A&amp;style=flat" alt="runtime tests" height="20">
  <a href="https://github.com/seb5594/Home-Assistant-Assist-AI-Router-App/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/seb5594/Home-Assistant-Assist-AI-Router-App/ci.yml?branch=dev&amp;label=checks&amp;style=flat" alt="checks" height="20"></a>
  <a href="https://github.com/seb5594/Home-Assistant-Apps#license"><img src="https://img.shields.io/github/license/seb5594/Home-Assistant-Assist-AI-Router-App?label=license&amp;style=flat" alt="license" height="20"></a>
</p>
<!-- header:end -->

**Mehrere KI-Anbieter. Ein Zugang für Home Assistant Assist.**

Die experimentelle Home-Assistant-App bündelt LiteLLM-kompatible Anbieter hinter einem lokalen Endpunkt. Profile, Schlüssel, Modelle, Prioritäten und Limits verwaltest du in der Ingress-Weboberfläche. Die native **LiteLLM-Integration** verbindet den Router mit Assist.

Version **2026-10-27** · LiteLLM **1.106.4** · amd64 / aarch64 · Home Assistant **2026.8+**

* **21 Anbietervorlagen** einschließlich Groq, Gemini, Cerebras, OpenRouter, Mistral und lokaler Modelle.
* **Automatisches Ausweichen** bei Rate-Limits und Ausfällen, persistente Abkühlzeiten und gemeinsame Kontingentgruppen.
* **Vier Routing-Presets** und eigene Regeln mit Modellalias und Tool-Bedingung.
* **Verbrauch pro API-Anfrage** mit Eingabe-/Ausgabetokens, Dauer, Fallback-Historie und CSV-Export.
* **Ohne Textdateien**: Webänderungen landen in der App-Konfiguration; vorhandene `!secret`-Verweise bleiben erhalten.
* **Geführte Assist-Einrichtung** über die native LiteLLM-Integration und optionale MCP-Einrichtung.
* **Deutsch und Englisch**, stabile Versionsprüfung und per Tag plus Digest gepinnte LiteLLM-Komponente.

## Schnellstart

1. App installieren/starten und Weboberfläche öffnen.
2. Unter **Anbieter** Profile hinzufügen, Modell und Schlüssel eintragen, speichern und testen.
3. Reihenfolge oder Routing-Preset wählen; für normale Assist-Nutzung **assist-auto** verwenden.
4. Unter **Assist verbinden** die Router-Verbindungsdaten anzeigen und **LiteLLM in Home Assistant hinzufügen** öffnen.
5. Im LiteLLM-Eintrag einen Konversationsagenten für **assist-auto** hinzufügen, benötigte Assist-Werkzeuge/Entitäten freigeben und diesen Agenten im Sprachassistenten auswählen.

LiteLLM ist bereits enthalten. Ein zusätzlicher Proxy oder eine eigene Custom-Integration ist nicht nötig. Der interne API-Port 8000 verlangt einen eigenen Router-Schlüssel; die Verwaltung ist ausschließlich über Ingress erreichbar.

## Kontingente ehrlich darstellen

Die Oberfläche zeigt den lokal erfassten Verbrauch dieser App gegen deine eingetragenen Limits. Eine universelle Live-Guthabenabfrage der Anbieter gibt es in dieser Version nicht; die Anbieterportale sind verlinkt. Externe Nutzung bleibt unbekannt. Gratis-Zugang hängt vom Modell und deinem Konto ab und wird nicht durch eine Vorlage garantiert.

Sind alle erlaubten Anbieter erschöpft und kein lokales Modell verfügbar, kann eine Anfrage weiterhin scheitern. Ein zusätzliches lokales, Tool-fähiges Modell verbessert die Verfügbarkeit. Prompts und Antworten werden nicht gespeichert.

## Dokumentation

[Deutsche Anleitung](assist_ai_router/DOCS.md) · [English guide](assist_ai_router/DOCS.en.md) · [English overview](README.en.md) · [Entwicklung und Abnahme](CONTRIBUTING.md) · [Änderungen](assist_ai_router/CHANGELOG.md)

Die erste Version ist ausdrücklich **experimental**. Tests prüfen Routing, Secrets, HTTP-Zugänge und die tatsächliche LiteLLM-SDK-Anbindung; die Abnahme mit realem Home Assistant und echten Anbieter-Kontingenten steht separat an.

<!-- support:begin (generated, shared text) -->
## Say thanks

All my projects are built in my spare time, just for the fun of it. Still, they take a lot of time and care, and many of the smart home gadgets I buy end up here because I want to make them cloud-free and smart-home ready. Every bit of support means a lot to me.

If my work helped you or turned out to be useful, show your appreciation with a hot drink for my next sleepless night.

[![PayPal](https://img.shields.io/static/v1?label=Support&message=PayPal&color=0070BA&logo=paypal&logoColor=white&style=for-the-badge)](https://paypal.me/seb5594) [![Buy Me a Coffee](https://img.shields.io/static/v1?label=Support&message=Buy%20Me%20a%20Coffee&color=FFDD00&logo=buy-me-a-coffee&logoColor=black&style=for-the-badge)](https://buymeacoffee.com/seb5594)
<!-- support:end -->

<!-- license:begin (generated from the license file) -->
## License

[![license](https://img.shields.io/static/v1?label=license&message=Apache-2.0&color=5B6770&style=flat)](LICENSE)

Published under the [Apache License 2.0](LICENSE).
<!-- license:end -->
