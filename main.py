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


def prompt_for_token() -> str:
    """Fragt nach einem API-Token und nutzt vorhandene Umgebungsvariablen nach Rückfrage."""
    env_token = os.getenv("NOTION_TOKEN")
    if env_token:
        use_env = (
            input("Umgebungsvariable NOTION_TOKEN gefunden. Verwenden? [J/n]: ")
            .strip()
            .lower()
        )
        if use_env in ("", "j", "ja", "y", "yes"):
            return env_token

    while True:
        token = input("Bitte NOTION_TOKEN eingeben: ").strip()
        if token:
            return token
        print("Token darf nicht leer sein.")


def prompt_action() -> str:
    """Zeigt das Aktionsmenü und liefert die Auswahl."""
    print("\nWas möchtest du tun?")
    print("1) Fehlende Daten für ein bestimmtes Buch ergänzen")
    print("2) Fehlende Daten für alle Bücher ergänzen")
    print("q) Beenden")
    return input("Auswahl: ").strip().lower()


def handle_single_book(notion: Client):
    book_id = input("Bitte Notion Page ID des Buches eingeben: ").strip()
    if not book_id:
        print("Keine ID angegeben, Aktion abgebrochen.")
        return
    try:
        books.complete_missing_data(notion, book_id=book_id)
        print("Fertig.")
    except Exception as err:
        print(f"Fehler beim Aktualisieren: {type(err)}: {err}")


def handle_all_books(notion: Client):
    try:
        books.complete_missing_data(notion)
        print("Fertig.")
    except Exception as err:
        print(f"Fehler beim Aktualisieren: {type(err)}: {err}")


def main():
    print("Notion Bücher-Tool")
    token = prompt_for_token()
    notion = build_client(token)

    while True:
        action = prompt_action()
        if action == "1":
            handle_single_book(notion)
        elif action == "2":
            handle_all_books(notion)
        elif action in {"q", "quit", "exit"}:
            print("Tschüss!")
            break
        else:
            print("Ungültige Auswahl. Bitte erneut versuchen.")



if __name__ == "__main__":
    main()
