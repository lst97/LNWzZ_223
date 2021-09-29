"""Controller module

Entry point, runing the HTTPS controller server.
"""

from utils.debug import dbg
from dcapi import api
from gsender import gsmtp
from database import db
from utils.resources import HTML
from utils import otp as OTP

from cryptography import fernet

from aiohttp import web
from aiohttp_session import setup, get_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage

import ssl
import base64
import os
import hashlib
import json

LOG = dbg("[controller]")
SSL_CTX = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
PARENT_PATH = os.path.dirname(__file__)
SSL_CTX.load_cert_chain(
    PARENT_PATH + "/domain/domain_srv.crt", PARENT_PATH + "/domain/domain_srv.key"
)
ROLE = ["Admin", "Member"]

DATABASE = db("sqlite3.db")
RESOURCES = HTML()

#####
# Naming
# Naming using snak_case
# html_function_name:   Responsable for HTML rendering for static content.
# function_name:        Need to execute SQL, Email sender or Discord API for dynamic content.
################

#####
# HTML
################
async def html_panel(request: web.Request) -> web.Response:
    LOG.print("Panel Resources Detected.", status="info")

    LOG.print("Use Cookie")
    session = await get_session(request)

    html_data = RESOURCES.read_html("index.html")
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


async def html_login(request: web.Request) -> web.Response:
    text = "Login Resources Atteptemed"
    LOG.print(text, status="info")

    session = await get_session(request)

    if "email" in session:
        LOG.print("Double login attempt", status="warning")
        raise web.HTTPFound("/index.html")

    html_data = RESOURCES.read_html("login.html")

    return web.Response(text=str.format(html_data, ""), content_type="text/html")


async def html_register(request: web.Request) -> web.Response:
    LOG.print("Register Resources Detected.")

    html_data = RESOURCES.read_html("register.html")
    html_data = str.format(html_data, "^[0-9]{1,6}$", "")
    return web.Response(text=html_data, content_type="text/html")


async def html_join(request: web.Request) -> web.Response:
    LOG.print("Join Resources Detected.")

    session = await get_session(request)

    if "email" in session:
        html_data = RESOURCES.read_html("join.html")

        # 0. Contact DiscordBot API to generate one time Invite Link.
        # 1. React base on feedback from Discord.
        # 2. Get the Ivlink from database.
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

        ivlink = "https://discord.gg/" + DATABASE.get_ivlink(session["email"])
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

    raise web.HTTPFound("/index.html")


async def html_query(request: web.Request):
    LOG.print("Query Resources Detected.", status="info")

    html_data = RESOURCES.read_html("query.html")

    session = await get_session(request)
    if "email" in session:
        LOG.print("Use Cookie")
        status = api.member_status()

        # display online member count
        html_data = str.format(
            html_data,
            f"<p>Server: {status[0]}</br>Online members: {status[1]}</p></br>"
            + "<form id='sql_form'>{}</form></br>",
        )

        # additional admin function
        if session["role"] == 0:
            html_data = str.format(
                html_data,
                "<input type='submit' onclick='show_sql()' value='Show SQL' />",
            )
        else:
            html_data = str.format(html_data, "")

        return web.Response(text=html_data, content_type="text/html")

    raise web.HTTPFound("/index.html")


#####
# Dynamic HTML or Functions
################
async def login(request: web.Request) -> web.Response:
    # 0. Compare User name && password hash
    LOG.print("Login Atteptemed", status="info")

    session = await get_session(request)
    LOG.print("Use Cookie", status="info")

    if "email" in session:
        # Double login
        LOG.print("Possible Email bypass", status="warning")
        raise web.HTTPFound("/index.html")
    else:
        # guess session
        LOG.print("Creating Cookie...")

        html_data = RESOURCES.read_html("redirect.html")

        try:
            email = request.query["email"]
        except:
            LOG.print("Guest Session.")
            raise web.HTTPFound("/index.html")

        password_binary = request.query["pwd"].encode()
        password_sha256 = hashlib.sha256(password_binary).hexdigest()

        LOG.print("Identity Check...", status="info")
        if DATABASE.login(email, password_sha256.upper()):
            session["email"] = email
            # base on SQL, 0: admin, 1: member
            session["role"] = DATABASE.get_role(email)

            LOG.print("Login SUCCESS.", status="info")
            login_status = "Logged in as {}".format(session["email"])

        else:
            LOG.print("Login FAIL.", status="warning")
            login_status = "Invalid Email or Password."

        # redirect: (html_data, wait_time, main_content)
        return web.Response(
            text=str.format(html_data, 3, login_status), content_type="text/html"
        )


async def logout(request: web.Request) -> web.Response:
    LOG.print("Logout Detected.", status="info")

    session = await get_session(request)

    html_data = RESOURCES.read_html("redirect.html")

    if "email" in session:
        session.pop("email", None)
        session.pop("role", None)
        return web.Response(
            text=str.format(html_data, 3, "Logout Success."), content_type="text/html"
        )
    else:
        LOG.print("Logout with Guest Session.", "warning")
        raise web.HTTPFound("/index.html")


async def register(request: web.Request) -> web.Response:
    # 0. Contact Database if already registed.
    # 1. Contact Email Server to send OTP.
    # 2. Add user into Database.
    # 3. React base on feedback from Email Server.
    # 4. Check OTP with Database.
    # 5. Update verify status.

    LOG.print("Register Form Detected.", status="info")

    email = request.query["email"]
    verify_status = DATABASE.verified(email)

    response = ""
    if verify_status == 0:
        # check OTP
        if DATABASE.get_otp(email) == request.query["otp"]:
            # update user to DB

            password_binary = request.query["pwd"].encode()
            password_sha256 = hashlib.sha256(password_binary).hexdigest()

            if DATABASE.register(email, password_sha256.upper()) is False:
                LOG.print("Register Fail.", status="critical")
                response = "Register fail, please try again later."
            else:
                LOG.print("Register Pass.", status="info")
                response = "Register Success, Please login."
        else:
            # incorrect otp
            LOG.print("Incorrect OTP.", status="info")
            response = "Incorrect OTP."
    else:
        if verify_status == -1:  # OTP not send
            LOG.print("Email not send while execute OTP check.", status="warning")
            response = "Incorrect OTP."
        else:
            LOG.print("Email registered.", status="warning")
            response = "Email already registered."

    return web.Response(text=response, content_type="text/plain")


async def otp(request: web.Request) -> web.Response:
    LOG.print("OTP request Detected.", status="info")

    receiver_email = request.query["email"]
    mail_server = gsmtp(receiver_email)

    response = ""
    if mail_server.send_otp(OTP.generate()):
        response = "OTP Send, please check your email."
    else:
        response = "Send Fail, please try again later."

    return web.Response(text=response, content_type="text/plain")


async def query(request: web.Request) -> web.Response:
    LOG.print("Query Detected.", status="info")

    session = await get_session(request)

    try:
        if request.query["command"] == "show_table" and session["role"] == 0:
            response = DATABASE.get_table("users")
            json_res = json.dumps(response)
            return web.Response(text=json_res, content_type="application/json")
    except:
        raise web.HTTPFound("/index.html")

    raise web.HTTPFound("/index.html")


######
# Rescourse Function
#########################
async def css_reset(request: web.Application):
    # LOG.print("css reset Detected.", status="info")

    css_data = RESOURCES.read_css("reset.css")
    return web.Response(text=css_data, content_type="text/css")


async def css_style(request: web.Application):
    # LOG.print("css style Detected.", status="info")

    css_data = RESOURCES.read_css("style.css")
    return web.Response(text=css_data, content_type="text/css")


async def imgs_main(request: web.Application):
    # LOG.print("img main Detected.", status="info")

    img_data = RESOURCES.read_img("main.png")
    return web.Response(body=img_data, content_type="image/png")


async def js_register(request: web.Application):
    # LOG.print("js register Detected.", status="info")

    js_data = RESOURCES.read_js("register.js")
    return web.Response(text=js_data, content_type="application/javascript")


async def js_query(request: web.Application):
    # LOG.print("js query Detected.", status="info")

    js_data = RESOURCES.read_js("query.js")
    return web.Response(text=js_data, content_type="application/javascript")


######
# Launcher
#########################
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
            web.get("/scripts/query.js", js_query),
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
            web.get("/query.html", html_query),
            web.get("/query", query),
        ]
    )
    return app


if __name__ == "__main__":
    DATABASE.reset()  # remember to delete when launch
    DATABASE.insert_test()

    web.run_app(init_app(), ssl_context=SSL_CTX)
