"""
Asynchronous progressbar decorator for iterators.
Includes a default `range` iterator printing to `stderr`.

Usage:
>>> from tqdm.asyncio import trange, tqdm
>>> async for i in trange(10):
...     ...
"""
from .std import tqdm as std_tqdm
from .utils import ensure_lock
import asyncio
__author__ = {"github.com/": ["casperdcl"]}
__all__ = ['tqdm_asyncio', 'tarange', 'tqdm', 'trange']


class tqdm_asyncio(std_tqdm):
    """
    Asynchronous-friendly version of tqdm (Python 3.5+).
    """
    def __init__(self, iterable=None, *args, **kwargs):
        super(tqdm_asyncio, self).__init__(iterable, *args, **kwargs)
        self.iterable_awaitable = False
        if iterable is not None:
            if hasattr(iterable, "__anext__"):
                self.iterable_next = iterable.__anext__
                self.iterable_awaitable = True
            elif hasattr(iterable, "__next__"):
                self.iterable_next = iterable.__next__
            else:
                self.iterable_iterator = iter(iterable)
                self.iterable_next = self.iterable_iterator.__next__

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            if self.iterable_awaitable:
                res = await self.iterable_next()
            else:
                res = self.iterable_next()
            self.update()
            return res
        except StopIteration:
            self.close()
            raise StopAsyncIteration
        except:
            self.close()
            raise

    def send(self, *args, **kwargs):
        return self.iterable.send(*args, **kwargs)

    @classmethod
    def as_completed(cls, fs, *, loop=None, timeout=None, total=None,
                     lock_name="", **tqdm_kwargs):
        """
        Wrapper for `asyncio.as_completed`.
        """
        if total is None:
            total = len(fs)
        with ensure_lock(cls, lock_name=lock_name):
            yield from cls(asyncio.as_completed(fs, loop=loop, timeout=timeout),
                           total=total, **tqdm_kwargs)

    @classmethod
    async def map_async(cls, fn, *iterables, **kwargs):
        """
        Equivalent of `[(await i) for i in map(fn, *iterables)]`.

        Parameters
        ----------
        kwargs  : optional
            Passed to `cls.as_completed`.
        """
        with ensure_lock(cls, lock_name=kwargs.get('lock_name', "")):
            tasks = [asyncio.create_task(i) for i in map(fn, *iterables)]
            _ = [await i for i in cls.as_completed(tasks, **kwargs)]
        return [i.result() for i in tasks]


def tarange(*args, **kwargs):
    """
    A shortcut for `tqdm.asyncio.tqdm(range(*args), **kwargs)`.
    """
    return tqdm_asyncio(range(*args), **kwargs)


# Aliases
tqdm = tqdm_asyncio
trange = tarange