import multiprocessing
from multiprocessing.queues import Queue


class Counter(object):
    def __init__(self, n=0):
        self.count = multiprocessing.Value("i", n)

    def increment(self, n=1):
        """ Increment the counter by n (default = 1) """
        with self.count.get_lock():
            self.count.value += n

    @property
    def value(self):
        """ Return the value of the counter """
        return self.count.value


class WaluigiQueue(Queue):
    def __init__(self):
        super().__init__(ctx=multiprocessing.get_context())
        self.size = Counter(0)

    def __getstate__(self):
        return {
            "parent_state": super().__getstate__(),
            "size": self.size,
        }

    def __setstate__(self, state):
        super().__setstate__(state["parent_state"])
        self.size = state["size"]

    def put(self, *args, **kwargs):
        super().put(*args, **kwargs)
        self.size.increment(1)

    def get(self, *args, **kwargs):
        item = super().get(*args, **kwargs)
        self.size.increment(-1)
        return item

    def qsize(self):
        return self.size.value

    def empty(self):
        return not self.qsize()
