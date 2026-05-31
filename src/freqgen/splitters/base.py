"""Sentence splitter abstract interface."""

from abc import ABC, abstractmethod


class SentenceSplitter(ABC):
    """Split a long sentence into shorter independent sentences ."""

    @abstractmethod
    def split(self, sentence: str) -> list[str]:
        """Split a sentence. Returns list of short sentences (2-5 items).

        If the sentence is already short or splitting fails, returns [sentence].
        """
        ...
