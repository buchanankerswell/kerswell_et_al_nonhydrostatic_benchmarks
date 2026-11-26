-- Pandoc filter for notes that wrap TeX math in inline-code backticks.
-- Usage: pandoc --lua-filter=notes/pandoc-math-in-code.lua --math-method=mathml ...

function Code(el)
  local s = el.text
  if #s > 4 and s:sub(1, 2) == '$$' and s:sub(-2) == '$$' then
    return pandoc.Math('DisplayMath', s:sub(3, -3))
  end
  if #s > 2 and s:sub(1, 1) == '$' and s:sub(-1) == '$' then
    return pandoc.Math('InlineMath', s:sub(2, -2))
  end
  -- A few expressions are written as code with no dollar delimiters.
  if s:find('\\%a') and not s:find('%$') then
    return pandoc.Math('InlineMath', s)
  end
  return nil
end
