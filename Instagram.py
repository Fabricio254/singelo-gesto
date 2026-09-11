"""Coleta de produtos do Instagram por links publicos."""
from __future__ import annotations
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote
import requests

PRICE_RE = re.compile(r"(?:R\$\s*|rs\.?\s*)(\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?|\d+(?:,\d{1,2})?)", re.IGNORECASE)
POST_URL_RE = re.compile(r"https?://(?:www\.)?instagram\.com/(?:p|reel|tv)/[A-Za-z0-9_-]+/?(?:\?[^\s]*)?", re.IGNORECASE)

def parse_brl(value: str) -> float:
    return float(value.replace(".", "").replace(",", "."))

def extract_prices(caption: str) -> List[float]:
    prices = []
    for match in PRICE_RE.finditer(caption or ""):
        try: prices.append(parse_brl(match.group(1)))
        except ValueError: pass
    return prices

def extract_post_urls(text: str) -> List[str]:
    found = []
    for url in POST_URL_RE.findall(text or ""):
        clean = url.rstrip(".,);]")
        if clean not in found: found.append(clean)
    return found

def guess_category(text: str) -> str:
    value = (text or "").lower()
    categories = [("Cafe da manha", ("cafe", "manha")), ("Aniversario", ("aniversario", "birthday", "15 anos")), ("Maternidade", ("maternidade", "bebe")), ("Casamento e noivado", ("casamento", "noivado", "noivos", "romantica")), ("Flores e mimos", ("flores", "flor", "caneca", "mimo", "presente")), ("Datas especiais", ("pais", "maes", "namorados", "formatura"))]
    for category, keywords in categories:
        if any(keyword in value for keyword in keywords): return category
    return "Outros"

def title_from_caption(caption: str) -> str:
    for line in (caption or "").splitlines():
        title = line.strip().strip("#*- ")
        if title and not PRICE_RE.fullmatch(title): return title[:120]
    return "Produto do Instagram"

def _url_value(value: Any) -> Optional[str]: return str(value) if value else None

def media_to_product(media: Any, username: str = "singelo_gesto") -> Dict[str, Any]:
    caption = getattr(media, "caption_text", "") or ""
    prices = extract_prices(caption)
    shortcode = getattr(media, "code", "") or ""
    image_urls = []
    thumbnail = _url_value(getattr(media, "thumbnail_url", None))
    if thumbnail: image_urls.append(thumbnail)
    for resource in getattr(media, "resources", []) or []:
        resource_url = _url_value(getattr(resource, "thumbnail_url", None))
        if resource_url and resource_url not in image_urls: image_urls.append(resource_url)
    return {"instagram_id": str(getattr(media, "pk", "")), "username": username, "title": title_from_caption(caption), "category": guess_category(caption), "description": caption, "price": prices[-1] if prices else None, "prices_found": prices, "image_url": image_urls[0] if image_urls else None, "image_urls": image_urls, "permalink": f"https://www.instagram.com/p/{shortcode}/" if shortcode else "", "taken_at": getattr(media, "taken_at", None)}

def collect_post_links(text: str, username: str = "singelo_gesto") -> List[Dict[str, Any]]:
    """Coleta publicacoes publicas sem pedir a senha do Instagram."""
    try:
        from instagrapi import Client
    except ImportError as exc:
        raise RuntimeError("A dependencia instagrapi nao esta instalada. Execute pip install -r requirements.txt.") from exc
    links = extract_post_urls(text)
    if not links: raise ValueError("Nenhum link publico do Instagram foi encontrado.")
    client = Client()
    products = []
    errors = []
    for link in links:
        try:
            media_pk = client.media_pk_from_url(link)
            try: media = client.media_info_gql(media_pk)
            except Exception: media = client.media_info(media_pk)
            product = media_to_product(media, username)
            product["permalink"] = link.split("?")[0]
            products.append(product)
        except Exception as exc:
            errors.append(f"{link}: {exc}")
    if not products:
        raise RuntimeError("Nenhuma publicacao foi lida. " + " | ".join(errors[:3]))
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

def product_message(product: Dict[str, Any]) -> str:
    price = product.get("price")
    price_text = "Consultar valor" if price is None else f"R$ {float(price):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"Ola! Seguem os detalhes do produto:\n\n{product.get('title', 'Produto')}\n{price_text}\n\n{product.get('description', '')}".strip()
