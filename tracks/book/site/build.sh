#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
site_dir="$repo_root/tracks/book/site"
dist="$site_dir/dist"

mkdir -p "$dist/assets" "$dist/book" "$dist/downloads"
find "$dist/downloads" -maxdepth 1 -type f -name '*.pdf' -delete

cp "$site_dir/src/index.html" "$dist/index.html"
cp "$site_dir/src/.nojekyll" "$dist/.nojekyll"
cp "$site_dir/src/site.css" "$dist/assets/site.css"
cp "$repo_root/tracks/book/assets/cover-art-v0.1.png" "$dist/assets/cover-art-v0.1.png"
cp "$repo_root/tracks/book/assets/fonts/NotoSansKR-Book-Regular.ttf" "$dist/assets/NotoSansKR-Book-Regular.ttf"
cp "$repo_root/tracks/book/assets/fonts/NotoSansKR-Book-Bold.ttf" "$dist/assets/NotoSansKR-Book-Bold.ttf"
cp "$repo_root/tracks/book/web/dist/First_Output_Is_Not_Completion_v0.4.html" "$dist/book/index.html"
cp "$repo_root/tracks/book/epub/dist/First_Output_Is_Not_Completion_v0.4.epub" "$dist/downloads/First_Output_Is_Not_Completion_v0.4.epub"

test -s "$dist/index.html"
test -s "$dist/book/index.html"
test -s "$dist/downloads/First_Output_Is_Not_Completion_v0.4.epub"

echo "$dist"
