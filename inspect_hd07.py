import sys
from pypdf import PdfReader

sys.stdout.reconfigure(encoding='utf-8')

pdf_path = 'references/Danh mục vị trí việc làm/huongdan07xaydungvitrivieclam-1793507710542668978313.pdf'
reader = PdfReader(pdf_path)
print(f"Tổng số trang: {len(reader.pages)}")

# In trang 1, 2, 3 và mục lục / tiêu đề
for i in range(min(5, len(reader.pages))):
    print(f"\n==================== TRANG {i+1} ====================")
    print(reader.pages[i].extract_text()[:2000])

