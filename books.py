from typing import List, Literal, Optional

import requests
from notion_client import Client
from pydantic import BaseModel, Field
from pydantic.config import ConfigDict
from tqdm import tqdm


BUECHER_DATABASE_ID = "2b0615078a9980c2bde7e500c53a8c8f"


class SelectOption(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    color: Optional[str] = None


class SelectProperty(BaseModel):
    id: str
    type: Literal["select"]
    select: Optional[SelectOption]


class NumberProperty(BaseModel):
    id: str
    type: Literal["number"]
    number: Optional[int]


class TextContent(BaseModel):
    content: str
    link: Optional[str] = None


class RichTextObject(BaseModel):
    type: Literal["text"] = "text"
    text: TextContent
    plain_text: str
    href: Optional[str] = None


class RichTextProperty(BaseModel):
    id: Optional[str] = None
    type: Literal["rich_text"] = "rich_text"
    rich_text: List[RichTextObject]


class RelationItem(BaseModel):
    id: str


class RelationProperty(BaseModel):
    id: str
    type: Literal["relation"]
    relation: List[RelationItem]
    has_more: Optional[bool] = None


class FileObject(BaseModel):
    name: Optional[str] = None


class FilesProperty(BaseModel):
    id: str
    type: Literal["files"]
    files: List[FileObject]


class DateValue(BaseModel):
    start: Optional[str]
    end: Optional[str] = None
    time_zone: Optional[str] = None


class DateProperty(BaseModel):
    id: str
    type: Literal["date"]
    date: Optional[DateValue] = None


class TitleProperty(BaseModel):
    id: str
    type: Literal["title"]
    title: List[RichTextObject]


class BookProperties(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    language: SelectProperty = Field(alias="Sprache")
    isbn: RichTextProperty = Field(alias="ISBN")
    original_title: RichTextProperty = Field(alias="Originaltitel")
    cover: FilesProperty = Field(alias="Cover")
    publisher: RichTextProperty = Field(alias="Verlag")
    autor: RelationProperty = Field(alias="Autor")
    pages: NumberProperty = Field(alias="Seiten")
    pub_date: DateProperty = Field(alias="Veröffentlichungsdatum")
    title: TitleProperty = Field(alias="Titel")
    description: RichTextProperty = Field(alias="Klappentext")


def _parse_book_properties(raw_properties: dict) -> BookProperties:
    """Parst die Notion-Properties eines Buches in ein stark typisiertes Modell."""
    return BookProperties.model_validate(raw_properties)


def get_cover(isbn) -> str:
    cover = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"
    is_cover = requests.get(f"{cover}?default=false")
    if is_cover.status_code == 200:
        return ""
    return cover
    

def _complete_missing_data(notion: Client, book):
    properties = _parse_book_properties(book["properties"])

    book_title = properties.title.title[0].text.content
    isbn = properties.isbn.rich_text[0].plain_text if properties.isbn.rich_text else ""
    author_id = properties.autor.relation[0].id if properties.autor.relation else ""
    cover = properties.cover.files[0].name if properties.cover.files else ""
    original_title = properties.original_title.rich_text[0].plain_text if properties.original_title.rich_text else ""
    pub_date = properties.pub_date.date.start if properties.pub_date.date else ""
    publisher = properties.publisher.rich_text[0].plain_text if properties.publisher.rich_text else ""
    description = properties.description.rich_text[0].plain_text if properties.description.rich_text else ""
    language = properties.language.select.name if properties.language.select else ""
    pages = properties.pages.number

    if not isbn:
        raise ValueError("ISBN missing")

    response = requests.get(f"https://openlibrary.org/isbn/{isbn}.json")
    if response.status_code != 200:
        raise ValueError(
            f"ISBN {isbn} für Buch {book_title} nicht korrekt oder Open Library nicht bekannt"
        )
    data = response.json()

    if not cover:
        cover = get_cover(isbn)
    if not original_title:
        original_title = data["translation_of"]
        print(f"Original title laut open library: {original_title}")
        to_insert_original_title = {
            "Originaltitel": RichTextProperty(
                rich_text=[
                    RichTextObject(
                        text=TextContent(content=original_title), plain_text=original_title
                    )
                ]
            ).dict(exclude={"id", "link", "href"})
        }
    if not pub_date:
        pub_date = data["publish_date"]
    if not publisher:
        publisher = ", ".join(data["publishers"])
    if not description:
        description = data["description"]["value"]
    if not language:
        language = "Deutsch" if data["languages"][0]["key"] == "/languages/ger" else "Englisch"
    if not pages:
        pages = data["number_of_pages"]


    # print(original_title, pages, language, pub_date)
    # print(to_insert_original_title)

    updated_book = notion.pages.update(page_id=book["id"], properties=to_insert_original_title)

def complete_missing_data(notion: Client, book_id: str | None = None):
        if book_id:
            book = notion.pages.retrieve(book_id)
            _complete_missing_data(notion, book)
        else:
            database = notion.databases.retrieve(database_id=BUECHER_DATABASE_ID)
            database_source_id = database["data_sources"][0]["id"]
            books = notion.data_sources.query(database_source_id)["results"]

            for book in tqdm(books):
                # print(book["id"])
                try:
                    _complete_missing_data(notion, book)
                except Exception as err:
                    print(type(err), err)
                    continue