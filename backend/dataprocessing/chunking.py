import re


def chunk_text(
    text,
    max_chars=1200,
    overlap_chars=200
):
    # =========================================================
    # 1. Normalize line endings
    # =========================================================
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove excessive spaces but PRESERVE newlines
    lines = [line.strip() for line in text.split("\n")]

    # =========================================================
    # 2. Build natural blocks
    # =========================================================
    blocks = []
    current_block = []

    def flush_block():
        if current_block:
            block = "\n".join(current_block).strip()

            if block:
                blocks.append(block)

            current_block.clear()

    for line in lines:

        # Blank line = natural paragraph boundary
        if not line:
            flush_block()
            continue

        # Detect bullet / numbered item
        is_bullet = bool(
            re.match(
                r"^(\-|\*|•|\d+[\.\)]|[a-zA-Z][\.\)])\s+",
                line
            )
        )

        if is_bullet:
            # Keep consecutive bullets together
            current_block.append(line)

        else:
            # If previous block contains bullets,
            # finish that list before starting normal text.
            if current_block and any(
                re.match(
                    r"^(\-|\*|•|\d+[\.\)]|[a-zA-Z][\.\)])\s+",
                    x
                )
                for x in current_block
            ):
                flush_block()

            current_block.append(line)

    flush_block()

    # =========================================================
    # 3. Convert blocks into manageable pieces
    # =========================================================
    #
    # We preserve your existing behavior:
    #
    #   - Small blocks remain intact
    #   - Blocks are merged until max_chars
    #   - Oversized blocks are split by sentences
    #
    # The only difference is that oversized blocks are converted
    # into sentence-level pieces first.
    # =========================================================

    pieces = []

    for block in blocks:

        if len(block) <= max_chars:
            pieces.append(block)
            continue

        # -----------------------------------------------------
        # Oversized block
        # -----------------------------------------------------

        # Split by sentences
        sentences = re.split(
            r"(?<=[.!?])\s+",block
        )

        current_piece = ""

        for sentence in sentences:
            sentence = sentence.strip()

            if not sentence:
                continue

            candidate = (
                sentence
                if not current_piece
                else current_piece + " " + sentence
            )

            if len(candidate) <= max_chars:
                current_piece = candidate

            else:
                if current_piece:
                    pieces.append(current_piece)

                # -------------------------------------------------
                # A single sentence itself is larger than max_chars
                # -------------------------------------------------
                if len(sentence) > max_chars:

                    # Hard split as a final fallback
                    start = 0

                    while start < len(sentence):
                        end = start + max_chars
                        pieces.append(sentence[start:end].strip())
                        start = end

                    current_piece = ""

                else:
                    current_piece = sentence

        if current_piece:
            pieces.append(current_piece)

    # =========================================================
    # 4. Merge pieces into final chunks
    # =========================================================
    #
    # This preserves the original "merge small blocks" behavior.
    # =========================================================

    chunks = []
    current_chunk = ""

    for piece in pieces:

        candidate = (
            piece
            if not current_chunk
            else current_chunk + "\n\n" + piece
        )

        if len(candidate) <= max_chars:
            current_chunk = candidate

        else:
            if current_chunk:
                chunks.append(current_chunk)

            current_chunk = piece

    if current_chunk:
        chunks.append(current_chunk)

    # =========================================================
    # 5. Add sentence-aware overlap
    # =========================================================
    #
    # Instead of blindly taking the last N characters, we take
    # complete sentences from the previous chunk.
    #
    # Example:
    #
    # Chunk 1:
    # "Sentence A. Sentence B. Sentence C."
    #
    # Chunk 2:
    # "Sentence C. Sentence D. Sentence E."
    #
    # This prevents overlap from starting in the middle of a
    # sentence.
    # =========================================================

    if overlap_chars <= 0 or len(chunks) <= 1:
        return chunks

    final_chunks = [chunks[0]]

    for i in range(1, len(chunks)):

        previous_chunk = chunks[i - 1]
        current_chunk = chunks[i]

        # -----------------------------------------------------
        # Extract complete sentences from previous chunk
        # -----------------------------------------------------

        previous_sentences = re.split(
            r"(?<=[.!?])\s+",
            previous_chunk
        )

        previous_sentences = [
            s.strip()
            for s in previous_sentences
            if s.strip()
        ]

        # -----------------------------------------------------
        # Build overlap from the END of previous chunk
        # -----------------------------------------------------

        overlap_sentences = []
        overlap_length = 0

        for sentence in reversed(previous_sentences):

            additional_length = (
                len(sentence)
                if not overlap_sentences
                else len(sentence) + 1
            )

            # Don't add more than requested overlap
            if (
                overlap_sentences
                and overlap_length + additional_length > overlap_chars
            ):
                break

            overlap_sentences.insert(0, sentence)
            overlap_length += additional_length

        overlap = " ".join(overlap_sentences)

        # -----------------------------------------------------
        # If there was no sentence boundary, use a safe
        # character-based fallback.
        # -----------------------------------------------------

        if not overlap:
            overlap = previous_chunk[-overlap_chars:].strip()

        # -----------------------------------------------------
        # Combine overlap + current chunk
        # -----------------------------------------------------

        candidate = (
            overlap + "\n\n" + current_chunk
            if overlap
            else current_chunk
        )

        # -----------------------------------------------------
        # Safety: never exceed max_chars
        # -----------------------------------------------------

        if len(candidate) > max_chars:

            # Current chunk should already be <= max_chars.
            # Therefore reduce the overlap until it fits.

            available_overlap = (
                max_chars - len(current_chunk) - 2
            )

            if available_overlap > 0:

                overlap = overlap[-available_overlap:].strip()

                # Try to avoid starting in the middle of a word
                if " " in overlap:
                    overlap = overlap[
                        overlap.find(" ") + 1:
                    ]

                candidate = (
                    overlap + "\n\n" + current_chunk
                )

            else:
                candidate = current_chunk

        final_chunks.append(candidate)
    print("Total chunks:", final_chunks)

    return final_chunks