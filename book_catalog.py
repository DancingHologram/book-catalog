#!/usr/bin/env python3

from __future__ import annotations

import ast
import json
from pathlib import Path
from pprint import pformat


CATALOG_FILE = Path("book_catalog.txt")


def default_catalog() -> dict[str, dict[str, object]]:
    return {
        "001": {
            "title": "To Kill a Mockingbird",
            "author": "Harper Lee",
            "year": 1960,
            "genre": "Fiction",
            "rating": 4.9,
        },
        "002": {
            "title": "1984",
            "author": "George Orwell",
            "year": 1949,
            "genre": "Dystopian",
            "rating": 4.8,
        },
        "003": {
            "title": "The Great Gatsby",
            "author": "F. Scott Fitzgerald",
            "year": 1925,
            "genre": "Tragedy",
            "rating": 4.5,
        },
        "004": {
            "title": "The Catcher in the Rye",
            "author": "J.D. Salinger",
            "year": 1951,
            "genre": "Fiction",
            "rating": 4.6,
        },
    }


def save_catalog(catalog: dict[str, dict[str, object]]) -> None:
    with CATALOG_FILE.open("w", encoding="utf-8") as file:
        json.dump(catalog, file, indent=4)


def load_catalog() -> dict[str, dict[str, object]]:
    if not CATALOG_FILE.exists():
        catalog = default_catalog()
        save_catalog(catalog)
        return catalog

    try:
        with CATALOG_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError:
        raw = CATALOG_FILE.read_text(encoding="utf-8").strip()
        if not raw:
            return {}

        try:
            legacy_data = ast.literal_eval(raw)
        except (SyntaxError, ValueError):
            print("Warning: book_catalog.txt is invalid JSON. Starting with an empty catalog.")
            return {}

        if isinstance(legacy_data, dict):
            save_catalog(legacy_data)
            print("Legacy catalog migrated to JSON format.")
            return legacy_data

        print("Warning: book_catalog.txt does not contain a valid catalog dictionary.")
        return {}

    if not isinstance(data, dict):
        print("Warning: book_catalog.txt does not contain a dictionary. Starting with an empty catalog.")
        return {}

    return data


def generate_book_id(catalog: dict[str, dict[str, object]]) -> str:
    numeric_ids = [int(book_id) for book_id in catalog if book_id.isdigit()]
    next_id = max(numeric_ids, default=0) + 1
    return f"{next_id:03d}"


def input_int(prompt: str) -> int:
    while True:
        value = input(prompt).strip()
        try:
            return int(value)
        except ValueError:
            print("Please enter a valid whole number.")


def input_rating(prompt: str) -> float:
    while True:
        value = input(prompt).strip()
        try:
            rating = float(value)
        except ValueError:
            print("Please enter a valid number between 0 and 5.")
            continue

        if 0 <= rating <= 5:
            return round(rating, 2)
        print("Rating must be between 0 and 5.")


def format_rows(catalog: dict[str, dict[str, object]]) -> list[list[str]]:
    rows: list[list[str]] = []
    for book_id, details in sorted(catalog.items(), key=lambda item: item[0]):
        rows.append(
            [
                str(book_id),
                str(details.get("title", "")),
                str(details.get("author", "")),
                str(details.get("year", "")),
                str(details.get("genre", "")),
                f"{float(details.get('rating', 0)):.2f}",
            ]
        )
    return rows


def print_books_table(catalog: dict[str, dict[str, object]]) -> None:
    if not catalog:
        print("No books found.")
        return

    headers = ["ID", "Title", "Author", "Year", "Genre", "Rating"]
    rows = format_rows(catalog)

    widths = [len(header) for header in headers]
    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))

    def format_row(row: list[str], header: bool = False) -> str:
        cells: list[str] = []
        for index, value in enumerate(row):
            if index == 5 and not header:
                cells.append(value.rjust(widths[index]))
            else:
                cells.append(value.ljust(widths[index]))
        return "| " + " | ".join(cells) + " |"

    separator = "+-" + "-+-".join("-" * width for width in widths) + "-+"
    print(separator)
    print(format_row(headers, header=True))
    print(separator)
    for row in rows:
        print(format_row(row))
    print(separator)


def add_book(catalog: dict[str, dict[str, object]]) -> None:
    print("Add a New Book")
    custom_id = input("Book ID (leave blank to auto-generate): ").strip()
    if custom_id:
        if custom_id in catalog:
            print(f"Book ID {custom_id} already exists.")
            return
        book_id = custom_id
    else:
        book_id = generate_book_id(catalog)

    title = input("Title: ").strip()
    author = input("Author: ").strip()
    year = input_int("Year of publication: ")
    genre = input("Genre: ").strip()
    rating = input_rating("Average rating (0 to 5): ")

    catalog[book_id] = {
        "title": title,
        "author": author,
        "year": year,
        "genre": genre,
        "rating": rating,
    }
    save_catalog(catalog)
    print(f"Book {book_id} added successfully.")


def search_by_title(catalog: dict[str, dict[str, object]]) -> None:
    query = input("Enter title keyword: ").strip().lower()
    results = {
        book_id: details
        for book_id, details in catalog.items()
        if query in str(details.get("title", "")).lower()
    }
    print_books_table(results)


def search_by_author(catalog: dict[str, dict[str, object]]) -> None:
    query = input("Enter author keyword: ").strip().lower()
    results = {
        book_id: details
        for book_id, details in catalog.items()
        if query in str(details.get("author", "")).lower()
    }
    print_books_table(results)


def search_by_year(catalog: dict[str, dict[str, object]]) -> None:
    year = input_int("Enter publication year: ")
    results = {
        book_id: details
        for book_id, details in catalog.items()
        if int(details.get("year", -1)) == year
    }
    print_books_table(results)


def update_book(catalog: dict[str, dict[str, object]]) -> None:
    book_id = input("Enter book ID to update: ").strip()
    if book_id not in catalog:
        print(f"Book ID {book_id} not found.")
        return

    print("What do you want to update?")
    print("1. rating")
    print("2. genre")
    choice = input("Enter choice (1 or 2): ").strip()

    if choice == "1":
        catalog[book_id]["rating"] = input_rating("New rating (0 to 5): ")
        save_catalog(catalog)
        print("Rating updated successfully.")
    elif choice == "2":
        catalog[book_id]["genre"] = input("New genre: ").strip()
        save_catalog(catalog)
        print("Genre updated successfully.")
    else:
        print("Invalid choice.")


def delete_book(catalog: dict[str, dict[str, object]]) -> None:
    book_id = input("Enter book ID to delete: ").strip()
    if book_id in catalog:
        confirm = input(f"Are you sure you want to delete book {book_id}? (y/n): ").strip().lower()
        if confirm != "y":
            print("Delete cancelled.")
            return
        del catalog[book_id]
        save_catalog(catalog)
        print(f"Book {book_id} deleted successfully.")
    else:
        print(f"Book ID {book_id} not found.")


def top_rated_books(catalog: dict[str, dict[str, object]]) -> None:
    ranked = sorted(
        catalog.items(),
        key=lambda item: float(item[1].get("rating", 0)),
        reverse=True,
    )
    top_three = dict(ranked[:3])
    print_books_table(top_three)


def export_catalog(catalog: dict[str, dict[str, object]]) -> None:
    save_catalog(catalog)
    print("Catalog exported successfully!")


def import_catalog() -> dict[str, dict[str, object]]:
    catalog = load_catalog()
    print("Catalog imported successfully!")
    print("Imported Catalog:", pformat(catalog, sort_dicts=False))
    return catalog


def display_menu() -> None:
    print("\nCommand Menu:\n")
    print("           add - Add a Book")
    print("           view - View All Books")
    print("           search_by_title - Search for a Book by Title")
    print("           search_by_author - Search for a Book by Author")
    print("           search_by_year - Search for a Book by Year")
    print("           update - Update a Book (rating or genre)")
    print("           delete - Delete a Book")
    print("           top_rated - Top Rated Books")
    print("           export - Export to Catalog")
    print("           import - Import Catalog")
    print("           exit - exit program")


def main() -> None:
    catalog = load_catalog()
    display_menu()

    while True:
        print()
        command = input("Command: ").strip().lower()

        if command == "add":
            add_book(catalog)
        elif command == "view":
            catalog = load_catalog()
            print_books_table(catalog)
        elif command == "search_by_title":
            search_by_title(catalog)
        elif command == "search_by_author":
            search_by_author(catalog)
        elif command == "search_by_year":
            search_by_year(catalog)
        elif command == "update":
            update_book(catalog)
        elif command == "delete":
            delete_book(catalog)
        elif command == "top_rated":
            top_rated_books(catalog)
        elif command == "export":
            export_catalog(catalog)
        elif command == "import":
            catalog = import_catalog()
        elif command == "exit":
            print("Exiting program.")
            break
        else:
            print("Unknown command. Please try again.")


if __name__ == "__main__":
    main()
