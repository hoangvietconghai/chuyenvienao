import os
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import win32com.client

doc_path = os.path.abspath(r"van_ban_den\2026\12. TB KẾT LUẬN KIỂM TRA PCTNLPTC ĐỐI VỚI CB THÔN SUỐI GIẾNG.doc")
docx_path = os.path.abspath(r"van_ban_den\2026\12_TB_KET_LUAN_KIEM_TRA_PCTNLPTC_DOI_VOI_CB_THON_SUOI_GIENG.docx")
txt_path = os.path.abspath(r"van_ban_den\2026\extracted_content.txt")

print(f"Opening: {doc_path}")
word = win32com.client.Dispatch("Word.Application")
word.Visible = False

try:
    doc = word.Documents.Open(doc_path)
    text = doc.Content.Text
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Extracted text written to: {txt_path}")
    print(f"Text length: {len(text)}")
    
    # Save as docx
    doc.SaveAs2(docx_path, FileFormat=16) # 16 = wdFormatXMLDocument
    print(f"Converted to docx: {docx_path}")
    doc.Close()
except Exception as e:
    print(f"Error: {e}")
finally:
    word.Quit()
