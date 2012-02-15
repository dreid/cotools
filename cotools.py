from twisted.internet.task import coiterate
from twisted.internet.defer import maybeDeferred, Deferred

def coforeach(func, iterator, _coiterate=coiterate):
    def _do_foreach(iterator):
        for item in iterator:
            d = maybeDeferred(lambda: item)
            d.addCallback(lambda i: func(i))

            yield d

    return _coiterate(_do_foreach(iterator))


def cosum(iterator, _coiterate=coiterate):
    return cofoldl(lambda a, b: a + b, 0, iterator, _coiterate=coiterate)


def comap(func, iterator, _coiterate=coiterate):
    results = []

    def _do_map(iterator):
        for item in iterator:
            d = maybeDeferred(lambda: item)
            d.addCallback(lambda i: func(i))
            d.addCallback(results.append)
            yield d

    return _coiterate(_do_map(iterator)).addCallback(lambda _: results)


class _CoFolder(object):
    def __init__(self, func, initial, iterator):
        self._iterator = iterator
        self._func = func
        self._acc = initial

    def getAcc(self):
        return self._acc

    def _setAcc(self, acc):
        self._acc = acc

    def dofold(self):
        for item in self._iterator:
            d = maybeDeferred(lambda: item)
            d.addCallback(lambda b: self._func(self._acc, b))
            d.addCallback(self._setAcc)
            yield d


def cofoldl(func, initial, iterator, _coiterate=coiterate):
    folder = _CoFolder(func, initial, iterator)
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
        deferreds = [Deferred(), Deferred()]

        def _checkResult(result):
            self.assertEquals(result, [2, 4])

        d = comap(lambda x: x * 2, deferreds)
        d.addCallback(_checkResult)

        deferreds[0].callback(1)
        deferreds[1].callback(2)

        return d

    def test_cofoldl(self):
        def _checkResult(result):
            self.assertEquals(result, 15)

        d = cofoldl(lambda a, b: a + b, 0, [0, 1, 2, 3, 4, 5])
        d.addCallback(_checkResult)

        return d

    def test_cofoldl_deferred(self):
        deferreds = [Deferred(), Deferred()]

        def _checkResult(result):
            self.assertEquals(result, 15)

        d = cofoldl(lambda a, b: a + b, 0, deferreds)
        d.addCallback(_checkResult)

        deferreds[0].callback(10)
        deferreds[1].callback(5)

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
