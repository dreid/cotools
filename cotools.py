from twisted.internet.task import coiterate
from twisted.internet.defer import maybeDeferred, succeed

def coforeach(function, iterator, _coiterate=coiterate):
    def _do_foreach(iterator):
        for item in iterator:
            d = maybeDeferred(lambda: item)
            d.addCallback(lambda i: function(i))

            yield d

    return _coiterate(_do_foreach(iterator))


def cosum(iterator, _coiterate=coiterate):
    return cofoldl(lambda a, b: a + b, 0, iterator, _coiterate=coiterate)


def cofilter(function, iterator, _coiterate=coiterate):
    results = []

    def _filterResult(item):
        def _checkFilter(res, item):
            if res == True:
                results.append(item)

        d = maybeDeferred(function, item)
        d.addCallback(_checkFilter, item)
        return d

    def _do_filter(iterator):
        for item in iterator:
            d = maybeDeferred(lambda: item)
            d.addCallback(_filterResult)
            yield d

    return _coiterate(_do_filter(iterator)).addCallback(lambda _: results)

def comap(function, iterator, _coiterate=coiterate):
    results = []

    def _do_map(iterator):
        for item in iterator:
            d = maybeDeferred(lambda: item)
            d.addCallback(lambda i: function(i))
            d.addCallback(results.append)
            yield d

    return _coiterate(_do_map(iterator)).addCallback(lambda _: results)


class _CoFolder(object):
    def __init__(self, function, initial, iterator):
        self._iterator = iterator
        self._function = function
        self._acc = initial

    def getAcc(self):
        return self._acc

    def _setAcc(self, acc):
        self._acc = acc

    def dofold(self):
        for item in self._iterator:
            d = maybeDeferred(lambda: item)
            d.addCallback(lambda b: self._function(self._acc, b))
            d.addCallback(self._setAcc)
            yield d


def cofoldl(function, initial, iterator, _coiterate=coiterate):
    folder = _CoFolder(function, initial, iterator)
    return _coiterate(folder.dofold()).addCallback(lambda _: folder.getAcc())

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

    def test_cofoldl(self):
        def _checkResult(result):
            self.assertEquals(result, 15)

        d = cofoldl(lambda a, b: a + b, 0, [0, 1, 2, 3, 4, 5])
        d.addCallback(_checkResult)

        return d

    def test_cofoldl_deferred(self):
        def _checkResult(result):
            self.assertEquals(result, 15)

        d = cofoldl(lambda a, b: a + b, 0, [succeed(10), succeed(5)])
        d.addCallback(_checkResult)

        return d

    def test_cofoldl_deferred_function(self):
        def _checkResult(result):
            self.assertEquals(result, 15)

        d = cofoldl(lambda a, b: succeed(a + b), 0, [10, 5])
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
