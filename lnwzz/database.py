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
                if cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users(
                        email_address TEXT PRIMARY KEY,
                        user_name TEXT,
                        password TEXT,
                        OTP INT,
                        verified INT,
                        invite_link TEXT,
                        role INT
                    );
                    """
                ):  # query && Exception handling
                    LOG.print("Table Created.")
            except sqlite3.Error as ex:
                LOG.print(str(ex), status="critical")
                self.__close(cur)
                return False
            return self.__close(cur)

        return False

    def login(self, email: str, password: str) -> bool:
        pass

    def register(self, email: str, password: str, otp: int) -> bool:
        pass

    def insert_ivlink(self, email: str, ivlink: str) -> bool:
        pass

    def insert_otp(self, email: str, otp: int) -> bool:
        pass

    def get_ivlink(self, email: str) -> str:
        pass
    
    def get_otp(self, email: str) -> int:
        pass
    
    def get_role(self, email:str) -> int:
        pass
    
    def isVerified(self, email:str) -> bool:
        pass

    def change_pwd(self, email:str, old_pwd: str, new_pwd:str) -> bool:
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
                if cur.execute("""DROP TABLE users;"""):  # query
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
        return self.create() if self.drop() else False

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


class dc(db):
    """Provide database operation for Discord API

    Inheritance from class db.
    """

    def __init__(self, db_name: str) -> None:
        super().__init__(db_name)

    def insert_ivlink(self, ivlink: str) -> bool:
        """Insert invite code to database.

        Args:
            ivlink (str): invite code generated from Discord API.

        Returns:
            bool:
                True: success.
                False: fail.
        """
        LOG.print("Insert Invite Link to DB...")
        if self.query(ivlink) is False:
            return False

        return True


class smtp(db):
    """Provide database operation for Gmail smtp

    Inheritance from class db.
    """

    def __init__(self, db_name: str) -> None:
        super().__init__(db_name)

    def insert_otp(self, code: str) -> bool:
        """Insert OTP to database.

        Args:
            code (str): OTP which send to the recipient.

        Returns:
            bool:
                True: success.
                False: fail.
        """
        LOG.print("Insert OTP to DB...")
        if self.query(code) is False:
            return False

        return True
