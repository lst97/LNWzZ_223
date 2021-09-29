from pathlib import Path
from utils.debug import dbg

LOG = dbg("[resources]")

SCRIPT_PATH = Path( __file__ ).absolute()


class HTML:
    """HTML class

    For reading html resources.
    """
    def __init__(self) -> None:
        """Set absolute path to "html" folder
        """
        self._parent_path = str(SCRIPT_PATH.parent.parent) + "/html/"

    @staticmethod
    def __open(path: str, binary=False) -> str:
        """Open file in read mode

        Args:
            path (str): Path to the file
            binary (bool, optional): Binary read flag. Defaults to False.

        Returns:
            str: String format of a text file, mage excluded.
        """
        mode = "r"
        if binary:
            mode += "b"

        try:
            with open(path, mode) as file:
                return file.read()
        except Exception as ex:
            LOG.print(str(ex), "critical")

        return None

    def read_html(self, file_name: str) -> str:
        """Read html file

        Args:
            file_name (str): File name.

        Returns:
            str: HTML code in a string format.
        """
        if file_name == "index.html":
            path = self._parent_path + file_name
        else:
            path = self._parent_path + "commons/" + file_name

        return self.__open(path)

    def read_js(self, file_name: str) -> str:
        """Read Javascript file

        Args:
            file_name (str): File name.

        Returns:
            str: Javascript code in a string format.
        """
        path = self._parent_path + "scripts/" + file_name
        return self.__open(path)

    def read_css(self, file_name: str) -> str:
        """Read CSS file

        Args:
            file_name (str): File name.

        Returns:
            str: CSS code in a string format.
        """
        path = self._parent_path + "styles/" + file_name
        return self.__open(path)

    def read_img(self, file_name: str) -> bytes:
        """Read image file

        Args:
            file_name (str): File name.

        Returns:
            bytes: Binary format of the image.
        """
        path = self._parent_path + "imgs/" + file_name
        return self.__open(path, binary=True)
