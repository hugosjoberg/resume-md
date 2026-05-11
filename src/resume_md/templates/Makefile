# Optional alternative to the resume-md CLI. Same pipeline, no Python.
#
# Requires:
#   - pandoc      (https://pandoc.org)
#   - weasyprint  (https://weasyprint.org)
#
# Usage:
#   make            # Build index.html + resume.pdf with the default theme.
#   make THEME=classic
#   make clean

THEME ?= warm-ink
SOURCE := resume.md
HTML := index.html
PDF := resume.pdf
CSS := .build/style.css

.PHONY: all generate clean

all: generate

generate: $(HTML) $(PDF)

$(CSS): themes/_base.css themes/$(THEME).css
	@mkdir -p .build
	cat themes/$(THEME).css themes/_base.css > $(CSS)

$(HTML): $(SOURCE) $(CSS)
	pandoc $(SOURCE) \
		--standalone \
		--css $(CSS) \
		--embed-resources \
		-o $(HTML)

$(PDF): $(HTML)
	weasyprint $(HTML) $(PDF)

clean:
	rm -rf .build $(HTML) $(PDF)
