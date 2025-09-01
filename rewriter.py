"""
advanced_rewriter.py
--------------------
Advanced article rewriter for Politie-Forum.nl using the "option 10" pipeline,
with extras:
- canonical / discussion / AMP / API URLs
- share links
- JSON-LD (NewsArticle + Breadcrumbs) and seed for DiscussionForumPosting
- duplicate checking
- configurable batch size, sleep, style/language, and dry-run mode
- optional static HTML export to match your front-end route (/article/{slug}/index.html)

Requirements (install as needed):
    pip install firebase-admin openai beautifulsoup4 nltk

Environment:
    GROQ_API_KEY (or GROC_API_KEY): your Groq API key

Usage examples:
    python advanced_rewriter.py
    python advanced_rewriter.py --limit 5 --sleep 2 --style Normal --language Dutch
    python advanced_rewriter.py --write-static --output-base "/path/to/public"

Author: Politie-Forum.nl
"""
from __future__ import annotations

import os
import re
import json
import time
import argparse
import unicodedata
from datetime import datetime
from typing import Dict, Any, Tuple, Optional

# Firestore
import firebase_admin
from firebase_admin import credentials, firestore

# OpenAI client (Groq-compatible endpoint)
try:
    from openai import OpenAI
except Exception as e:
    OpenAI = None  # type: ignore

# ---------------------------
# Config / Defaults
# ---------------------------

BASE_URL = "https://politie-forum.nl"
FORUM_SECTION_SLUG = "recente-incidenten"         # forum route section for discussion links
SOURCE_COLLECTION = "articles_full"               # where unprocessed full articles live
DEST_COLLECTION = "articles_rewritten"            # where rewritten articles will be saved

DEFAULT_STYLE = "Normal"                          # Technical, Normal, Easy, Populair, News Reader
DEFAULT_LANGUAGE = "Dutch"                        # Dutch, English, German
MODEL_NAME = "mixtral-8x7b-32768"                 # Groq model id

# Optional static export
WRITE_STATIC_DEFAULT = False
OUTPUT_BASE_DIR_DEFAULT = "/Users/_akira/CSAD/websites-new-2025/politie-forum-nl/public"

# Batch controls
DEFAULT_LIMIT = 3
DEFAULT_SLEEP = 3

SERVICE_ACCOUNT_CANDIDATES = [
    "./serviceAccountKey.json",
    "../serviceAccountKey.json",
    os.path.expanduser("~/serviceAccountKey.json"),
    os.path.expanduser("~/.config/firebase/serviceAccountKey.json"),
    os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "./serviceAccountKey.json")
]

# ---------------------------
# Globals (client/state)
# ---------------------------

_ai_client = None
_ai_model = None
_client_type = "openai"  # Groq via OpenAI-compatible endpoint

# ---------------------------
# Utilities
# ---------------------------

def strip_diacritics(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))

def slugify(s: str, max_len: int = 80) -> str:
    s = strip_diacritics(s or "")
    s = s.replace("'", "")
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s[:max_len].rstrip("-") or "artikel"

def build_urls(slug: str, category_slug: str = "nieuws", ts: Optional[datetime] = None) -> Dict[str, str]:
    canonical = f"{BASE_URL}/article/{slug}"
    discussion = f"{BASE_URL}/forum/{FORUM_SECTION_SLUG}/{slug}"
    amp = f"{canonical}/amp"
    api = f"{BASE_URL}/api/articles/{slug}.json"
    return {"canonical": canonical, "discussion": discussion, "amp": amp, "api": api}

def build_share_urls(title: str, url: str) -> Dict[str, str]:
    from urllib.parse import quote
    t = quote(title or "Nieuwsartikel")
    u = quote(url or BASE_URL)
    return {
        "facebook": f"https://www.facebook.com/sharer/sharer.php?u={u}",
        "twitter": f"https://twitter.com/intent/tweet?text={t}&url={u}",
        "whatsapp": f"https://wa.me/?text={t}%20{u}",
        "linkedin": f"https://www.linkedin.com/shareArticle?mini=true&url={u}&title={t}",
        "email": f"mailto:?subject={t}&body={t}%0A%0A{u}"
    }

def build_newsarticle_ld(article: Dict[str, Any]) -> Dict[str, Any]:
    """Schema.org NewsArticle + BreadcrumbList, with discussionUrl."""
    headline = (article.get("title") or "")[:110]
    desc = (re.sub(r"<[^>]+>", " ", article.get("summary") or "") or "").strip()[:160]
    tags = article.get("tags") or []
    category = article.get("category") or "Nieuws"
    image = article.get("image_url")
    published = article.get("timestamp_iso") or datetime.utcnow().isoformat()
    urls = article.get("urls", {})
    canonical = urls.get("canonical") or BASE_URL

    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "NewsArticle",
                "@id": f"{canonical}#news",
                "url": canonical,
                "mainEntityOfPage": canonical,
                "headline": headline,
                "description": desc,
                "inLanguage": "nl-NL",
                "isAccessibleForFree": True,
                "datePublished": published,
                "dateModified": published,
                "articleSection": category,
                "keywords": ", ".join(tags) if tags else None,
                "discussionUrl": urls.get("discussion"),
                "author": {"@type": "Organization", "name": "Politie-Forum.nl", "url": BASE_URL},
                "publisher": {
                    "@type": "Organization",
                    "name": "Politie-Forum.nl",
                    "url": BASE_URL,
                    "logo": {
                        "@type": "ImageObject",
                        "url": f"{BASE_URL}/politie-nl-logo.svg",
                        "width": 300,
                        "height": 60,
                    },
                },
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE_URL}/"},
                    {"@type": "ListItem", "position": 2, "name": "Artikel", "item": canonical},
                ],
            },
        ],
    }
    if image:
        ld["@graph"][0]["image"] = {"@type": "ImageObject", "url": image}
    return ld

def build_forum_ld_seed(urls: Dict[str, str], title: str, ts_iso: str) -> Dict[str, Any]:
    return {
        "@context": "https://schema.org",
        "@type": "DiscussionForumPosting",
        "mainEntityOfPage": urls.get("discussion"),
        "url": urls.get("discussion"),
        "headline": title,
        "about": {"@id": f"{urls.get('canonical')}#news"},
        "inLanguage": "nl-NL",
        "author": {"@type": "Organization", "name": "Politie-Forum.nl", "url": BASE_URL},
        "datePublished": ts_iso,
    }

def ensure_firebase(project_id: str) -> firestore.Client:
    path = next((p for p in SERVICE_ACCOUNT_CANDIDATES if p and os.path.exists(p)), None)
    if not path:
        raise RuntimeError(
            "Firebase service account key not found. Set FIREBASE_SERVICE_ACCOUNT_PATH "
            "or place serviceAccountKey.json in the project directory."
        )
    if not firebase_admin._apps:
        cred = credentials.Certificate(path)
        firebase_admin.initialize_app(cred, {"projectId": project_id})
    return firestore.client()

# ---------------------------
# AI helpers (Groq via OpenAI client)
# ---------------------------

def get_ai_client() -> Tuple[Any, str, str]:
    """Initialize Groq client via OpenAI-compatible endpoint."""
    global _ai_client, _ai_model, _client_type

    api_key = (
        os.getenv("GROQ_API_KEY")
        or os.getenv("GROC_API_KEY")
        or ""  # leave empty to allow dry-run
    )

    if OpenAI is None:
        print("❌ openai package not installed. Run: pip install openai")
        return None, None, None

    if not api_key:
        print("⚠️ GROQ_API_KEY not set. Running in 'no-AI' fallback mode (will reuse original text).")
        return None, None, None

    try:
        client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        return client, MODEL_NAME, "openai"
    except Exception as e:
        print(f"❌ Failed to initialize Groq client: {e}")
        return None, None, None

def get_style_prompt(style: str, language: str) -> str:
    base_prompts = {
        "Technical": {
            "Dutch": "Herschrijf de tekst in het Nederlands in een technische, formele stijl. Gebruik professionele terminologie en gedetailleerde uitleg. Behoud alle belangrijke informatie maar presenteer het professioneel.",
            "English": "Rewrite the text in English in a technical, formal style. Use professional terminology and detailed explanations. Maintain all important information but present it professionally.",
            "German": "Schreiben Sie den Text auf Deutsch in einem technischen, formalen Stil. Verwenden Sie professionelle Terminologie und detaillierte Erklärungen. Behalten Sie alle wichtigen Informationen bei, aber präsentieren Sie sie professionell.",
        },
        "Normal": {
            "Dutch": "Herschrijf de tekst in het Nederlands in een standaard nieuwsstijl. Gebruik duidelijke taal en behoud alle belangrijke informatie.",
            "English": "Rewrite the text in English in a standard news style. Use clear language and maintain all important information.",
            "German": "Schreiben Sie den Text auf Deutsch in einem Standard-Nachrichtenstil. Verwenden Sie klare Sprache und behalten Sie alle wichtigen Informationen bei.",
        },
        "Easy": {
            "Dutch": "Herschrijf de tekst in het Nederlands in een eenvoudige, begrijpelijke stijl. Gebruik korte zinnen en eenvoudige woorden. Maak het toegankelijk voor iedereen.",
            "English": "Rewrite the text in English in a simple, understandable style. Use short sentences and simple words. Make it accessible to everyone.",
            "German": "Schreiben Sie den Text auf Deutsch in einem einfachen, verständlichen Stil. Verwenden Sie kurze Sätze und einfache Wörter. Machen Sie es für jeden zugänglich.",
        },
        "Populair": {
            "Dutch": "Herschrijf de tekst in het Nederlands in een populaire, aantrekkelijke stijl. Gebruik levendige taal, maak het boeiend en toegankelijk voor een breed publiek. Voeg waar mogelijk emotie en relatabiliteit toe.",
            "English": "Rewrite the text in English in a popular, attractive style. Use vivid language, make it engaging and accessible to a broad audience. Add emotion and relatability where possible.",
            "German": "Schreiben Sie den Text auf Deutsch in einem populären, attraktiven Stil. Verwenden Sie lebendige Sprache, machen Sie es fesselnd und zugänglich für ein breites Publikum. Fügen Sie wo möglich Emotion und Nachvollziehbarkeit hinzu.",
        },
        "News Reader": {
            "Dutch": "Herschrijf de tekst in het Nederlands in de stijl van een professionele nieuwslezer. Gebruik formele maar toegankelijke taal, duidelijke structuur en professionele presentatie. Vermijd jargon en maak complexe onderwerpen begrijpelijk.",
            "English": "Rewrite the text in English in the style of a professional news reader. Use formal but accessible language, clear structure and professional presentation. Avoid jargon and make complex topics understandable.",
            "German": "Schreiben Sie den Text auf Deutsch im Stil eines professionellen Nachrichtensprechers. Verwenden Sie formale aber zugängliche Sprache, klare Struktur und professionelle Präsentation. Vermeiden Sie Fachjargon und machen Sie komplexe Themen verständlich.",
        },
    }
    return base_prompts.get(style, {}).get(language, base_prompts["Normal"]["Dutch"])

def generate_text(prompt: str, style: str, language: str, max_tokens: int = 512) -> str:
    if _ai_client is None or _ai_model is None:
        # Fallback: return the prompt (or empty string to avoid echoing input)
        return ""
    try:
        system_prompt = get_style_prompt(style, language)
        resp = _ai_client.chat.completions.create(  # type: ignore
            model=_ai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=1.0,
        )
        content = resp.choices[0].message.content if resp and resp.choices else ""
        return (content or "").strip()
    except Exception as e:
        print(f"Error generating text: {e}")
        return ""

def get_category(full_text: str, language: str) -> str:
    if _ai_client is None or _ai_model is None:
        return "Nieuws"
    try:
        system_content = (
            "Classificeer de categorie van de volgende Nederlandse tekst met één woord."
            " Kies uit: Politiek, Sport, Economie, Gezondheid, Technologie, Cultuur,"
            " Onderwijs, Milieu, Internationaal, of Nieuws."
        )
        resp = _ai_client.chat.completions.create(  # type: ignore
            model=_ai_model,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": full_text[:1000]},
            ],
            max_tokens=10,
        )
        content = resp.choices[0].message.content if resp and resp.choices else ""
        category = (content or "Nieuws").strip().split()[0]
        return category or "Nieuws"
    except Exception as e:
        print(f"Error getting category: {e}")
        return "Nieuws"

def get_tags(full_text: str, language: str) -> list[str]:
    if _ai_client is None or _ai_model is None:
        return ["Nederland", "Nieuws", "Actueel"]
    try:
        system_content = (
            "Genereer precies drie Nederlandse tags gescheiden door komma's."
            " Bijvoorbeeld: 'Politiek, Nederland, Verkiezingen'."
            " Gebruik korte woorden van 1-3 woorden elk."
        )
        resp = _ai_client.chat.completions.create(  # type: ignore
            model=_ai_model,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": full_text[:400]},
            ],
            max_tokens=30,
        )
        content = resp.choices[0].message.content if resp and resp.choices else ""
        if content and "," in content:
            tags = [t.strip() for t in content.split(",")]
            tags = [t for t in tags if t][:3]
            return tags if len(tags) == 3 else ["Nederland", "Nieuws", "Actueel"]
        return ["Nederland", "Nieuws", "Actueel"]
    except Exception as e:
        print(f"Error getting tags: {e}")
        return ["Nederland", "Nieuws", "Actueel"]

# ---------------------------
# Formatting helpers
# ---------------------------

def format_full_text_with_html(text: str) -> str:
    """Ensure paragraphs wrapped in <p> and add <br><br> between blocks.
       If the text already contains HTML, we keep it minimalistic.
    """
    if not text:
        return "<p>Geen inhoud beschikbaar.</p>"
    # If AI returned HTML headings/paragraphs already, keep as-is
    if "<p" in text or "<h3" in text:
        return text

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    html_parts = []
    for i, line in enumerate(lines):
        if len(line) < 80 and i > 0:
            html_parts.append(f"<h3>{line}</h3>")
        else:
            html_parts.append(f"<p>{line}</p>")
            if (i + 1) % 2 == 0:
                html_parts.append("<br><br>")
    return "\n".join(html_parts)

def generate_summary(full_text: str, char_limit: int = 140) -> str:
    plain = re.sub(r"<[^>]+>", " ", full_text or "").strip()
    if len(plain) <= char_limit:
        return plain
    cut = plain[:char_limit]
    if cut.endswith(" ") and plain[char_limit:]:
        return cut.rstrip() + "..."
    return cut.rsplit(" ", 1)[0] + "..."

# ---------------------------
# Firestore helpers
# ---------------------------

def check_duplicate_article(db: firestore.Client, collection_name: str, link: str, title: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """Check if an article already exists in the specified collection (by link, then title)."""
    try:
        collection_ref = db.collection(collection_name)
        if link:
            link_docs = collection_ref.where("link", "==", link).limit(1).get()
            if len(link_docs) > 0:
                return True, "link"
        if title:
            title_docs = collection_ref.where("title", "==", title).limit(1).get()
            if len(title_docs) > 0:
                return True, "title"
        return False, None
    except Exception as e:
        print(f"Error checking duplicates: {e}")
        return False, None

# ---------------------------
# Rewriter core
# ---------------------------

def rewrite_article(
    article: Dict[str, Any],
    style: str,
    language: str,
) -> Dict[str, Any]:
    """Rewrite a single article dict and return the enriched payload."""
    original_title = (article.get("title") or "").strip()
    original_body = article.get("body") or article.get("full_text") or ""

    print(f"🔄 Rewriting article: {original_title[:80]}")

    # 1) Body rewrite in chunks
    chunk_size = 1200  # larger chunk since mixtral can handle longer context
    rewritten_body = ""
    for i in range(0, len(original_body), chunk_size):
        chunk = original_body[i : i + chunk_size]
        prompt = (
            f"Herschrijf dit nieuwsartikel in het Nederlands in {style.lower()} stijl. "
            f"Gebruik professionele HTML: <h3>Titel</h3>, paragrafen in <p>...</p>, "
            f"plaats <br><br> tussen blokken. Duidelijke structuur en leesbaarheid."
        )
        out = generate_text(f"{prompt}\n\n{chunk}", style=style, language=language, max_tokens=1000)
        rewritten_body += (out or "") + " "
    rewritten_body = rewritten_body.strip() or original_body

    # 2) HTML tidy pass
    formatted_body = format_full_text_with_html(rewritten_body)
    print("✨ Applied HTML formatting")

    # 3) Title
    tprompt = (
        "Genereer een krachtige Nederlandstalige nieuws-titel (max 110 tekens) voor onderstaande tekst:\n\n"
        f"{rewritten_body[:600]}"
    )
    rewritten_title = generate_text(tprompt, style=style, language=language, max_tokens=80).strip() or original_title
    rewritten_title = rewritten_title[:160]

    # 4) Summary / meta description
    summary = generate_summary(formatted_body, char_limit=140)

    # 5) Category & tags
    category = get_category(formatted_body, language=language) or "Nieuws"
    tags = get_tags(formatted_body, language=language) or ["Nederland", "Nieuws", "Actueel"]

    # 6) Slug + URLs
    category_slug = slugify(category)
    title_slug = slugify(rewritten_title)
    now = datetime.utcnow()
    ts_iso = now.isoformat()
    urls = build_urls(title_slug, category_slug, now)

    # 7) Share links & JSON-LD
    share = build_share_urls(rewritten_title, urls["canonical"])

    payload = {
        "title": rewritten_title,
        "original_title": original_title,
        "link": article.get("link", ""),
        "summary": summary,
        "full_text": formatted_body,
        "timestamp": now,                  # Firestore will store as timestamp
        "timestamp_iso": ts_iso,
        "slug": title_slug,
        "category": category,
        "tags": tags,
        "language": language,
        "style": style,
        "processed": True,
        "image_url": article.get("image_url") or None,
        "published": ts_iso,
        "urls": urls,
        "share": share,
    }
    payload["jsonld"] = build_newsarticle_ld(payload)
    payload["forum_ld_seed"] = build_forum_ld_seed(urls, rewritten_title, ts_iso)
    return payload

# ---------------------------
# Static HTML export (optional)
# ---------------------------

def article_html_template(article: Dict[str, Any]) -> str:
    """Minimal static HTML for /article/{slug}/index.html export."""
    title = article.get("title") or "Politie-Forum.nl"
    desc = article.get("summary") or "Laatste politienieuws uit Nederland."
    urls = article.get("urls", {})
    canonical = urls.get("canonical", BASE_URL)
    og_image = article.get("image_url") or f"{BASE_URL}/og/politie-forum-1200x630.jpg"
    jsonld = json.dumps(article.get("jsonld", {}), ensure_ascii=False)

    body_html = article.get("full_text") or ""

    return f"""<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <link rel="canonical" href="{canonical}">
  <meta name="description" content="{desc}">

  <meta property="og:type" content="article">
  <meta property="og:site_name" content="Politie-Forum.nl">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{og_image}">

  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{desc}">
  <meta name="twitter:image" content="{og_image}">

  <script type="application/ld+json">{jsonld}</script>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif; max-width: 780px; margin: 2rem auto; padding: 0 1rem; line-height: 1.6; }}
    h1,h2,h3 {{ color: #1e3a8a; }}
    .share {{ margin: 1.5rem 0; display: flex; gap: .5rem; flex-wrap: wrap; }}
    .share a {{ display:inline-block; padding:.6rem 1rem; border:1px solid #ddd; border-radius:6px; text-decoration:none; }}
  </style>
</head>
<body>
  <article>
    <h1>{title}</h1>
    <div class="meta">Gepubliceerd op {article.get("timestamp_iso","")}</div>
    <div class="content">{body_html}</div>
  </article>
  <div class="share">
    <a href="{article['share']['facebook']}" rel="noopener nofollow">Facebook</a>
    <a href="{article['share']['twitter']}" rel="noopener nofollow">Twitter/X</a>
    <a href="{article['share']['whatsapp']}" rel="noopener nofollow">WhatsApp</a>
    <a href="{article['share']['linkedin']}" rel="noopener nofollow">LinkedIn</a>
    <a href="{article['share']['email']}" rel="noopener nofollow">E-mail</a>
  </div>
  <p><a href="{urls.get("discussion","#")}">→ Ga naar de discussie op het forum</a></p>
</body>
</html>"""

def write_static_article(article: Dict[str, Any], output_base: str) -> str:
    slug = article.get("slug", "artikel")
    out_dir = os.path.join(output_base, "article", slug)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(article_html_template(article))
    return out_path

# ---------------------------
# Main batch pipeline
# ---------------------------

def process_batch(
    db: firestore.Client,
    limit: int,
    sleep_s: int,
    style: str,
    language: str,
    dest_collection: str,
    source_collection: str,
    dry_run: bool = False,
    write_static: bool = False,
    output_base_dir: Optional[str] = None,
) -> None:
    global _ai_client, _ai_model, _client_type

    # init AI client (if key is absent, runs no-AI fallback)
    _ai_client, _ai_model, _client_type = get_ai_client()

    print(f"\n🚀 Advanced Rewriter starting")
    print(f"   Source: {source_collection} → Dest: {dest_collection}")
    print(f"   Style: {style} | Language: {language} | Model: {MODEL_NAME}")
    print(f"   Limit: {limit} | Sleep: {sleep_s}s | Dry-run: {dry_run}")
    print(f"   Write static: {write_static} | Output base: {output_base_dir or '(disabled)'}")

    # Fetch unprocessed documents
    docs = []
    try:
        docs = db.collection(source_collection).where("processed", "==", False).limit(limit).get()
    except Exception as e:
        print(f"⚠️ Query by processed failed ({e}), falling back to full scan...")
        all_docs = db.collection(source_collection).get()
        for d in all_docs:
            data = d.to_dict()
            if not data.get("processed"):
                docs.append(d)
            if len(docs) >= limit:
                break

    print(f"🧾 Found {len(docs)} unprocessed article(s)")

    processed_count = 0
    duplicate_count = 0
    error_count = 0

    for idx, doc in enumerate(docs, start=1):
        data = doc.to_dict() or {}
        link = data.get("link", "")
        title = data.get("title", "")

        print(f"\n[{idx}/{len(docs)}] {title[:80]}")

        # dedupe against destination collection (by link, then title)
        is_dupe, reason = check_duplicate_article(db, dest_collection, link, title)
        if is_dupe:
            print(f"⚠️ Duplicate detected in '{dest_collection}' (by {reason}). Skipping.")
            # Still mark source as processed to avoid loop
            try:
                if not dry_run:
                    db.collection(source_collection).document(doc.id).update({"processed": True})
                print("✅ Marked original as processed")
            except Exception as e:
                print(f"❌ Failed to mark original processed: {e}")
            duplicate_count += 1
            continue

        try:
            rewritten = rewrite_article(data, style=style, language=language)

            if dry_run:
                print("🧪 Dry-run: not saving to Firestore")
            else:
                # Save to destination
                dest_ref = db.collection(dest_collection).document()
                dest_ref.set(rewritten)
                print(f"✅ Saved rewritten article → {dest_ref.id}")

                # Mark source processed
                db.collection(source_collection).document(doc.id).update({"processed": True})
                print("✅ Marked original as processed")

                # Optional static export
                if write_static and output_base_dir:
                    out_path = write_static_article(rewritten, output_base_dir)
                    print(f"📝 Wrote static HTML → {out_path}")

            processed_count += 1

        except Exception as e:
            print(f"❌ Error processing article: {e}")
            error_count += 1

        # respect pacing
        if idx < len(docs) and sleep_s > 0:
            print(f"⏳ Sleeping {sleep_s}s...")
            time.sleep(sleep_s)

    print("\n📊 Summary")
    print(f"   ✅ Rewritten & saved: {processed_count}")
    print(f"   ⚠️ Duplicates skipped: {duplicate_count}")
    print(f"   ❌ Errors: {error_count}")
    print(f"   📈 Total handled: {processed_count + duplicate_count + error_count}")

# ---------------------------
# CLI
# ---------------------------

def main():
    global FORUM_SECTION_SLUG
    
    parser = argparse.ArgumentParser(description="Advanced rewriter (option 10) for Politie-Forum.nl")
    parser.add_argument("--project-id", default="blockchainkix-com-fy", help="Firebase project ID")
    parser.add_argument("--source", default=SOURCE_COLLECTION, help="Source collection name")
    parser.add_argument("--dest", default=DEST_COLLECTION, help="Destination collection name")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Max docs to process")
    parser.add_argument("--sleep", type=int, default=DEFAULT_SLEEP, help="Sleep seconds between docs")
    parser.add_argument("--style", default=DEFAULT_STYLE, choices=["Technical", "Normal", "Easy", "Populair", "News Reader"], help="Writing style")
    parser.add_argument("--language", default=DEFAULT_LANGUAGE, choices=["Dutch", "English", "German"], help="Language for style prompts")
    parser.add_argument("--dry-run", action="store_true", help="Process without writing to Firestore")
    parser.add_argument("--write-static", action="store_true", default=WRITE_STATIC_DEFAULT, help="Also export static HTML")
    parser.add_argument("--output-base", default=OUTPUT_BASE_DIR_DEFAULT, help="Base dir for static HTML export")
    parser.add_argument("--forum-section", default=FORUM_SECTION_SLUG, help="Forum section slug for discussion links")
    args = parser.parse_args()

    FORUM_SECTION_SLUG = args.forum_section

    # Firebase
    try:
        db = ensure_firebase(args.project_id)
        print("✅ Connected to Firebase Firestore")
    except Exception as e:
        print(f"❌ Firebase init failed: {e}")
        return

    process_batch(
        db=db,
        limit=args.limit,
        sleep_s=args.sleep,
        style=args.style,
        language=args.language,
        dest_collection=args.dest,
        source_collection=args.source,
        dry_run=bool(args.dry_run),
        write_static=bool(args.write_static),
        output_base_dir=args.output_base if args.write_static else None,
    )

if __name__ == "__main__":
    main()
