"""Helper one-shot para extrair texto do PDF atualizado da CEFIS."""
import io
import sys

from pypdf import PdfReader

# forca UTF-8 no stdout (Windows usa cp1252 por default)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

path = sys.argv[1] if len(sys.argv) > 1 else r"D:\Projects\CEFIS\Docs\CEFIS_Hackathon_Docs_Dev_atualizado.pdf"
r = PdfReader(path)
print(f"Total pages: {len(r.pages)}")
for i, p in enumerate(r.pages, 1):
    print(f"\n========== PAGE {i} ==========")
    print(p.extract_text())
