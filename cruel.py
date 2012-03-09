
# C.ached
# R.ecently
# U.sed
# E.xpirey
# L.east

import heapq
import time


class Cell(object):
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.access = time.time()

    def __cmp__(self, other):
        return cmp(self.access, other.access)

    def touch(self):
        self.access = time.time()

    @property
    def expired(self):
        pass


class Client(object):
    """Replicates a tiny subset of memcached client interface."""

    def __init__(self, max_size=32, *args, **kwargs):
        """Ignores the passed in args."""
        self.__max_size = max_size
        self._init_db()

    def get(self, key):
        """Retrieves the value for a key or None."""
        # for key in list(self.__db.iterkeys()):
        #     (expires, value) = self.__db.get(key, (0, None))
        #     if expires and time.time() >= expires:
        #         del self.__db[key]
        cell = self.__db.get(key)
        if cell:
            if cell.expired:
                self._delete(cell.key)
            else:
                cell.touch()
                return cell.value

    def set(self, key, value, time=0, min_compress_len=0):
        """Sets the value for a key."""
        if key in self.__db:
            cell = self.__db[key]
            cell.value = value
            cell.touch()
            heapq.heapify(self.__lru)
        else:
            self._prepare_for_insert()
            cell = Cell(key, value)
            self.__db[key] = cell
            heapq.heappush(self.__lru, cell)

    @property
    def db(self):
        return self.__db

    def _init_db(self):
        self.__db = {}
        self.__lru = []
        self.__expire = []

    def _prepare_for_insert(self):
        if len(self.__db) >= self.__max_size:
            cell = heapq.heappop(self.__lru)
            del self.__db[cell.key]

    def _delete(self, key):
        '''remove a given key from datastore'''
        cell = self.__db.get(key)
        if cell:
            del self.__db[key]
            self.__lru.remove(cell)
            heapq.heapify(self.__lru)

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
    c = Client(max_size=10)
    c.set(1, 'expected')
    assert c.get(1) == 'expected'

    # check that we only keep most recent 10 items
    for i in xrange(100):
        c.set(i, pow(i, 2))
    assert c.get(1) == None

    # getting an item ensures it isn't removed via lru
    for i in xrange(100):
        c.set(i, pow(i, 2))
        c.get(1)
    assert c.get(1) == 1

    # setting an item ensures it isn't removed via lru
    for i in xrange(100):
        c.set(i, pow(i, 2))
        c.set(1, 1)
    assert c.get(1) == 1

    print c.db.keys()
