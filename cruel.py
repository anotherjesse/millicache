
# C.ached
# R.ecently
# U.sed
# E.xpirey
# L.east

import time


class Client(object):
    """Replicates a tiny subset of memcached client interface."""

    def __init__(self, max_size=32, *args, **kwargs):
        """Ignores the passed in args."""
        self.__db = {}
        self.__max_size = 32
        self.__lru = []
        self.__expire = []

    def get(self, key):
        """Retrieves the value for a key or None.

        this expunges expired keys during each get"""
        for key in list(self.__db.iterkeys()):
            (expires, value) = self.__db.get(key, (0, None))
            if expires and time.time() >= expires:
                del self.__db[key]
        return self.__db.get(key, (0, None))[1]

    def set(self, key, value, time=0, min_compress_len=0):
        """Sets the value for a key."""
        timeout = 0
        if time != 0:
            timeout = time.time() + time
        self.__db[key] = (timeout, value)
        return True

    def add(self, key, value, time=0, min_compress_len=0):
        """Sets the value for a key if it doesn't exist."""
        if not self.get(key) is None:
            return False
        return self.set(key, value, time, min_compress_len)

    def incr(self, key, delta=1):
        """Increments the value for a key."""
        value = self.get(key)
        if value is None:
            return None
        new_value = int(value) + delta
        self.__db[key] = (self.__db[key][0], str(new_value))
        return new_value


if __name__ == '__main__':
    c = Client()
    c.set(1, 'expected')
    assert c.get(1) == 'expected'
