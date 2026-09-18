import heapq
import string
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from functools import reduce
from typing import Any

import matplotlib.pyplot as plt
import requests


def get_text(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Перевірка на помилки HTTP
        return response.text
    except requests.RequestException:
        return None


# Функція для видалення знаків пунктуації
def remove_punctuation(text):
    return text.translate(str.maketrans("", "", string.punctuation))


def map_chunk(chunk: list[str]):
    return [map_word(word) for word in chunk]


def map_word(word: str):
    return word.lower(), 1


def shuffle_function(mapped_values):
    reduced_chunks = reduce(lambda acc, x: acc + x, mapped_values, [])
    shuffled = defaultdict(list)
    for key, value in reduced_chunks:
        shuffled[key].append(value)
    return shuffled.items()


def reduce_function(key_values):
    key, values = key_values
    return key, sum(values)


# Виконання MapReduce
def map_reduce(text, chunk_size=100, search_words=None):
    # Видалення знаків пунктуації
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
