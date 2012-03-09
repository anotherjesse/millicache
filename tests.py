import smallcache

import unittest

MAX_SIZE = 128


class LRUTestCase(unittest.TestCase):

    def setUp(self):
        self.cache = smallcache.Client(MAX_SIZE)
        for i in xrange(MAX_SIZE):
            self.cache.set(i, i)

    def testlen(self):
        assert len(self.cache.db) == MAX_SIZE

    def test_exists(self):
        for i in xrange(MAX_SIZE):
            assert self.cache.get(i) == i

    def test_non_exist(self):
        assert self.cache.get('dog') is None

    def test_most_recent_MAX_SIZE(self):
        for i in xrange(2 * MAX_SIZE):
            self.cache.set('test-%s' % i, i)
        for i in xrange(MAX_SIZE):
            self.cache.get('test-%s' % i) is None
        for i in xrange(MAX_SIZE, 2 * MAX_SIZE):
            self.cache.get('test-%s' % i) == i

    def test_accessed_items_are_kept(self):
        for i in xrange(MAX_SIZE * 2):
            self.cache.set(i, i)
            self.cache.set(1, 1)
        assert self.cache.get(1) == 1


class ExpiryTestCase(unittest.TestCase):

    def setUp(self):
        self.cache = smallcache.Client(MAX_SIZE)

    def test_past_expirey_dont_return(self):
        self.cache.set(1, 'past', -1)
        assert self.cache.get(1) == None

    def test_future_expirey_return(self):
        self.cache.set(1, 'future', 1)
        assert self.cache.get(1) == 'future'

    def test_remove_expired_keys_first(self):
        for i in xrange(MAX_SIZE / 2):
            self.cache.set(i, i)
        self.cache.set('bad', 'past', -10)
        for i in xrange(MAX_SIZE / 2, MAX_SIZE - 1):
            self.cache.set(i, i)

        self.cache.set('overflow', 'overflow')

        for i in xrange(MAX_SIZE / 2):
            assert self.cache.get(i) == i
        for i in xrange(MAX_SIZE / 2, MAX_SIZE - 1):
            assert self.cache.get(i) == i
        assert self.cache.get('overflow') == 'overflow', 'overflow test'

    def test_stuff(self):
        for i in xrange(MAX_SIZE - 1):
            self.cache.set(i, i)
        self.cache.set('old', 'past', -10)
        # adding MAX_SIZE-1 should: remove 'old', ensure 0 ... MAX_SIZE present
        self.cache.set(MAX_SIZE - 1, MAX_SIZE - 1)
        assert self.cache.get('old') is None
        for i in xrange(MAX_SIZE):
            assert self.cache.get(i) == i

    def test_things(self):
        for i in xrange(MAX_SIZE - 1):
            self.cache.set(i, i)
        self.cache.set('changing', 'past', -10)
        self.cache.set('changing', 'new', 10)
        # adding 'another' should result in 0 being removed not 'changing'
        self.cache.set('another', 'one')
        assert self.cache.get('changing') == 'new'
        assert self.cache.get(0) is None
        for i in xrange(1, MAX_SIZE - 1):
            assert self.cache.get(i) == i


if __name__ == "__main__":
    unittest.main()
