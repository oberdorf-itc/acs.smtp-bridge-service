import datetime
import json
import logging
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

# Ensure local package imports resolve (e.g., src/app/service imports lib.smtp)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "app"))

from src.app import service


class DummyCounter:
    def __init__(self):
        self.count = 0
        self.label_values = None

    def inc(self):
        self.count += 1

    def labels(self, **kwargs):
        self.label_values = kwargs
        return self


class TestService(unittest.TestCase):
    def setUp(self) -> None:
        self.env_backup = os.environ.copy()
        self.orig_log = getattr(service, "log", None)
        service.log = logging.getLogger("test_service")
        service.metrics = {
            "service_info": DummyCounter(),
            "mqtt_connects": DummyCounter(),
            "mqtt_messages": DummyCounter(),
            "mqtt_messages_refused": DummyCounter(),
            "acs_access_granted": DummyCounter(),
            "acs_access_denied": DummyCounter(),
            "acs_status_messages": DummyCounter(),
            "smtp_mails_sent": DummyCounter(),
        }

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.env_backup)
        if self.orig_log is None:
            delattr(service, "log")
        else:
            service.log = self.orig_log
        delattr(service, "metrics")

    def test_initialize_logger_valid_and_invalid(self):
        init_logger = getattr(service, "__initialize_logger")
        log = init_logger(logging.DEBUG)
        self.assertEqual(log.level, logging.DEBUG)

        with self.assertRaises(ValueError):
            init_logger(1234)

    def test_validate_configuration_missing_env_raises(self):
        for key in [
            "MQTT_SERVER",
            "MQTT_TOPIC_DOOR_ACCESS",
            "MQTT_TOPIC_ACS_STATUS",
            "SMTP_RECIPIENTS_ADDRESSES",
            "SMTP_PASSWORD",
            "SMTP_PASSWORD_FILE",
        ]:
            os.environ.pop(key, None)

        with self.assertRaises(ValueError):
            getattr(service, "__validate_configuration")()

    def test_validate_configuration_from_password_file(self):
        with tempfile.NamedTemporaryFile(mode="w+t", delete=False) as fp:
            fp.write("super-password")
            fp.flush()
            password_file = fp.name

        os.environ.update(
            {
                "MQTT_SERVER": "localhost",
                "MQTT_TOPIC_DOOR_ACCESS": "door/access",
                "MQTT_TOPIC_ACS_STATUS": "acs/status",
                "SMTP_RECIPIENTS_ADDRESSES": "user@example.com",
                "SMTP_PASSWORD_FILE": password_file,
            }
        )

        try:
            validate_configuration = getattr(service, "__validate_configuration")
            password = validate_configuration()
            self.assertEqual(password, "super-password")
        finally:
            os.remove(password_file)

    def test_prepare_access_message_granted_and_denied_metrics(self):
        payload_granted = {
            "user_display_name": "Alice",
            "user_id": "123",
            "entrypoint_location": "Front Door",
            "entrypoint_ip": "10.0.0.1",
            "status": "granted",
            "timestamp": "2026-03-23T12:00:00Z",
        }

        prepare_access_message = getattr(service, "__prepare_access_message")
        subject, body = prepare_access_message(payload_granted)
        self.assertIn("Alice is authorized", subject)
        self.assertIn("Access time: 2026-03-23T12:00:00Z", body)
        self.assertEqual(service.metrics["acs_access_granted"].count, 1)
        self.assertEqual(service.metrics["acs_access_granted"].label_values, {"entrypoint_ip": "10.0.0.1"})

        payload_denied = payload_granted.copy()
        payload_denied["status"] = "denied"

        subject, body = prepare_access_message(payload_denied)
        self.assertIn("not authorized", subject)
        self.assertIn("<b>not</b>", body)
        self.assertEqual(service.metrics["acs_access_denied"].count, 1)

    def test_prepare_status_message_metrics(self):
        payload = {
            "severity": "warning",
            "status": "offline",
            "description": "Alert message",
        }

        prepare_status_message = getattr(service, "__prepare_status_message")
        subject, body = prepare_status_message(payload)
        self.assertIn("WARNING offline", subject)
        self.assertIn("Alert message", body)
        self.assertEqual(service.metrics["acs_status_messages"].count, 1)
        self.assertEqual(service.metrics["acs_status_messages"].label_values, {"severity": "warning"})

    def test_on_message_unknown_topic_calls_send_email(self):
        service.metrics["mqtt_messages"].count = 0
        service.metrics["smtp_mails_sent"].count = 0

        os.environ.update(
            {
                "MQTT_TOPIC_ACS_STATUS": "acs/status",
                "MQTT_TOPIC_DOOR_ACCESS": "door/access",
                "SMTP_SUBJECT_PREFIX": "[OITC Access Control System]",
            }
        )

        message_payload = json.dumps({"timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()})
        msg = mock.Mock(topic="unknown/topic", qos=0, retain=False, payload=message_payload.encode("utf-8"))

        with mock.patch.object(service, "__send_email") as mocked_send:
            service.on_message(client=None, userdata=None, msg=msg)

        mocked_send.assert_called_once()
        self.assertEqual(service.metrics["mqtt_messages"].count, 1)


if __name__ == "__main__":
    unittest.main()
