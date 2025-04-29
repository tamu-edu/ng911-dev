from fpdf import FPDF


class PDFService(FPDF):
    def __init__(self):
        super().__init__()
        self.set_font("Helvetica", "", 11)

    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "Conformance Test Report", ln=True, align="C")
        self.ln(10)

    def chapter_title(self, title):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, title, ln=True)
        self.ln(2)

    def requirement_title(self, title):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(0, 51, 102)
        self.cell(0, 8, title, ln=True)
        self.set_text_color(0, 0, 0)

    def variation_title(self, title):
        self.set_font("Helvetica", "I", 11)
        self.set_text_color(60, 60, 60)
        self.cell(0, 8, title, ln=True)
        self.set_text_color(0, 0, 0)

    def add_table_header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_fill_color(200, 200, 200)
        self.cell(130, 8, "Check", border=1, fill=True)
        self.cell(40, 8, "Verdict", border=1, fill=True, ln=True)

    def add_table_row(self, check, verdict):
        self.set_font("Helvetica", "", 10)
        self.cell(130, 8, self.sanitize_text(str(check)), border=1)
        self.cell(40, 8, self.sanitize_text(str(verdict)), border=1, ln=True)

    def add_line(self):
        self.ln(4)

    def _wrap_long_words(self, text, max_len=40):
        """
        Insert zero-width space into long words to allow wrapping.
        """
        import re
        return re.sub(r'(\S{' + str(max_len) + r',})', lambda m: '\u200b'.join(m.group(1)), text)

    def sanitize_text(self, text):
        if not text:
            return ""

        replacements = {
            "\u201c": '"', "\u201d": '"',
            "\u2018": "'", "\u2019": "'",
            "\u2013": "-", "\u2014": "-",
            "\xa0": " ",  # non-breaking space
        }
        for bad, good in replacements.items():
            text = text.replace(bad, good)

        # Latin-1 cleanup
        text = ''.join([c if ord(c) < 256 else '?' for c in text])

        return text

    def safe_multi_cell(self, w, h, text, border=0, align="L", fill=False):
        try:
            sanitized = self.sanitize_text(text)

            # ✅ Proper width respecting margins
            if w == 0 or w > self.w - self.l_margin - self.r_margin:
                w = self.w - self.l_margin - self.r_margin

            self.multi_cell(w, h, sanitized, border=border, align=align, fill=fill)

        except Exception as e:
            print(f"⚠️ safe_multi_cell failed on: {text[:40]} → {e}")
            self.multi_cell(100, h, "[Rendering Error]", border=border, align=align, fill=fill)

    def split_text_to_width(self, text, max_width):
        """
        Split a string into lines that fit within max_width (in points)
        """
        words = text.split(' ')
        lines = []
        current_line = ''

        for word in words:
            if self.get_string_width(current_line + ' ' + word) <= max_width:
                current_line += (' ' if current_line else '') + word
            else:
                if not current_line:
                    # The word itself is too long, force-split it
                    for i in range(0, len(word), 40):
                        lines.append(word[i:i + 40])
                else:
                    lines.append(current_line)
                    current_line = word
        if current_line:
            lines.append(current_line)
        return lines