#!/usr/bin/env bash
# ==============================================================================
# Palazzo Usellini - Image Optimization Utility (Project Skill)
# Strips EXIF metadata, resizes according to architectural profiles, and converts to WebP.
# ==============================================================================

set -euo pipefail

# Ensure Homebrew tools are in PATH if available
if [ -d "/home/linuxbrew/.linuxbrew/bin" ]; then
  export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"
fi

PROFILE="gallery"
QUALITY=""
KEEP_ORIGINAL=false
CUSTOM_OUTPUT=""

print_usage() {
  echo "Usage: $0 [--profile hero|gallery|thumb] [--quality 1-100] [--keep-original] [--output file.webp] <image_files...>"
  echo ""
  echo "Profiles:"
  echo "  hero     : Max 2000px, Quality 85% (for full-width hero banners / cover backgrounds)"
  echo "  gallery  : Max 1400px, Quality 82% (for gallery photos and article figures)"
  echo "  thumb    : Max 800px,  Quality 80% (for thumbnails and preview cards)"
  exit 1
}

# Parse command line arguments
POSITIONAL_ARGS=()
while [[ $# -gt 0 ]]; do
  case $1 in
    --profile)
      PROFILE="$2"
      shift 2
      ;;
    --quality)
      QUALITY="$2"
      shift 2
      ;;
    --keep-original)
      KEEP_ORIGINAL=true
      shift
      ;;
    --output)
      CUSTOM_OUTPUT="$2"
      shift 2
      ;;
    -h|--help)
      print_usage
      ;;
    *)
      POSITIONAL_ARGS+=("$1")
      shift
      ;;
  esac
done

if [ ${#POSITIONAL_ARGS[@]} -eq 0 ]; then
  echo "Error: No image files specified."
  print_usage
fi

# Verify dependencies
MAGICK_BIN=$(which magick 2>/dev/null || which convert 2>/dev/null || true)
CWEBP_BIN=$(which cwebp 2>/dev/null || true)

if [ -z "$MAGICK_BIN" ] && [ -z "$CWEBP_BIN" ]; then
  echo "Error: Neither 'magick' nor 'cwebp' found in PATH. Ensure Homebrew is configured."
  exit 1
fi

# Define profile parameters
case "$PROFILE" in
  hero)
    MAX_DIM=2000
    DEFAULT_Q=85
    ;;
  thumb)
    MAX_DIM=800
    DEFAULT_Q=80
    ;;
  gallery|*)
    MAX_DIM=1400
    DEFAULT_Q=82
    ;;
esac

FINAL_QUALITY="${QUALITY:-$DEFAULT_Q}"

format_bytes() {
  local bytes=$1
  if [ "$bytes" -ge 1048576 ]; then
    awk -v b="$bytes" 'BEGIN { printf "%.2f MB", b / 1048576 }'
  elif [ "$bytes" -ge 1024 ]; then
    awk -v b="$bytes" 'BEGIN { printf "%.1f KB", b / 1024 }'
  else
    echo "${bytes} B"
  fi
}

# Process each file
for input_file in "${POSITIONAL_ARGS[@]}"; do
  if [ ! -f "$input_file" ]; then
    echo "Warning: File not found: $input_file (skipping)"
    continue
  fi

  orig_size=$(stat -c%s "$input_file")
  dir_name=$(dirname "$input_file")
  base_name=$(basename "$input_file")
  name_without_ext="${base_name%.*}"

  if [ -n "$CUSTOM_OUTPUT" ] && [ ${#POSITIONAL_ARGS[@]} -eq 1 ]; then
    output_file="$CUSTOM_OUTPUT"
  else
    output_file="${dir_name}/${name_without_ext}.webp"
  fi

  echo "Processing [$PROFILE | ${MAX_DIM}px | Q:${FINAL_QUALITY}%]: $input_file"

  # Use cwebp or magick for resizing, EXIF stripping, and WebP conversion
  if [ -n "$CWEBP_BIN" ]; then
    if [ -n "$MAGICK_BIN" ]; then
      "$MAGICK_BIN" "$input_file" -strip -resize "${MAX_DIM}x${MAX_DIM}>" -quality "$FINAL_QUALITY" "$output_file"
    else
      "$CWEBP_BIN" -q "$FINAL_QUALITY" -metadata none "$input_file" -o "$output_file"
    fi
  else
    "$MAGICK_BIN" "$input_file" -strip -resize "${MAX_DIM}x${MAX_DIM}>" -quality "$FINAL_QUALITY" "$output_file"
  fi

  new_size=$(stat -c%s "$output_file")
  orig_fmt=$(format_bytes "$orig_size")
  new_fmt=$(format_bytes "$new_size")
  savings=$(awk -v o="$orig_size" -v n="$new_size" 'BEGIN { printf "%.1f", ((o - n) / o) * 100 }')

  echo "  ✓ Generated: $output_file ($orig_fmt -> $new_fmt, savings: -$savings%)"

  if [ "$KEEP_ORIGINAL" = false ] && [ "$input_file" != "$output_file" ]; then
    :
  fi
done

echo "Optimization completed successfully."
