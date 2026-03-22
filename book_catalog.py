#!/usr/bin/env python3

# This program provides a GUI-based Book Catalog manager.
# It stores book records in an embedded dictionary and persists data in JSON.

# I want to make this program use an API call in the future to pull data about books from the internet and make it more dynamic.
# For example, we could use the Open Library API (https://openlibrary.org/developers/api) to fetch book details by ISBN.


from __future__ import annotations

# ast is kept only for one-time migration from older non-JSON file content.
import ast
import json
from pathlib import Path
from pprint import pformat
import tkinter as tk
from tkinter import messagebox, ttk

# Path to the file used for saving/loading the catalog.
CATALOG_FILE = Path("book_catalog.txt")


def default_catalog() -> dict[str, dict[str, object]]:
    # The initial sample records used when the storage file does not exist yet.
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
    # Write the current in-memory dictionary to disk as pretty JSON.
    with CATALOG_FILE.open("w", encoding="utf-8") as file:
        json.dump(catalog, file, indent=4)


def load_catalog() -> dict[str, dict[str, object]]:
    # If there is no file yet, create one using default data.
    if not CATALOG_FILE.exists():
        catalog = default_catalog()
        save_catalog(catalog)
        return catalog

    try:
        # Normal path: load JSON from file.
        with CATALOG_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError:
        # Compatibility path: try reading older Python-dict string format once.
        raw = CATALOG_FILE.read_text(encoding="utf-8").strip()
        if not raw:
            return {}

        try:
            legacy_data = ast.literal_eval(raw)
        except (SyntaxError, ValueError):
            # If neither JSON nor legacy format can be parsed, start clean.
            return {}

        if isinstance(legacy_data, dict):
            # Migrate parsed legacy data into JSON format and keep it.
            save_catalog(legacy_data)
            return legacy_data

        return {}

    if not isinstance(data, dict):
        # Safety check: the top-level JSON must be a dictionary.
        return {}

    return data


def generate_book_id(catalog: dict[str, dict[str, object]]) -> str:
    # Auto-generated IDs are 3-digit strings like 001, 002, 003.
    numeric_ids = [int(book_id) for book_id in catalog if book_id.isdigit()]
    next_id = max(numeric_ids, default=0) + 1
    return f"{next_id:03d}"


def parse_year(year_text: str) -> int:
    # Convert a year string to int and raise ValueError with a clear message if invalid.
    try:
        return int(year_text)
    except ValueError as error:
        raise ValueError("Year must be a whole number.") from error


def parse_rating(rating_text: str) -> float:
    # Convert rating to float and enforce the allowed range [0, 5].
    try:
        rating = float(rating_text)
    except ValueError as error:
        raise ValueError("Rating must be a number between 0 and 5.") from error

    if not 0 <= rating <= 5:
        raise ValueError("Rating must be between 0 and 5.")
    return round(rating, 2)


class BookCatalogApp(tk.Tk):
    # Main window class. Inherits from Tk so we can create widgets and event handlers.
    def __init__(self) -> None:
        super().__init__()

        # Window title and size for a desktop-friendly layout.
        self.title("Book Catalog (GUI)")
        self.geometry("1100x700")
        self.minsize(1000, 620)

        # In-memory working copy of the catalog loaded from JSON file.
        self.catalog: dict[str, dict[str, object]] = load_catalog()

        # Build all GUI sections, then show current records in the table.
        self._build_form_section()
        self._build_action_buttons()
        self._build_search_section()
        self._build_table_section()
        self._build_status_section()
        self.refresh_table(self.catalog)

    def _build_form_section(self) -> None:
        # Form frame contains input fields used to add books and edit selected books.
        form_frame = ttk.LabelFrame(self, text="Book Details")
        form_frame.pack(fill="x", padx=10, pady=(10, 6))

        # StringVar values keep widget input easy to read/write from code.
        self.book_id_var = tk.StringVar()
        self.title_var = tk.StringVar()
        self.author_var = tk.StringVar()
        self.year_var = tk.StringVar()
        self.genre_var = tk.StringVar()
        self.rating_var = tk.StringVar()

        # Left side fields: ID, Title, Author.
        ttk.Label(form_frame, text="Book ID (optional):").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        ttk.Entry(form_frame, textvariable=self.book_id_var, width=24).grid(row=0, column=1, padx=6, pady=6, sticky="w")

        ttk.Label(form_frame, text="Title:").grid(row=1, column=0, padx=6, pady=6, sticky="w")
        ttk.Entry(form_frame, textvariable=self.title_var, width=40).grid(row=1, column=1, padx=6, pady=6, sticky="w")

        ttk.Label(form_frame, text="Author:").grid(row=2, column=0, padx=6, pady=6, sticky="w")
        ttk.Entry(form_frame, textvariable=self.author_var, width=40).grid(row=2, column=1, padx=6, pady=6, sticky="w")

        # Right side fields: Year, Genre, Rating.
        ttk.Label(form_frame, text="Year:").grid(row=0, column=2, padx=6, pady=6, sticky="w")
        ttk.Entry(form_frame, textvariable=self.year_var, width=16).grid(row=0, column=3, padx=6, pady=6, sticky="w")

        ttk.Label(form_frame, text="Genre:").grid(row=1, column=2, padx=6, pady=6, sticky="w")
        ttk.Entry(form_frame, textvariable=self.genre_var, width=24).grid(row=1, column=3, padx=6, pady=6, sticky="w")

        ttk.Label(form_frame, text="Rating (0-5):").grid(row=2, column=2, padx=6, pady=6, sticky="w")
        ttk.Entry(form_frame, textvariable=self.rating_var, width=16).grid(row=2, column=3, padx=6, pady=6, sticky="w")

    def _build_action_buttons(self) -> None:
        # Action buttons map directly to catalog operations.
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", padx=10, pady=6)

        ttk.Button(button_frame, text="Add Book", command=self.add_book).pack(side="left", padx=4)
        ttk.Button(button_frame, text="View All", command=self.view_all_books).pack(side="left", padx=4)
        ttk.Button(button_frame, text="Update Selected", command=self.update_selected_book).pack(side="left", padx=4)
        ttk.Button(button_frame, text="Delete Selected", command=self.delete_selected_book).pack(side="left", padx=4)
        ttk.Button(button_frame, text="Top Rated (3)", command=self.show_top_rated).pack(side="left", padx=4)
        ttk.Button(button_frame, text="Export", command=self.export_catalog).pack(side="left", padx=4)
        ttk.Button(button_frame, text="Import", command=self.import_catalog).pack(side="left", padx=4)
        ttk.Button(button_frame, text="Clear Form", command=self.clear_form).pack(side="left", padx=4)

    def _build_search_section(self) -> None:
        # Search section allows filtering by title, author, or year.
        search_frame = ttk.LabelFrame(self, text="Search")
        search_frame.pack(fill="x", padx=10, pady=6)

        self.search_var = tk.StringVar()
        ttk.Label(search_frame, text="Search value:").pack(side="left", padx=(8, 4), pady=8)
        ttk.Entry(search_frame, textvariable=self.search_var, width=40).pack(side="left", padx=4, pady=8)
        ttk.Button(search_frame, text="By Title", command=self.search_by_title).pack(side="left", padx=4)
        ttk.Button(search_frame, text="By Author", command=self.search_by_author).pack(side="left", padx=4)
        ttk.Button(search_frame, text="By Year", command=self.search_by_year).pack(side="left", padx=4)

    def _build_table_section(self) -> None:
        # Table frame shows books in a grid-like structure.
        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=6)

        columns = ("id", "title", "author", "year", "genre", "rating")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        # Configure each column heading and width.
        self.tree.heading("id", text="ID")
        self.tree.heading("title", text="Title")
        self.tree.heading("author", text="Author")
        self.tree.heading("year", text="Year")
        self.tree.heading("genre", text="Genre")
        self.tree.heading("rating", text="Rating")

        # Left align all columns except rating, which is right aligned.
        self.tree.column("id", width=90, anchor="w")
        self.tree.column("title", width=280, anchor="w")
        self.tree.column("author", width=220, anchor="w")
        self.tree.column("year", width=90, anchor="w")
        self.tree.column("genre", width=160, anchor="w")
        self.tree.column("rating", width=100, anchor="e")

        # Add scrollbars so the table remains usable when data grows.
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        # When a row is selected, copy values into form fields for easy editing.
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

    def _build_status_section(self) -> None:
        # Status area is used for friendly operation feedback and import preview text.
        status_frame = ttk.LabelFrame(self, text="Status")
        status_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(status_frame, textvariable=self.status_var).pack(anchor="w", padx=8, pady=8)

    def refresh_table(self, source_catalog: dict[str, dict[str, object]]) -> None:
        # Remove current rows, then repopulate from the provided source dictionary.
        for item in self.tree.get_children():
            self.tree.delete(item)

        for book_id, details in sorted(source_catalog.items(), key=lambda item: item[0]):
            self.tree.insert(
                "",
                "end",
                values=(
                    book_id,
                    str(details.get("title", "")),
                    str(details.get("author", "")),
                    str(details.get("year", "")),
                    str(details.get("genre", "")),
                    f"{float(details.get('rating', 0)):.2f}",
                ),
            )

    def clear_form(self) -> None:
        # Reset all data-entry fields to blank.
        self.book_id_var.set("")
        self.title_var.set("")
        self.author_var.set("")
        self.year_var.set("")
        self.genre_var.set("")
        self.rating_var.set("")

    def on_row_select(self, _event: tk.Event) -> None:
        # Load selected row data into entry fields for quick update/delete workflows.
        selection = self.tree.selection()
        if not selection:
            return

        values = self.tree.item(selection[0], "values")
        if not values:
            return

        self.book_id_var.set(str(values[0]))
        self.title_var.set(str(values[1]))
        self.author_var.set(str(values[2]))
        self.year_var.set(str(values[3]))
        self.genre_var.set(str(values[4]))
        self.rating_var.set(str(values[5]))

    def add_book(self) -> None:
        # Read inputs and validate required fields before creating a new catalog entry.
        custom_id = self.book_id_var.get().strip()
        title = self.title_var.get().strip()
        author = self.author_var.get().strip()
        year_text = self.year_var.get().strip()
        genre = self.genre_var.get().strip()
        rating_text = self.rating_var.get().strip()

        if not title or not author or not year_text or not genre or not rating_text:
            messagebox.showerror("Missing Data", "Please complete Title, Author, Year, Genre, and Rating.")
            return

        try:
            year = parse_year(year_text)
            rating = parse_rating(rating_text)
        except ValueError as error:
            messagebox.showerror("Invalid Input", str(error))
            return

        if custom_id:
            if custom_id in self.catalog:
                messagebox.showerror("Duplicate ID", f"Book ID {custom_id} already exists.")
                return
            book_id = custom_id
        else:
            book_id = generate_book_id(self.catalog)

        self.catalog[book_id] = {
            "title": title,
            "author": author,
            "year": year,
            "genre": genre,
            "rating": rating,
        }
        save_catalog(self.catalog)
        self.refresh_table(self.catalog)
        self.status_var.set(f"Book {book_id} added successfully.")

    def view_all_books(self) -> None:
        # Requirement alignment: view reads latest data from file before showing table.
        self.catalog = load_catalog()
        self.refresh_table(self.catalog)
        self.status_var.set("Showing all books from book_catalog.txt.")

    def update_selected_book(self) -> None:
        # Update rule for this project: only rating and/or genre are changed.
        book_id = self.book_id_var.get().strip()
        if not book_id or book_id not in self.catalog:
            messagebox.showerror("Book Not Found", "Select a row (or enter a valid Book ID) to update.")
            return

        genre = self.genre_var.get().strip()
        rating_text = self.rating_var.get().strip()
        if not genre and not rating_text:
            messagebox.showerror("No Update Data", "Provide a new genre and/or rating.")
            return

        if genre:
            self.catalog[book_id]["genre"] = genre

        if rating_text:
            try:
                self.catalog[book_id]["rating"] = parse_rating(rating_text)
            except ValueError as error:
                messagebox.showerror("Invalid Rating", str(error))
                return

        save_catalog(self.catalog)
        self.refresh_table(self.catalog)
        self.status_var.set(f"Book {book_id} updated successfully (genre/rating).")

    def delete_selected_book(self) -> None:
        # Delete uses a confirmation prompt to prevent accidental data loss.
        book_id = self.book_id_var.get().strip()
        if not book_id or book_id not in self.catalog:
            messagebox.showerror("Book Not Found", "Select a row (or enter a valid Book ID) to delete.")
            return

        confirmed = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete book {book_id}?",
        )
        if not confirmed:
            self.status_var.set("Delete cancelled.")
            return

        del self.catalog[book_id]
        save_catalog(self.catalog)
        self.refresh_table(self.catalog)
        self.status_var.set(f"Book {book_id} deleted successfully.")
        self.clear_form()

    def show_top_rated(self) -> None:
        # Build a temporary dictionary of the top 3 books sorted by rating descending.
        ranked = sorted(
            self.catalog.items(),
            key=lambda item: float(item[1].get("rating", 0)),
            reverse=True,
        )
        top_three = dict(ranked[:3])
        self.refresh_table(top_three)
        self.status_var.set("Showing top 3 highest-rated books.")

    def search_by_title(self) -> None:
        # Filter in memory by title substring (case-insensitive).
        query = self.search_var.get().strip().lower()
        results = {
            book_id: details
            for book_id, details in self.catalog.items()
            if query in str(details.get("title", "")).lower()
        }
        self.refresh_table(results)
        self.status_var.set(f"Title search complete. Matches: {len(results)}")

    def search_by_author(self) -> None:
        # Filter in memory by author substring (case-insensitive).
        query = self.search_var.get().strip().lower()
        results = {
            book_id: details
            for book_id, details in self.catalog.items()
            if query in str(details.get("author", "")).lower()
        }
        self.refresh_table(results)
        self.status_var.set(f"Author search complete. Matches: {len(results)}")

    def search_by_year(self) -> None:
        # Year search uses strict integer comparison.
        query = self.search_var.get().strip()
        try:
            year = parse_year(query)
        except ValueError as error:
            messagebox.showerror("Invalid Year", str(error))
            return

        results = {
            book_id: details
            for book_id, details in self.catalog.items()
            if int(details.get("year", -1)) == year
        }
        self.refresh_table(results)
        self.status_var.set(f"Year search complete. Matches: {len(results)}")

    def export_catalog(self) -> None:
        # Explicit export writes current memory state to JSON file.
        save_catalog(self.catalog)
        self.status_var.set("Catalog exported successfully!")
        messagebox.showinfo("Export", "Catalog exported successfully!")

    def import_catalog(self) -> None:
        # Import reloads from file and displays the exact style message requested.
        self.catalog = load_catalog()
        self.refresh_table(self.catalog)
        imported_text = pformat(self.catalog, sort_dicts=False)
        self.status_var.set("Catalog imported successfully!")
        messagebox.showinfo(
            "Import",
            "Catalog imported successfully!\n"
            f"Imported Catalog: {imported_text}",
        )


if __name__ == "__main__":
    # Start the Tkinter event loop.
    app = BookCatalogApp()
    app.mainloop()
