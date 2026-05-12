# resume-md — Markdown → HTML → PDF pipeline.
#
# Requires:
#   - pandoc      (https://pandoc.org)
#   - weasyprint  (https://weasyprint.org)
#
# Usage:
#   make            # Build index.html + resume.pdf with the default theme.
#   make THEME=classic
#   make preview    # Build, then open the HTML in the default browser.
#   make check      # Verify required tools are installed.
#   make clean

THEME ?= warm-ink
SOURCE := resume.md
HTML := index.html
PDF := resume.pdf
CSS := .build/style.css

.PHONY: all generate preview check clean

all: generate

generate: $(HTML) $(PDF)

# Base first, theme last: both files declare :root with the same specificity,
# so the later one wins in the cascade. The theme overrides base defaults.
$(CSS): themes/_base.css themes/$(THEME).css
	@mkdir -p .build
	cat themes/_base.css themes/$(THEME).css > $(CSS)

$(HTML): $(SOURCE) $(CSS) templates/resume.html filters/split-date.lua
	pandoc $(SOURCE) \
		--template templates/resume.html \
		--lua-filter filters/split-date.lua \
		--css $(CSS) \
		--embed-resources \
		-o $(HTML)

$(PDF): $(HTML)
	weasyprint $(HTML) $(PDF)

preview: generate
	@open $(HTML) 2>/dev/null || xdg-open $(HTML) 2>/dev/null || echo "open $(HTML) manually"

check:
	@command -v pandoc >/dev/null || { echo "pandoc not found — install: brew install pandoc (macOS) | apt-get install pandoc (Linux)"; exit 1; }
	@command -v weasyprint >/dev/null || { echo "weasyprint not found — install: pipx install weasyprint"; exit 1; }
	@echo "OK"

clean:
	rm -rf .build $(HTML) $(PDF)
