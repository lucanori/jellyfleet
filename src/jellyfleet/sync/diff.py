from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable

from .server_comparisons import (
    compare_libraries,
    compare_server_configs,
)
from .user_comparisons import (
    compare_user_configs,
    compare_user_policies,
    compare_users,
)

T = TypeVar("T")


class DiffResult:
    def __init__(
        self, added: list[T], removed: list[T], modified: list[tuple[T, T]]
    ) -> None:
        self.added = added
        self.removed = removed
        self.modified = modified

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.modified)

    @property
    def total_changes(self) -> int:
        return len(self.added) + len(self.removed) + len(self.modified)


def compute_diff(
    source_items: list[T],
    target_items: list[T],
    key_func: Callable[[T], str],
    compare_func: Callable[[T, T], bool] | None = None,
) -> DiffResult:
    source_dict = {key_func(item): item for item in source_items}
    target_dict = {key_func(item): item for item in target_items}

    source_keys = set(source_dict.keys())
    target_keys = set(target_dict.keys())

    added_keys = source_keys - target_keys
    removed_keys = target_keys - source_keys
    common_keys = source_keys & target_keys

    added = [source_dict[key] for key in added_keys]
    removed = [target_dict[key] for key in removed_keys]

    modified = []
    if compare_func:
        for key in common_keys:
            source_item = source_dict[key]
            target_item = target_dict[key]
            if not compare_func(source_item, target_item):
                modified.append((source_item, target_item))

    return DiffResult(added, removed, modified)


__all__ = [
    "DiffResult",
    "compare_libraries",
    "compare_server_configs",
    "compare_user_configs",
    "compare_user_policies",
    "compare_users",
    "compute_diff",
]
