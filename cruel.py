
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
        self.expiry = None
        self.update(value)

    def update(self, value, timeout=None):
        self.touch()
        self.value = value

    def __cmp__(self, other):
        return cmp(self.access, other.access)

    def __repr__(self):
        return "<cached[%s] = %s>" % (self.key, self.value)

    def touch(self):
        self.access = time.time()

    @property
    def expired(self):
        return self.expiry and self.expiry.expired


class Expiry(object):
    def __init__(self, key, timeout):
        self.key = key
        self.update(timeout)

    def update(self, timeout=None):
        self._expires = time.time() + timeout

    @property
    def expired(self):
        return time.time() >= self._expires

    def __cmp__(self, other):
        return cmp(self._expires, other._expires)

    def __repr__(self):
        return "<cached[%s] = %s>" % (self.key, self.timeout)


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
                self._delete(cell.key)
            else:
                cell.touch()
                heapq.heapify(self.__lru)
                return cell.value

    def set(self, key, value, time=0, min_compress_len=0):
        """Sets the value for a key."""
        if key in self.__db:
            cell = self.__db[key]
            cell.update(value)
            heapq.heapify(self.__lru)
            if time:
                if cell.expiry:
                    cell.expiry.update(time)
                    heapq.heapify(self.__expire)
                else:
                    expiry = Expiry(key, time)
                    cell.expiry = expiry
                    heapq.heappush(self.__expire, expiry)
        else:
            self._prepare_for_insert()
            cell = Cell(key, value)
            self.__db[key] = cell
            heapq.heappush(self.__lru, cell)
            if time:
                expiry = Expiry(key, time)
                cell.expiry = expiry
                heapq.heappush(self.__expire, expiry)
        return True

    @property
    def db(self):
        return self.__db

    def _init_db(self):
        self.__db = {}
        self.__lru = []
        self.__expire = []

    def _prepare_for_insert(self):
        if len(self.__db) >= self.__max_size:
            if len(self.__expire) and self.__expire[0].expired:
                expired = heapq.heappop(self.__expire)
                cell = self.__db.get(expired.key)
                del self.__db[expired.key]
                self.__lru.remove(cell)
            else:
                cell = heapq.heappop(self.__lru)
                del self.__db[cell.key]

    def _delete(self, key):
        '''remove a given key from datastore

        removing an item from a list doesn't need to trigger a heapify
        '''
        cell = self.__db.get(key)
        if cell:
            del self.__db[key]
            self.__lru.remove(cell)
            if cell.expiry:
                self.__expire.remove(cell.expiry)

    def add(self, key, value, time=0, min_compress_len=0):
        """Sets the value for a key if it doesn't exist."""
        if not key in self.__db:
            return self.set(key, value, time, min_compress_len)

    def replace(self, key, value, time=0, min_compress_len=0):
        """Sets the value for a key if it already exists."""
        if key in self.__db:
            return self.set(key, value, time, min_compress_len)

    def incr(self, key, delta=1):
        """Increments the value for a key."""
        value = self.get(key)
        if value is None:
            return None
        new_value = int(value) + delta
        self.set(key, new_value)
        return new_value


def tests(max_size=32):
    c = Client(max_size=max_size)

    c._init_db()
    c.set(1, 'expected')
    assert c.get(1) == 'expected'
    assert c.get(2) == None

    # check we can store max_size values
    c._init_db()
    for i in xrange(max_size):
        c.set(i, i)
    for i in xrange(max_size):
        assert c.get(i) == i

    c._init_db()
    # check that we only keep most recent items
    for i in xrange(max_size * 2):
        c.set(i, i)
    assert c.get(1) == None

    c._init_db()
    # getting an item ensures it isn't removed via lru
    for i in xrange(max_size * 2):
        c.set(i, i)
        c.get(1)
    assert c.get(1) == 1

    c._init_db()
    # setting an item ensures it isn't removed via lru
    for i in xrange(max_size * 2):
        c.set(i, i)
        c.set(1, 1)
    assert c.get(1) == 1

    c._init_db()
    # don't return expired keys
    c.set(1, 'past', -1)
    assert c.get(1) == None

    c._init_db()
    # prefer to delete expired keys
    for i in xrange(max_size / 2):
        c.set(i, i)
    c.set('bad', 'past', -10)
    for i in xrange(max_size / 2, max_size - 1):
        c.set(i, i)

    c.set('overflow', 'overflow')

    for i in xrange(max_size / 2):
        assert c.get(i) == i
    for i in xrange(max_size / 2, max_size - 1):
        assert c.get(i) == i
    assert c.get('overflow') == 'overflow', 'overflow test'

    c._init_db()
    for i in xrange(max_size - 1):
        c.set(i, i)
    c.set('old', 'past', -10)
    # adding max_size-1 should: remove 'old', ensure 0 ... max_size present
    c.set(max_size - 1, max_size - 1)
    assert c.get('old') is None
    for i in xrange(max_size):
        assert c.get(i) == i

    c._init_db()
    for i in xrange(max_size - 1):
        c.set(i, i)
    c.set('changing', 'past', -10)
    c.set('changing', 'new', 10)
    # adding 'another' should result in 0 being removed not 'changing'
    c.set('another', 'one')
    assert c.get('changing') == 'new'
    assert c.get(0) is None
    for i in xrange(1, max_size - 1):
        assert c.get(i) == i

if __name__ == '__main__':
    import cProfile
    p = cProfile.Profile()
    p.runcall(tests, 128)
    p.print_stats()
