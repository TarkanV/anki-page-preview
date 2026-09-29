# 🔍 Note Preview for Anki (Obsidian-Style Hovercards)

[![Anki Version](https://img.shields.io/badge/Anki-23%2B%20%7C%2024%2B%20%7C%2025%2B%20%7C%2026%2B-blue.svg)](https://apps.ankiweb.net/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Pure Vanilla JS](https://img.shields.io/badge/JavaScript-Vanilla%20(No%20jQuery)-brightgreen.svg)]()

Bring **Obsidian-style interactive page, section, and block previews** straight into your Anki review sessions. Hover over any wikilink to instantly peek into notes, specific headings, bullet points, or reference images without cluttering your cards or interrupting your review flow.

---

## ✨ Features

- **⚡ Instant Hover Previews:** Hover over any link to peek at specific sections, diagrams, or entire cards without breaking your review flow.
- **🔍 Flexible Linking:** Link to cards naturally by Title (with smart search) or by permanent Note ID so links never break when renamed.
- **🎯 Block References (`^tag`):** Tag individual bullet points, paragraphs, or images with `^tag` to preview just that item without creating huge headers.
- **🌳 Outline-Aware:** Previewing a bullet point automatically includes all of its indented sub-bullets and lists.
- **🔄 Nested Popovers:** Open previews *inside* previews without losing your place—hovering back to the parent neatly closes the child.
- **📐 Smart Positioning:** Popups automatically flip above or below your text and adapt to your screen size so they never run off-screen.
- **🎨 Automatic Dark & Light Mode:** Seamlessly matches your active Anki theme with zero setup.
- **⚙️ Easy Visual Settings:** Tweak popup sizes, font size, and hover timing from a dedicated menu under **Tools $\rightarrow$ Note Preview Settings...**.


---

## 🔗 Supported Link Syntax

| Syntax | Description |
| :--- | :--- |
| `[[#Heading Name]]` | Previews a specific section on the **current card**. |
| `[[Note Title#Heading]]` | Finds a card by its Front field and previews that section. |
| `[[Note Title]]` | Previews the **entire card** with subtle field indicators. |
| `[[#^block-tag]]` | Previews an isolated paragraph, image, or bullet point on the same card. |
| `[[Note#^block-tag]]` | Previews an isolated block or image from another note. |
| `[[nid1790608012445#Header]]` | Permanent, rename-proof link by Anki Note ID. |
| `[[Target#Header\|Display Label]]` | Custom display alias (hides brackets, hashes, and pipes). |

---


