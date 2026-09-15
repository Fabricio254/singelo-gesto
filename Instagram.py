"""Coleta de produtos do Instagram por links publicos."""
from __future__ import annotations
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote
import requests

PRICE_RE = re.compile(r"(?:R\$\s*|rs\.?\s*|\$\s*|💲\s*)(\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?|\d+(?:,\d{1,2})?)", re.IGNORECASE)
POST_URL_RE = re.compile(r"https?://(?:www\.)?instagram\.com/(?:p|reel|tv)/([A-Za-z0-9_-]+)/?(?:\?[^\s]*)?", re.IGNORECASE)

def parse_brl(value: str) -> float:
    return float(value.replace(".", "").replace(",", "."))

def extract_prices(caption: str) -> List[float]:
    prices = []
    for match in PRICE_RE.finditer(caption or ""):
        try: prices.append(parse_brl(match.group(1)))
        except ValueError: pass
    return prices

def shortcode_from_url(url: str) -> str:
    match = POST_URL_RE.search(url or "")
    return match.group(1) if match else ""


def normalized_post_url(shortcode: str) -> str:
    return f"https://www.instagram.com/p/{shortcode}/"


def extract_post_urls(text: str) -> List[str]:
    found = []
    for match in POST_URL_RE.finditer(text or ""):
        shortcode = match.group(1)
        clean = normalized_post_url(shortcode)
        if clean not in found:
            found.append(clean)
    return found

def clean_caption(text: str) -> str:
    text = (text or "").replace("\ufffd", "").replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def guess_category(text: str) -> str:
    value = (text or "").lower()
    categories = [("Cafe da manha", ("cafe", "manha")), ("Aniversario", ("aniversario", "birthday", "15 anos")), ("Maternidade", ("maternidade", "bebe")), ("Casamento e noivado", ("casamento", "noivado", "noivos", "romantica")), ("Flores e mimos", ("flores", "flor", "caneca", "mimo", "presente")), ("Datas especiais", ("pais", "maes", "namorados", "formatura"))]
    for category, keywords in categories:
        if any(keyword in value for keyword in keywords): return category
    return "Outros"

def title_from_caption(caption: str) -> str:
    for line in clean_caption(caption).splitlines():
        title = line.strip().strip("#*- ")
        if title and not PRICE_RE.fullmatch(title): return title[:120]
    return "Produto do Instagram"

def _url_value(value: Any) -> Optional[str]: return str(value) if value else None

def media_to_product(media: Any, username: str = "singelo_gesto") -> Dict[str, Any]:
    caption = clean_caption(getattr(media, "caption_text", "") or "")
    prices = extract_prices(caption)
    shortcode = getattr(media, "code", "") or ""
    image_urls = []
    thumbnail = _url_value(getattr(media, "thumbnail_url", None))
    if thumbnail: image_urls.append(thumbnail)
    for resource in getattr(media, "resources", []) or []:
        resource_url = _url_value(getattr(resource, "thumbnail_url", None))
        if resource_url and resource_url not in image_urls: image_urls.append(resource_url)
    return {"instagram_id": shortcode or str(getattr(media, "pk", "")), "username": username, "title": title_from_caption(caption), "category": guess_category(caption), "description": caption, "price": prices[-1] if prices else None, "prices_found": prices, "image_url": image_urls[0] if image_urls else None, "image_urls": image_urls, "permalink": f"https://www.instagram.com/p/{shortcode}/" if shortcode else "", "taken_at": getattr(media, "taken_at", None)}

def fallback_product_from_link(link: str, username: str = "singelo_gesto", error: str = "") -> Dict[str, Any]:
    shortcode = shortcode_from_url(link)
    permalink = normalized_post_url(shortcode) if shortcode else link.split("?")[0]
    return {
        "instagram_id": shortcode or permalink,
        "username": username,
        "title": "Produto do Instagram",
        "category": "Outros",
        "description": "",
        "price": None,
        "prices_found": [],
        "image_url": f"https://www.instagram.com/p/{shortcode}/media/?size=l" if shortcode else None,
        "image_urls": [f"https://www.instagram.com/p/{shortcode}/media/?size=l"] if shortcode else [],
        "permalink": permalink,
        "taken_at": None,
        "_import_error": error,
    }

def collect_post_links_manual(text: str, username: str = "singelo_gesto", progress_callback=None) -> List[Dict[str, Any]]:
    links = extract_post_urls(text)
    if not links:
        raise ValueError("Nenhum link publico do Instagram foi encontrado.")
    products = []
    for index, link in enumerate(links, start=1):
        if progress_callback:
            progress_callback(index, len(links), link, "manual")
        products.append(fallback_product_from_link(link, username, "Cadastro rapido por link"))
    return products


def collect_post_links(text: str, username: str = "singelo_gesto", progress_callback=None) -> List[Dict[str, Any]]:
    try:
        from instagrapi import Client
    except ImportError as exc:
        raise RuntimeError("A dependencia instagrapi nao esta instalada. Execute pip install -r requirements.txt.") from exc
    links = extract_post_urls(text)
    if not links:
        raise ValueError("Nenhum link publico do Instagram foi encontrado.")
    client = Client()
    products = []
    for index, link in enumerate(links, start=1):
        if progress_callback:
            progress_callback(index, len(links), link, "lendo")
        try:
            media_pk = client.media_pk_from_url(link)
            try:
                media = client.media_info_gql(media_pk)
            except Exception:
                media = client.media_info(media_pk)
            product = media_to_product(media, username)
            product["permalink"] = link
            products.append(product)
            if progress_callback:
                progress_callback(index, len(links), link, "ok")
        except Exception as exc:
            products.append(fallback_product_from_link(link, username, str(exc)))
            if progress_callback:
                progress_callback(index, len(links), link, "manual")
    return products

def collect_profile(username: str, password: str, amount: int = 0, session_file: Optional[str] = None) -> List[Dict[str, Any]]:
    try: from instagrapi import Client
    except ImportError as exc: raise RuntimeError("A dependencia instagrapi nao esta instalada. Execute pip install -r requirements.txt.") from exc
    client = Client()
    session_path = Path(session_file) if session_file else Path(__file__).with_name("instagram_session.json")
    if session_path.exists():
        try: client.load_settings(str(session_path))
        except Exception: pass
    client.login(username, password)
    client.dump_settings(str(session_path))
    profile_id = client.user_id_from_username(username)
    return [media_to_product(media, username) for media in client.user_medias(profile_id, amount=amount)]

def whatsapp_url(phone: str, message: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    return f"https://wa.me/{digits}?text={quote(message)}" if digits else f"https://wa.me/?text={quote(message)}"

def clean_whatsapp_text(text: str, limit: Optional[int] = None) -> str:
    text = clean_caption(str(text or ""))
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = re.sub(r"[^A-Za-z0-9\s:/?&=._,%+@#()\-]", "", ascii_text)
    ascii_text = re.sub(r"[ \t]+", " ", ascii_text)
    ascii_text = re.sub(r" *\n *", "\n", ascii_text)
    lines = []
    for line in ascii_text.splitlines():
        line = line.strip(" -.,;:!|")
        if line and any(char.isalnum() for char in line):
            lines.append(line)
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if limit and len(text) > limit:
        text = text[:limit].rstrip(" ,.;:-") + "..."
    return text


def product_message(product: Dict[str, Any]) -> str:
    title = clean_whatsapp_text(product.get("title", "Produto")) or "Produto"
    category = clean_whatsapp_text(product.get("category", ""))
    description = clean_whatsapp_text(product.get("description", ""), limit=300)
    permalink = clean_whatsapp_text(product.get("permalink", ""))
    price = product.get("price")
    price_text = "Consulte o valor e a disponibilidade" if price is None else f"R$ {float(price):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    lines = [
        "Ola! Tudo bem?",
        "",
        "Tenho interesse nesta opcao da Singelo Gesto:",
        "",
        f"Produto: {title}",
        f"Categoria: {category}",
        f"Valor: {price_text}",
    ]
    if permalink:
        lines.extend(["", "Link do produto:", permalink])
    if description:
        lines.extend(["", "Detalhes:", description])
    lines.extend(["", "Para reservar, me diga a data e a cidade da entrega."])
    return "\n".join(lines).strip()
