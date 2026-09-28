function BlockQuote(block)
  local content = pandoc.utils.stringify(block)
  if content:match("Version:%s*SAMPLE MVP") and content:match("Status:%s*READER TEST READY") then
    return {}
  end
end

