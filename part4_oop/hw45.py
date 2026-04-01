from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

from part4_oop.interfaces import Cache, HasCache, Policy, Storage

K = TypeVar("K")
V = TypeVar("V")


@dataclass
class DictStorage(Storage[K, V]):
    _data: dict[K, V] = field(default_factory=dict, init=False)

    def set(self, key: K, value: V) -> None:
        self._data[key] = value

    def get(self, key: K) -> V | None:
        return self._data.get(key)

    def exists(self, key: K) -> bool:
        return key in self._data

    def remove(self, key: K) -> None:
        self._data.pop(key, None)

    def clear(self) -> None:
        self._data.clear()


@dataclass
class FIFOPolicy(Policy[K]):
    capacity: int = 5
    _order: list[K] = field(default_factory=list, init=False)

    def register_access(self, key: K) -> None:
        if key in self._order:
            return
        self._order.append(key)

    def get_key_to_evict(self) -> K | None:
        if len(self._order) > self.capacity:
            return self._order[0]
        return None

    def remove_key(self, key: K) -> None:
        if key in self._order:
            self._order.remove(key)

    def clear(self) -> None:
        self._order.clear()

    @property
    def has_keys(self) -> bool:
        return bool(self._order)


@dataclass
class LRUPolicy(Policy[K]):
    capacity: int = 5
    _order: list[K] = field(default_factory=list, init=False)

    def register_access(self, key: K) -> None:
        if key in self._order:
            self._order.remove(key)
        self._order.append(key)

    def get_key_to_evict(self) -> K | None:
        if len(self._order) > self.capacity:
            return self._order[0]
        return None

    def remove_key(self, key: K) -> None:
        if key in self._order:
            self._order.remove(key)

    def clear(self) -> None:
        self._order.clear()

    @property
    def has_keys(self) -> bool:
        return bool(self._order)


@dataclass
class LFUPolicy(Policy[K]):
    capacity: int = 5
    _key_counter: dict[K, int] = field(default_factory=dict, init=False)
    _order: list[K] = field(default_factory=list, init=False)

    def register_access(self, key: K) -> None:
        current = self._key_counter.get(key)

        if current is not None:
            self._key_counter[key] = current + 1
            return

        self._key_counter[key] = 1
        self._order.append(key)

    def get_key_to_evict(self) -> K | None:
        if len(self._key_counter) <= self.capacity:
            return None

        candidates = self._order[:-1]

        min_count = min(self._key_counter[key] for key in candidates)

        for key in candidates:
            if self._key_counter[key] == min_count:
                return key

        return None

    def remove_key(self, key: K) -> None:
        self._key_counter.pop(key, None)
        if key in self._order:
            self._order.remove(key)

    def clear(self) -> None:
        self._key_counter.clear()
        self._order.clear()

    @property
    def has_keys(self) -> bool:
        return bool(self._key_counter)


class MIPTCache(Cache[K, V]):
    def __init__(self, storage: Storage[K, V], policy: Policy[K]) -> None:
        self.storage = storage
        self.policy = policy

    def set(self, key: K, value: V) -> None:
        self.storage.set(key, value)
        self.policy.register_access(key)

        evict_key = self.policy.get_key_to_evict()
        if evict_key is not None:
            self.storage.remove(evict_key)
            self.policy.remove_key(evict_key)

    def get(self, key: K) -> V | None:
        if not self.storage.exists(key):
            return None

        self.policy.register_access(key)
        return self.storage.get(key)

    def exists(self, key: K) -> bool:
        return self.storage.exists(key)

    def remove(self, key: K) -> None:
        self.storage.remove(key)
        self.policy.remove_key(key)

    def clear(self) -> None:
        self.storage.clear()
        self.policy.clear()


class CachedProperty[V]:
    def __init__(self, func: Callable[..., V]) -> None:
        self._func = func
        self._name = func.__name__

    def __get__(
        self,
        instance: HasCache[Any, Any] | None,
        owner: type,
    ) -> Any:
        if instance is None:
            return self

        cache = instance.cache

        value = cache.get(self._name)
        if value is not None:
            return value

        value = self._func(instance)
        cache.set(self._name, value)
        return value
