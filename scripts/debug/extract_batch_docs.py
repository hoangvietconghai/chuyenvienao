import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import win32com.client
import docx

files = [
    r"van_ban_den\2026\12. TB KẾT LUẬN KIỂM TRA PCTNLPTC ĐỐI VỚI CB THÔN SUỐI GIẾNG.doc",
    r"van_ban_den\2026\13. TB KẾT LUẬN KIỂM TRA PCTNLPTC ĐỐI VỚI CB MẪU GIÁO CH.doc",
    r"van_ban_den\2026\14. TB KẾT LUẬN KIỂM TRA PCTNLPTC ĐỐI VỚI CB CÔNG AN XÃ.doc"
]

word = win32com.client.Dispatch("Word.Application")
word.Visible = False

try:
    for f in files:
        abs_path = os.path.abspath(f)
        txt_path = abs_path.replace(".doc", ".txt")
        docx_path = abs_path.replace(".doc", ".docx")
        
        print(f"Opening: {abs_path}")
        doc = word.Documents.Open(abs_path)
        text = doc.Content.Text
        
        with open(txt_path, "w", encoding="utf-8") as out:
            out.write(text)
        print(f"  -> Extracted text to: {txt_path} ({len(text)} chars)")
        
        doc.SaveAs2(docx_path, FileFormat=16) # 16 = wdFormatXMLDocument
        print(f"  -> Converted to docx: {docx_path}")
        doc.Close()
except Exception as e:
    print(f"Error: {e}")
finally:
    word.Quit()
