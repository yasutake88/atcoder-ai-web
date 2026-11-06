import pymupdf

def pdf_bytes(text):
    width, height = pymupdf.paper_size("a4")
    margin, font_size, line_height = 36, 10, 15
    font = pymupdf.Font("japan")

    with pymupdf.open() as document:
        page = None
        y = height
        for line in text.expandtabs(8).split("\n"):
            start = 0
            used = 0
            breaks = []
            for index, advance in enumerate(font.char_lengths(line, fontsize=font_size)):
                if used + advance > width - 2 * margin:
                    breaks.append(index)
                    used = 0
                used += advance
            for end in [*breaks, len(line)]:
                if y > height - margin:
                    page = document.new_page(width=width, height=height)
                    page.insert_font(fontname="JPFont", fontbuffer=font.buffer)
                    y = margin + font_size
                if end > start:
                    page.insert_text((margin, y), line[start:end], fontname="JPFont",
                                     fontsize=font_size)
                y += line_height
                start = end
        document.subset_fonts()
        return document.tobytes(deflate=True)
