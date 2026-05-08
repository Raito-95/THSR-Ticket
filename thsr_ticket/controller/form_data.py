from typing import Any, Dict, Optional

from bs4 import BeautifulSoup
from bs4.element import Tag


def compose_form_defaults(
    page: BeautifulSoup,
    form_id: Optional[str] = None,
    submit_name: Optional[str] = None,
) -> Dict[str, Any]:
    form = page.find("form", id=form_id) if form_id else page.find("form")
    root = form if isinstance(form, Tag) else page

    data: Dict[str, Any] = {}

    for field in root.find_all(["input", "select", "textarea"]):
        if not isinstance(field, Tag):
            continue
        if field.has_attr("disabled"):
            continue

        name = _attr(field, "name")
        if not name:
            continue

        if field.name == "input":
            input_type = (_attr(field, "type") or "text").lower()
            if input_type in {"button", "image", "reset"}:
                continue
            if input_type == "submit" and name != submit_name:
                continue
            if input_type in {"radio", "checkbox"} and not field.has_attr("checked"):
                continue

            data[name] = _attr(field, "value") or ""
            continue

        if field.name == "select":
            option = field.find("option", selected=True) or field.find("option")
            data[name] = _attr(option, "value") if isinstance(option, Tag) else ""
            continue

        if field.name == "textarea":
            data[name] = field.get_text()

    return data


def parse_form_action(page: BeautifulSoup, form_id: Optional[str] = None) -> Optional[str]:
    form = page.find("form", id=form_id) if form_id else page.find("form")
    if not isinstance(form, Tag):
        return None
    action = form.get("action")
    if action is None:
        return None
    return str(action)


def _attr(tag: Tag, name: str) -> Optional[str]:
    value = tag.get(name)
    if value is None:
        return None
    return str(value)
