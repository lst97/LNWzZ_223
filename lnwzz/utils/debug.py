"""Debug module."""
import logging


class dbg:
    """Handle useful debug message, write to "debug.log"

    Attributes:
        _dbgprint: flag indicate rather the debug string will be print to console.
        _module_name: Generate module name in the log file, it also affect the print method.

    Method:
        print: write the message to log file then print to the console.
    """

    def __init__(self, module_name: str, dbgprint=True) -> None:
        """All log save at debug.log in the current directry.

        Args:
            module_name (str): Generate module name in the log file, also affect the print method.
            dbgprint (bool, optional): Print the string to console if set to True. Defaults to True.
        """
        self._dbgprint = dbgprint
        self._module_name = module_name

        logging.basicConfig(
            filename="debug.log",
            level=logging.DEBUG,
            format="%(asctime)s:%(levelname)s:%(message)s",
        )

    def print(self, message: str, status="debug") -> None:
        """Print message to console.

        Args:
            string (str): Description that will show on log file.
            status (str, optional): Type of the debug message. Defaults to "debug".

        status types:
            debug: extra information that will not affect the program flow.
            info: showing the operation status.
            warning: unusual behaviour for example Incorrect Password.
            critical: it effecting the normal program flow.
            exception: it can terminate the process unexpetlly.
        """
        if self._dbgprint is True:
            print(self._module_name + message)

        if status == "debug":
            logging.debug(self._module_name + message)

        elif status == "info":
            logging.info(self._module_name + message)

        elif status == "warning":
            logging.warning(self._module_name + message)

        elif status == "critical":
            logging.critical(self._module_name + message)

        else:
            logging.exception(self._module_name + message)
