"""Tests for the Dolby Atmos Renderer client: each documented command is sent with its address and types."""

import socket
import unittest

from pythonosc.dar import DEFAULT_PORT, RendererClient
from pythonosc.osc_message import OscMessage


class _Receiver:
    """A UDP socket on localhost that the client sends to, and reads one datagram from."""

    def __init__(self) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.settimeout(2)
        self.port = self.sock.getsockname()[1]

    def recv(self) -> OscMessage:
        return OscMessage(self.sock.recv(4096))

    def close(self) -> None:
        self.sock.close()


class RendererClientTest(unittest.TestCase):
    def setUp(self) -> None:
        self.receiver = _Receiver()
        self.client = RendererClient("127.0.0.1", self.receiver.port)

    def tearDown(self) -> None:
        self.client.close()
        self.receiver.close()

    def assertSent(self, address: str, args: list) -> None:
        msg = self.receiver.recv()
        self.assertEqual(msg.address, address)
        self.assertEqual(list(msg.params), args)

    def test_default_port_is_the_renderer_osc_port(self) -> None:
        self.assertEqual(DEFAULT_PORT, 8001)
        self.assertEqual(RendererClient().__dict__["_port"], 8001)

    def test_transport(self) -> None:
        self.client.play()
        self.assertSent("/dar/transport/play", [])
        self.client.stop()
        self.assertSent("/dar/transport/stop", [])
        self.client.pause()
        self.assertSent("/dar/transport/pause", [])
        self.client.seek(12.5)
        self.assertSent("/dar/transport/seek", [12.5])
        self.client.set_external_sync(True)
        self.assertSent("/dar/transport/external_sync", [1])
        self.client.set_external_sync(False)
        self.assertSent("/dar/transport/external_sync", [0])

    def test_monitoring(self) -> None:
        self.client.set_attenuation(0.5)
        self.assertSent("/dar/monitoring/attenuation", [0.5])
        for mode in (0, 1, 2, 3):
            self.client.set_mute(mode)
            self.assertSent("/dar/monitoring/mute", [mode])
        self.client.set_dim(True)
        self.assertSent("/dar/monitoring/dim", [1])
        self.client.enable_record_in_out(False)
        self.assertSent("/dar/monitoring/enable_record_in_out", [0])
        self.client.set_record_in_out(10.0, 20.5)
        self.assertSent("/dar/monitoring/set_record_in_out", [10.0, 20.5])
        self.client.arm_record(True)
        self.assertSent("/dar/monitoring/arm_record", [1])
        self.client.set_input_master_source(True)
        self.assertSent("/dar/monitoring/input_master_source", [1])
        self.client.set_monitoring_layout(3)
        self.assertSent("/dar/monitoring/monitoring_layout", [3])

    def test_integer_arguments_are_sent_as_integers(self) -> None:
        self.client.set_mute(2)
        msg = self.receiver.recv()
        self.assertIsInstance(msg.params[0], int)

    def test_refuses_values_outside_the_documented_range(self) -> None:
        with self.assertRaises(ValueError):
            self.client.set_attenuation(1.5)
        with self.assertRaises(ValueError):
            self.client.set_attenuation(-0.1)
        with self.assertRaises(ValueError):
            self.client.set_mute(4)
        with self.assertRaises(ValueError):
            self.client.set_dim(2)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            self.client.seek(-1)
        with self.assertRaises(ValueError):
            self.client.set_record_in_out(-1, 5)
        with self.assertRaises(ValueError):
            self.client.set_monitoring_layout(-1)
        # nothing was sent for the refused calls
        self.receiver.sock.settimeout(0.2)
        with self.assertRaises(socket.timeout):
            self.receiver.sock.recv(4096)


if __name__ == "__main__":
    unittest.main()
