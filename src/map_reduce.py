"""Download text from a URL, count word frequencies with MapReduce, and plot the top words."""

import heapq
import string
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from functools import reduce
from typing import Any

import matplotlib.pyplot as plt
import requests


def get_text(url):
    """Fetch the document body from ``url``.

    Args:
        url: HTTP(S) address of the text to download.

    Returns:
        Response text on success, or ``None`` if the request fails.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Перевірка на помилки HTTP
        return response.text
    except requests.RequestException:
        return None


def remove_punctuation(text):
    """Strip ASCII punctuation characters from ``text``.

    Args:
        text: Raw input string.

    Returns:
        ``text`` with punctuation removed.
    """
    return text.translate(str.maketrans("", "", string.punctuation))


def map_chunk(chunk: list[str]):
    """Map every word in a chunk to a ``(word, 1)`` pair.

    Args:
        chunk: Consecutive words from the tokenized text.

    Returns:
        Mapped pairs produced by :func:`map_word`.
    """
    return [(word.lower(), 1) for word in chunk]


def shuffle_function(mapped_values):
    """Group mapped counts by word (the shuffle step).

    Args:
        mapped_values: Iterable of per-chunk lists of ``(word, 1)`` pairs.

    Returns:
        Items of a mapping from word to a list of partial counts.
    """
    reduced_chunks = reduce(lambda acc, x: acc + x, mapped_values, [])
    shuffled = defaultdict(list)
    for key, value in reduced_chunks:
        shuffled[key].append(value)
    return shuffled.items()


def reduce_function(key_values):
    """Sum partial counts for one word (the reduce step).

    Args:
        key_values: A ``(word, counts)`` pair from the shuffle step.

    Returns:
        A ``(word, total_count)`` pair.
    """
    key, values = key_values
    return key, sum(values)


def map_reduce(text, chunk_size=100, search_words=None):
    """Count word frequencies in ``text`` using a parallel MapReduce pipeline.

    Args:
        text: Input document.
        chunk_size: Number of words processed by each map worker.
        search_words: If given, keep only these tokens before mapping.

    Returns:
        Mapping from lowercase word to occurrence count.
    """
    text = remove_punctuation(text)
    words = text.split()

    # Якщо задано список слів для пошуку, враховувати тільки ці слова
    if search_words:
        words = [word for word in words if word in search_words]

    chunks = []
    for i in range(0, len(words), chunk_size):
        chunks.append(words[i : i + chunk_size])

    # Паралельний Мапінг
    with ProcessPoolExecutor(max_workers=5) as executor:
        mapped_values = list(executor.map(map_chunk, chunks))

        # Крок 2: Shuffle
        shuffled_values = shuffle_function(mapped_values)

        # Паралельна Редукція
        reduced_values = list(executor.map(reduce_function, shuffled_values))

    return dict(reduced_values)


def visualize_top_words(words: dict[Any, int], N: int = 10):
    """Draw a horizontal bar chart of the ``N`` most frequent words.

    Args:
        words: Mapping from word to occurrence count.
        N: How many top words to display. Defaults to ``10``.
    """
    top = heapq.nlargest(N, words.items(), key=lambda item: item[1])
    labels = [word for word, _ in top]
    counts = [count for _, count in top]
    positions = range(len(labels))

    # Use numeric y positions; passing string labels to plot() makes matplotlib
    # hash numpy arrays internally and raises TypeError: unhashable type.
    fig, ax = plt.subplots()
    ax.barh(positions, counts)
    ax.set_yticks(positions, labels)
    ax.set_xlabel("Occurrences")
    ax.set_ylabel("Words")
    ax.set_title(f"Top {N} occurences")
    ax.invert_yaxis()
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    # Вхідний текст для обробки
    url = "https://gutenberg.net.au/ebooks01/0100021.txt"
    text = get_text(url)
    if text:
        # Виконання MapReduce на вхідному тексті
        result = map_reduce(text)
        visualize_top_words(result)
    else:
        print("Помилка: Не вдалося отримати вхідний текст.")
