"""Client for the OSC controls of the Dolby Atmos Renderer (5.3).

The Renderer listens for OSC on UDP port 8001 on the same network. The commands are the ones of the
Dolby Atmos Renderer User's Guide, section 29 ("OSC transport and monitoring controls", table 13), also table 16
of the Renderer for Cinema User's Guide. Argument types follow the table: ``i`` is an integer, ``f`` a float.
Values outside the documented range raise ``ValueError`` before anything is sent.
"""

from pythonosc.udp_client import SimpleUDPClient

DEFAULT_PORT = 8001

# Monitoring mute values (table 13): 0 all off, 1 global, 2 bed, 3 object.
MUTE_OFF, MUTE_GLOBAL, MUTE_BED, MUTE_OBJECT = 0, 1, 2, 3


def _flag(value: int, name: str) -> int:
    if value not in (0, 1):
        raise ValueError(f"{name} must be 0 or 1, got {value!r}")
    return value


def _seconds(value: float, name: str) -> float:
    if value < 0:
        raise ValueError(f"{name} must be 0 seconds or more, got {value!r}")
    return float(value)


class RendererClient(SimpleUDPClient):
    """Sends the documented OSC controls to a Dolby Atmos Renderer.

    The Renderer sends no reply to these commands, so the client only sends.
    """

    def __init__(self, address: str = "127.0.0.1", port: int = DEFAULT_PORT, **kwargs: object) -> None:
        super().__init__(address, port, **kwargs)  # type: ignore[arg-type]

    # Transport. Each one switches the Renderer to its internal transport first.

    def play(self) -> None:
        """/dar/transport/play: resume transport."""
        self.send_message("/dar/transport/play", [])

    def stop(self) -> None:
        """/dar/transport/stop: stop transport."""
        self.send_message("/dar/transport/stop", [])

    def pause(self) -> None:
        """/dar/transport/pause: pause transport."""
        self.send_message("/dar/transport/pause", [])

    def seek(self, seconds: float) -> None:
        """/dar/transport/seek f: move the playhead to ``seconds``."""
        self.send_message("/dar/transport/seek", float(_seconds(seconds, "seconds")))

    def set_external_sync(self, enabled: bool) -> None:
        """/dar/transport/external_sync i 0/1: engage (1) or disengage (0) the external sync to LTC."""
        self.send_message("/dar/transport/external_sync", _flag(int(enabled), "enabled"))

    # Monitoring.

    def set_attenuation(self, amplitude: float) -> None:
        """/dar/monitoring/attenuation f 0.0-1.0: amplitude, 0 is -inf dB, 1 is 0 dB."""
        if not 0.0 <= amplitude <= 1.0:
            raise ValueError(f"attenuation must be between 0.0 and 1.0, got {amplitude!r}")
        self.send_message("/dar/monitoring/attenuation", float(amplitude))

    def set_mute(self, mode: int) -> None:
        """/dar/monitoring/mute i 0-3: 0 all off, 1 global, 2 bed, 3 object."""
        if mode not in (MUTE_OFF, MUTE_GLOBAL, MUTE_BED, MUTE_OBJECT):
            raise ValueError(f"mute must be 0, 1, 2 or 3, got {mode!r}")
        self.send_message("/dar/monitoring/mute", mode)

    def set_dim(self, enabled: bool) -> None:
        """/dar/monitoring/dim i 0/1: enable (1) or disable (0) dim."""
        self.send_message("/dar/monitoring/dim", _flag(int(enabled), "enabled"))

    def enable_record_in_out(self, enabled: bool) -> None:
        """/dar/monitoring/enable_record_in_out i 0/1: bounded recording. The master must be unlocked."""
        self.send_message("/dar/monitoring/enable_record_in_out", _flag(int(enabled), "enabled"))

    def set_record_in_out(self, in_seconds: float, out_seconds: float) -> None:
        """/dar/monitoring/set_record_in_out f f: In and Out points in seconds. Bounded recording must be enabled."""
        self.send_message(
            "/dar/monitoring/set_record_in_out",
            [float(_seconds(in_seconds, "in")), float(_seconds(out_seconds, "out"))],
        )

    def arm_record(self, armed: bool) -> None:
        """/dar/monitoring/arm_record i 0/1: arm (1) or disarm (0) recording. A master must be loaded and unlocked."""
        self.send_message("/dar/monitoring/arm_record", _flag(int(armed), "armed"))

    def set_input_master_source(self, master: bool) -> None:
        """/dar/monitoring/input_master_source i 0/1: 0 is Input, 1 is Master."""
        self.send_message("/dar/monitoring/input_master_source", _flag(int(master), "master"))

    def set_monitoring_layout(self, index: int) -> None:
        """/dar/monitoring/monitoring_layout i: index in the Monitoring drop-down of the Renderer."""
        if index < 0:
            raise ValueError(f"monitoring layout index must be 0 or more, got {index!r}")
        self.send_message("/dar/monitoring/monitoring_layout", int(index))

