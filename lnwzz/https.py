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
import random

LOG = dbg("[controller]")
SSL_CTX = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
PARENT_PATH = os.path.dirname(__file__)
SSL_CTX.load_cert_chain(
    PARENT_PATH + "/domain/domain_srv.crt", PARENT_PATH + "/domain/domain_srv.key"
)
ROLE = ["Admin", "Member"]

DATABASE = db("sqlite3.db")

# TODO only avaliable after login (using cookie)

#####
# HTML
################
async def html_panel(request: web.Request):
    text = "Panel Detected."
    LOG.print(text, status="info")

    LOG.print("Use Cookie")
    session = await get_session(request)

    try:
        with open("./tests/html/index.html", "r") as file:
            html_data = file.read().replace("\n", "")
    except Exception as ex:
        LOG.print(str(ex), "critical")

    if "email" in session:
        text = f"Logged in as [{session['email']}]"
        html_data = str.format(
            html_data,
            str.format(
                "Logged in as {} | role: {} | <a href='/logout'>logout<a>",
                session["email"],
                ROLE[session["role"]],
            ),
        )
    else:

        html_data = str.format(
            html_data,
            "<p>Please <a href='/login.html'>Login</a> or <a href='/register.html'>Register</a>.</p>",
        )
    return web.Response(text=html_data, content_type="text/html")


async def login(request: web.Request):
    # 0. Contact SQL if it registed
    # 1. Compare User name && password
    text = "Login Atteptemed"
    LOG.print(text, status="info")

    session = await get_session(request)

    if "email" in session:
        # compare role
        LOG.print("Use Cookie")
        raise web.HTTPFound("/index.html")
    else:
        # guess
        LOG.print("Creating Cookie...")
        try:
            LOG.print("Identity Check...")
            try:
                with open("./tests/html/commons/redirect.html", "r") as file:
                    html_data = file.read().replace("\n", "")
            except Exception as ex:
                LOG.print(str(ex), "critical")

            email = request.query["email"]
            password = request.query["pwd"]
            if DATABASE.login(email, password):
                session["email"] = email
                session["role"] = DATABASE.get_role(
                    email
                )  # base on SQL, 0: admin, 1: member

                login_status = "Logged in as {}".format(session["email"])
                LOG.print("Login SUCCESS.", status="info")

            else:
                LOG.print("Login FAIL.", status="warning")
                login_status = "Invalid Email or Password"

            return web.Response(
                text=str.format(html_data, 3, login_status), content_type="text/html"
            )
        except:
            LOG.print("Guest Session.")
            raise web.HTTPFound("/index.html")


async def html_login(request: web.Request, login_status=""):
    # 0. Contact SQL if it registed
    # 1. Compare User name && password
    text = "Login Atteptemed"
    LOG.print(text, status="info")

    session = await get_session(request)

    if "email" in session:
        # compare role
        LOG.print("Use Cookie")
        raise web.HTTPFound("/index.html")
    else:
        # guess
        try:
            with open("./tests/html/commons/login.html", "r") as file:
                html_data = file.read().replace("\n", "")
        except Exception as ex:
            LOG.print(str(ex), "critical")

    return web.Response(
        text=str.format(html_data, login_status), content_type="text/html"
    )


async def logout(request: web.Request):
    text = "Logout Detected."
    LOG.print(text, status="info")

    try:
        with open("./tests/html/commons/redirect.html", "r") as file:
            html_data = file.read().replace("\n", "")
    except Exception as ex:
        LOG.print(str(ex), "critical")

    session = await get_session(request)
    if "email" in session:
        session.pop("email", None)
        session.pop("role", None)
        return web.Response(
            text=str.format(html_data, 3, "Logout Success."), content_type="text/html"
        )
    else:
        LOG.print("Logout with Guest Session.", "warning")
        raise web.HTTPFound("/index.html")


async def html_join(request: web.Request):
    text = "Join Detected."
    LOG.print(text)

    session = await get_session(request)

    if "email" in session:
        try:
            with open("./tests/html/commons/join.html", "r") as file:
                html_data = file.read().replace("\n", "")
        except Exception as ex:
            LOG.print(str(ex), "critical")

        # 0. Contact DiscordBot API to send One Time Invite Link
        # 1. React base on feedback from Discord
        ivlink = DATABASE.get_ivlink(session["email"])
        if ivlink == "":
            # Link not yet generated
            discord_api = api(session["email"])
            if discord_api.ivlink() is not True:
                LOG("Get ivlink FAIL")
                html_data = str.format(
                    html_data, "Error occure, plase try again later."
                )
                return web.Response(text=html_data, content_type="text/html")

            ivlink = DATABASE.get_ivlink(session["email"])

        ivlink = "https://discord.gg/" + ivlink
        html_data = str.format(
            html_data,
            str.format(
                "<p>{}</br><a href={}>{}</a>",
                "* This link can only be used once.</p>",
                ivlink,
                ivlink,
            ),
        )
        return web.Response(text=html_data, content_type="text/html")

    else:
        raise web.HTTPFound("/index.html")


async def register(request: web.Request):
    # 0. Contact Database if already registed
    # 1. Contact Email Server to send OTP
    # 2. React base on feedback from Email Server (Use IPC or TCP/UDP?)
    # 3. Wait for OTP confirm from client
    # 4. Add user into Database

    # TODO Database needs to delete outdated OTP query.
    text = "Register Form Detected."
    LOG.print(text)

    email = request.query["email"]
    verify_status = DATABASE.verified(email)
    if verify_status == 0:
        # check OTP
        if DATABASE.get_otp(email) == request.query["otp"]:
            # update user to DB
            if DATABASE.register(email, request.query["pwd"]) is False:
                LOG.print("Register Fail.", status="critical")
                return web.Response(
                    text="Register fail, please try again later.",
                    content_type="text/plain",
                )
            else:
                return web.Response(text="Register Success, Please login.", content_type="text/plain")
        else:
            # incorrect otp
            return web.Response(text="Incorrect OTP.", content_type="text/plain")
    else:
        # email already taken
        if verify_status == -1:
            return web.Response(text="Incorrect OTP.", content_type="text/plain")

        return web.Response(text="Email already registered.", content_type="text/plain")


async def html_register(request: web.Request):
    # TODO Database needs to delete outdated OTP query.
    text = "Register Detected."
    LOG.print(text)
    try:
        with open("./tests/html/commons/register.html", "r") as file:
            html_data = file.read().replace("\n", "")
    except Exception as ex:
        LOG.print(str(ex), "critical")

    text = str.format(html_data, "^[0-9]{1,6}$", "")
    return web.Response(text=text, content_type="text/html")


async def otp(request: web.Request):
    text = "OTP request Detected."
    LOG.print(text)

    email = request.query["email"]
    mail_server = gsmtp(email)
    otp = f"{int(random.random() * 1000000)}".zfill(6)
    if mail_server.send_otp(otp):
        return web.Response(
            text="OTP Send, please check your email.", content_type="text/plain"
        )
    else:
        return web.Response(
            text="Send Fail, please try again later.", content_type="text/plain"
        )


async def query(request: web.Request):
    text = "Feedback Detected."
    LOG.print(text, status="info")
    return web.Response(text=text)


async def html_query(request: web.Request):
    text = "Feedback Detected."
    LOG.print(text, status="info")
    return web.Response(text=text)


async def feedback(request: web.Request):
    text = "Feedback Detected."
    LOG.print(text, status="info")
    return web.Response(text=text)


######
# Rescourse Function
#########################
async def css_reset(request: web.Application):
    text = "css reset Detected."
    LOG.print(text, status="info")
    try:
        with open("./tests/html/styles/reset.css", "r") as file:
            css_data = file.read()
    except Exception as ex:
        LOG.print(str(ex), "critical", content_type="text/css")

    return web.Response(text=css_data)


async def css_style(request: web.Application):
    text = "css style Detected."
    LOG.print(text, status="info")
    try:
        with open("./tests/html/styles/style.css", "r") as file:
            css_data = file.read()
    except Exception as ex:
        LOG.print(str(ex), "critical")
    return web.Response(text=css_data, content_type="text/css")


async def imgs_main(request: web.Application):
    text = "imgs_main Detected."
    LOG.print(text, status="info")
    try:
        with open("./tests/html/imgs/main.png", "rb") as file:
            img_data = file.read()
    except Exception as ex:
        LOG.print(str(ex), "critical")
    return web.Response(body=img_data, content_type="image/png")


async def js_register(request: web.Application):
    text = "js register Detected."
    LOG.print(text, status="info")
    try:
        with open("./tests/html/scripts/register.js", "r") as file:
            js_data = file.read()
    except Exception as ex:
        LOG.print(str(ex), "critical")
    return web.Response(text=js_data, content_type="application/javascript")


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
            # res
            web.get("/styles/reset.css", css_reset),
            web.get("/styles/style.css", css_style),
            web.get("/imgs/main.png", imgs_main),
            web.get("/scripts/register.js", js_register),
            # main
            web.get("/", html_panel),
            web.get("/index.html", html_panel),
            web.get("/login", login),
            web.get("/login.html", html_login),
            web.get("/logout", logout),
            web.get("/join.html", html_join),
            web.get("/register", register),
            web.get("/register.html", html_register),
            web.get("/otp", otp),
            web.get("/feedback.html", feedback),
            web.get("/change_pwd.html", feedback),
        ]
    )
    return app


if __name__ == "__main__":
    database = db("sqlite3.db")
    database.reset()  # remember to delete when launch
    database.insert_test()

    web.run_app(init_app(), ssl_context=SSL_CTX)
