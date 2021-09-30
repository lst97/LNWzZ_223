#import hashing lib
import hashlib

##hashing function for password
class zokit_hash:
    def __init__(self, value:str) -> None:
        self._value = value

    def get_hash(self):
        encoded=self._value.encode()
        result=hashlib.sha256(encoded)
        encrypted = result.hexdigest().upper()
        return encrypted
