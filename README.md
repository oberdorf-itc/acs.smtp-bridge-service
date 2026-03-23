# OITC Access Control System: SMTP bridge service

## Quick reference

Maintained by: [Michael Oberdorf IT-Consulting](https://www.oberdorf-itc.de/)

Source code: [GitHub](https://github.com/oberdorf-itc/acs.smtp-bridge-service)

Container image: [DockerHub](https://hub.docker.com/r/oitc/acs.smtp-bridge-service)

Access Control System documentation: [ACS Documentation](https://github.com/oberdorf-itc/acs.documentation/tree/main)

<!-- SHIELD GROUP -->
[![][github-action-test-shield]][github-action-test-link]
[![][github-action-release-shield]][github-action-release-link]
[![][github-release-shield]][github-release-link]
[![][github-releasedate-shield]][github-releasedate-link]
[![][github-stars-shield]][github-stars-link]
[![][github-forks-shield]][github-forks-link]
[![][github-issues-shield]][github-issues-link]
[![][github-license-shield]][github-license-link]

[![][docker-release-shield]][docker-release-link]
[![][docker-pulls-shield]][docker-pulls-link]
[![][docker-stars-shield]][docker-stars-link]
[![][docker-size-shield]][docker-size-link]

## Supported tags and respective `Dockerfile` links

* [`latest`, `1.0.0`](https://github.com/oberdorf-itc/acs.smtp-bridge-service/blob/v1.0.0/Dockerfile)

## Description

This service is part of the Michael Oberdorf IT-Consulting (OITC) Access Control System (ACS).

On accessing entry points, this information is available in the internal bus system. This service listens on these events and send them via Mail.

This service is *NO* standalone service. It requires an OITC ACS system to be running.

## Configuration

### Container configuration

The container get's the configuration from environment variables.

| Variable name               | Description                                                                                     | Required      | Default value                        |
|-----------------------------|-------------------------------------------------------------------------------------------------|---------------|--------------------------------------|
| `MQTT_SERVER`               | The MQTT server hostname or IP address.                                                         | OPTIONAL      | `localhost`                          |
| `MQTT_PORT`                 | The TCP port of the MQTT server.                                                                | OPTIONAL      | `1883`                               |
| `MQTT_PROTOCOL_VERSION`     | The MQTT protocol version to use. Currently supported `3` (means 3.1.1) and `5`.                | OPTIONAL      | `3`                                  |
| `MQTT_TLS`                  | Should SSL communication be enabled (`true`) or not (`false`).                                  | OPTIONAL      | `false`                              |
| `MQTT_CACERT_FILE`          | If TLS is enabled, the path to the CA certificate file to validate the MQTT server certificate. | OPTIONAL      | `/etc/ssl/certs/ca-certificates.crt` |
| `MQTT_TLS_INSECURE`         | If TLS is enabled, skip the hostname validation of the TLS certificate.                         | OPTIONAL      | `false`                              |
| `MQTT_CLIENT_ID`            | The MQTT client id to use for the MQTT connection.                                              | OPTIONAL      |                                      |
| `MQTT_USERNAME`             | The MQTT username for MQTT authentication.                                                      | OPTIONAL      |                                      |
| `MQTT_PASSWORD`             | The MQTT password for MQTT authentication.                                                      | OPTIONAL      |                                      |
| `MQTT_PASSWORD_FILE`        | The filepath where the MQTT password is stored for MQTT authentication.                         | OPTIONAL      |                                      |
| `MQTT_TOPIC_ACS_STATUS`     | The MQTT topic to subscribe that contains the status messages of the ACS.                       | **MANDATORY** |                                      |
| `MQTT_TOPIC_DOOR_ACCESS`    | The MQTT topic to subscribe that contains the door access information.                          | **MANDATORY** |                                      |
| `SMTP_SERVER`               | The SMTP mailserver.                                                                            | OPTIONAL      | `localhost`                          |
| `SMTP_PORT`                 | The SMTP mailserver TCP port.                                                                   | OPTIONAL      | `25`                                 |
| `SMTP_TLS`                  | Should SSL communication be enabled (`true`) or not (`false`).                                  | OPTIONAL      | `false`                              |
| `SMTP_TLS_INSECURE`         | If TLS is enabled, skip the hostname validation of the TLS certificate.                         | OPTIONAL      | `false`                              |
| `SMTP_USERNAME`             | The SMTP username for SMTP authentication.                                                      | OPTIONAL      |                                      |
| `SMTP_PASSWORD`             | The SMTP password for SMTP authentication.                                                      | OPTIONAL      |                                      |
| `SMTP_PASSWORD_FILE`        | The filepath where the SMTP password is stored for SMTP authentication.                         | OPTIONAL      |                                      |
| `SMTP_SENDER_ADDRESS`       | The envelope sender address.                                                                    | OPTIONAL      | `acs@<hostname>`                     |
| `SMTP_RECIPIENTS_ADDRESSES` | Comma separated list of SMTP recipents.                                                         | **MANDATORY** |                                      |
| `SMTP_SUBJECT_PREFIX`       | A prefic that will be always added to the SMTP subject.                                         | OPTIONAL      | `[OITC Access Control System]`       |
| `SMTP_SEND_MAIL_BY_DEFAULT` | Overwrite send mail configuration and always send a mail notification.                          | OPTIONAL      | `false`                              |
| `PROMETHEUS_LISTENER_ADDR`  | The listener address to expose the prometheus exporter.                                         | OPTIONAL      | `0.0.0.0`                            |
| `PROMETHEUS_LISTENER_PORT`  | The TCP listener port to expose the prometheus exporter.                                        | OPTIONAL      | `8080`                               |
| `TZ`                        | Timezone                                                                                        | OPTIONAL      | `UTC`                                |

**HINT:**

* `MQTT_PASSWORD_FILE` will be priorized before `MQTT_PASSWORD`
* `SMTP_PASSWORD_FILE` will be priorized before `SMTP_PASSWORD`

## Docker compose configuration

```yaml
services:
  smtp-bridge-service:
    restart: always
    user: 2200:2200
    image: oitc/acs.smtp-bridge-service:latest
    environment:
      MQTT_SERVER: test.mosquitto.org
      MQTT_PORT: 1883
      MQTT_PROTOCOL_VERSION: 3
      MQTT_TOPIC_ACS_STATUS: location/oitc-acs/general/status
      MQTT_TOPIC_DOOR_ACCESS: location/oitc-acs/entrypoints/+/access
      SMTP_RECIPIENTS_ADDRESSES: "noreply@example.com"
```

A bigger example can be found here: [`docker-compose.yaml`](./docker-compose.yaml)

## MQTT message formats

Please have a look to the main documentation: [MQTT message reference](https://github.com/oberdorf-itc/acs.documentation/blob/main/docs/mqtt-message-reference.md)

## Donate

I would appreciate a small donation to support the further development of my open source projects.

[![Donate with PayPal][donate-paypal-button]][donate-paypal-link]

<!-- LINK GROUP -->
[docker-pulls-link]: https://hub.docker.com/r/oitc/acs.smtp-bridge-service
[docker-pulls-shield]: https://img.shields.io/docker/pulls/oitc/acs.smtp-bridge-service?color=45cc11&labelColor=black&style=flat-square
[docker-release-link]: https://hub.docker.com/r/oitc/acs.smtp-bridge-service
[docker-release-shield]: https://img.shields.io/docker/v/oitc/acs.smtp-bridge-service?color=369eff&label=docker&labelColor=black&logo=docker&logoColor=white&style=flat-square
[docker-size-link]: https://hub.docker.com/r/oitc/acs.smtp-bridge-service
[docker-size-shield]: https://img.shields.io/docker/image-size/oitc/acs.smtp-bridge-service?color=369eff&labelColor=black&style=flat-square
[docker-stars-link]: https://hub.docker.com/r/oitc/acs.smtp-bridge-service
[docker-stars-shield]: https://img.shields.io/docker/stars/oitc/acs.smtp-bridge-service?color=45cc11&labelColor=black&style=flat-square
[donate-paypal-button]: https://raw.githubusercontent.com/cybcon/paypal-donate-button/refs/heads/master/paypal-donate-button_200x77.png
[donate-paypal-link]: https://www.paypal.com/donate/?hosted_button_id=BHGJGGUS6RH44
[github-action-release-link]: https://github.com/oberdorf-itc/acs.smtp-bridge-service/actions/workflows/release-from-label.yaml
[github-action-release-shield]: https://img.shields.io/github/actions/workflow/status/oberdorf-itc/acs.smtp-bridge-service/release-from-label.yaml?label=release&labelColor=black&logo=githubactions&logoColor=white&style=flat-square
[github-action-test-link]: https://github.com/oberdorf-itc/acs.smtp-bridge-service/actions/workflows/test.yaml
[github-action-test-shield]: https://img.shields.io/github/actions/workflow/status/oberdorf-itc/acs.smtp-bridge-service/test.yaml?label=tests&labelColor=black&logo=githubactions&logoColor=white&style=flat-square
[github-forks-link]: https://github.com/oberdorf-itc/acs.smtp-bridge-service/network/members
[github-forks-shield]: https://img.shields.io/github/forks/oberdorf-itc/acs.smtp-bridge-service?color=8ae8ff&labelColor=black&style=flat-square
[github-issues-link]: https://github.com/oberdorf-itc/acs.smtp-bridge-service/issues
[github-issues-shield]: https://img.shields.io/github/issues/oberdorf-itc/acs.smtp-bridge-service?color=ff80eb&labelColor=black&style=flat-square
[github-license-link]: https://github.com/oberdorf-itc/acs.smtp-bridge-service/blob/main/LICENSE
[github-license-shield]: https://img.shields.io/badge/license-MIT-blue?labelColor=black&style=flat-square
[github-release-link]: https://github.com/oberdorf-itc/acs.smtp-bridge-service/releases
[github-release-shield]: https://img.shields.io/github/v/release/oberdorf-itc/acs.smtp-bridge-service?color=369eff&labelColor=black&logo=github&style=flat-square
[github-releasedate-link]: https://github.com/oberdorf-itc/acs.smtp-bridge-service/releases
[github-releasedate-shield]: https://img.shields.io/github/release-date/oberdorf-itc/acs.smtp-bridge-service?labelColor=black&style=flat-square
[github-stars-link]: https://github.com/oberdorf-itc/acs.smtp-bridge-service
[github-stars-shield]: https://img.shields.io/github/stars/oberdorf-itc/acs.smtp-bridge-service?color=ffcb47&labelColor=black&style=flat-square
