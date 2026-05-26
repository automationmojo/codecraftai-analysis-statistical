"""
    .. module:: reader
        :synopsis: The :class:`Reader` abstract base class. Every reader
                   returns a ``(row, in_flags, cur_key, next_key)`` tuple so
                   the engine never branches on input mode.

    .. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"


from abc import ABC, abstractmethod


class Reader(ABC):
    """
        Abstract base for all engine input sources. Concrete readers implement
        :meth:`has_more` and :meth:`next_obs`. The engine's READ phase consumes
        readers uniformly; new input modes (databases, raw text, parquet, etc.)
        plug in as new :class:`Reader` subclasses with no engine changes.
    """

    @abstractmethod
    def has_more(self) -> bool:
        """
            Indicate whether additional observations are available.

            :returns: ``True`` when at least one more observation can be read.
        """

    @abstractmethod
    def next_obs(self) -> tuple[dict, dict, tuple | None, tuple | None]:
        """
            Read the next observation.

            :returns: A tuple ``(row, in_flags, cur_key, next_key)`` where:

                * ``row`` is a ``{var: value}`` dictionary,
                * ``in_flags`` is a ``{flag_name: 0|1}`` dictionary (empty for
                  single-source readers),
                * ``cur_key`` is the current BY-key tuple or ``None``,
                * ``next_key`` is the next BY-key tuple or ``None`` at EOF.
        """
