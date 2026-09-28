console.log("%c[Page Preview Addon] Initialized with Full Configuration Suite!", "color: #a6e3a1; font-weight: bold;");

(function initSmartPreview() {
    let activePopups = [];
    let closeTimer = null;
    let openTimer = null;
    let pruneTimer = null;

    function getConfig() {
        return window.__PAGE_PREVIEW_CONFIG__ || {};
    }

    function getHeaderLevel(el) {
        const match = el.tagName.match(/^H([1-6])$/);
        return match ? parseInt(match[1], 10) : null;
    }

    function extractSection(headerEl) {
        const targetLevel = getHeaderLevel(headerEl);
        const content = [headerEl.cloneNode(true)];
        let sibling = headerEl.nextElementSibling;

        while (sibling) {
            const lvl = getHeaderLevel(sibling);
            if (lvl !== null && lvl <= targetLevel) break;
            content.push(sibling.cloneNode(true));
            sibling = sibling.nextElementSibling;
        }
        return content;
    }

    function cancelClose() {
        if (closeTimer) {
            clearTimeout(closeTimer);
            closeTimer = null;
        }
    }

    function cancelOpen() {
        if (openTimer) {
            clearTimeout(openTimer);
            openTimer = null;
        }
    }

    function cancelPrune() {
        if (pruneTimer) {
            clearTimeout(pruneTimer);
            pruneTimer = null;
        }
    }

    function scheduleClose() {
        cancelClose();
        const conf = getConfig();
        const delay = typeof conf.closeDelay === "number" ? conf.closeDelay : 150;

        closeTimer = setTimeout(() => {
            activePopups.forEach(popup => popup.remove());
            activePopups = [];
        }, delay);
    }

    function closePopupsAbove(targetDepth) {
        cancelPrune();
        while (activePopups.length > targetDepth) {
            const popup = activePopups.pop();
            popup.remove();
        }
    }

    function handlePopupActive(popup, event) {
        cancelClose();
        const depth = parseInt(popup.dataset.depth, 10);
        const conf = getConfig();
        const delay = typeof conf.closeDelay === "number" ? conf.closeDelay : 150;

        if (activePopups.length === depth) {
            cancelPrune();
        } 
        else if (activePopups.length > depth) {
            const childPopup = activePopups[depth];
            let onTrigger = false;
            
            if (childPopup && childPopup._triggerElement) {
                if (event && (event.target === childPopup._triggerElement || childPopup._triggerElement.contains(event.target))) {
                    onTrigger = true;
                }
            }

            if (onTrigger) {
                cancelPrune();
            } else if (!pruneTimer) {
                pruneTimer = setTimeout(() => {
                    closePopupsAbove(depth);
                    pruneTimer = null;
                }, delay);
            }
        }
    }

    function positionPopup(popup, triggerRect) {
        const conf = getConfig();
        const GAP = typeof conf.gap === "number" ? conf.gap : 2;
        const VIEWPORT_MARGIN = typeof conf.viewportMargin === "number" ? conf.viewportMargin : 24;

        const spaceBelow = window.innerHeight - triggerRect.bottom - VIEWPORT_MARGIN;
        const spaceAbove = triggerRect.top - VIEWPORT_MARGIN;

        const placeBelow = (spaceBelow >= spaceAbove) || (spaceBelow >= 240);
        const availableHeight = placeBelow ? spaceBelow : spaceAbove;

        popup.style.minWidth = conf.minWidth || "320px";
        popup.style.maxWidth = conf.maxWidth || "65vw";
        popup.style.borderRadius = conf.borderRadius || "8px";
        popup.style.padding = conf.popupPadding || "16px 20px";
        popup.style.fontSize = conf.fontSize || "14px";
        popup.style.lineHeight = conf.lineHeight || "1.5";

        const maxHeightSetting = conf.maxHeight || "52vh";
        popup.style.maxHeight = `min(${maxHeightSetting}, ${Math.max(120, availableHeight - GAP)}px)`;

        popup.classList.remove("theme-light", "theme-dark");
        if (conf.theme === "light") popup.classList.add("theme-light");
        if (conf.theme === "dark") popup.classList.add("theme-dark");

        const actualWidth = popup.offsetWidth;
        const actualHeight = popup.offsetHeight;

        let top;
        if (placeBelow) {
            top = triggerRect.bottom + GAP;
        } else {
            top = triggerRect.top - actualHeight - GAP;
        }

        const linkCenterX = triggerRect.left + (triggerRect.width / 2);
        let idealLeft = linkCenterX - (actualWidth / 2);

        const maxLeft = window.innerWidth - actualWidth - VIEWPORT_MARGIN;
        const minLeft = VIEWPORT_MARGIN;
        const left = Math.max(minLeft, Math.min(idealLeft, maxLeft));

        popup.style.top = `${top}px`;
        popup.style.left = `${left}px`;
    }

    function processLinkMatch(rawText, inheritedNote = "") {
        let [linkPart, alias] = rawText.split('|');
        linkPart = linkPart.trim();
        alias = alias ? alias.trim() : null;

        let targetNote = "";
        let targetHeader = "";

        if (linkPart.startsWith("#")) {
            targetHeader = linkPart.slice(1).trim();
            if (inheritedNote) {
                targetNote = inheritedNote;
            }
        } else if (linkPart.includes("#")) {
            const parts = linkPart.split("#");
            targetNote = parts[0].trim();
            targetHeader = parts[1].trim();
        } else {
            targetNote = linkPart.trim();
        }

        let displayName = alias;
        if (!displayName) {
            if (targetHeader && (!targetNote || targetNote === inheritedNote)) {
                displayName = targetHeader;
            } else if (targetHeader && targetNote) {
                displayName = `${targetNote} > ${targetHeader}`;
            } else {
                displayName = targetNote;
            }
        }

        return { targetNote, targetHeader, displayName };
    }

    function createLinkElement(info) {
        const a = document.createElement("a");
        a.className = "anki-preview-link";
        a.href = "javascript:void(0);";
        a.textContent = info.displayName;
        a.dataset.targetNote = info.targetNote;
        a.dataset.targetHeader = info.targetHeader;
        return a;
    }

    function transformLinks(container = document.body) {
        const popupContext = container.closest ? (container.closest(".anki-preview-popup") || (container.classList.contains("anki-preview-popup") ? container : null)) : null;
        const inheritedNote = popupContext ? (popupContext.dataset.originNote || "") : "";

        // Pass 1: Existing template highlight spans
        const highlightedSpans = container.querySelectorAll(".bracket-highlight");
        highlightedSpans.forEach((el) => {
            if (el.classList.contains("anki-preview-link")) return;

            const prev = el.previousSibling;
            const next = el.nextSibling;
            const isDouble = prev && prev.nodeType === Node.TEXT_NODE && prev.textContent.endsWith("[") &&
                             next && next.nodeType === Node.TEXT_NODE && next.textContent.startsWith("]");

            if (!isDouble) return;

            const raw = el.textContent.replace(/^\[+|\]+$/g, '').trim();
            prev.textContent = prev.textContent.slice(0, -1);
            next.textContent = next.textContent.slice(1);

            const info = processLinkMatch(raw, inheritedNote);
            const a = createLinkElement(info);
            if (el.parentNode) {
                el.parentNode.replaceChild(a, el);
            }
        });

        // Pass 2: Direct text TreeWalker
        const walker = document.createTreeWalker(
            container,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode: (node) => {
                    if (!node.parentElement) return NodeFilter.FILTER_REJECT;
                    if (node.parentElement.closest(".anki-preview-link, script, style, pre")) {
                        return NodeFilter.FILTER_REJECT;
                    }
                    return node.textContent.includes("[[") ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP;
                }
            }
        );

        // Pass 3: Detect and hide ^block-tags while stamping parent container
        const blockWalker = document.createTreeWalker(
            container,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode: (node) => {
                    if (!node.parentElement || node.parentElement.closest("script, style, pre, .anki-preview-popup")) {
                        return NodeFilter.FILTER_REJECT;
                    }
                    return /\s+\^([a-zA-Z0-9_-]+)\s*$/.test(node.textContent) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP;
                }
            }
        );

        const blockNodes = [];
        let bNode;
        while (bNode = blockWalker.nextNode()) {
            blockNodes.push(bNode);
        }

        blockNodes.forEach((tNode) => {
            const m = tNode.textContent.match(/\s+\^([a-zA-Z0-9_-]+)\s*$/);
            if (m) {
                const tag = m[1].toLowerCase();
                const parent = tNode.parentElement;
                const blockEl = parent.closest("p, div, li, blockquote, h1, h2, h3, h4, h5, h6") || parent;
                blockEl.dataset.blockId = tag;
                tNode.textContent = tNode.textContent.replace(/\s+\^[a-zA-Z0-9_-]+\s*$/, "");
            }
        });

        const nodesToReplace = [];
        let currentNode;
        while (currentNode = walker.nextNode()) {
            nodesToReplace.push(currentNode);
        }

        const wikiRegex = /\[\[(.*?)\]\]/g;
        nodesToReplace.forEach((textNode) => {
            const text = textNode.textContent;
            if (!wikiRegex.test(text)) return;
            wikiRegex.lastIndex = 0;

            const fragment = document.createDocumentFragment();
            let lastIndex = 0;
            let match;

            while ((match = wikiRegex.exec(text)) !== null) {
                if (match.index > lastIndex) {
                    fragment.appendChild(document.createTextNode(text.slice(lastIndex, match.index)));
                }

                const info = processLinkMatch(match[1].trim(), inheritedNote);
                fragment.appendChild(createLinkElement(info));

                lastIndex = match.index + match[0].length;
            }

            if (lastIndex < text.length) {
                fragment.appendChild(document.createTextNode(text.slice(lastIndex)));
            }

            if (textNode.parentNode) {
                textNode.parentNode.replaceChild(fragment, textNode);
            }
        });
    }

    window.forcePreviewRefresh = () => {
        transformLinks();
    };

    const observer = new MutationObserver(() => {
        transformLinks();
    });
    observer.observe(document.body, { childList: true, subtree: true });

    transformLinks();

    function triggerPreview(target) {
        const targetNote = target.dataset.targetNote;
        const targetHeader = target.dataset.targetHeader;

        const parentPopup = target.closest(".anki-preview-popup");
        const currentDepth = parentPopup ? parseInt(parentPopup.dataset.depth, 10) : 0;
        const targetDepth = currentDepth + 1;

        if (activePopups[currentDepth] && activePopups[currentDepth]._triggerElement === target) {
            return;
        }

        closePopupsAbove(currentDepth);

        const popup = document.createElement("div");
        popup.className = "anki-preview-popup";
        popup.dataset.depth = targetDepth;
        popup.dataset.originNote = targetNote || (parentPopup ? parentPopup.dataset.originNote : "");
        popup.style.zIndex = (100000 + targetDepth * 10).toString();
        popup._triggerElement = target;

        popup.addEventListener("mouseenter", (ev) => handlePopupActive(popup, ev));
        popup.addEventListener("mousemove", (ev) => handlePopupActive(popup, ev));
        popup.addEventListener("mouseleave", scheduleClose);

        document.body.appendChild(popup);

        function renderExternalMarkdown(rawMarkdown) {
            let processed = rawMarkdown.replace(/!\[\[(.*?)\]\]/g, '<img src="$1">');

            if (window.markdownit) {
                const md = window.markdownit({ breaks: true, html: true });
                popup.innerHTML = md.render(processed);
            } else {
                popup.innerHTML = processed;
            }

            if (window.renderMathInElement) {
                renderMathInElement(popup, {
                    delimiters: [
                        {left: "$$", right: "$$", display: true},
                        {left: "$", right: "$", display: false}
                    ],
                    throwOnError: false
                });
            }

            const conf = getConfig();
            if (conf.showFieldBadges === false) {
                popup.querySelectorAll(".anki-preview-field-badge").forEach(el => el.style.display = "none");
            } else {
                popup.querySelectorAll(".anki-preview-field-badge").forEach(el => {
                    if (conf.fieldBadgeFontSize) el.style.fontSize = conf.fieldBadgeFontSize;
                    if (typeof conf.fieldBadgeOpacity === "number") el.style.opacity = conf.fieldBadgeOpacity;
                });
            }

            if (conf.showFieldDividers === false) {
                popup.querySelectorAll(".anki-preview-field-divider").forEach(el => el.style.display = "none");
            }

            transformLinks(popup);
            positionPopup(popup, target.getBoundingClientRect());
        }

        // Case 1: Same-note header OR ^block-tag
        if (!targetNote && targetHeader) {
            // Sub-case A: Block tag lookup (^tag)
            if (targetHeader.startsWith("^")) {
                const blockTag = targetHeader.slice(1).toLowerCase();
                const match = document.querySelector(`[data-block-id="${blockTag}"]:not(.anki-preview-popup *)`);
                if (match) {
                    const clone = match.cloneNode(true);
                    if (match.tagName === "LI") {
                        const isOrdered = match.parentElement && match.parentElement.tagName === "OL";
                        const listWrapper = document.createElement(isOrdered ? "ol" : "ul");
                        listWrapper.style.margin = "0";
                        listWrapper.style.paddingLeft = "20px";
                        listWrapper.appendChild(clone);
                        popup.appendChild(listWrapper);
                    } else {
                        popup.appendChild(clone);
                    }
                    transformLinks(popup);
                } else {
                    popup.innerHTML = `<span style="color: #f38ba8; font-style: italic;">Block reference "${targetHeader}" not found on this card.</span>`;
                }
            } 
            // Sub-case B: Standard header lookup (RESTORED!)
            else {
                const allHeaders = Array.from(
                    document.querySelectorAll("h1, h2, h3, h4, h5, h6")
                ).filter(h => !h.closest(".anki-preview-popup"));

                const match = allHeaders.find(h => h.textContent.trim().toLowerCase() === targetHeader.toLowerCase());

                if (match) {
                    const nodes = extractSection(match);
                    nodes.forEach(node => popup.appendChild(node));
                    transformLinks(popup);
                } else {
                    popup.innerHTML = `<span style="color: #f38ba8; font-style: italic;">Header "#${targetHeader}" not found on this card.</span>`;
                }
            }

            positionPopup(popup, target.getBoundingClientRect());
        } 
        // Case 2: Cross-note
        else {
            popup.innerHTML = `<span style="color: var(--preview-badge-fg); opacity: 0.5; font-style: italic;">Loading note preview...</span>`;
            positionPopup(popup, target.getBoundingClientRect());

            const requestPayload = { note: targetNote, header: targetHeader };

            pycmd(`previewNote:${JSON.stringify(requestPayload)}`, (response) => {
                if (!response) {
                    popup.innerHTML = `<span style="color: #f38ba8;">Error: Python returned empty response.</span>`;
                    positionPopup(popup, target.getBoundingClientRect());
                    return;
                }

                try {
                    const data = JSON.parse(response);
                    if (data.error) {
                        popup.innerHTML = `<span style="color: #f38ba8; font-style: italic;">${data.error}</span>`;
                        positionPopup(popup, target.getBoundingClientRect());
                    } else {
                        renderExternalMarkdown(data.content);
                    }
                } catch (err) {
                    popup.innerHTML = `<span style="color: #f38ba8;">JSON Parse Error.</span>`;
                    positionPopup(popup, target.getBoundingClientRect());
                }
            });
        }

        activePopups.push(popup);
    }

    document.addEventListener("mouseover", (e) => {
        const target = e.target;
        if (!target.classList.contains("anki-preview-link")) return;

        cancelClose();
        cancelOpen();
        cancelPrune();

        const conf = getConfig();
        const openDelay = typeof conf.openDelay === "number" ? conf.openDelay : 120;

        openTimer = setTimeout(() => {
            triggerPreview(target);
        }, openDelay);
    });

    document.addEventListener("mouseout", (e) => {
        const target = e.target;
        if (target.classList.contains("anki-preview-link")) {
            cancelOpen(); 
            scheduleClose();
        }
    });
})();