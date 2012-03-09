import collections
import heapq
import time


class Cell(object):
    '''holds a key, value, and expiry'''

    def __init__(self, key, value, timeout=None):
        self.key = key
        self.update(value, timeout)

    def update(self, value, timeout=None):
        self.value = value
        if timeout:
            self._expires = time.time() + timeout
        else:
            self._expires = None

    def __cmp__(self, other):
        return cmp(self._expires, other._expires)

    def __repr__(self):
        return "<cached[%s] = %s>" % (self.key, self.value)

    @property
    def expired(self):
        return self._expires and time.time() >= self._expires


class Client(object):
    """Replicates a tiny subset of memcached client interface."""

    def __init__(self, max_size=32, *args, **kwargs):
        """Ignores the passed in args."""
        self.__max_size = max_size
        self._init_db()

    def get(self, key):
        """Retrieves the value for a key or None."""
        cell = self.__db.get(key)
        if cell:
            if cell.expired:
                self._delete(cell)
            else:
                self._touch(cell)
                return cell.value

    def set(self, key, value, time=0, min_compress_len=0):
        """Sets the value for a key."""
        if self._exists(key):
            return self.replace(key, value, time, min_compress_len)
        else:
            return self.add(key, value, time, min_compress_len)

    def add(self, key, value, time=0, min_compress_len=0):
        """Sets the value for a key if it doesn't exist."""
        if not self._exists(key):
            self._prepare_for_insert()
            cell = Cell(key, value, time)
            self.__db[key] = cell
            if time:
                heapq.heappush(self.__expire, cell)
            self.__lru.append(cell)
            return True

    def replace(self, key, value, time=0, min_compress_len=0):
        """Sets the value for a key if it already exists."""
        if self._exists(key):
            cell = self.__db[key]
            if not time and cell._expires:
                self.__expire.remove(cell)
            cell.update(value, time)
            if time:
                heapq.heapify(self.__expire)
            self._touch(cell)
            return True

    @property
    def db(self):
        return self.__db

    def _init_db(self):
        self.__db = {}
        self.__expire = []
        self.__lru = collections.deque()

    def _prepare_for_insert(self):
        if len(self.__db) >= self.__max_size:
            if len(self.__expire) and self.__expire[0].expired:
                cell = heapq.heappop(self.__expire)
                del self.__db[cell.key]
                self.__lru.remove(cell)
            else:
                self._delete(self.__lru[0])

    def _exists(self, key):
        return key in self.__db

    def _delete(self, cell):
        '''remove a given cell from datastore'''
        del self.__db[cell.key]
        self.__lru.remove(cell)
        if cell._expires:
            self.__expire.remove(cell)

    def _touch(self, cell):
        '''move a cell to the end of the list (it was accesed)'''
        self.__lru.remove(cell)
        self.__lru.append(cell)

    def incr(self, key, delta=1):
        """Increments the value for a key."""
        value = self.get(key)
        if value is None:
            return None
        new_value = int(value) + delta
        self.set(key, new_value)
        return new_value
