#!/usr/bin/env bash
set -euo pipefail
repo_root="$(git rev-parse --show-toplevel)"
output="$repo_root/tracks/book/epub/dist/First_Output_Is_Not_Completion_v0.5.md"
mkdir -p "$(dirname "$output")"
pandoc \
  "$repo_root/tracks/book/epub/src/frontmatter.md" \
  "$repo_root/tracks/book/drafts/Chapter_01_First_Output_Is_Not_Completion_v0.2.md" \
  "$repo_root/tracks/book/drafts/Chapter_02_When_Helpfulness_Loses_The_Goal_v0.1.md" \
  "$repo_root/tracks/book/drafts/Chapter_03_Same_Words_Different_Meanings_v0.1.md" \
  "$repo_root/tracks/book/epub/src/part-02.md" \
  "$repo_root/tracks/book/drafts/Chapter_04_Check_Four_Lines_Before_Creating_v0.3.md" \
  "$repo_root/tracks/book/drafts/Chapter_05_A_Relationship_That_Does_Not_Erase_Differences_v0.1.md" \
  "$repo_root/tracks/book/drafts/Chapter_06_Judgment_And_Partner_Responsibility_v0.1.md" \
  "$repo_root/tracks/book/drafts/Chapter_07_Every_Choice_Needs_A_Reason_v0.1.md" \
  "$repo_root/tracks/book/epub/src/part-03.md" \
  "$repo_root/tracks/book/drafts/Chapter_08_When_Conversation_Disappears_v0.1.md" \
  "$repo_root/tracks/book/drafts/Chapter_09_Recording_Misunderstanding_And_Correction_v0.1.md" \
  "$repo_root/tracks/book/drafts/Chapter_10_Completion_Without_Finality_v0.1.md" \
  "$repo_root/tracks/book/epub/src/appendix.md" \
  --from=markdown --to=gfm --wrap=none \
  --lua-filter="$repo_root/tracks/book/epub/src/strip_draft_header.lua" \
  --output="$output"
echo "$output"
