-- Pandoc filter for the notes/ directory.
-- Compatibility shim: older notes wrapped TeX math in inline-code backticks.
-- Notes now use plain $...$ / $$...$$, so the first rule is normally a no-op.
-- The second rule points links between notes at the rendered .html pages.

function Code(el)
  local s = el.text
  if #s > 4 and s:sub(1, 2) == '$$' and s:sub(-2) == '$$' then
    return pandoc.Math('DisplayMath', s:sub(3, -3))
  end
  if #s > 2 and s:sub(1, 1) == '$' and s:sub(-1) == '$' then
    return pandoc.Math('InlineMath', s:sub(2, -2))
  end
  return nil
end

function Link(el)
  local t = el.target
  if not t:match('^%a[%w+.-]*://') and not t:match('^mailto:') then
    t = t:gsub('%.md#', '.html#', 1)
    t = t:gsub('%.md$', '.html')
    el.target = t
  end
  return el
end
