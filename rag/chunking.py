import re
from typing import List, Dict, Any

def chunk_markdown_document(
    content: str, 
    file_name: str, 
    max_chunk_size: int = 800
) -> List[Dict[str, Any]]:
    """
    Semantic Markdown Chunker:
    Splits policy documents by logical section headers (## / ###) so that each policy rule
    (e.g., Fare Class Rules, 24-Hour Cooling Off, Cabin Baggage, Schedule Changes) remains
    a complete, coherent semantic unit without fragmented sentences.
    """
    category = file_name.replace("_policy.md", "").replace(".md", "").upper()

    # Extract main document title
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    main_title = title_match.group(1).strip() if title_match else file_name.replace("_", " ").title()

    # Split by markdown section headers (## or ###)
    raw_sections = re.split(r'\n(?=##+\s+)', content)
    
    chunks = []
    chunk_idx = 0

    for sec in raw_sections:
        sec = sec.strip()
        if not sec:
            continue

        # Extract section header
        sec_header_match = re.search(r'^##+\s+(.+)$', sec, re.MULTILINE)
        section_title = sec_header_match.group(1).strip() if sec_header_match else "General Policy Terms"

        # If section is small/medium (<= max_chunk_size), keep it whole
        if len(sec) <= max_chunk_size:
            formatted_text = f"[{main_title} > {section_title}]\n{sec}"
            chunks.append({
                "id": f"{file_name}_sec_{chunk_idx}",
                "text": formatted_text,
                "metadata": {
                    "file_name": file_name,
                    "category": category,
                    "main_title": main_title,
                    "section_title": section_title,
                    "chunk_index": chunk_idx
                }
            })
            chunk_idx += 1
        else:
            # For unusually large sections, split by paragraph boundaries cleanly
            paras = [p.strip() for p in re.split(r'\n\s*\n', sec) if p.strip()]
            current_block = ""
            for p in paras:
                if len(current_block) + len(p) + 2 <= max_chunk_size:
                    current_block = (current_block + "\n\n" + p) if current_block else p
                else:
                    if current_block:
                        chunks.append({
                            "id": f"{file_name}_sec_{chunk_idx}",
                            "text": f"[{main_title} > {section_title}]\n{current_block}",
                            "metadata": {
                                "file_name": file_name,
                                "category": category,
                                "main_title": main_title,
                                "section_title": section_title,
                                "chunk_index": chunk_idx
                            }
                        })
                        chunk_idx += 1
                    current_block = p
            if current_block:
                chunks.append({
                    "id": f"{file_name}_sec_{chunk_idx}",
                    "text": f"[{main_title} > {section_title}]\n{current_block}",
                    "metadata": {
                        "file_name": file_name,
                        "category": category,
                        "main_title": main_title,
                        "section_title": section_title,
                        "chunk_index": chunk_idx
                    }
                })
                chunk_idx += 1

    return chunks
