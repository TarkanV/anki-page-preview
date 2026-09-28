import re
import json
import time
import html
from typing import Optional, Tuple, List
from aqt import mw, gui_hooks
from aqt.reviewer import Reviewer
from aqt.previewer import Previewer

mw.addonManager.setWebExports(__name__, r"web/.*\.(css|js)")

def sanitize_field_content(raw_html: str) -> str:
    """Cleans editor wrappers while preserving <img>, media, and HTML headers."""
    text = re.sub(r"<br\s*/?>", "\n", raw_html, flags=re.IGNORECASE)
    text = re.sub(r"</?(?:div|p|pre|span)[^>]*>", "\n", text, flags=re.IGNORECASE)
    return html.unescape(text).strip()

def extract_block_from_text(text: str, target_tag: str) -> Optional[str]:
    """Finds a paragraph, image, or list item (including all nested child bullet points)."""
    tag = target_tag.lstrip("^").strip().lower()
    lines = text.splitlines()

    for idx, line in enumerate(lines):
        m = re.search(rf"\s+\^{re.escape(tag)}\s*$", line, flags=re.IGNORECASE)
        if not m:
            continue

        clean_first_line = line[:m.start()].rstrip()

        # Check if this line is a bullet point or numbered list item
        list_match = re.match(r"^(\s*)([-*+]|\d+[.)])\s+", clean_first_line)
        if list_match:
            base_indent = len(list_match.group(1))
            collected = [clean_first_line]

            # Scoop up all nested child bullets underneath it
            for next_line in lines[idx + 1:]:
                if not next_line.strip():
                    collected.append(next_line)
                    continue

                # Measure indentation of subsequent line
                next_indent = len(next_line) - len(next_line.lstrip())
                if next_indent > base_indent:
                    collected.append(next_line)
                else:
                    break  # Hit a sibling bullet or unindented block -> stop

            return "\n".join(collected)
        else:
            # Normal paragraph or single line
            return clean_first_line

    return None

def extract_section_from_text(text: str, target_header: str) -> Tuple[Optional[str], List[str]]:
    """Extracts a section matching target_header. Supports both Markdown (#) and HTML (<hX>) headers."""
    lines = text.splitlines()
    start_idx = None
    target_level = None
    normalized_target = target_header.strip().lower()
    discovered_headers = []

    for idx, line in enumerate(lines):
        clean_line = line.strip()
        if not clean_line:
            continue

        level = None
        title = None

        # Check Markdown syntax: ## Header
        m_md = re.match(r"^(#{1,6})\s+(.*?)\s*$", clean_line)
        if m_md:
            level = len(m_md.group(1))
            title = m_md.group(2).strip()
        else:
            # Check Native Anki HTML syntax: <h2>Header</h2>
            m_html = re.match(r"^<h([1-6])[^>]*>(.*?)</h\1>$", clean_line, flags=re.IGNORECASE)
            if m_html:
                level = int(m_html.group(1))
                title = re.sub(r"<[^>]+>", "", m_html.group(2)).strip()

        if level and title:
            discovered_headers.append(f"{'#' * level} {title}")

            if start_idx is None:
                if title.lower() == normalized_target:
                    start_idx = idx
                    target_level = level
            else:
                if level <= target_level:
                    return "\n".join(lines[start_idx:idx]), discovered_headers

    if start_idx is not None:
        return "\n".join(lines[start_idx:]), discovered_headers

    return None, discovered_headers

def resolve_note_content(target: str, header: Optional[str]) -> dict:
    target = target.strip()
    id_match = re.match(r"^(?:nid)?(\d{13})$", target)
    note = None

    if id_match:
        try:
            note = mw.col.get_note(int(id_match.group(1)))
        except Exception:
            return {"error": f"Note ID '{target}' not found."}
    else:
        if len(target) < 2:
            return {"error": "Search query too short (min 2 characters)."}

        escaped = target.replace('"', '\\"')
        exact_results = mw.col.find_notes(f'"Front:{escaped}"')
        if len(exact_results) == 1:
            note = mw.col.get_note(exact_results[0])
        else:
            prefix_results = mw.col.find_notes(f'"Front:{escaped}*"')
            if len(prefix_results) == 1:
                note = mw.col.get_note(prefix_results[0])
            elif len(prefix_results) > 1:
                return {"error": f"⚠️ Multiple matches ({len(prefix_results)} cards start with '{target}*'). Please be more specific."}
            else:
                return {"error": f"⚠️ No card found matching '{target}'."}

    field_names = [f["name"] for f in note.note_type()["flds"]]

    # CASE A: A specific header was requested -> Scope search field-by-field
    if header:
        is_block_tag = header.startswith("^")
        all_discovered = []

        for f_name, raw_val in zip(field_names, note.fields):
            cleaned = sanitize_field_content(raw_val)

            if is_block_tag:
                block_content = extract_block_from_text(cleaned, header)
                if block_content:
                    return {"content": block_content}
            else:
                section, discovered = extract_section_from_text(cleaned, header)
                all_discovered.extend(discovered)
                if section:
                    return {"content": section}

        if is_block_tag:
            return {"error": f"Block reference '{header}' not found in note."}
        
        hint = f" Available headers: {', '.join(all_discovered)}" if all_discovered else " No headers found."
        return {"error": f"Header '#{header}' not found.{hint}"}

    # CASE B: Full card preview -> Render each field with labels and dividers
    rendered_fields = []
    for f_name, raw_val in zip(field_names, note.fields):
        cleaned = sanitize_field_content(raw_val)
        if not cleaned:
            continue
        field_block = (
            f'<div class="anki-preview-field">'
            f'<div class="anki-preview-field-badge">{f_name}</div>'
            f'<div class="anki-preview-field-body">\n\n{cleaned}\n\n</div>'
            f'</div>'
        )
        rendered_fields.append(field_block)

    full_card_html = '\n<hr class="anki-preview-field-divider">\n'.join(rendered_fields)
    return {"content": full_card_html}

def is_valid_context(context) -> bool:
    return isinstance(context, (Reviewer, Previewer))

def on_webview_will_set_content(web_content, context):
    if not is_valid_context(context):
        return
    t = int(time.time())
    addon_pkg = __name__

    # Read centralized config.json
    addon_config = mw.addonManager.getConfig(__name__) or {}
    config_json = json.dumps(addon_config)

    # Inject settings as a global JS variable before scripts load
    web_content.head += f"<script>window.__PAGE_PREVIEW_CONFIG__ = {config_json};</script>"

    web_content.css.append(f"/_addons/{addon_pkg}/web/preview.css?t={t}")
    web_content.js.append(f"/_addons/{addon_pkg}/web/preview.js?t={t}")

def on_webview_did_receive_js_message(handled, message, context):
    if not is_valid_context(context) or not message.startswith("previewNote:"):
        return handled
    try:
        payload = json.loads(message[len("previewNote:"):])
        result = resolve_note_content(payload.get("note", ""), payload.get("header"))
        return (True, json.dumps(result))
    except Exception as e:
        return (True, json.dumps({"error": f"Bridge Error: {str(e)}"}))

def on_note_edited(*args, **kwargs):
    if mw.state == "review" and hasattr(mw, "reviewer") and mw.reviewer.web:
        mw.reviewer.web.eval("if (window.forcePreviewRefresh) { window.forcePreviewRefresh(); }")

gui_hooks.operation_did_execute.append(lambda *args, **kwargs: on_note_edited())
gui_hooks.reviewer_did_show_question.append(lambda *args, **kwargs: on_note_edited())
gui_hooks.reviewer_did_show_answer.append(lambda *args, **kwargs: on_note_edited())
gui_hooks.webview_will_set_content.append(on_webview_will_set_content)
gui_hooks.webview_did_receive_js_message.append(on_webview_did_receive_js_message)

from .settings import setup_menu
setup_menu()