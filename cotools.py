"""
cotools is a collection of functional programming primitives utilizing the
cooperative multitasking facilities provided by the Twisted framework.
"""

from twisted.internet.task import coiterate
from twisted.internet.defer import maybeDeferred, succeed


class _CoFunCaller(object):
    def __init__(self, function=None, stopFunction=None, resultCollector=None):
        self._function = function
        self._stopFunction = stopFunction
        self._resultCollector = resultCollector
        self._stopped = False


    def _maybeStop(self, result):
        if self._stopFunction(result):
            self._stopped = True


    def do(self, iterator):
        for item in iterator:
            d = maybeDeferred(lambda: item)
            if self._function is not None:
                d.addCallback(self._function)

            if self._resultCollector is not None:
                d.addCallback(self._resultCollector)

            if self._stopFunction is not None:
                d.addCallback(self._maybeStop)

            yield d

            if self._stopped:
                return


    def coiterate(self, iterator):
        return coiterate(self.do(iterator))



def coforeach(function, iterator):
    """
    Apply function to each item in iterator.
    """
    return _CoFunCaller(function=function).coiterate(iterator)



def cofilter(function, iterator):
    """
    Return items in iterator for which `function(item)` returns True.
    """
    results = []

    def checkFilter(notfiltered, item):
        if notfiltered == True:
            results.append(item)

    def dofilter(item):
        d = maybeDeferred(function, item)
        d.addCallback(checkFilter, item)
        return d

    d = _CoFunCaller(resultCollector=dofilter).coiterate(iterator)
    d.addCallback(lambda _: results)
    return d



def comap(function, iterator):
    """
    Applies function to each item in iterator returning a list of the return
    values of `function(item)`.
    """
    results = []
    cfc = _CoFunCaller(function, resultCollector=results.append)
    d = cfc.coiterate(iterator)
    d.addCallback(lambda _: results)
    return d



def cofold(function, initial, iterator):
    """
    Calls `function(accumulator, item)` for each item in iterator using the
    return value as the accumulator for the next item. `cofold` will return
    the last accumulator.
    """
    acc = [initial]

    def handleAcc(newAcc):
        acc[0] = newAcc

    def dofold(item):
        return function(acc[0], item)

    d = _CoFunCaller(dofold, resultCollector=handleAcc).coiterate(iterator)
    d.addCallback(lambda _: acc[0])
    return d



def cosum(iterator):
    """
    Sum all the items in iterator.  Implemented as
    `cofold(lambda a, b: a + b, 0, iterator)`.
    More of a toy than a useful primitive.
    """
    return cofold(lambda a, b: a + b, 0, iterator)



def cotakewhile(function, iterator):
    """
    Take items found in iterator and return them until an item is found where
    `function(item)` does not return true.
    """
    results = []

    def checkTake(shouldTake, item):
        if shouldTake == True:
            results.append(item)
            return item

    def dotake(item):
        d = maybeDeferred(function, item)
        d.addCallback(checkTake, item)
        return d

    def dostop(takeResult):
        return takeResult is None

    cfc = _CoFunCaller(resultCollector=dotake, stopFunction=dostop)
    return cfc.coiterate(iterator).addCallback(lambda _: results)



#
# Unit tests
#

from twisted.trial import unittest

class CotoolsTests(unittest.TestCase):
    def test_comap(self):
        def _checkResult(result):
            self.assertEquals(result, [0, 2, 4, 6, 8, 10])

        d = comap(lambda x: x * 2, [0, 1, 2, 3, 4, 5])
        d.addCallback(_checkResult)

        return d


    def test_comap_deferred(self):
        def _checkResult(result):
            self.assertEquals(result, [2, 4])

        d = comap(lambda x: x * 2, [succeed(1), succeed(2)])
        d.addCallback(_checkResult)

        return d


    def test_comap_deferred_function(self):
        def _checkResult(result):
            self.assertEquals(result, [2, 4])

        d = comap(lambda x: succeed(x * 2), [1, 2])
        d.addCallback(_checkResult)

        return d


    def test_cofold(self):
        def _checkResult(result):
            self.assertEquals(result, 15)

        d = cofold(lambda a, b: a + b, 0, [0, 1, 2, 3, 4, 5])
        d.addCallback(_checkResult)

        return d


    def test_cofold_deferred(self):
        def _checkResult(result):
            self.assertEquals(result, 15)

        d = cofold(lambda a, b: a + b, 0, [succeed(10), succeed(5)])
        d.addCallback(_checkResult)

        return d


    def test_cofold_deferred_function(self):
        def _checkResult(result):
            self.assertEquals(result, 15)

        d = cofold(lambda a, b: succeed(a + b), 0, [10, 5])
        d.addCallback(_checkResult)

        return d


    def test_cosum(self):
        def _checkResult(result):
            self.assertEquals(result, 15)
        d = cosum([0, 1, 2, 3, 4, 5])
        d.addCallback(_checkResult)

        return d



    def test_coforeach(self):
        results = []

        def _handleItem(i):
            results.append(i * 2)

        def _checkResult(_):
            self.assertEquals(results, [0, 2, 4, 6, 8, 10])

        d = coforeach(_handleItem, [0, 1, 2, 3, 4, 5])
        d.addCallback(_checkResult)

        return d


    def test_coforeach_deferred(self):
        results = []

        def _handleItem(i):
            results.append(i * 2)

        def _checkResult(_):
            self.assertEquals(results, [2, 4])

        d = coforeach(_handleItem, [succeed(1), succeed(2)])
        d.addCallback(_checkResult)

        return d


    def test_coforeach_deferred_function(self):
        results = []

        def _handleItem(i):
            results.append(i * 2)
            return succeed(None)

        def _checkResult(_):
            self.assertEquals(results, [2, 4])

        d = coforeach(_handleItem, [1, 2])
        d.addCallback(_checkResult)

        return d


    def test_cofilter(self):
        def _checkResult(result):
            self.assertEquals(result, [0, 2, 4, 6, 8, 10])

        d = cofilter(lambda x: x % 2 == 0, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        d.addCallback(_checkResult)

        return d


    def test_cofilter_deferred(self):
        def _checkResult(result):
            self.assertEquals(result, [2])

        d = cofilter(lambda x: x % 2 == 0, [succeed(1), succeed(2)])
        d.addCallback(_checkResult)

        return d


    def test_cofilter_deferred_function(self):
        def _checkResult(result):
            self.assertEquals(result, [2])

        d = cofilter(lambda x: succeed(x % 2 == 0), [1, 2])
        d.addCallback(_checkResult)

        return d


    def test_cotakewhile(self):
        def _checkResult(result):
            self.assertEqual(result, [0, 1, 2, 3, 4])

        d = cotakewhile(lambda x: x < 5, [0, 1, 2, 3, 4, 5])
        d.addCallback(_checkResult)

        return d


    def test_cotakewhile_deferred(self):
        def _checkResult(result):
            self.assertEquals(result, [1])

        d = cotakewhile(lambda x: x < 2, [succeed(1), succeed(2)])
        d.addCallback(_checkResult)

        return d


    def test_cotakewhile_deferred_function(self):
        def _checkResult(result):
            self.assertEquals(result, [1])

        d = cofilter(lambda x: succeed(x < 2), [1, 2])
        d.addCallback(_checkResult)

        return d
