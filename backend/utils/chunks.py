def make_chunk(text, page_num, source_doc, chunk_type):
    """Standard shape of a parsed document chunk stored in the vector store."""
    return {
        "text": text,
        "page_num": page_num,
        "source_doc": source_doc,
        "type": chunk_type
    }


def format_chunks(chunks, header="[Source: {source}, Page: {page}]", separator="\n\n"):
    """Renders chunks as traceable, source-annotated LLM context."""
    blocks = []
    for chunk in chunks:
        source = chunk.get("source_doc", "Unknown")
        page = chunk.get("page_num", "Unknown")
        blocks.append(f"{header.format(source=source, page=page)}\n{chunk.get('text', '')}")
    return separator.join(blocks)
