#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
site_dir="$repo_root/tracks/book/site"
dist="$site_dir/dist"

mkdir -p "$dist/assets" "$dist/book" "$dist/downloads"

cp "$site_dir/src/index.html" "$dist/index.html"
cp "$site_dir/src/.nojekyll" "$dist/.nojekyll"
cp "$site_dir/src/site.css" "$dist/assets/site.css"
cp "$repo_root/tracks/book/assets/cover-art-v0.1.png" "$dist/assets/cover-art-v0.1.png"
cp "$repo_root/tracks/book/assets/fonts/NotoSansKR-Book-Regular.ttf" "$dist/assets/NotoSansKR-Book-Regular.ttf"
cp "$repo_root/tracks/book/assets/fonts/NotoSansKR-Book-Bold.ttf" "$dist/assets/NotoSansKR-Book-Bold.ttf"
cp "$repo_root/tracks/book/web/dist/First_Answer_Is_Not_The_End_v0.1.html" "$dist/book/index.html"
cp "$repo_root/output/pdf/First_Answer_Is_Not_The_End_v0.1.pdf" "$dist/downloads/First_Answer_Is_Not_The_End_v0.1.pdf"
cp "$repo_root/tracks/book/epub/dist/First_Answer_Is_Not_The_End_v0.1.epub" "$dist/downloads/First_Answer_Is_Not_The_End_v0.1.epub"

test -s "$dist/index.html"
test -s "$dist/book/index.html"
test -s "$dist/downloads/First_Answer_Is_Not_The_End_v0.1.pdf"
test -s "$dist/downloads/First_Answer_Is_Not_The_End_v0.1.epub"

echo "$dist"

