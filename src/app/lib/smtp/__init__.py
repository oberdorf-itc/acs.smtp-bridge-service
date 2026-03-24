"""
OITC Access Control System: MQTT to SMTP Bridge
Author: Michael Oberdorf <info@oberdorf-itc.de>
Date: 2024-12-09
Copyright (c) 2024, Michael Oberdorf IT-Consulting. All rights reserved.
This software may be modified and distributed under the terms of the Apache 2.0 license. See the LICENSE file for details.
"""

__author__ = "Michael Oberdorf <michael.oberdorf@gmx.de>"
__status__ = "production"
__date__ = "2026-03-23"
__version_info__ = ("1", "0", "2")
__version__ = ".".join(__version_info__)

__all__ = ["mailer"]

import logging
import os

# smtplib provides functionality to send emails using SMTP.
import smtplib
import socket

# MIMEApplication attaching application-specific data (like CSV files) to email messages.
from email.mime.application import MIMEApplication

# MIMEMultipart send emails with both text content and attachments.
from email.mime.multipart import MIMEMultipart

# MIMEText for creating body of the email message.
from email.mime.text import MIMEText

# format addresses with name text and smtp address
from email.utils import formataddr, parseaddr

log = logging.getLogger()


class mailer:
    """
    Wrapper class to send emails
    """

    script_path = os.path.dirname(__file__)

    def __init__(self):
        """
        Class initializer - register class attributes and initializes default values
        """
        log.debug("Init class")
        self.smtp_server: str = "localhost"
        self.smtp_port: int = 25
        self.smtp_useTLS: bool = False
        self.use_server_login = False
        self.smtp_user: str = None
        self.smtp_pass: str = None
        self.smtp_from: str = None
        self.smtp_to: list[str] = list()
        self.smtp_cc: list[str] = list()
        self.smtp_bcc: list[str] = list()
        self.smtp_subject: str = None
        self.smtp_body: str = None
        self.smtp_attachments: list[str] = list()

    def setMailserver(self, server: str, port: int = 25, tls: bool = False) -> bool:
        """
        setMailserver - configure the mailserver

        :param server: The SMTP server to send the mail to
        :type server: str
        :param port: The SMTP TCP port (default: 25)
        :type port: int
        :param tls: Using TLS to connect to the server  (default: false)
        :type tls: bool
        :return bool: True if configuration was successful
        :raise LookupError: If the given server is not resolveable
        :raise Exception: If the TCP port is out of range
        """
        log.debug(f"def setMailserver(self, server: str = {server}, port: int = {port}, tls: bool = {tls}) -> bool:")
        try:
            socket.gethostbyaddr(server)
        except Exception as resolutionError:
            raise LookupError(resolutionError)
        log.debug(f"Set SMTP server to: {server}")
        self.smtp_server = server

        if not 1 <= port <= 65535:
            raise Exception(f"Given SMTP port {port} is out of TCP port range.")
        log.debug(f"Set SMTP TCP port to: {port}")
        self.smtp_port = port

        log.debug(f"Enable TLS encrypted communication: {tls}")
        self.smtp_useTLS = tls

        return True

    def setSmtpAuth(self, username: str, password: str) -> bool:
        """
        setSmtpAuth - Store credentials for SMTP authentication

        :param username: The username to authenticate to the SMTP server
        :type username: str
        :param password: The password to authenticate to the SMTP server
        :type password: str
        :return bool: True if configuration was successful
        """
        log.debug(f"def setSmtpAuth(self, username: str = {username}, password: str = ***) -> bool:")

        if username == "":
            log.error("Given username is an empty string!")
            return False
        self.smtp_user = username

        if password == "":
            log.error("Given password is an empty string!")
            return False
        self.smtp_pass = password
        self.use_server_login = True
        return True

    def setSender(self, mailaddress: str, name: str = None) -> bool:
        """
        setSender - set the from mail address

        :param mailaddress: The mailaddress of the SMTP sender
        :type mailaddress: str
        :param name: The name of the SMTP sender (default: None)
        :type name: str
        :return bool: True if configuration was successful
        """
        log.debug(f"def setSender(self, mailaddress: str = {mailaddress}, name: str = {name}) -> bool:")

        if "@" not in parseaddr(mailaddress)[1]:
            log.error(f"Given Mailaddress {mailaddress} is not paraseable!")
            return False
        if name and name != "":
            self.smtp_from = formataddr((name, mailaddress))
            log.debug(f"Formatted SMTP address: {self.smtp_from}")
        else:
            self.smtp_from = mailaddress
        return True

    def addTo(self, mailaddress: str, name: str = None) -> bool:
        """
        setTo - add a to address (can be called multiple times)

        :param mailaddress: The mailaddress of the SMTP "to" receiver
        :type mailaddress: str
        :param name: The name of the SMTP "to" receiver (default: None)
        :type name: str
        :return bool: True if configuration was successful
        """
        log.debug(f"def addTo(self, mailaddress: str = {mailaddress}, name: str = {name}) -> bool:")

        if "@" not in parseaddr(mailaddress)[1]:
            log.error(f"Given Mailaddress {mailaddress} is not paraseable!")
            return False
        smtp_address = mailaddress

        if name and name != "":
            smtp_address = formataddr((name, mailaddress))
            log.debug(f"Formatted SMTP address: {smtp_address}")

        log.debug(f'Append mailaddress "{smtp_address}" to list.')
        self.smtp_to.append(smtp_address)
        return True

    def addCc(self, mailaddress: str, name: str = None) -> bool:
        """
        setCc - add a CC address (can be called multiple times)

        :param mailaddress: The mailaddress of the SMTP "cc" receiver
        :type mailaddress: str
        :param name: The name of the SMTP "cc" receiver (default: None)
        :type name: str
        :return bool: True if configuration was successful
        """
        log.debug(f"def addCc(self, mailaddress: str = {mailaddress}, name: str = {name}) -> bool:")

        if "@" not in parseaddr(mailaddress)[1]:
            log.error(f"Given Mailaddress {mailaddress} is not paraseable!")
            return False
        smtp_address = mailaddress
        if name and name != "":
            smtp_address = formataddr((name, mailaddress))
            log.debug(f"Formatted SMTP address: {smtp_address}")

        log.debug(f'Append mailaddress "{smtp_address}" to list.')
        self.smtp_cc.append(smtp_address)
        return True

    def addBcc(self, mailaddress: str, name: str = None) -> bool:
        """
        setBcc - add a BCC address (can be called multiple times)

        :param mailaddress: The mailaddress of the SMTP "bcc" receiver
        :type mailaddress: str
        :param name: The name of the SMTP "bcc" receiver (default: None)
        :type name: str
        :return bool: True if configuration was successful
        """
        log.debug(f"def addBcc(self, mailaddress: str = {mailaddress}, name: str = {name}) -> bool:")

        if "@" not in parseaddr(mailaddress)[1]:
            log.error(f"Given Mailaddress {mailaddress} is not paraseable!")
            return False
        smtp_address = mailaddress
        if name and name != "":
            smtp_address = formataddr((name, mailaddress))
            log.debug(f"Formatted SMTP address: {smtp_address}")

        log.debug(f'Append mailaddress "{smtp_address}" to list.')
        self.smtp_bcc.append(smtp_address)
        return True

    def setSubject(self, subject: str) -> bool:
        """
        setSubject - set the mail subject

        :param subject: The mail subject
        :type subject: str
        :return bool: True if configuration was successful
        """
        log.debug(f"def setSubject(self, subject: str = {subject}) -> bool:")

        if subject == "":
            log.error("Given subject is an empty string!")
            return False
        self.smtp_subject = subject
        return True

    def setBody(self, body: str):
        """
        setBody - set a mail body

        :param body: The mail text body
        :type body: str
        :return bool: True if configuration was successful
        """
        log.debug(f"def setBody(self, body: str = {body}) -> bool:")

        if body == "":
            log.warning("Given body is an empty string!")
        self.smtp_body = body
        return True

    def addAttachment(self, filename: str) -> bool:
        """
        addAttachment - adding a file as mail attachment

        :param filename: The path to the file to attach to the mail
        :type filename: str
        :return bool: True if configuration was successful
        """
        log.debug(f"def addAttachment(self, filename: str = {filename}) -> bool:")
        # convert relative paths to absolute paths
        if not filename.startswith("./") and not filename.startswith("/"):
            filename = "./" + filename
        if filename.startswith("./"):
            log.debug(f"Releative path found: {filename}")
            filename = self.script_path + filename[1:]
            log.debug(f"Absolute path is: {filename}")

        if not os.path.isfile(filename):
            log.error(f"File not found exception for: {filename}")
            return False

        log.debug(f'Attach file: "{filename}" to mail')
        self.smtp_attachments.append(filename)
        return True

    def send(self):
        """
        send - sending the mail
        """
        message = MIMEMultipart()
        message["Subject"] = self.smtp_subject
        message["From"] = self.smtp_from
        message["To"] = ",".join(self.smtp_to)
        message["Cc"] = ",".join(self.smtp_cc)
        # message['Bcc'] = ','.join(self.smtp_bcc)
        body_part = MIMEText(self.smtp_body)
        message.attach(body_part)

        # Attach files
        if len(self.smtp_attachments) > 0:
            for filename in self.smtp_attachments:
                with open(filename, "rb") as file:
                    message.attach(MIMEApplication(file.read(), Name=os.path.basename(filename)))

        # connect to the SMTP Server and send mail
        if self.smtp_useTLS:
            with smtplib.SMTP_SSL(host=self.smtp_server, port=self.smtp_port) as server:
                if self.use_server_login:
                    server.login(user=self.smtp_user, password=self.smtp_pass)
                to_addrs = self.smtp_to + self.smtp_cc + self.smtp_bcc
                log.debug(f"Sending E-Mail to: {to_addrs}")
                server.sendmail(from_addr=self.smtp_from, to_addrs=to_addrs, msg=message.as_string())
        else:
            with smtplib.SMTP(host=self.smtp_server, port=self.smtp_port) as server:
                if self.use_server_login:
                    server.login(user=self.smtp_user, password=self.smtp_pass)
                to_addrs = self.smtp_to + self.smtp_cc + self.smtp_bcc
                log.debug(f"Sending E-Mail to: {to_addrs}")
                result = server.sendmail(from_addr=self.smtp_from, to_addrs=to_addrs, msg=message.as_string())
                server.quit()
                if result:
                    log.error(f"Errors occurred while sending email: {result}")
