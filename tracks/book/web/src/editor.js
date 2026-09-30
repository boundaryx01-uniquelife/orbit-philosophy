(function () {
  "use strict";

  const STORAGE_KEY = "orbit-book-corrections:first-output:v0.7";
  const manuscript = document.getElementById("editable-manuscript");
  const toggleButton = document.getElementById("edit-toggle");
  const exportButton = document.getElementById("export-corrections");
  const resetButton = document.getElementById("reset-corrections");
  const status = document.getElementById("editor-status");
  const originalHtml = manuscript.innerHTML;
  let editing = false;
  let saveTimer = null;

  function formatTime(value) {
    return new Intl.DateTimeFormat("ko-KR", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit"
    }).format(new Date(value));
  }

  function setStatus(message) {
    status.textContent = message;
  }

  function sanitizeHtml(html) {
    const template = document.createElement("template");
    template.innerHTML = html;
    template.content.querySelectorAll("script, style, iframe, object, embed, form, input, textarea, button, link, meta").forEach(function (node) {
      node.remove();
    });
    template.content.querySelectorAll("*").forEach(function (node) {
      Array.from(node.attributes).forEach(function (attribute) {
        const name = attribute.name.toLowerCase();
        const value = attribute.value.trim().toLowerCase();
        if (name.startsWith("on") || ((name === "href" || name === "src") && value.startsWith("javascript:"))) {
          node.removeAttribute(attribute.name);
        }
      });
    });
    return template.innerHTML;
  }

  function loadSavedCorrection() {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
      if (!saved || !saved.html) return;
      manuscript.innerHTML = sanitizeHtml(saved.html);
      setStatus("저장된 교정본을 불러왔습니다 · " + formatTime(saved.savedAt));
    } catch (error) {
      setStatus("저장된 교정본을 읽지 못했습니다. 원문으로 시작합니다.");
    }
  }

  function saveCorrection() {
    const savedAt = new Date().toISOString();
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        version: "v0.7",
        savedAt: savedAt,
        html: sanitizeHtml(manuscript.innerHTML)
      }));
      setStatus("이 브라우저에 자동 저장됨 · " + formatTime(savedAt));
    } catch (error) {
      setStatus("브라우저 저장이 제한되었습니다. Markdown으로 내려받아 보관하세요.");
    }
  }

  function scheduleSave() {
    setStatus("교정 중 · 저장 대기");
    window.clearTimeout(saveTimer);
    saveTimer = window.setTimeout(saveCorrection, 650);
  }

  function setEditing(next) {
    editing = next;
    manuscript.contentEditable = editing ? "true" : "false";
    manuscript.classList.toggle("is-editing", editing);
    toggleButton.textContent = editing ? "교정 종료" : "교정 시작";
    if (editing) {
      setStatus("교정 모드 · 문장을 눌러 바로 수정하세요.");
      manuscript.focus({ preventScroll: true });
    } else {
      window.clearTimeout(saveTimer);
      saveCorrection();
    }
  }

  function inlineMarkdown(node) {
    if (node.nodeType === Node.TEXT_NODE) return node.textContent;
    if (node.nodeType !== Node.ELEMENT_NODE) return "";
    const text = Array.from(node.childNodes).map(inlineMarkdown).join("");
    const tag = node.tagName.toLowerCase();
    if (tag === "strong" || tag === "b") return "**" + text + "**";
    if (tag === "em" || tag === "i") return "*" + text + "*";
    if (tag === "code") return "`" + text + "`";
    if (tag === "br") return "\n";
    return text;
  }

  function blockMarkdown(node) {
    if (node.nodeType === Node.TEXT_NODE) return node.textContent.trim();
    if (node.nodeType !== Node.ELEMENT_NODE) return "";
    const tag = node.tagName.toLowerCase();
    const children = Array.from(node.children);
    if (/^h[1-3]$/.test(tag)) {
      return "#".repeat(Number(tag.slice(1))) + " " + inlineMarkdown(node).trim() + "\n\n";
    }
    if (tag === "p") return inlineMarkdown(node).trim() + "\n\n";
    if (tag === "blockquote") {
      const quote = Array.from(node.childNodes).map(inlineMarkdown).join("").trim();
      return quote.split("\n").map(function (line) { return "> " + line; }).join("\n") + "\n\n";
    }
    if (tag === "ul" || tag === "ol") {
      return children.map(function (item, index) {
        const marker = tag === "ol" ? String(index + 1) + "." : "-";
        return marker + " " + inlineMarkdown(item).trim();
      }).join("\n") + "\n\n";
    }
    if (tag === "hr") return "---\n\n";
    if (tag === "figure") {
      const image = node.querySelector("img");
      const caption = node.querySelector("figcaption");
      const alt = image ? image.alt : "본문 삽화";
      const note = caption ? caption.textContent.trim() : alt;
      return "![" + alt + "](chapter-01-first-output-v0.1.png)\n\n*" + note + "*\n\n";
    }
    return children.map(blockMarkdown).join("");
  }

  function exportMarkdown() {
    if (editing) saveCorrection();
    const exportedAt = new Date().toISOString();
    const markdown = [
      "---",
      "title: \"첫 결과물이 곧 완성은 아니다 - 교정본\"",
      "source: \"ORBIT web correction v0.7\"",
      "exported_at: \"" + exportedAt + "\"",
      "---",
      "",
      Array.from(manuscript.children).map(blockMarkdown).join("").trim(),
      ""
    ].join("\n");
    const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "First_Output_Is_Not_Completion_corrections_v0.7.md";
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    setStatus("Markdown 교정본을 내려받았습니다.");
  }

  function resetCorrection() {
    const confirmed = window.confirm("이 브라우저에 저장된 교정 내용을 지우고 원문으로 복원할까요?");
    if (!confirmed) return;
    localStorage.removeItem(STORAGE_KEY);
    manuscript.innerHTML = originalHtml;
    setEditing(false);
    setStatus("원문으로 복원했습니다.");
  }

  toggleButton.addEventListener("click", function () { setEditing(!editing); });
  exportButton.addEventListener("click", exportMarkdown);
  resetButton.addEventListener("click", resetCorrection);
  manuscript.addEventListener("input", scheduleSave);
  window.addEventListener("beforeunload", function () {
    if (editing) saveCorrection();
  });

  loadSavedCorrection();
})();
