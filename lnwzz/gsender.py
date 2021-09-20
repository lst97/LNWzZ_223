"""Gmail SMTP API module"""

import smtplib
import ssl
import os
import time

from dotenv import load_dotenv

from utils.debug import dbg
from database import smtp


load_dotenv()

LOG = dbg("[gsmtpAPI]")


class gsmtp:
    """Send email using deakinit.dc@gmail.com with SSL enabled.

    Attributes:
        _contex: ssl context.
        _smtp_server: smtp server for Gmail. -- smtp.gmail.com
        _sender_email: sender Gmail address. -- deakinit.dc@gmail.com
        _reciver_email = reciver email address.
        _message = message to be sent, subject included.
        _password = password for deakinit.dc@gmail.com
        _port = port number for smtp.gmail.com
    """

    def __init__(
        self,
        receiver: str,
        subject="Subject: DEBUG - Default Message",
        message="This message is send from Pythoh.",
    ) -> None:

        self._context = ssl.create_default_context()
        self._smtp_server = "smtp.gmail.com"
        self._port = 465
        self._sender_email = "deakinit.dc@gmail.com"
        self._password = os.getenv("EMAIL_PASSWORD")
        self._reciver_email = receiver
        self._message = f"""{subject}\n{message}"""

    def send_otp(self) -> str:
        """Send OTP to specified email address with prefix messages.

        >>> self.write_message("Email Verify - DeakinIT.dc", f"Your code: {str(otp)}")

        Returns:
            bool:
                True: database and email operation success.
                False: failied database or email operation after 3 attempts.
        """
        # generate OTP with secure way
        otp = None

        db_smtp = smtp()
        LOG.print("Sending OTP...")

        message = "Email Verify - DeakinIT.dc" + f"Your code: {str(otp)}"
        if self.send(message=message) is not True and db_smtp.insert_otp(otp) is not True:
            LOG.print("Failied database or email operation", status="critical")
            return False

        LOG.print("OTP Send.")
        return True

    def send(self, message=None) -> bool:
        """Send custom email to specified email.

        Returns:
            bool:
                True: email successfully send.
                False: email fail to send after 3 attempts.
        """
        for attempts in range(3):
            try:
                with smtplib.SMTP_SSL(
                    self._smtp_server, self._port, context=self._context
                ) as server:
                    server.login(self._sender_email, self._password)

                    if message is None:
                        message = self._message
                    server.sendmail(self._sender_email, self._reciver_email, message)

                    break

            except smtplib.SMTPResponseException as ex:
                if isinstance(ex, smtplib.SMTPHeloError):
                    time.sleep(1)
                    LOG.print("No reply from smtp server, retring...")

                    if attempts == 2:
                        LOG.print("Email fail to send!", "critical")
                        return False
                else:
                    LOG.print(str(ex), "critical")
                    return False

        LOG.print("Email send.")
        return True

    def write_message(self, subject: str, message: str) -> None:
        """Write message to buffer and waiting to be send.

        Args:
            subject: email subject.
            message: email content.
        """
        self._message = f"""Subject: {subject}\n{message}"""
