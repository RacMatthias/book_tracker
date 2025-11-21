import os

from notion_client import Client

import books


def build_client(token: str | None = None) -> Client:
    """Erstellt einen authentifizierten Notion-Client."""
    api_token = token or os.getenv("NOTION_TOKEN")
    if not api_token:
        raise RuntimeError(
            "Kein API-Token gefunden. Setze NOTION_TOKEN oder übergib token explizit."
        )
    return Client(auth=api_token)


def main():
    notion = build_client()
    
    books.complete_missing_data(notion)



if __name__ == "__main__":
    main()
