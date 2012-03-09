smallcache
==========

An in-memory, in-process, LRU cache with expiration for python

The goal is to mirror the python-memcache interface - allowing you to use
smallcache as a drop in replacement for those times you can't use memcache.

Example
-------

    import smallcache

    # create a cache, maximum of 100 items
    c = smallcache.Client(100)

    c.set('dog', 'fred')
    => True
    c.get('dog')
    => 'fred'

    # The third parameter is how long the value is valid, in seconds.
    # In this example we are specifying a negative value, so it expired
    # 10 seconds ago.
    c.set('dog', 'dead', -10)
    c.get('dog')
    => None

Architecture
------------

smallcache maintains 2 heapq lists: access time & expiry time.  All access
and updates to the keys update the heapqs.

If the cache is full (determined by key count), smallcache first tries to 
remove an expired key, if none, it removes the least resently used key.
