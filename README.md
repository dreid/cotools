# cotools

cotools is a collection of functional programming primitives that make use of
the cooperative multitasking facilities found in Twisted.

The goal is to provide a more comfortable mechanism for breaking up and
cooperatively scheduling computation than those discussed in my talk
[Cooperative Multitasking with Twisted](http://speakerdeck.com/u/dreid/p/cooperative-multitasking-with-twisted-getting-things-done-concurrently) ([video](http://blip.tv/pycon-us-videos-2009-2010-2011/pycon-2010-cooperative-multitasking-with-twisted-getting-things-done-concurrently-11-3277759))
where I discuss how to break up and schedule work using `reactor.callLater`
and `twisted.internet.task.coiterate`.  The primitives provided by cotools
utilize `twisted.internet.task.coiterate` and also attempt to be fully
`Deferred` aware.  Meaning that `Deferred`s are valid values as iterators,
in iterators, and as return values of the functions to be applied to the
items in the iterators.

I admit that these examples are rather contrived and the implementation
though having significant test coverage may not be optimal or performant.
My goal is more to facilitate discussion about how to make Cooperative
Multitasking a more comfortable programming paradigm and to attempt to give
novice Twisted users some level of cooperation 'for free'.


## Non-blocking vs Cooperative

These primitives much like the `Deferred` they are built on do not magically
make your code non-blocking.  The primary unit of work is the item in the
iterator and whatever function does with that item may block your
application for any period of time.


## Primitives

All primitives return a Deferred which will callback when iteration is
completed.  For the purposes of brevity in the documentation "returns"
always means "returns a `Deferred` that callbacks with" unless otherwise
noted.

* `coforeach(function, iterator)` - Applies function to each item in iterator.
* `comap(function, iterator)` - Applies function to each item in iterator returning a list of the return values of `function(item)`.
* `cofilter(function, iterator)` - Return items in iterator for which `function(item)` returns True.
* `cofold(funciton, accumulator, iterator)` - Calls `function(accumulator, item)` for each item in iterator using the return value as the accumulator for the next item. `cofold` will return the last accumulator.
* `cotakewhile(function, iterator)` - Take items found in iterator and return them until an item is found where `function(item)` does not return true.
* `cosum(iterator)` - Sum all the items in iterator.  Implemented as `cofold(lambda a, b: a + b, 0, iterator)`.  More of a toy than a useful primitive.


## Examples

    def printr(r):
        print r

    def double(x):
        return x * 2

    d = comap(double, xrange(0, 5))
    d.addCallback(printr)

The above would print `[0, 2, 4, 6, 8]`.

    d = cosum(comap(double, xrange(0, 5)))
    d.addCallback(printr)

This would print `20`


