smallcache
==========

An in-memory, in-process, least resently used (LRU) cache with expiration
for python.

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

smallcache maintains 2 datastructures:
 * heapq - for tracking when items have expired
 * deque - for tracking least recently used items

LRU:
 * new items are placed into the end of the deque
 * when an item is accessed it is moved to the end of the deque
 * to remove the LRU item, remove the first item in the list

Expiration:
 * maintain a heap of items sorted by expiration
 * only items that have expiration are kept in heapq
 * item[0] will be the most likely expired object

If the cache is full (determined by key count), smallcache first tries to 
remove an expired key, if none, it removes the least resently used key.
