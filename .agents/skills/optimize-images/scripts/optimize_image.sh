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
  echo "Uso: $0 [--profile hero|gallery|thumb] [--quality 1-100] [--keep-original] [--output file.webp] <file_immagine...>"
  echo ""
  echo "Profili:"
  echo "  hero     : Max 2000px, Qualità 85% (per banner full-width / hero background)"
  echo "  gallery  : Max 1400px, Qualità 82% (per foto della galleria e figure articoli)"
  echo "  thumb    : Max 800px,  Qualità 80% (per miniature e card di anteprima)"
  exit 1
}

# Parsing argomenti
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
  echo "Errore: Nessun file immagine specificato."
  print_usage
fi

# Verifica dipendenze
MAGICK_BIN=$(which magick 2>/dev/null || which convert 2>/dev/null || true)
CWEBP_BIN=$(which cwebp 2>/dev/null || true)

if [ -z "$MAGICK_BIN" ] && [ -z "$CWEBP_BIN" ]; then
  echo "Errore: Impossibile trovare né 'magick' né 'cwebp' in PATH. Assicurati che Homebrew sia configurato."
  exit 1
fi

# Definizione parametri per profilo
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

# Elaborazione di ciascun file
for input_file in "${POSITIONAL_ARGS[@]}"; do
  if [ ! -f "$input_file" ]; then
    echo "Attenzione: File non trovato: $input_file (salto)"
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

  echo "Elaborazione [$PROFILE | ${MAX_DIM}px | Q:${FINAL_QUALITY}%]: $input_file"

  # Utilizzo di cwebp o magick per ridimensionamento, rimozione EXIF e WebP
  if [ -n "$CWEBP_BIN" ]; then
    # cwebp gestisce direttamente resize (-resize width height con aspect ratio o tramite ImageMagick preprocess)
    # Per ridimensionamento con vincolo proporzionale max (downscale only), usiamo ImageMagick se presente per pipeline robusta
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

  echo "  ✓ Generato: $output_file ($orig_fmt -> $new_fmt, risparmio: -$savings%)"

  # Se l'output sovrascrive lo stesso file o se non è richiesta conservazione ed è cambiato formato
  if [ "$KEEP_ORIGINAL" = false ] && [ "$input_file" != "$output_file" ]; then
    # Verifica se l'utente vuole mantenere o rimuovere l'originale
    # Per sicurezza in batch, lasciamo l'originale a meno che non sia specificato
    :
  fi
done

echo "Ottimizzazione completata con successo."
