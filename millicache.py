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
        # NOTE(ja): explain why we compare keys
        return cmp(self._expires, other._expires) or cmp(self.key, other.key)

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
        # print 'add', key, value, time
        if not self._exists(key):
            # self.ensure()
            self._prepare_for_insert()
            # self.ensure()
            cell = Cell(key, value, time)
            # self.ensure()
            self.__db[key] = cell
            self.__lru.append(cell)
            if time:
                heapq.heappush(self.__timeq, cell)
            # self.ensure()
            return True

    def replace(self, key, value, time=0, min_compress_len=0):
        """Sets the value for a key if it already exists."""
        # print 'replace', key, value, time
        if self._exists(key):
            # self.ensure()
            cell = self.__db[key]
            # self.ensure()
            if not time and cell._expires:
                self.__timeq.remove(cell)
            cell.update(value, time)
            if time:
                heapq.heappush(self.__timeq, cell)
            # self.ensure()
            self._touch(cell)
            # self.ensure('finished replace')
            return True

    @property
    def db(self):
        return self.__db

    def _init_db(self):
        self.__db = {}
        self.__timeq = []
        self.__lru = []

    def _prepare_for_insert(self):
        '''Remove the least useful item from the cache if needed.

        First try to remove an expired item, otherwise remove
        the least recently used item.'''
        if len(self.__db) >= self.__max_size:
            # print 'need to remove something'
            if len(self.__timeq) and self.__timeq[0].expired:
                cell = heapq.heappop(self.__timeq)
                del self.__db[cell.key]
                self.__lru.remove(cell)
            else:
                self._delete(self.__lru[0])

    def _exists(self, key):
        return key in self.__db

    def _delete(self, cell):
        '''Remove a given cell.

        remove it from the db, remove it from the __lru
        and if it has an expiry, remove it from the expiry
        heap.'''
        # print 'deleting', cell
        del self.__db[cell.key]
        self.__lru.remove(cell)
        if cell._expires:
            self.__timeq.remove(cell)

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
        self.set(key, str(new_value))
        return new_value

    def _ensure_sanity(self):
    #     print 'ensure: %s' % what
    #     print ' * db   ', self.__db.keys()
    #     print ' * lru  ', [c.key for c in self.__lru]
    #     print ' * timeq', [c.key for c in self.__timeq]
        # tests for LRU
        assert len(self.db.keys()) == len(self.__lru)
        for cell in self.db.values():
            assert cell in self.__lru
        for cell in self.__lru:
            assert cell == self.__db[cell.key]
        assert len(set(self.db.keys())) == len(self.db.keys())
        lru_keys = [l.key for l in self.__lru]
        assert len(set(lru_keys)) == len(lru_keys)
        # tests for expiry
        for cell in self.db.values():
            if cell._expires:
                assert cell in self.__timeq
            else:
                assert not cell in self.__timeq


def perf(size=128):
    c = Client(size)
    for i in xrange(10000):
        if i % 3 == 0:
            c.set(i % size, i)
        if i % 3 == 1:
            c.set(i % size, i, ((size % 7) - 3) / 49)
        if i % 7 == 0:
            c.get(i % size)

if __name__ == '__main__':
    import cProfile
    p = cProfile.Profile()
    p.runcall(perf, 1024)
    p.print_stats()
