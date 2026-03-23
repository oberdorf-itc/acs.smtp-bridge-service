"""
OITC Access Control System: MQTT to SMTP Bridge
Author: Michael Oberdorf <info@oberdorf-itc.de>
Date: 2021-01-02
Copyright (c) 2021, Michael Oberdorf IT-Consulting. All rights reserved.
This software may be modified and distributed under the terms of the Apache 2.0 license. See the LICENSE file for details.
"""

import datetime
import json
import logging
import os
import socket
import ssl
import sys

import paho.mqtt.client as mqtt
import prometheus_client as prom
import pytz
from lib.smtp import mailer

__author__ = "Michael Oberdorf <info@oberdorf-itc.de>"
__status__ = "production"
__date__ = "2026-03-21"
__version_info__ = ("1", "0", "0")
__version__ = ".".join(__version_info__)

__local_tz__ = pytz.timezone(os.environ.get("TZ", "UTC"))

"""
###############################################################################
# F U N C T I O N S
###############################################################################
"""


def __initialize_logger(severity: int = logging.INFO) -> logging.Logger:
    """
    Initialize the logger with the given severity level.

    :param severity int: The optional severity level for the logger. (default: 20 (INFO))
    :return logging.RootLogger: The initialized logger.
    :raise ValueError: If the severity level is not valid.
    :raise TypeError: If the severity level is not an integer.
    :raise Exception: If the logger cannot be initialized.
    """
    valid_severity = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]
    if severity not in valid_severity:
        raise ValueError(f"Invalid severity level: {severity}. Must be one of {valid_severity}.")

    log = logging.getLogger()
    log_handler = logging.StreamHandler(sys.stdout)

    log.setLevel(severity)
    log_handler.setLevel(severity)
    log_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    log_handler.setFormatter(log_formatter)
    log.addHandler(log_handler)

    return log


def __validate_configuration() -> tuple[str, str]:
    """
    Validate the configuration from environment variables.

    :return tuple[str, str]: The validated pushover app token and user key.
    :raise ValueError: If the configuration is not valid.
    :raise Exception: If the configuration cannot be validated.
    """
    if os.environ.get("MQTT_SERVER", None) is None:
        raise ValueError("MQTT_SERVER environment variable is not set.")
    if os.environ.get("MQTT_TOPIC_DOOR_ACCESS", None) is None:
        raise ValueError("MQTT_TOPIC_DOOR_ACCESS environment variable is not set.")
    if os.environ.get("MQTT_TOPIC_ACS_STATUS", None) is None:
        raise ValueError("MQTT_TOPIC_ACS_STATUS environment variable is not set.")
    if os.environ.get("SMTP_RECIPIENTS_ADDRESSES", None) is None:
        raise ValueError("SMTP_RECIPIENTS_ADDRESSES environment variable is not set.")

    # validate and read smtp user password from environment variables or files
    __smtp_password__ = None
    if os.environ.get("SMTP_PASSWORD_FILE", None) is not None:
        if not os.path.isfile(os.environ.get("SMTP_PASSWORD_FILE", None)):
            raise ValueError(f"SMTP_PASSWORD_FILE file {os.environ.get("SMTP_PASSWORD_FILE")} not found.")
        with open(os.environ["SMTP_PASSWORD_FILE"]) as file:
            __smtp_password__ = file.read().strip().replace("\n", "")
            if __smtp_password__ == "":
                raise ValueError(f"SMTP_PASSWORD_FILE file {os.environ.get("SMTP_PASSWORD_FILE")} is empty.")
    else:
        if os.environ.get("SMTP_PASSWORD", None) is not None:
            log.debug("Use smtp password from environment variable.")
            __smtp_password__ = os.environ.get("SMTP_PASSWORD")

    return __smtp_password__


def __initialize_prometheus_exporter() -> dict:
    """
    Intialize and start the prometheus exporter endpoint

    :return The different initialized prometheus metrics as a dict of objects
    :rtype dict
    :raise Exception: If the prometheus exporter cannot be initialized or started.
    """
    log.debug("def initialize_prometheus_exporter() -> dict:")

    m = {
        "service_info": prom.Info("service_info", "Information about the service"),
        "mqtt_connects": prom.Counter("mqtt_connects", "Count all MQTT connection events"),
        "mqtt_messages": prom.Counter("mqtt_messages", "Count all received MQTT messages"),
        "mqtt_messages_refused": prom.Counter(
            "mqtt_messages_refused", "Count all refused MQTT messages due to timestamp drift."
        ),
        "acs_access_granted": prom.Counter(
            "acs_access_granted",
            "Count all access granted events received by transponders",
            labelnames=["entrypoint_ip"],
        ),
        "acs_access_denied": prom.Counter(
            "acs_access_denied", "Count all access denied events received by transponders", labelnames=["entrypoint_ip"]
        ),
        "acs_status_messages": prom.Counter(
            "acs_status_messages",
            "Count all status messages received by the access control system",
            labelnames=["severity"],
        ),
        "smtp_mails_sent": prom.Counter("smtp_mails_sent", "Count all emails sent via SMTP"),
    }

    prometheus_listener_addr = os.environ.get("PROMETHEUS_LISTENER_ADDR", "0.0.0.0")
    prometheus_listener_port = int(os.environ.get("PROMETHEUS_LISTENER_PORT", "8080"))
    log.info("Starting prometheus exporter listener: %s:%s", prometheus_listener_addr, prometheus_listener_port)
    s, t = prom.start_http_server(port=prometheus_listener_port, addr=prometheus_listener_addr)
    if not s or not t:
        raise RuntimeError("The Prometheus exporter http endpoint failed to start.")

    return m


def __initialize_mqtt_client() -> mqtt.Client:
    """
    Initialize the MQTT client with the given configuration from environment.

    :return mqtt.Client: The initialized MQTT client.
    :raise ValueError: If the MQTT client configuration is not valid.
    :raise Exception: If the MQTT client cannot be initialized.
    """
    if os.environ.get("MQTT_CLIENT_ID", None) is not None:
        log.debug("Use MQTT client ID: {}".format(os.environ.get("MQTT_CLIENT_ID", None)))

    if os.environ.get("MQTT_PROTOCOL_VERSION") == "5":
        log.debug("MQTT protocol version 5")
        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=os.environ.get("MQTT_CLIENT_ID", None),
            userdata=None,
            transport="tcp",
            protocol=mqtt.MQTTv5,
        )
    else:
        log.debug("MQTT protocol version 3.1.1")
        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=os.environ.get("MQTT_CLIENT_ID", None),
            clean_session=True,
            userdata=None,
            transport="tcp",
            protocol=mqtt.MQTTv311,
        )

    # configure TLS
    if os.environ.get("MQTT_TLS", "false").lower() == "true":
        log.debug("Configure MQTT connection to use TLS encryption.")

        __ca_cert_file__ = "/etc/ssl/certs/ca-certificates.crt"
        if os.environ.get("REQUESTS_CA_BUNDLE", None) is not None:
            __ca_cert_file__ = os.environ.get("REQUESTS_CA_BUNDLE")
        if os.environ.get("MQTT_CACERT_FILE", None) is not None:
            __ca_cert_file__ = os.environ.get("MQTT_CACERT_FILE")

        if os.environ.get("MQTT_TLS_INSECURE", "false").lower() == "true":
            log.debug("Configure MQTT connection to use TLS with insecure mode.")
            client.tls_set(
                ca_certs=__ca_cert_file__,
                cert_reqs=ssl.CERT_NONE,
                tls_version=ssl.PROTOCOL_TLSv1_2,
                ciphers=None,
            )
            client.tls_insecure_set(True)
        else:
            log.debug("Configure MQTT connection to use TLS with secure mode.")
            client.tls_set(
                ca_certs=__ca_cert_file__,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLSv1_2,
                ciphers=None,
            )
            client.tls_insecure_set(False)

    # configure authentication
    mqtt_pass = None
    if os.environ.get("MQTT_PASSWORD", None) is not None:
        mqtt_pass = os.environ.get("MQTT_PASSWORD")
    if os.environ.get("MQTT_PASSWORD_FILE", None) is not None:
        if not os.path.isfile(os.environ.get("MQTT_PASSWORD_FILE", None)):
            raise ValueError("MQTT password file {} not found.".format(os.environ.get("MQTT_PASSWORD_FILE", None)))
        with open(os.environ.get("MQTT_PASSWORD_FILE", None)) as f:
            mqtt_pass = f.read().strip().replace("\n", "")
    if os.environ.get("MQTT_USERNAME", None) is not None and mqtt_pass is not None:
        log.debug("Set username ({}) and password for MQTT connection".format(os.environ.get("MQTT_USERNAME", None)))
        client.username_pw_set(os.environ.get("MQTT_USERNAME", None), mqtt_pass)

    # register callback functions
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_subscribe = on_subscribe

    return client


def on_connect(client: mqtt.Client, userdata: dict, flags: dict, rc: int, properties: mqtt.Properties) -> None:
    """
    on_connect - The MQTT callback for when the client receives a CONNACK response from the server.

    :param client: The object of the MQTT connection
    :type client: paho.mqtt.client.Client
    :param userdata: the user data of the MQTT connection
    :type userdata: dict
    :param flags: connection parameters
    :type flags: dict
    :param rc: the return code
    :type rc: int
    :return None
    """
    log.debug(f"MQTT client connected with result code {rc}")
    log.debug(f"MQTT connection flags: {flags}")
    log.debug(f"MQTT connection userdata: {userdata}")
    log.debug(f"MQTT connection properties: {properties}")

    metrics["mqtt_connects"].inc()

    # check for return code
    if rc != 0:
        log.error(f"Error in connecting to MQTT Server, RC={rc}")
        sys.exit(1)

    # Subscribing in on_connect() means that if we lose the connection and reconnect then subscriptions will be renewed.
    for topic in [os.environ.get("MQTT_TOPIC_DOOR_ACCESS", None), os.environ.get("MQTT_TOPIC_ACS_STATUS", None)]:
        log.debug(f"MQTT client subscribing to topic: {topic}")
        client.subscribe(topic)


def on_subscribe(
    client: mqtt.Client, userdata: dict, mid: int, reason_code_list: list, properties: mqtt.Properties
) -> None:
    """
    on_subscribe - The MQTT callback for when the client receives a SUBACK response from the server.

    :param client: The object of the MQTT connection
    :type client: paho.mqtt.client.Client
    :param userdata: the user data of the MQTT connection
    :type userdata: dict
    :param mid: the message ID of the subscribe request
    :type mid: int
    :param reason_code_list: the list of reason codes for the subscribe request
    :type reason_code_list: list
    :param properties: the MQTT properties of the subscribe response
    :type properties: paho.mqtt.client.MQTTProperties
    :return None
    """
    log.debug(
        f"MQTT client received SUBACK for message ID {mid} with reason codes {reason_code_list} and properties {properties}"
    )
    log.debug(f"MQTT client userdata: {userdata}")
    if reason_code_list[0].is_failure:
        log.error(f"Broker rejected you subscription: {reason_code_list[0]}")
    else:
        log.debug(f"Broker granted the following QoS: {reason_code_list[0].value}")


def on_message(client: mqtt.Client, userdata: dict, msg: mqtt.MQTTMessage) -> None:
    """
    on_message - The MQTT callback for when a PUBLISH message is received from the server.

    :param client: the object of the MQTT connection
    :type client: paho.mqtt.client.Client
    :param userdata: the user data of the MQTT connection
    :type userdata: dict
    :param msg: the object of the MQTT message received
    :type msg: paho.mqtt.client.MQTTMessage
    :return None
    """
    log.debug(f"MQTT message received on topic {msg.topic} with QoS {msg.qos} and retain flag {msg.retain}")
    metrics["mqtt_messages"].inc()

    # parse message payload as JSON object
    PAYLOAD = json.loads(str(msg.payload.decode("utf-8")))
    log.debug(f"MQTT message payload: {PAYLOAD}")

    # parse timestamp from payload and compare with current time to check if message is not too old (older than 10 seconds)
    timestamp = PAYLOAD.get("timestamp", None)
    if timestamp:
        # Convert timestamp to datetime object
        msg_timestamp = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        # Get current time
        current_time = datetime.datetime.now(__local_tz__)
        # Check if message is older than 10 seconds
        if (current_time - msg_timestamp).total_seconds() > 10:
            log.warning(f"MQTT message is too old: {timestamp}")
            metrics["mqtt_messages_refused"].inc()
            return

    if not PAYLOAD.get("notification", True) and os.environ.get("SMTP_SEND_MAIL_BY_DEFAULT", "false").lower() != "true":
        log.debug(
            "MQTT message has notification flag set to false and SMTP_SEND_MAIL_BY_DEFAULT is not true, skipping email sending."
        )
        metrics["mqtt_messages_refused"].inc()
        return

    if mqtt.topic_matches_sub(os.environ.get("MQTT_TOPIC_ACS_STATUS", None), msg.topic):
        subject, body = __prepare_status_message(PAYLOAD)
    elif mqtt.topic_matches_sub(os.environ.get("MQTT_TOPIC_DOOR_ACCESS", None), msg.topic):
        subject, body = __prepare_access_message(PAYLOAD)
    else:
        subject = os.environ.get("SMTP_SUBJECT_PREFIX", "[OITC Access Control System]")
        subject += " Unknown message type"
        body = f"Received message on topic {msg.topic} with payload {PAYLOAD}"

    # Send email via SMTP with subject and body
    __send_email(subject, body)


def __prepare_access_message(payload: dict) -> tuple[str, str]:
    """
    Prepare the message to be sent to smtp based on the payload of the MQTT message received.

    :param payload: The payload of the MQTT message received.
    :type payload: dict
    :return tuple[str, str]: The formatted subject and body to be sent to smtp.
    """

    # prepare smtp message subject
    subject = os.environ.get("SMTP_SUBJECT_PREFIX", "[OITC Access Control System]")
    subject += " " + payload.get("user_display_name", "Unknown User") + " is "
    if payload.get("status") != "granted":
        subject += "not "
    subject += "authorized to access resource at " + payload.get("timestamp", "Unknown Time")

    # prepare smtp message
    body = (
        "User: "
        + payload.get("user_display_name", "Unknown User")
        + " ("
        + payload.get("user_id", "Unknown ID")
        + ")"
        + "\n"
    )
    body += "Entrypoint: " + payload.get("entrypoint_location", "Unknown Entrypoint") + "\n"
    body += "is "
    if payload.get("status") != "granted":
        body += "<b>not</b> "
    body += "authorized to access resource" + "\n"
    body += "Access time: " + payload.get("timestamp", "Unknown Time")

    # increment appropriate metric
    if payload.get("status") == "granted":
        metrics["acs_access_granted"].labels(entrypoint_ip=payload.get("entrypoint_ip", "unknown")).inc()
    else:
        metrics["acs_access_denied"].labels(entrypoint_ip=payload.get("entrypoint_ip", "unknown")).inc()

    return subject, body


def __prepare_status_message(payload: dict) -> tuple[str, str]:
    """
    Prepare the message to be sent to smtp based on the payload of the MQTT message received.

    :param payload: The payload of the MQTT message received.
    :type payload: dict
    :return tuple[str, str]: The formatted subject and body to be sent to smtp.
    """
    # set message priority to 1 if acs status is not ok, otherwise 0
    severity = payload.get("severity", "unknown").lower().strip()
    if severity == "info":
        pass
    elif severity == "warning":
        pass
    elif severity == "error":
        pass
    else:
        pass

    # prepare smtp message subject
    subject = os.environ.get("SMTP_SUBJECT_PREFIX", "[OITC Access Control System]")
    subject += f" {severity.upper()} {payload.get('status', '')}"

    # prepare smtp message
    body = payload.get("description", "No message provided.") + "\n"

    # metrics
    metrics["acs_status_messages"].labels(severity=severity).inc()

    return subject, body


def __send_email(subject: str, body: str) -> None:
    """
    Send an email via SMTP with the given subject and body.

    :param subject: The subject of the email to be sent.
    :type subject: str
    :param body: The body of the email to be sent.
    :type body: str
    :return None
    :raise Exception: If the email cannot be sent.
    """
    mailWrapper = mailer()
    __smtp_tls__ = False
    if os.environ.get("SMTP_TLS", "false").lower() == "true":
        __smtp_tls__ = True
    # __smtp_tls_insecure__ = os.environ.get("SMTP_TLS_INSECURE", "false").lower() == "true"
    mailWrapper.setMailserver(
        server=os.environ.get("SMTP_SERVER", "localhost"), port=int(os.environ.get("SMTP_PORT", 25)), tls=__smtp_tls__
    )
    if os.environ.get("SMTP_USERNAME", None) and __smtp_password__:
        mailWrapper.setSmtpAuth(username=os.environ.get("SMTP_USERNAME", None), password=__smtp_password__)
    mailWrapper.setSender(mailaddress=os.environ.get("SMTP_SENDER_ADDRESS", f"acs@{socket.gethostname()}"))
    mailWrapper.setSubject(subject=subject)
    mailWrapper.setBody(body=body)

    for __smtp_recipient_address__ in os.environ.get("SMTP_RECIPIENTS_ADDRESSES", None).lower().split(","):
        mailWrapper.addTo(mailaddress=__smtp_recipient_address__.strip())

    mailWrapper.send()
    metrics["smtp_mails_sent"].inc()
    log.debug(f"SMTP email sent successfully with subject: {subject}")


"""
###############################################################################
# M A I N
###############################################################################
"""
if __name__ == "__main__":
    # initialize logger
    if os.getenv("DEBUG", "false").lower() == "true":
        log = __initialize_logger(logging.DEBUG)
    else:
        log = __initialize_logger(logging.INFO)
    log.info(f"Starting OITC Access Control System SMTP bridge service version {__version__}")

    # validate configuration
    __smtp_password__ = __validate_configuration()

    # initialize prometheus exporter
    metrics = __initialize_prometheus_exporter()
    metrics["service_info"].info(
        {
            "version": __version__,
            "author": __author__,
            "status": __status__,
            "timezone": __local_tz__.zone,
        }
    )

    # Initialize MQTT client
    client = __initialize_mqtt_client()
    log.debug("MQTT client initialized")
    # connect to MQTT server
    log.debug(
        "Connecting to MQTT server {}:{}".format(
            os.environ.get("MQTT_SERVER", "localhost"), os.environ.get("MQTT_PORT", 1883)
        )
    )
    try:
        client.connect(os.environ.get("MQTT_SERVER", "localhost"), int(os.environ.get("MQTT_PORT", 1883)), 60)
    except ssl.SSLCertVerificationError as e:
        log.error("SSL certificate verification error: {}".format(e))
        sys.exit(1)
    log.debug("Connected to MQTT server")

    client.loop_forever()

    client.disconnect()

    log.info(f"Stopping OITC Access Control System SMTP bridge service version {__version__}")
    sys.exit()
