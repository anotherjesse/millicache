millicache
==========

An in-memory, in-process, least resently used (LRU) cache with expiration
for python.

Use case:

 * 1000 items
 * 1 ms or less for get/set

The goal is to mirror the python-memcache interface - allowing you to use
millicache as a drop in replacement for those times you can't use memcache.

Example
-------

    import millicache

    # create a cache, maximum of 1024 items
    c = millicache.Client(1024)

    c.set('dog', 'fred')
    => True
    c.get('dog')
    => 'fred'

    # The third parameter is how long the value is valid, in seconds.
    # In this example we are specifying a negative value, so it expired
    # 10 seconds ago.
    c.set('dog', 'dead', -10)
    => True
    c.get('dog')
    => None

Architecture
------------

millicache maintains 2 datastructures:

 * heapq - for tracking when items have expired
 * sorted list - for tracking least recently used items

LRU:

 * new items are placed into the end of the list
 * when an item is accessed it is moved to the end of the list
 * to remove the LRU item, remove the first item in the list

Expiration:

 * maintain a heap of items sorted by expiration
 * only items that have expiration are kept in heapq
 * item[0] will be the most likely expired object

If the cache is full (determined by key count), millicache first tries to 
remove an expired key, if none, it removes the least resently used key.

License
-------

MIT
