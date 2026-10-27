-- Keep the document language while formatting citations and references in English.
-- Opt-in pages disable automatic citeproc so citations are processed only once.
function Pandoc(doc)
  local document_language = doc.meta.lang
  doc.meta.lang = pandoc.MetaString("en-US")
  doc = pandoc.utils.citeproc(doc)
  doc.meta.lang = document_language
  return doc
end
