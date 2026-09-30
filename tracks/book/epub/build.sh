#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
epub_dir="$repo_root/tracks/book/epub"
output="$epub_dir/dist/First_Output_Is_Not_Completion_v0.6.epub"
build_dir="$(mktemp -d)"
trap 'rm -rf "$build_dir"' EXIT

mkdir -p "$epub_dir/dist"

python3 "$epub_dir/src/embed_cover.py" \
  "$repo_root/tracks/book/assets/cover-layout-v0.1.svg" \
  "$repo_root/tracks/book/assets/cover-art-v0.1.png" \
  "$build_dir/cover.svg"

pandoc \
  "$epub_dir/src/frontmatter.md" \
  "$repo_root/tracks/book/drafts/Chapter_01_First_Output_Is_Not_Completion_v0.2.md" \
  "$repo_root/tracks/book/drafts/Chapter_02_When_Helpfulness_Loses_The_Goal_v0.1.md" \
  "$repo_root/tracks/book/drafts/Chapter_03_Same_Words_Different_Meanings_v0.1.md" \
  "$epub_dir/src/part-02.md" \
  "$repo_root/tracks/book/drafts/Chapter_04_Check_Four_Lines_Before_Creating_v0.3.md" \
  "$repo_root/tracks/book/drafts/Chapter_05_A_Relationship_That_Does_Not_Erase_Differences_v0.1.md" \
  "$repo_root/tracks/book/drafts/Chapter_06_Judgment_And_Partner_Responsibility_v0.1.md" \
  "$repo_root/tracks/book/drafts/Chapter_07_Every_Choice_Needs_A_Reason_v0.1.md" \
  "$epub_dir/src/part-03.md" \
  "$repo_root/tracks/book/drafts/Chapter_08_When_Conversation_Disappears_v0.1.md" \
  "$repo_root/tracks/book/drafts/Chapter_09_Recording_Misunderstanding_And_Correction_v0.1.md" \
  "$repo_root/tracks/book/drafts/Chapter_10_Completion_Without_Finality_v0.1.md" \
  "$epub_dir/src/appendix.md" \
  --from=markdown \
  --to=epub3 \
  --metadata-file="$epub_dir/src/metadata.yaml" \
  --css="$epub_dir/src/epub.css" \
  --lua-filter="$epub_dir/src/strip_draft_header.lua" \
  --epub-cover-image="$build_dir/cover.svg" \
  --resource-path="$repo_root:$repo_root/tracks/book:$epub_dir/src" \
  --toc \
  --toc-depth=2 \
  --split-level=1 \
  --output="$output"

test "$(unzip -p "$output" mimetype)" = "application/epub+zip"
unzip -t "$output" >/dev/null

contents="$(unzip -Z1 "$output")"
for required in "META-INF/container.xml" "EPUB/content.opf" "EPUB/nav.xhtml"; do
  if ! grep -Fxq "$required" <<<"$contents"; then
    echo "Missing required EPUB entry: $required" >&2
    exit 1
  fi
done

if ! grep -Eq 'cover\.svg' <<<"$contents"; then
  echo "Cover image was not packaged" >&2
  exit 1
fi

if ! grep -Eq 'chapter-01-first-output-v0\.1|media/file[0-9]+\.png' <<<"$contents"; then
  echo "Chapter illustration was not packaged" >&2
  exit 1
fi

if command -v epubcheck >/dev/null 2>&1; then
  epubcheck "$output"
fi

echo "$output"
