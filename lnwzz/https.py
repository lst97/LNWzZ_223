"""Controller module

Entry point, runing the HTTPS controller server.
"""

from utils.debug import dbg
from dcapi import api
from gsender import gsmtp
from database import db

from cryptography import fernet

from aiohttp import web
from aiohttp_session import setup, get_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage

import ssl
import base64
import os


LOG = dbg("[controller]")
SSL_CTX = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
PARENT_PATH = os.path.dirname(__file__)
SSL_CTX.load_cert_chain(
    PARENT_PATH + "/domain/domain_srv.crt", PARENT_PATH + "/domain/domain_srv.key"
)

# TODO only avaliable after login (using cookie)


async def join(request: web.Request):
    text = "Join Detected: " + request.query["email"]
    LOG.print(text)
    # 0. Contact DiscordBot API to send One Time Invite Link
    discord_api = api()
    # 1. React base on feedback from Discord
    if discord_api.ivlink():
        database = db()
        database.query()
        # database.#TODO

    # 2. Get the Invite link from SQL and Post to Client
    return web.Response(text=request.query["email"])


# TODO Cookies
# https://us-pycon-2019-tutorial.readthedocs.io/aiohttp_session.html


async def login(request: web.Request):
    # 0. Contact SQL if it registed
    # 1. Compare User name && password
    text = "Login Atteptemed"
    LOG.print(text, status="info")

    session = await get_session(request)

    if "username" in session:
        LOG.print("Use Cookie")
        text = f"Logged in as [{session['username']}]"
    else:
        # Only for demo Need SQL
        LOG.print("Creating Cookie...")
        try:
            LOG.print("Identity Check...")
            if (
                request.query["email"] == "test@deakin.edu.au"
                and request.query["pwd"] == "1234"
            ):
                session["username"] = request.query["email"]
                session["role"] = 0  # base on SQL, 0: admin, 1: member

                text = "Logged in as {}".format(session["username"])
                LOG.print("Login SUCCESS.", status="info")
            else:
                LOG.print("Login FAIL.", status="warning")
                text = "Invalid Username or Password"
        except:
            LOG.print("Guest Session.")
            text = "You must First Loggin!"

    LOG.print(text)
    return web.Response(text=text)


async def logout(request: web.Request):
    # 0. Contact SQL if it registed
    # 1. Compare User name && password
    text = "Login Detected."
    LOG.print(text, status="info")

    session = await get_session(request)
    role = session["role"] if "role" in session else None
    session["role"] = 0
    text = "Logged in as {}".format(role)
    LOG.print(text)
    return web.Response(text=text)


async def register(request: web.Request):
    # 0. Contact Database if already registed
    # 1. Contact Email Server to send OTP
    # 2. React base on feedback from Email Server (Use IPC or TCP/UDP?)
    # 3. Wait for OTP confirm from client
    # 4. Add user into Database

    # TODO Database needs to delete outdated OTP query.
    text = "Register Detected."
    email_sender = gsmtp(request.query["email"])
    
    if email_sender.send_otp():
        LOG.print(text)
    return web.Response(text=text)


async def feedback(request: web.Request):
    text = "Feedback Detected."
    LOG.print(text, status="info")
    return web.Response(text=text)

async def panel(request: web.Request):
    text = "Panel Detected."
    LOG.print(text, status="info")
    
    LOG.print("Use Cookie")
    session = await get_session(request)
    
    if "username" in session:
        text = f"Logged in as [{session['username']}]"
        # show panel html
   
    return web.Response(text=text)


def init_app() -> web.Application:
    """Init app direct path to call back function and generate cookie.

    Returns:
        web.Application: application instance.
    """
    app = web.Application()
    # secret_key must be 32 url-safe base64-encoded bytes
    fernet_key = fernet.Fernet.generate_key()
    secret_key = base64.urlsafe_b64decode(fernet_key)
    setup(app, EncryptedCookieStorage(secret_key))
    
    app.add_routes(
        [
            web.get("/", panel),
            web.get("/join", join),
            web.get("/register", register),
            web.get("/login", login),
            web.get("/feedback", feedback),
            web.get("/change_pwd", feedback),
        ]
    )
    return app


if __name__ == "__main__":
    web.run_app(init_app(), ssl_context=SSL_CTX)
