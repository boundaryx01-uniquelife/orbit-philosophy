function BlockQuote(block)
  local content = pandoc.utils.stringify(block)
  if content:match("^Version:") and content:match("Status:") and content:match("Sources:") then
    return {}
  end
end
