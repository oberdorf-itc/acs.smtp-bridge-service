"""
***************************************************************************\n
test_smtp.py is a python unit test for the python class
   smtp\n
Author: Michael Oberdorf\n
Date:   2025-02-24\n
Last modified by: Michael Oberdorf\n
Last modified at: 2025-03-06\n
***************************************************************************\n
"""

__author__ = "Michael Oberdorf <michael.oberdorf@gmx.de>"
__status__ = "production"
__date__ = "2025-03-06"
__version_info__ = ("1", "0", "0")
__version__ = ".".join(__version_info__)

__all__ = ["TestSmtp"]

import logging
import sys
import unittest

from src.app.lib.smtp import mailer


class TestSmtp(unittest.TestCase):
    """
    Test smtp mail wrapper class
    """

    log = logging.getLogger()
    log_handler = logging.StreamHandler(sys.stdout)
    log_handler.setLevel(logging.CRITICAL)
    log_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    log.addHandler(log_handler)

    mailer = mailer()

    def test_instance_creation(self) -> None:
        """
        Test if the mailer instance can be created:

        Args:
            self, class: The class representation
        Raises:
            AssertionError: when the assertion failes
        Returns:
            None
        """
        self.assertIsInstance(self.mailer, mailer, msg="smtp mailer class initialization")

    def test_setMailserver(self) -> None:
        """
        Test the method setMailserver

        Args:
            self, class: The class representation
        Raises:
            AssertionError: when the assertion failes
        Returns:
            None
        """
        with self.assertRaises(TypeError):
            self.mailer.setMailserver()
        self.assertTrue(self.mailer.setMailserver(server="localhost", port=25, tls=False))

        with self.assertRaises(LookupError):
            self.mailer.setMailserver(server="notWorkingExample", port=25, tls=False)

        with self.assertRaises(Exception):
            self.mailer.setMailserver(server="localhost", port=99999, tls=False)

    def test_setSmtpAuth(self) -> None:
        """
        Test the method setSmtpAuth

        Args:
            self, class: The class representation
        Raises:
            AssertionError: when the assertion failes
        Returns:
            None
        """
        with self.assertRaises(TypeError):
            self.mailer.setSmtpAuth()
        self.assertTrue(self.mailer.setSmtpAuth(username="Foo", password="Bar"))
        self.assertFalse(self.mailer.setSmtpAuth(username="Foo", password=""))
        self.assertFalse(self.mailer.setSmtpAuth(username="", password="Bar"))

    def test_setSender(self) -> None:
        """
        Test the method setSender

        Args:
            self, class: The class representation
        Raises:
            AssertionError: when the assertion failes
        Returns:
            None
        """
        with self.assertRaises(TypeError):
            self.mailer.setSender()
        with self.assertRaises(TypeError):
            self.mailer.setSender(name="Name")
        self.assertTrue(self.mailer.setSender(mailaddress="michael.oberdorf@gmx.de"))
        self.assertTrue(self.mailer.setSender(mailaddress="michael.oberdorf@gmx.de", name=""))
        self.assertTrue(self.mailer.setSender(mailaddress="michael.oberdorf@gmx.de", name="Name"))
        self.assertFalse(self.mailer.setSender(mailaddress="notWorkingExample"))

    def test_addTo(self) -> None:
        """
        Test the method addTo

        Args:
            self, class: The class representation
        Raises:
            AssertionError: when the assertion failes
        Returns:
            None
        """
        with self.assertRaises(TypeError):
            self.mailer.addTo()
        with self.assertRaises(TypeError):
            self.mailer.addTo(name="Name")
        self.assertTrue(self.mailer.addTo(mailaddress="michael.oberdorf@gmx.de"))
        self.assertTrue(self.mailer.addTo(mailaddress="michael.oberdorf@gmx.de", name=""))
        self.assertTrue(self.mailer.addTo(mailaddress="michael.oberdorf@gmx.de", name="Name"))
        self.assertFalse(self.mailer.addTo(mailaddress="notWorkingExample"))

    def test_addCc(self) -> None:
        """
        Test the method addCc

        Args:
            self, class: The class representation
        Raises:
            AssertionError: when the assertion failes
        Returns:
            None
        """
        with self.assertRaises(TypeError):
            self.mailer.addCc()
        with self.assertRaises(TypeError):
            self.mailer.addCc(name="Name")
        self.assertTrue(self.mailer.addCc(mailaddress="michael.oberdorf@gmx.de"))
        self.assertTrue(self.mailer.addCc(mailaddress="michael.oberdorf@gmx.de", name=""))
        self.assertTrue(self.mailer.addCc(mailaddress="michael.oberdorf@gmx.de", name="Name"))
        self.assertFalse(self.mailer.addCc(mailaddress="notWorkingExample"))

    def test_addBcc(self) -> None:
        """
        Test the method addBcc

        Args:
            self, class: The class representation
        Raises:
            AssertionError: when the assertion failes
        Returns:
            None
        """
        with self.assertRaises(TypeError):
            self.mailer.addBcc()
        with self.assertRaises(TypeError):
            self.mailer.addBcc(name="Name")
        self.assertTrue(self.mailer.addBcc(mailaddress="michael.oberdorf@gmx.de"))
        self.assertTrue(self.mailer.addBcc(mailaddress="michael.oberdorf@gmx.de", name=""))
        self.assertTrue(self.mailer.addBcc(mailaddress="michael.oberdorf@gmx.de", name="Name"))
        self.assertFalse(self.mailer.addBcc(mailaddress="notWorkingExample"))

    def test_setSubject(self) -> None:
        """
        Test the method setSubject

        Args:
            self, class: The class representation
        Raises:
            AssertionError: when the assertion failes
        Returns:
            None
        """
        with self.assertRaises(TypeError):
            self.mailer.setSubject()
        self.assertTrue(self.mailer.setSubject(subject="Subject"))
        self.assertFalse(self.mailer.setSubject(subject=""))

    def test_setBody(self) -> None:
        """
        Test the method setBody

        Args:
            self, class: The class representation
        Raises:
            AssertionError: when the assertion failes
        Returns:
            None
        """
        with self.assertRaises(TypeError):
            self.mailer.setBody()
        self.assertTrue(self.mailer.setBody(body="Subject"))
        self.assertTrue(self.mailer.setBody(body=""))

    def test_addAttachment(self) -> None:
        """
        Test the method addAttachment

        Args:
            self, class: The class representation
        Raises:
            AssertionError: when the assertion failes
        Returns:
            None
        """
        with self.assertRaises(TypeError):
            self.mailer.addAttachment()
        self.assertTrue(self.mailer.addAttachment(filename=__file__))
        self.assertFalse(self.mailer.addAttachment(filename="notWorkingExample"))


if __name__ == "__main__":
    unittest.main()
