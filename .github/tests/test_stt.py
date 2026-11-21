import asyncio
import copy
import json
import socket
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] if len(Path(__file__).resolve().parents) > 2 else Path("/opt/router")
sys.path.insert(0, str(ROOT / "assist_ai_router"))
from app import stt
from app.catalog import DEFAULTS
from app.settings import ConfigError, Settings, normalize
from app.stt import SttGateway
from app.wyoming import Event, WireError, parse_uri, read_event, write_event

AUDIO = bytes(range(256)) * 4


def free_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


class Engine:
    """A scripted Wyoming speech-to-text service."""

    def __init__(self, languages, reply="", mode="reply", name="engine"):
        self.languages, self.reply, self.mode, self.name = languages, reply, mode, name
        self.utterances, self.describes = [], 0

    async def start(self):
        self.server = await asyncio.start_server(self.handle, "127.0.0.1", 0)
        self.port = self.server.sockets[0].getsockname()[1]
        self.uri = f"tcp://127.0.0.1:{self.port}"

    async def stop(self):
        self.server.close()

    def info(self):
        attribution = dict(name="test", url="https://example.invalid")
        return dict(asr=[dict(name=self.name, installed=True, attribution=attribution, description="fake",
                              models=[dict(name=self.name + "-model", languages=self.languages, installed=True,
                                           attribution=attribution, description="fake")])])

    async def handle(self, reader, writer):
        current = dict(transcribe=None, start=None, audio=b"")
        try:
            while (event := await read_event(reader)) is not None:
                if event.type == "describe":
                    self.describes += 1
                    await write_event(writer, Event("info", self.info()))
                elif event.type == "transcribe":
                    current["transcribe"] = event.data
                elif event.type == "audio-start":
                    current["start"] = event.data
                elif event.type == "audio-chunk":
                    current["audio"] += event.payload
                elif event.type == "audio-stop":
                    self.utterances.append(current)
                    current = dict(transcribe=None, start=None, audio=b"")
                    if self.mode == "reply":
                        await write_event(writer, Event("transcript", dict(text=self.reply, language="de")))
                    elif self.mode == "error":
                        await write_event(writer, Event("error", dict(text="boom")))
                    elif self.mode == "close":
                        break
                    elif self.mode == "hang":
                        await asyncio.sleep(30)
        except (OSError, WireError, asyncio.CancelledError):
            pass
        finally:
            writer.close()


class FakeSupervisor:
    def __init__(self):
        self.announced, self.withdrawn = [], []

    def announce(self, uri):
        self.announced.append(uri)
        return "uuid-1"

    def withdraw(self, uuid):
        self.withdrawn.append(uuid)


async def speak(port, language="de", chunks=3, describe=False):
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    try:
        if describe:
            await write_event(writer, Event("describe"))
            return await asyncio.wait_for(read_event(reader), 20)
        await write_event(writer, Event("transcribe", dict(name="ignored-model", language=language)))
        await write_event(writer, Event("audio-start", dict(rate=16000, width=2, channels=1)))
        for _ in range(chunks):
            await write_event(writer, Event("audio-chunk", dict(rate=16000, width=2, channels=1), AUDIO))
        await write_event(writer, Event("audio-stop"))
        return await asyncio.wait_for(read_event(reader), 20)
    finally:
        writer.close()


class Gateway(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Settings(self.tmp.name)
        self.primary = Engine(["de", "en"], "turn on the light", name="phrase")
        self.fallback = Engine(["de", "en", "fr"], "what is the weather", name="whisper")
        for engine in (self.primary, self.fallback):
            await engine.start()
        self.supervisor = FakeSupervisor()
        self.gateway = SttGateway(self.settings, self.tmp.name, "9.9.9", host="127.0.0.1", port=0, supervisor=self.supervisor)
        await asyncio.to_thread(lambda: self.gateway.start().result(5))

    async def asyncTearDown(self):
        await asyncio.to_thread(self.gateway.stop)
        for engine in (self.primary, self.fallback):
            await engine.stop()
        self.tmp.cleanup()

    async def configure(self, **options):
        options = {"stt_enabled": True, "stt_primary": self.primary.uri, "stt_fallback": self.fallback.uri, **options}
        self.settings.save({**copy.deepcopy(DEFAULTS), **options}, self.settings.revision())
        await asyncio.to_thread(lambda: self.gateway.reconfigure().result(5))
        await asyncio.sleep(0.05)  # Let the start-up capability lookup finish before the first request.

    async def test_primary_answer_never_touches_the_fallback(self):
        await self.configure()
        reply = await speak(self.gateway.bound_port)
        self.assertEqual((reply.type, reply.data["text"]), ("transcript", "turn on the light"))
        self.assertEqual(len(self.primary.utterances), 1)
        self.assertEqual(self.fallback.utterances, [])
        self.assertEqual(self.gateway.status()["counters"], dict(requests=1, primary=1, fallback=0, none=0))

    async def test_empty_primary_result_replays_the_identical_audio_to_the_fallback(self):
        self.primary.reply = ""
        await self.configure()
        reply = await speak(self.gateway.bound_port, "de", chunks=5)
        self.assertEqual(reply.data["text"], "what is the weather")
        first, second = self.primary.utterances[0], self.fallback.utterances[0]
        self.assertEqual(second["audio"], first["audio"])
        self.assertEqual(len(second["audio"]), 5 * len(AUDIO))
        self.assertEqual(second["start"], first["start"])
        # The model name belongs to the gateway's merged list, every engine chooses its own.
        self.assertEqual(second["transcribe"], dict(language="de"))
        self.assertEqual(self.gateway.status()["recent"][0]["route"], "fallback")
        self.assertEqual(self.gateway.status()["recent"][0]["reason"], "empty")

    async def test_whitespace_only_text_counts_as_not_understood(self):
        self.primary.reply = "  \n"
        await self.configure()
        self.assertEqual((await speak(self.gateway.bound_port)).data["text"], "what is the weather")

    async def test_unreachable_primary_goes_straight_to_the_fallback(self):
        await self.configure(stt_primary=f"tcp://127.0.0.1:{free_port()}")
        reply = await speak(self.gateway.bound_port)
        self.assertEqual(reply.data["text"], "what is the weather")
        self.assertEqual(self.gateway.status()["recent"][0]["reason"], "error")

    async def test_erroring_or_dropping_primary_is_covered_by_the_fallback(self):
        for mode in ("error", "close"):
            with self.subTest(mode=mode):
                self.primary.mode = mode
                await self.configure()
                self.assertEqual((await speak(self.gateway.bound_port)).data["text"], "what is the weather")

    async def test_slow_primary_is_abandoned_after_its_time_budget(self):
        self.primary.mode = "hang"
        await self.configure(stt_primary_timeout=1)
        started = asyncio.get_running_loop().time()
        reply = await speak(self.gateway.bound_port)
        self.assertEqual(reply.data["text"], "what is the weather")
        self.assertLess(asyncio.get_running_loop().time() - started, 5)

    async def test_nothing_recognized_still_answers_with_an_empty_transcript(self):
        self.primary.reply = self.fallback.reply = ""
        await self.configure()
        reply = await speak(self.gateway.bound_port)
        self.assertEqual((reply.type, reply.data["text"]), ("transcript", ""))
        self.assertEqual(self.gateway.status()["counters"]["none"], 1)

    async def test_both_engines_down_answers_instead_of_hanging(self):
        await self.configure(stt_primary=f"tcp://127.0.0.1:{free_port()}", stt_fallback=f"tcp://127.0.0.1:{free_port()}")
        self.assertEqual((await speak(self.gateway.bound_port)).data["text"], "")

    async def test_primary_is_skipped_for_languages_only_the_fallback_knows(self):
        await self.configure()
        await speak(self.gateway.bound_port, describe=True)  # Home Assistant always asks first.
        reply = await speak(self.gateway.bound_port, "fr")
        self.assertEqual(reply.data["text"], "what is the weather")
        self.assertEqual(self.primary.utterances, [])
        self.assertEqual(self.gateway.status()["recent"][0]["reason"], "language")
        await speak(self.gateway.bound_port, "de")
        self.assertEqual(len(self.primary.utterances), 1)

    async def test_describe_merges_both_engines_into_one_program(self):
        await self.configure()
        info = (await speak(self.gateway.bound_port, describe=True)).data
        program = info["asr"][0]
        self.assertEqual((program["name"], program["version"]), ("Assist AI Router", "9.9.9"))
        self.assertEqual(sorted(model["name"] for model in program["models"]), ["phrase-model", "whisper-model"])
        self.assertEqual(stt.languages(info), {"de", "en", "fr"})
        self.assertFalse(program["supports_transcript_streaming"])
        self.assertTrue(program["requires_external_vad"])
        self.assertEqual(info["tts"], [])

    async def test_last_known_capabilities_survive_engines_that_are_not_up_yet(self):
        await self.configure()
        await speak(self.gateway.bound_port, describe=True)
        for engine in (self.primary, self.fallback):
            await engine.stop()
        cold = SttGateway(self.settings, self.tmp.name, "9.9.9", host="127.0.0.1", port=0)
        await asyncio.to_thread(lambda: cold.start().result(5))
        try:
            self.assertEqual(stt.languages((await speak(cold.bound_port, describe=True)).data), {"de", "en", "fr"})
        finally:
            await asyncio.to_thread(cold.stop)

    async def test_toggling_applies_without_restart(self):
        self.assertFalse(self.gateway.status()["listening"])
        await self.configure()
        port = self.gateway.bound_port
        self.assertTrue(self.gateway.status()["listening"])
        await self.configure(stt_enabled=False)
        self.assertFalse(self.gateway.status()["listening"])
        with self.assertRaises(OSError):
            await asyncio.open_connection("127.0.0.1", port)

    async def test_discovery_is_announced_with_the_listening_address_and_withdrawn_when_disabled(self):
        await self.configure()
        self.assertEqual(self.supervisor.announced, [f"tcp://localhost:{self.gateway.bound_port}"])
        self.assertEqual(self.gateway.status()["discovery"], "announced")
        await self.configure(stt_enabled=False)
        self.assertEqual(self.supervisor.withdrawn, ["uuid-1"])
        self.assertEqual(self.gateway.status()["discovery"], "off")

    async def test_too_long_audio_is_refused_without_growing_memory(self):
        original, stt.MAX_AUDIO_BYTES = stt.MAX_AUDIO_BYTES, len(AUDIO) * 2
        try:
            await self.configure()
            reply = await speak(self.gateway.bound_port, chunks=3)
        finally:
            stt.MAX_AUDIO_BYTES = original
        self.assertEqual(reply.data["text"], "")
        self.assertEqual(self.gateway.status()["recent"][0]["reason"], "too_long")
        self.assertEqual(self.fallback.utterances, [])

    async def test_the_gateway_never_forwards_to_itself(self):
        await self.configure()
        await self.configure(stt_primary=f"tcp://localhost:{self.gateway.bound_port}")
        self.assertEqual((await speak(self.gateway.bound_port)).data["text"], "what is the weather")
        self.assertEqual(self.primary.utterances, [])

    async def test_check_reports_each_engine_without_sending_audio(self):
        await self.configure(stt_fallback=f"tcp://127.0.0.1:{free_port()}")
        result = await asyncio.to_thread(self.gateway.check)
        primary, fallback = result["engines"]
        self.assertEqual((primary["ok"], primary["languages"], primary["error"]), (True, ["de", "en"], ""))
        self.assertEqual((fallback["ok"], fallback["error"]), (False, "stt_unreachable"))
        self.assertEqual(self.primary.utterances, [])

    async def test_transcripts_are_never_kept(self):
        await self.configure()
        await speak(self.gateway.bound_port)
        self.assertNotIn("turn on the light", json.dumps(self.gateway.status()))
        self.assertFalse(any("turn on the light" in path.read_text(errors="ignore") for path in Path(self.tmp.name).iterdir() if path.is_file()))

    async def test_new_connections_beyond_the_session_limit_are_dropped(self):
        await self.configure()
        held = [await asyncio.open_connection("127.0.0.1", self.gateway.bound_port) for _ in range(stt.MAX_SESSIONS)]
        await asyncio.sleep(0.1)
        reader, writer = await asyncio.open_connection("127.0.0.1", self.gateway.bound_port)
        self.assertEqual(await asyncio.wait_for(reader.read(), 5), b"")
        for _, held_writer in held + [(reader, writer)]:
            held_writer.close()


class Framing(unittest.IsolatedAsyncioTestCase):
    def feed(self, raw):
        reader = asyncio.StreamReader()
        reader.feed_data(raw)
        reader.feed_eof()
        return reader

    async def test_inline_and_separate_data_are_merged_and_payload_is_read(self):
        extra = b'{"b":2}'
        raw = b'{"type":"audio-chunk","data":{"a":1},"data_length":%d,"payload_length":3}\n' % len(extra) + extra + b"xyz"
        event = await read_event(self.feed(raw))
        self.assertEqual((event.type, event.data, event.payload), ("audio-chunk", dict(a=1, b=2), b"xyz"))

    async def test_clean_close_returns_none_and_garbage_is_rejected(self):
        self.assertIsNone(await read_event(self.feed(b"")))
        for raw in (b"not json\n", b"[]\n", b'{"type":""}\n', b'{"type":"x","payload_length":-1}\n',
                    b'{"type":"x","payload_length":99999999}\n', b'{"type":"x","data_length":"3"}\n',
                    b'{"type":"x","payload_length":5}\nabc', b'{"type":"x","data_length":2}\n[]'):
            with self.subTest(raw=raw), self.assertRaises(WireError):
                await read_event(self.feed(raw))

    async def test_written_events_can_be_read_back(self):
        class Sink:
            def __init__(self):
                self.raw = b""

            def write(self, data):
                self.raw += data

            async def drain(self):
                pass
        sink = Sink()
        await write_event(sink, Event("transcript", dict(text="Grüße")))
        await write_event(sink, Event("audio-chunk", dict(rate=1), b"\x00\xff"))
        reader = self.feed(sink.raw)
        self.assertEqual((await read_event(reader)).data, dict(text="Grüße"))
        self.assertEqual((await read_event(reader)).payload, b"\x00\xff")

    def test_uri_parsing(self):
        self.assertEqual(parse_uri("tcp://core-whisper:10300"), ("core-whisper", 10300))
        for bad in ("http://core-whisper:10300", "tcp://core-whisper", "tcp://:10300", "tcp://a:0", "tcp://a:99999",
                    "tcp://user@a:1", "tcp://a:1/path", "core-whisper:10300", ""):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                parse_uri(bad)

    def test_language_matching_is_tolerant_but_never_mixes_regions(self):
        self.assertTrue(stt.same_language("de", "de_DE"))
        self.assertTrue(stt.same_language("en-US", "en"))
        self.assertFalse(stt.same_language("en-US", "en-GB"))
        self.assertFalse(stt.same_language("de", "nl"))


class Validation(unittest.TestCase):
    def check(self, **options):
        return normalize({**copy.deepcopy(DEFAULTS), **options})

    def test_defaults_are_valid_and_disabled(self):
        self.assertFalse(self.check()["stt_enabled"])

    def test_enabling_requires_two_different_valid_engines(self):
        good = dict(stt_enabled=True, stt_primary="tcp://a:1", stt_fallback="tcp://b:1")
        self.assertTrue(self.check(**good)["stt_enabled"])
        for override in (dict(stt_fallback=""), dict(stt_primary=""), dict(stt_fallback="tcp://a:1")):
            with self.subTest(override=override), self.assertRaisesRegex(ConfigError, "invalid_stt_setup"):
                self.check(**{**good, **override})

    def test_addresses_and_budgets_are_bounded(self):
        for options, code in ((dict(stt_primary="http://a:1"), "invalid_stt_uri"),
                              (dict(stt_primary="tcp://supervisor:80"), "invalid_stt_uri"),
                              (dict(stt_fallback="tcp://localhost:10300"), "invalid_stt_uri"),
                              (dict(stt_primary="tcp://127.0.0.1:10300"), "invalid_stt_uri"),
                              (dict(stt_primary_timeout=0), "invalid_stt_primary_timeout"),
                              (dict(stt_fallback_timeout=301), "invalid_stt_fallback_timeout"),
                              (dict(stt_enabled="yes"), "invalid_settings")):
            with self.subTest(options=options), self.assertRaisesRegex(ConfigError, code):
                self.check(**options)


if __name__ == "__main__":
    unittest.main()
