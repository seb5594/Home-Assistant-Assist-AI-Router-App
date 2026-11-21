"""Wyoming speech-to-text front with an automatic second chance.

Home Assistant talks to this gateway like to any Wyoming speech-to-text service. The audio is
streamed live to the primary engine (for example Speech-to-Phrase) while it is buffered, so the
identical recording can be replayed to a fallback engine (for example Whisper) when the primary
returns no text or is unavailable. Wyoming transcripts carry no confidence value, therefore
"no text" is the signal that the primary did not understand the speech.

Transcript texts are never logged or stored; only outcome, language and timing are kept.
"""
import asyncio
import collections
import json
import os
import threading
import time
from pathlib import Path

from .router import GatewayError
from .wyoming import Event, WireError, parse_uri, read_event, write_event

PORT = 10300
MAX_SESSIONS = 4
MAX_AUDIO_BYTES = 8 * 1024 * 1024  # About four minutes of 16 kHz mono; longer audio is refused.
CONNECT_TIMEOUT = 3
IDLE_TIMEOUT = 60
INFO_TTL = 60
RECENT = 20
REPO = "https://github.com/seb5594/Home-Assistant-Assist-AI-Router-App"
NETWORK_ERRORS = (OSError, WireError, asyncio.TimeoutError)


def normalize_language(value):
    return value.lower().replace("_", "-")


def same_language(a, b):
    a, b = normalize_language(a), normalize_language(b)
    return a == b or (a.split("-")[0] == b.split("-")[0] and ("-" not in a or "-" not in b))


def languages(info):
    """All language codes announced by the ASR programs of an Info event."""
    return {lang for program in (info or {}).get("asr") or [] for model in program.get("models") or []
            for lang in model.get("languages") or [] if isinstance(lang, str)}


def supports(info, language):
    return any(same_language(language, known) for known in languages(info))


def merge_info(infos, version):
    """One ASR program that offers the models of every reachable engine."""
    models, seen, external_vad = [], set(), False
    for info in infos:
        for program in (info or {}).get("asr") or []:
            external_vad = external_vad or program.get("requires_external_vad", True)
            for model in program.get("models") or []:
                key = (model.get("name"), tuple(model.get("languages") or ()))
                if key not in seen:
                    seen.add(key)
                    models.append(model)
    program = dict(name="Assist AI Router", description="Fast first engine with an automatic second chance",
                   attribution=dict(name="seb5594", url=REPO), installed=True, version=version, models=models,
                   supports_transcript_streaming=False, requires_external_vad=external_vad or not models,
                   prefers_auto_gain_enabled=False, prefers_noise_reduction_enabled=False)
    return dict(asr=[program], tts=[], handle=[], intent=[], wake=[], mic=[], snd=[])


class Upstream:
    """One short-lived connection to a Wyoming service."""

    def __init__(self, reader, writer):
        self.reader, self.writer = reader, writer

    @classmethod
    async def connect(cls, uri, timeout=CONNECT_TIMEOUT):
        host, port = parse_uri(uri)
        return cls(*await asyncio.wait_for(asyncio.open_connection(host, port), timeout))

    async def send(self, event):
        await write_event(self.writer, event)

    async def receive(self, wanted, timeout):
        async def until_wanted():
            while True:
                event = await read_event(self.reader)
                if event is None or event.type == "error":
                    raise WireError("upstream_closed" if event is None else "upstream_error")
                if event.type == wanted:
                    return event
        return await asyncio.wait_for(until_wanted(), timeout)

    async def close(self):
        self.writer.close()
        try:
            await self.writer.wait_closed()
        except Exception:  # The peer may already be gone; nothing left to clean up.
            pass


class Session:
    """Audio of one utterance plus the live link to the primary engine."""

    def __init__(self):
        self.primary = self.transcribe = None
        self.clear()

    def clear(self):
        self.audio, self.size, self.sent, self.skip = [], 0, 0, ""
        self.overflow = self.primary_dead = False

    async def release(self):
        if self.primary:
            await self.primary.close()
        self.primary = None

    async def end(self):
        await self.release()
        self.transcribe = None
        self.clear()


class Stats:
    def __init__(self):
        self.lock = threading.Lock()
        self.counters = collections.Counter()
        self.recent = collections.deque(maxlen=RECENT)

    def record(self, route, reason, milliseconds, language):
        with self.lock:
            self.counters["requests"] += 1
            self.counters[route] += 1
            self.recent.appendleft(dict(ts=int(time.time()), route=route, reason=reason, ms=milliseconds, language=language or ""))

    def view(self):
        with self.lock:
            counters = {key: self.counters[key] for key in ("requests", "primary", "fallback", "none")}
            return dict(counters=counters, recent=list(self.recent))


class SttGateway:
    def __init__(self, settings, folder, version, *, host="0.0.0.0", port=PORT, supervisor=None):
        self.settings, self.version, self.host, self.port, self.supervisor = settings, version, host, port, supervisor
        self.cache_path = Path(folder) / "stt-info.json"
        self.stats = Stats()
        self.loop = self.thread = self.server = None
        self.writers, self.sessions, self.warm = set(), 0, None
        self.error, self.discovery, self.discovery_id = "", "off", ""
        self.infos = {}  # uri -> (monotonic time, Info data)
        self.saved = self._load()

    # ---- lifecycle (called from the HTTP threads) -------------------------------------------
    def start(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run, daemon=True, name="stt-gateway")
        self.thread.start()
        return self.reconfigure()

    def _run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def reconfigure(self):
        """Start or stop listening according to the saved settings. Safe to call at any time."""
        if self.loop:
            return asyncio.run_coroutine_threadsafe(self._apply(), self.loop)

    def stop(self):
        if not self.loop:
            return
        try:
            asyncio.run_coroutine_threadsafe(self._shutdown(), self.loop).result(10)
        except Exception:
            pass
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(5)
        if not self.thread.is_alive():
            self.loop.close()

    def check(self):
        """Ask both engines for their capabilities. Metadata only, no audio is sent."""
        if not self.loop:
            raise GatewayError("stt_unavailable", 503)
        return asyncio.run_coroutine_threadsafe(self._check(), self.loop).result(20)

    @property
    def bound_port(self):
        return self.server.sockets[0].getsockname()[1] if self.server else self.port

    def status(self):
        cfg = self.settings.snapshot()
        return dict(enabled=cfg["stt_enabled"], listening=self.server is not None, host=self.settings.hostname,
                    port=self.bound_port, error=self.error, discovery=self.discovery, sessions=self.sessions,
                    **self.stats.view())

    # ---- server side ------------------------------------------------------------------------
    async def _apply(self):
        enabled = self.settings.snapshot()["stt_enabled"]
        if enabled and self.server is None:
            try:
                self.server = await asyncio.start_server(self._client, self.host, self.port)
            except OSError:
                self.error = "stt_port_unavailable"
                return
            self.error = ""
            self.warm = asyncio.ensure_future(self.info())  # Learn the engines' languages before the first request.
            await self._announce()
        elif not enabled and self.server is not None:
            await self._shutdown()

    async def _shutdown(self):
        await self._withdraw()
        if self.server:
            self.server.close()
            self.server = None
        for writer in list(self.writers):
            writer.close()

    async def _announce(self):
        """Offer the service to Home Assistant's Wyoming integration through Supervisor discovery."""
        if not self.supervisor:
            return
        uri = f"tcp://{self.settings.hostname}:{self.bound_port}"
        try:
            self.discovery_id = await self.loop.run_in_executor(None, self.supervisor.announce, uri)
            self.discovery = "announced"
        except Exception:
            self.discovery = "unavailable"

    async def _withdraw(self):
        if self.discovery_id:
            try:
                await self.loop.run_in_executor(None, self.supervisor.withdraw, self.discovery_id)
            except Exception:
                pass
        self.discovery, self.discovery_id = "off", ""

    async def _client(self, reader, writer):
        if self.sessions >= MAX_SESSIONS:
            writer.close()
            return
        self.sessions += 1
        self.writers.add(writer)
        session = Session()
        try:
            await self._serve(reader, writer, session)
        except NETWORK_ERRORS:
            pass  # The client left or sent garbage; nothing to answer.
        finally:
            self.sessions -= 1
            self.writers.discard(writer)
            await session.end()
            writer.close()

    async def _serve(self, reader, writer, session):
        while True:
            event = await asyncio.wait_for(read_event(reader), IDLE_TIMEOUT)
            if event is None:
                return
            if event.type == "describe":
                await write_event(writer, Event("info", await self.info()))
            elif event.type == "ping":
                await write_event(writer, Event("pong", event.data))
            elif event.type == "transcribe":
                await session.end()
                session.transcribe = event
            elif event.type in ("audio-start", "audio-chunk", "audio-stop"):
                await self._audio(session, event)
                if event.type == "audio-stop":
                    await write_event(writer, await self._finish(session))
                    await session.end()

    # ---- one utterance ----------------------------------------------------------------------
    async def _audio(self, session, event):
        if event.type == "audio-start":
            await session.release()
            session.clear()
        session.size += len(event.payload)
        if session.size > MAX_AUDIO_BYTES:
            session.overflow, session.audio = True, []
            return
        session.audio.append(event)
        if event.type == "audio-start":
            await self._open_primary(session)
        await self._pump(session)

    async def _open_primary(self, session):
        cfg = self.settings.snapshot()
        language = (session.transcribe.data.get("language") if session.transcribe else "") or ""
        primary, fallback = (self.infos.get(cfg["stt_" + role], (0, None))[1] for role in ("primary", "fallback"))
        if language and primary and fallback and not supports(primary, language) and supports(fallback, language):
            session.skip = "language"  # The primary engine cannot understand this language at all.
            return
        try:
            session.primary = await self._connect(cfg["stt_primary"])
            if session.transcribe:
                await session.primary.send(self._for_engine(session.transcribe))
        except NETWORK_ERRORS:
            session.primary_dead = True

    async def _pump(self, session):
        """Forward buffered audio to the primary engine as it arrives."""
        while session.primary and not session.primary_dead and session.sent < len(session.audio):
            try:
                await session.primary.send(session.audio[session.sent])
            except NETWORK_ERRORS:
                session.primary_dead = True
                return
            session.sent += 1

    async def _finish(self, session):
        cfg = self.settings.snapshot()
        started = time.monotonic()
        language = (session.transcribe.data.get("language") if session.transcribe else "") or ""
        route, reason, text = "none", session.skip, ""
        if session.overflow:
            reason = "too_long"
        else:
            if session.primary and not session.primary_dead:
                try:
                    transcript = (await session.primary.receive("transcript", cfg["stt_primary_timeout"])).data
                    text, language = transcript.get("text") or "", transcript.get("language") or language
                    reason = "" if text.strip() else "empty"
                except NETWORK_ERRORS:
                    reason = "error"
            elif not session.skip:
                reason = "error"
            if text.strip():
                route = "primary"
            else:
                text, found = await self._second_chance(session, cfg)
                language = found or language
                route = "fallback" if text.strip() else "none"
        milliseconds = int((time.monotonic() - started) * 1000)
        self.stats.record(route, reason, milliseconds, language)
        return Event("transcript", dict(text=text, **({"language": language} if language else {})))

    async def _second_chance(self, session, cfg):
        try:
            engine = await self._connect(cfg["stt_fallback"])
        except NETWORK_ERRORS:
            return "", ""
        try:
            if session.transcribe:
                await engine.send(self._for_engine(session.transcribe))
            for event in session.audio:
                await engine.send(event)
            transcript = (await engine.receive("transcript", cfg["stt_fallback_timeout"])).data
            return transcript.get("text") or "", transcript.get("language") or ""
        except NETWORK_ERRORS:
            return "", ""
        finally:
            await engine.close()

    @staticmethod
    def _for_engine(transcribe):
        """The model name belongs to this gateway's merged list, so each engine picks its own."""
        return Event("transcribe", {key: value for key, value in transcribe.data.items() if key != "name"})

    async def _connect(self, uri):
        host, port = parse_uri(uri)
        if host == self.settings.hostname and port == self.bound_port:
            raise OSError("self_connection")  # Never forward to ourselves.
        return await Upstream.connect(uri)

    # ---- capabilities -----------------------------------------------------------------------
    async def info(self):
        cfg = self.settings.snapshot()
        return merge_info(await asyncio.gather(*(self._describe(cfg[key]) for key in ("stt_primary", "stt_fallback"))), self.version)

    async def _fetch_info(self, uri):
        engine = await self._connect(uri)
        try:
            await engine.send(Event("describe"))
            return (await engine.receive("info", CONNECT_TIMEOUT + 5)).data
        finally:
            await engine.close()

    async def _describe(self, uri):
        cached = self.infos.get(uri)
        if cached and time.monotonic() - cached[0] < INFO_TTL:
            return cached[1]
        try:
            data = await self._fetch_info(uri)
        except NETWORK_ERRORS:
            return cached[1] if cached else self.saved.get(uri)  # Last known capabilities keep HA usable.
        self.infos[uri] = (time.monotonic(), data)
        if self.saved.get(uri) != data:
            self.saved[uri] = data
            self._save()
        return data

    async def _check(self):
        cfg = self.settings.snapshot()

        async def probe(role):
            uri, started = cfg["stt_" + role], time.monotonic()
            row = dict(role=role, uri=uri, ok=False, ms=0, languages=[], error="")
            if not uri:
                row["error"] = "stt_not_configured"
                return row
            try:
                data = await self._fetch_info(uri)
                row["languages"] = sorted(languages(data))
                row["ok"], row["error"] = bool(data.get("asr")), "" if data.get("asr") else "stt_no_asr"
                if row["ok"]:
                    self.infos[uri] = (time.monotonic(), data)
            except asyncio.TimeoutError:
                row["error"] = "stt_timeout"
            except WireError:
                row["error"] = "stt_invalid_response"
            except OSError:
                row["error"] = "stt_unreachable"
            row["ms"] = int((time.monotonic() - started) * 1000)
            return row
        return dict(engines=await asyncio.gather(probe("primary"), probe("fallback")))

    def _load(self):
        try:
            data = json.loads(self.cache_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def _save(self):
        temp = self.cache_path.with_suffix(".tmp")
        try:
            temp.write_text(json.dumps(self.saved), encoding="utf-8")
            os.chmod(temp, 0o600)
            os.replace(temp, self.cache_path)
        except OSError:
            pass  # The cache only helps during start-up races; failing to write it is harmless.
