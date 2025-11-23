from typing import List, Literal, Optional

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


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