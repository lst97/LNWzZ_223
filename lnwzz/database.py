""" Database module.
SQLite is a database that is stored in a single file on disk.
SQLite is built into Python but is only built for access by a single connection at a time.
Therefore is highly recommended to not run a production web application with SQLite.
"""

import sqlite3
import time

from utils.debug import dbg

LOG = dbg("[database]")


class db:
    """Database operation

    Args:
        db_name: open or create database "*.db"
    """

    def __init__(self, db_name) -> None:
        self._dbname = db_name

    def __connect(self) -> sqlite3.connect:
        """Database connection.

        Get connection instance within 3 attempts.

        Returns:
            sqlite3.connect: instance of the connection.
        """

        for attempts in range(3):
            LOG.print("Connecting...")

            try:
                cur = sqlite3.connect(self._dbname)
                if cur is not None:
                    break
            except sqlite3.Error as ex:
                if attempts == 2:
                    LOG.print(str(ex), status="critical")
                    return None
                time.sleep(1)
                LOG.print("Retring...", status="warning")

        LOG.print("Connection success.")
        return cur

    def __close(self, cur: sqlite3.connect) -> bool:
        """Do commit before closing the database connection.

        Args:
            cur (sqlite3.connect): instance of the connection.

        Returns:
            bool:
                True: only return true in current stage.
        """
        cur.commit()
        cur.close()  # Need to check if success?
        return True

    def create(self) -> bool:
        """Create the table that our group project needs.

        Returns:
            bool:
                True: success.
                False: fail.
        """
        cur = self.__connect()

        if cur is not None:
            LOG.print("Create Table...")
            try:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users(
                        email_address TEXT PRIMARY KEY,
                        user_name TEXT,
                        password TEXT,
                        OTP TEXT,
                        verified INT,
                        invite_link TEXT,
                        role INT
                    );
                    """
                )  # query && Exception handling
                LOG.print("Table Created.")
            except sqlite3.Error as ex:
                LOG.print(str(ex), status="critical")
                self.__close(cur)
                return False
            return self.__close(cur)

        return False

    def insert_test(self):
        cur = self.__connect()

        cur.execute(
            'INSERT INTO users VALUES ("test@deakin.edu.au", "test", "1234", 123456, 1, "", 1);'
        )
        cur.execute(
            'INSERT INTO users VALUES ("admin@deakin.edu.au", "admin", "5678", 567891, 1, "HIJKLM", 0);'
        )
        LOG.print("Insert Test Data DONE.")
        return self.__close(cur)

    def login(self, email: str, password: str) -> bool:
        cur = self.__connect()

        if cur is not None:
            LOG.print("Login Check...")
            try:
                response = cur.execute(
                        "SELECT * FROM users WHERE email_address=? AND password=?;",
                        (
                            email,
                            password,
                        ),
                    ).fetchone()
                
                if (response is None):
                    msg = "Record Not Found."
                elif response[3] == 0:
                    msg = "Email Not Verified."
                else:
                    LOG.print("Record Found.")
                    return self.__close(cur)
                
                LOG.print(msg, status="warning")
                self.__close(cur)
                return False
            except sqlite3.Error as ex:
                LOG.print(str(ex), status="critical")
                self.__close(cur)
                return False

        return False

    def check_unique(self, email: str) -> bool:
        cur = self.__connect()

        if cur is not None:
            LOG.print("Check email...")
            try:
                response = cur.execute(
                    "SELECT * FROM users WHERE email_address=?", (email,)
                ).fetchone()
                if response is not None:
                    LOG.print("Record Found.")
                    return False

                LOG.print("Record Not Found.")
                return self.__close(cur)

            except sqlite3.Error as ex:
                LOG.print(str(ex), status="critical")
                self.__close(cur)
                return False

        return False

    def register(
        self,
        email: str,
        password: str,
    ) -> bool:

        cur = self.__connect()

        if cur is not None:
            LOG.print("Update ivlink...")
            try:
                cur.execute(
                    "UPDATE users SET password=?, verified=? WHERE email_address=?",
                    (
                        password,
                        1,
                        email,
                    ),
                )
                LOG.print("Update Complete.")
                return self.__close(cur)

            except sqlite3.Error as ex:
                LOG.print(str(ex), status="critical")
                self.__close(cur)
                return False

        return False

    def get_ivlink(self, email: str) -> str:
        cur = self.__connect()

        if cur is not None:
            LOG.print("ivlink Check...")
            try:
                response = cur.execute(
                    "SELECT invite_link FROM users WHERE email_address=? ;", (email,)
                ).fetchone()

            except sqlite3.Error as ex:
                LOG.print(str(ex), status="critical")
                self.__close(cur)
                return ""

            if response is None:
                LOG.print("Record Not Found", status="warning")
                self.__close(cur)
                return ""

            LOG.print("Record Found.")
            return response[0]

        return ""

    def update_ivlink(self, email: str, ivlink: str) -> bool:
        """Insert invite code to database.

        Args:
            ivlink (str): invite code generated from Discord API.

        Returns:
            bool:
                True: success.
                False: fail.
        """
        cur = self.__connect()

        if cur is not None:
            LOG.print("Update ivlink...")
            try:
                cur.execute(
                    "UPDATE users SET invite_link=? WHERE email_address=?",
                    (
                        ivlink,
                        email,
                    ),
                )
                LOG.print("Update Complete.")
                return self.__close(cur)

            except sqlite3.Error as ex:
                LOG.print(str(ex), status="critical")
                self.__close(cur)
                return False

        return False

    def insert_otp(self, email: str, code: str) -> bool:
        """Insert OTP to database.

        Args:
            code (str): OTP which send to the recipient.

        Returns:
            bool:
                True: success.
                False: fail.
        """
        LOG.print("Insert OTP to DB...")

        cur = self.__connect()

        if cur is not None:
            LOG.print("Insert OTP...")
            try:
                cur.execute(
                    "INSERT INTO users (email_address, password, OTP, verified, invite_link, role)\
                        VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        email,
                        "",
                        code,
                        0,
                        "",
                        1,
                    ),
                )
                LOG.print("Update Complete.")
                return self.__close(cur)

            except sqlite3.Error as ex:
                LOG.print(str(ex), status="critical")
                self.__close(cur)
                return False

        return False

    def get_otp(self, email: str) -> str:
        cur = self.__connect()

        if cur is not None:
            LOG.print("Role Check...")
            try:
                response = cur.execute(
                    "SELECT OTP FROM users WHERE email_address=? ;", (email,)
                ).fetchone()

            except sqlite3.Error as ex:
                LOG.print(str(ex), status="critical")
                self.__close(cur)
                return -1

            if response is None:
                LOG.print("Record Not Found", status="warning")
                self.__close(cur)
                return -1

            LOG.print("Record Found.")
            return response[0]

        return -1

    def get_role(self, email: str) -> int:
        cur = self.__connect()

        if cur is not None:
            LOG.print("Role Check...")
            try:
                response = cur.execute(
                    "SELECT role FROM users WHERE email_address=? ;", (email,)
                ).fetchone()

            except sqlite3.Error as ex:
                LOG.print(str(ex), status="critical")
                self.__close(cur)
                return -1

            if response is None:
                LOG.print("Record Not Found", status="warning")
                self.__close(cur)
                return -1

            LOG.print("Record Found.")
            return response[0]

        return -1

    def verified(self, email: str) -> bool:
        cur = self.__connect()

        if cur is not None:
            LOG.print("Verify Check...")
            try:
                response = cur.execute(
                    "SELECT verified FROM users WHERE email_address=? ;", (email,)
                ).fetchone()

            except sqlite3.Error as ex:
                LOG.print(str(ex), status="critical")
                self.__close(cur)
                return -1

            if response is None:
                LOG.print("Record Not Found", status="warning")
                self.__close(cur)
                return -1

            LOG.print("Record Found.")
            return response[0]

        return -1

    def change_pwd(self, email: str, old_pwd: str, new_pwd: str) -> bool:
        pass

    def drop(self) -> bool:
        """Drop the tables.

        Returns:
            bool:
                True: success.
                False: fail.
        """
        cur = self.__connect()

        if cur is not None:
            LOG.print("Drop Table...")
            try:
                cur.execute("""DROP TABLE users;""")  # query
                LOG.print("Drop DONE.")
            except sqlite3.Error as ex:
                LOG.print(str(ex), status="critical")
                self.__close(cur)
                return False
            return self.__close(cur)

        return False

    def reset(self) -> bool:
        """Reset database.

        Returns:
            bool:
                True: success.
                False: fail.
        """
        self.drop()
        self.create()
        return True

    # custom query
    def query(self, query_str: str) -> bool:
        """Run custom query

        Args:
            query_str (str): query string to run

        Returns:
            bool:
                True: success.
                False: fail.
        """
        cur = self.__connect()

        if cur is not None:
            try:
                if cur.execute(query_str):
                    LOG.print("Query DONE.")
            except sqlite3.Error as ex:
                LOG.print(str(ex), status="critical")
                self.__close(cur)
                return False
            return self.__close(cur)

        return False
