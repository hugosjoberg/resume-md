-- split-date.lua
--
-- Split level-3 headings on a dash separator into a heading whose right
-- portion is wrapped in <span class="period">. The existing CSS flexbox
-- right-aligns that span — giving the design's "right-margin timeline"
-- look without forcing the user to write Pandoc's attribute syntax
-- (`[…]{.period}`) in their Markdown.
--
-- Accepted separators (any of these work — Pandoc's smart-punctuation
-- handles the typing):
--   `### Company — Date`   (em-dash, U+2014)
--   `### Company – Date`   (en-dash, U+2013 — what Pandoc emits from `--`)
--   `### Company -- Date`  (double hyphen — Pandoc converts to en-dash)
--   `### Company --- Date` (triple hyphen — Pandoc converts to em-dash)
--
-- Lua's lazy quantifier `(.-)` matches at the FIRST occurrence, so an
-- en-dash later in the date range (e.g. "Jan 2022 – Present") doesn't
-- cause a wrong split.
--
-- Headings without one of these separators are returned unchanged, so
-- `### Education`, `### Tinydash` (side projects), etc. still work.

function Header(el)
  if el.level ~= 3 then return nil end
  local text = pandoc.utils.stringify(el.content)
  -- Lua patterns are byte-oriented, so [—–] as a character class would
  -- match individual UTF-8 bytes (broken). Try each separator in turn.
  local left, right = text:match("^(.-)%s—%s(.+)$")
  if not left then
    left, right = text:match("^(.-)%s–%s(.+)$")
  end
  if not left then return nil end
  return pandoc.Header(3, {
    pandoc.Str(left),
    pandoc.Space(),
    pandoc.Span(
      { pandoc.Str(right) },
      pandoc.Attr("", { "period" }, {})
    )
  }, el.attr)
end
