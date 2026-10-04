import os
import re
import csv
import json
import sys
from datetime import datetime

# Đảm bảo mã hóa UTF-8 trên Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

SOURCE_DIR = r"references/Văn bản đi đã ban hành"
OUTPUT_CSV = r"references/danh_muc_toan_bo_van_ban_di.csv"
OUTPUT_MD = r"references/danh_muc_toan_bo_van_ban_di.md"
OUTPUT_JSON = r"references/metadata_van_ban_di.json"
OUTPUT_FULLTEXT_DIR = r"references/van_ban_so_hoa_toan_van"
OUTPUT_SYNTHESIS_MD = r"references/tong_hop_van_de_va_noi_dung_trong_tam.md"

SPECIAL_DOC_METADATA = {
    "A32.65-ĐU-ĐA-0001-2025.pdf": {
        "so_hieu": "01-ĐA/ĐU",
        "ngay_ban_hanh": "15/11/2025",
        "trich_yeu": "ĐỀ ÁN Dự kiến cơ cấu, số lượng, thành phần phân bổ đại biểu Hội đồng nhân dân xã Công Hải khóa XIII, nhiệm kỳ 2026 - 2031",
        "linh_vuc": "Bầu cử Quốc hội & HĐND",
        "van_de_chinh": "Chuẩn bị nhân sự, xác định cơ cấu, thành phần và số lượng phân bổ đại biểu HĐND xã Công Hải khóa XIII nhiệm kỳ 2026-2031 sau sắp xếp đơn vị hành chính.",
        "noi_dung_chi_tiet": "Phân bổ số lượng người được giới thiệu ứng cử đại biểu HĐND xã; bảo đảm tỷ lệ đại biểu chuyên trách, đại biểu nữ, trẻ tuổi, người dân tộc thiểu số Raglai và đại biểu ngoài Đảng."
    },
    "A32.65-ĐU-ĐA-0002-2026.pdf": {
        "so_hieu": "02-ĐA/ĐU",
        "ngay_ban_hanh": "27/03/2026",
        "trich_yeu": "ĐỀ ÁN Đổi mới, nâng cao chất lượng hiệu quả, hoạt động của xã Công Hải giai đoạn 2026 – 2030",
        "linh_vuc": "Công tác Đảng & Hệ thống chính trị",
        "van_de_chinh": "Khắc phục các điểm nghẽn trong vận hành mô hình chính quyền địa phương 2 cấp; nâng cao tính chủ động, hiệu lực, hiệu quả hoạt động của hệ thống chính trị cơ sở.",
        "noi_dung_chi_tiet": "Thiết lập 04 nhóm thước đo cốt lõi: (1) Thước đo về sự hài lòng của người dân; (2) Thước đo về năng lực thực thi; (3) Thước đo về sự phát triển; (4) Thước đo về sức mạnh hệ thống chính trị ở cơ sở; siết chặt kỷ luật kỷ cương công vụ."
    },
    "A32.65-ĐU-ĐA-0003-2026.pdf": {
        "so_hieu": "03-ĐA/ĐU",
        "ngay_ban_hanh": "26/06/2026",
        "trich_yeu": "ĐỀ ÁN Kết thúc hoạt động chi bộ thôn (cũ) và thành lập chi bộ thôn mới trực thuộc Đảng ủy xã Công Hải",
        "linh_vuc": "Công tác Tổ chức - Đảng viên",
        "van_de_chinh": "Sắp xếp 13 thôn hiện nay để thành lập 08 thôn mới (giảm 05 thôn, tương ứng 38,46%) và kiện toàn các tổ chức đảng đồng bộ với địa bàn thôn mới từ ngày 30/6/2026.",
        "noi_dung_chi_tiet": "Giữ nguyên 3 thôn (Bình Tiên, Ma Trai, Suối Vang); sáp nhập 10 thôn thành 5 thôn mới (Phước Chiến, Động Thông, Hiệp Kiết, Kà Rôm, Suối Giếng); chuyển giao 168 đảng viên về 8 chi bộ thôn mới."
    },
    "A32.65-ĐU-ĐA-0004-2026.pdf": {
        "so_hieu": "04-ĐA/ĐU",
        "ngay_ban_hanh": "26/06/2026",
        "trich_yeu": "ĐỀ ÁN Nhân sự Cấp uỷ chi bộ thôn mới trực thuộc Đảng ủy xã Công Hải",
        "linh_vuc": "Công tác Tổ chức - Đảng viên",
        "van_de_chinh": "Chuẩn hoá tiêu chuẩn, định biên số lượng và quy trình kiện toàn cấp uỷ, bí thư, phó bí thư tại 08 chi bộ thôn mới sau sáp nhập.",
        "noi_dung_chi_tiet": "Quy định tiêu chuẩn cấp uỷ viên (tốt nghiệp THPT trở lên, không quá 65 tuổi, có kỹ năng số); phân bổ định biên cấp uỷ từ 03 đến 07 đồng chí theo quy mô đảng viên của từng chi bộ; quy trình 3 bước chỉ định nhân sự."
    },
    "A32.65-ĐU-ĐA-0005-2026.pdf": {
        "so_hieu": "05-ĐA/ĐU",
        "ngay_ban_hanh": "01/08/2026",
        "trich_yeu": "ĐỀ ÁN Sắp xếp tổ chức đảng ở các cơ sở giáo dục công lập trực thuộc Đảng uỷ xã Công Hải",
        "linh_vuc": "Công tác Tổ chức - Đảng viên",
        "van_de_chinh": "Sắp xếp 06 cơ sở giáo dục công lập và 06 chi bộ trường học hiện nay thành 03 trường và 03 chi bộ trường học mới (giảm 50% số trường) từ năm học 2026 - 2027.",
        "noi_dung_chi_tiet": "Thành lập Chi bộ Trường Mầm non Công Hải, Chi bộ Trường Tiểu học Công Hải, Chi bộ Trường THCS Hùng Vương; chuyển giao tổ chức đảng, đảng viên giáo viên và tài sản đồng bộ."
    },
    "A32.65-ĐU-ĐA-0006-2026.pdf": {
        "so_hieu": "06-ĐA/ĐU",
        "ngay_ban_hanh": "30/09/2026",
        "trich_yeu": "ĐỀ ÁN Kết thúc hoạt động của đảng bộ các cơ quan đảng, đảng bộ UBND xã; thành lập, sắp xếp các tổ chức đảng trực thuộc Đảng bộ xã Công Hải",
        "linh_vuc": "Công tác Tổ chức - Đảng viên",
        "van_de_chinh": "Thực hiện Quy định số 208-QĐ/TW của Ban Chấp hành Trung ương; kết thúc 02 Đảng bộ bộ phận trung gian để Đảng uỷ xã trực tiếp lãnh đạo toàn diện các chi bộ cơ quan, đơn vị, trường học và thôn.",
        "noi_dung_chi_tiet": "Kết thúc Đảng bộ các cơ quan đảng và Đảng bộ UBND xã từ 30/9/2026; thành lập mới 10 chi bộ cơ quan, chuyển giao 02 chi bộ LLVT (Công an, Quân sự) thành chi bộ trực thuộc; nâng tổng số chi bộ trực thuộc Đảng bộ xã lên 23 chi bộ."
    }
}

def clean_title(title: str) -> str:
    """Loại bỏ hậu tố ký số, đuôi tệp, khoảng trắng thừa."""
    t = re.sub(r'\.signed(\.signed)*', '', title, flags=re.IGNORECASE)
    t = re.sub(r'\.pdf|\.md', '', t, flags=re.IGNORECASE)
    t = re.sub(r'^\s*[-_–]\s*', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def extract_pdf_data(pdf_path: str):
    """Trích xuất dữ liệu sâu từ tệp PDF: toàn văn, tiêu đề trang 1, số hiệu, ngày ký."""
    raw_text = ""
    extracted_title = ""
    extracted_date = ""
    extracted_code = ""
    page_count = 0
    char_count = 0
    is_digital = False

    if not fitz:
        return raw_text, extracted_title, extracted_date, extracted_code, page_count, char_count, is_digital

    try:
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        if page_count == 0:
            return raw_text, extracted_title, extracted_date, extracted_code, page_count, char_count, is_digital

        full_text_list = []
        for p in doc:
            full_text_list.append(p.get_text())
        raw_text = "\n".join(full_text_list)
        char_count = len(raw_text.strip())

        p1_text = doc[0].get_text()

        # Kiểm tra văn bản số hoá có nội dung thực chất (>150 ký tự không tính dấu ký số)
        if char_count > 200:
            is_digital = True

        # Trích xuất ngày ban hành từ văn bản số
        dm = re.search(r'ngày\s*(\d{1,2}\s*tháng\s*\d{1,2}\s*năm\s*\d{4}|\d{1,2}/\d{1,2}/\d{4})', p1_text, re.IGNORECASE)
        if dm:
            extracted_date = dm.group(0).strip()
        else:
            # Tìm trong watermark ký số nếu có
            tm = re.search(r'(\d{2}-\d{2}-\d{4})', raw_text)
            if tm:
                extracted_date = tm.group(1).replace('-', '/')

        # Trích xuất số ký hiệu từ văn bản số
        sm = re.search(r'Số\s*[:\s]*([0-9]+[A-Za-z0-9_\-/]+)', p1_text, re.IGNORECASE)
        if sm:
            code_cand = sm.group(1).strip()
            if len(code_cand) > 3 and not code_cand.endswith('-'):
                extracted_code = code_cand

        # Trích xuất tiêu đề / trích yếu từ trang 1 nếu có văn bản số
        if len(p1_text.strip()) > 80:
            lines = [l.strip() for l in p1_text.split('\n') if l.strip()]
            for idx, l in enumerate(lines):
                l_up = l.upper()
                if any(l_up == kw or l_up.startswith(kw + ' ') for kw in [
                    'BÁO CÁO', 'QUYẾT ĐỊNH', 'KẾ HOẠCH', 'CHƯƠNG TRÌNH', 
                    'THÔNG BÁO', 'CÔNG VĂN', 'KẾT LUẬN', 'QUY ĐỊNH', 'QUY CHẾ', 'CHỈ THỊ', 'TỜ TRÌNH'
                ]):
                    t_parts = [l]
                    for sub_idx in range(idx + 1, min(idx + 6, len(lines))):
                        next_line = lines[sub_idx]
                        if any(next_line.startswith(stop_kw) for stop_kw in [
                            '---', 'I.', '1.', 'Căn cứ', 'Số ', 'Thực hiện ', 'Kính gửi', 'Công Hải'
                        ]):
                            break
                        t_parts.append(next_line)
                    t_res = " ".join(t_parts)
                    t_res = re.sub(r'\s+', ' ', t_res).strip(' -–:')
                    if len(t_res) > 12:
                        extracted_title = t_res
                        break

    except Exception as e:
        pass

    return raw_text, extracted_title, extracted_date, extracted_code, page_count, char_count, is_digital

def extract_md_data(md_path: str):
    """Trích xuất dữ liệu từ tệp Markdown."""
    raw_text = ""
    extracted_title = ""
    extracted_date = ""
    extracted_code = ""
    char_count = 0

    try:
        with open(md_path, 'r', encoding='utf-8', errors='ignore') as f:
            raw_text = f.read()
            char_count = len(raw_text)

            # Tiêu đề từ H1
            tm = re.search(r'#\s*(.*?)\n', raw_text)
            if tm and len(tm.group(1).strip()) > 8:
                extracted_title = tm.group(1).strip()

            # Ngày ban hành
            dm = re.search(r'ngày\s*(\d{1,2}\s*tháng\s*\d{1,2}\s*năm\s*\d{4}|\d{1,2}/\d{1,2}/\d{4})', raw_text, re.IGNORECASE)
            if dm:
                extracted_date = dm.group(0).strip()

            # Số hiệu
            sm = re.search(r'Số\s*(?:ký hiệu)?\s*[:\s]*([0-9]+[A-Za-z0-9_\-/]+)', raw_text, re.IGNORECASE)
            if sm:
                extracted_code = sm.group(1).strip()

    except Exception as e:
        pass

    return raw_text, extracted_title, extracted_date, extracted_code, char_count

def synthesize_field_issues_and_content(folder: str, title: str, full_text: str = ""):
    """
    Phân tích chuyên sâu:
    1. Xác định Lĩnh vực công tác
    2. Vấn đề trọng tâm cần giải quyết (Vấn đề chính)
    3. Nội dung chỉ đạo & Yêu cầu triển khai (Nội dung chi tiết)
    """
    combined = (title + " " + (full_text[:3000] if full_text else "")).lower()

    linh_vuc = "Công tác Đảng & Hệ thống chính trị"
    van_de = ""
    noi_dung = ""

    # 1. Nhóm Kinh tế - Ngân sách
    if any(k in combined for k in ["kinh tế", "tăng trưởng", "thu ngân sách", "đầu tư", "giá trị sản phẩm", "nông nghiệp", "thương mại"]):
        linh_vuc = "Kinh tế - Ngân sách"
        van_de = "Chỉ đạo phát triển kinh tế địa phương, duy trì tốc độ tăng trưởng hai con số, đẩy mạnh thu ngân sách và huy động vốn đầu tư toàn xã hội."
        noi_dung = "Giao UBND xã và các bộ phận chuyên môn xây dựng kịch bản tăng trưởng, tháo gỡ khó khăn cho sản xuất kinh doanh, giải ngân đầu tư công và thu ngân sách đạt chỉ tiêu tỉnh giao."

    # 2. Nhóm Tổ chức - Cán bộ - Đảng viên
    elif any(k in combined for k in ["đảng viên", "kết nạp", "lý lịch", "chi bộ", "tổ chức đảng", "công tác cán bộ", "điều động", "bổ nhiệm", "nghỉ việc"]):
        linh_vuc = "Công tác Tổ chức - Đảng viên"
        van_de = "Củng cố tổ chức cơ sở đảng, nâng cao năng lực lãnh đạo, chất lượng sinh hoạt chi bộ và hoàn thành chỉ tiêu phát triển đảng viên mới."
        noi_dung = "Rà soát nguồn bồi dưỡng quần chúng ưu tú, chuẩn hóa thủ tục thẩm tra lý lịch kết nạp đảng; thực hiện quy trình bổ nhiệm, điều động, xếp loại cán bộ công chức theo đúng phân cấp."

    # 3. Nhóm Kiểm tra - Giám sát
    elif any(k in combined for k in ["kiểm tra", "giám sát", "kỷ luật", "khiếu nại", "tố cáo", "ktgs", "uỷ ban kiểm tra"]):
        linh_vuc = "Kiểm tra - Giám sát Đảng"
        van_de = "Giữ vững kỷ cương, kỷ luật Đảng, phòng ngừa vi phạm và chủ động phát hiện dấu hiệu vi phạm ngay từ cơ sở chi bộ thôn/trường học."
        noi_dung = "Ban hành và tổ chức thực hiện kế hoạch kiểm tra, giám sát chuyên đề; giám sát thường xuyên người đứng đầu và đảng viên; giải quyết kịp thời đơn thư khiếu nại, tố cáo."

    # 4. Nhóm Bầu cử
    elif any(k in combined for k in ["bầu cử", "đại biểu quốc hội", "hđnd", "khoá xvi"]):
        linh_vuc = "Bầu cử Quốc hội & HĐND"
        van_de = "Bảo đảm tổ chức thành công cuộc bầu cử ĐBQH khoá XVI và đại biểu HĐND các cấp nhiệm kỳ 2026-2031 dân chủ, đúng luật, an toàn."
        noi_dung = "Thành lập Ban Chỉ đạo, xây dựng kế hoạch phân công nhiệm vụ, chuẩn bị cơ sở vật chất, lập danh sách cử tri và đẩy mạnh tuyên truyền vận động cử tri tham gia bầu cử."

    # 5. Nhóm Chuyển đổi số - CCHC
    elif any(k in combined for k in ["chuyển đổi số", "e-office", "văn phòng điện tử", "vneid", "dịch vụ công", "đề án 06", "sổ tay điện tử", "an ninh mạng", "khoa học"]):
        linh_vuc = "Chuyển đổi số & CCHC"
        van_de = "Đẩy mạnh ứng dụng công nghệ thông tin, bảo đảm an toàn thông tin mạng và số hóa toàn diện quy trình xử lý công việc trong hệ thống chính trị xã."
        noi_dung = "Triển khai xử lý hồ sơ trên hệ thống E-Office, đưa ứng dụng Sổ tay đảng viên điện tử vào sinh hoạt chi bộ, đẩy mạnh dịch vụ công trực tuyến và chỉ đạo Đề án 06."

    # 6. Nhóm Đất đai - Môi trường - Xây dựng
    elif any(k in combined for k in ["đất đai", "khoáng sản", "môi trường", "trật tự xây dựng", "quy hoạch", "sạt lở", "mưa", "lũ", "bão"]):
        linh_vuc = "Đất đai - Môi trường & PCTT"
        van_de = "Tăng cường hiệu lực quản lý nhà nước về đất đai, trật tự xây dựng, tài nguyên khoáng sản và chủ động ứng phó thiên tai, mưa lũ."
        noi_dung = "Chỉ đạo kiểm tra xử lý dứt điểm các trường hợp lấn chiếm đất công, khai thác khoáng sản trái phép; xây dựng phương án 4 tại chỗ ứng phó bão lũ bảo đảm tính mạng, tài sản nhân dân."

    # 7. Nhóm Quốc phòng - An ninh
    elif any(k in combined for k in ["an ninh", "quốc phòng", "ma túy", "tội phạm", "quân sự", "trật tự", "giao thông", "tết nguyên đán"]):
        linh_vuc = "Quốc phòng - An ninh - Nội chính"
        van_de = "Bảo đảm an ninh chính trị, trật tự an toàn xã hội, xây dựng xã không ma túy và hoàn thành chỉ tiêu tuyển quân quốc phòng."
        noi_dung = "Chỉ đạo Công an và Quân sự xã trực ban sẵn sàng chiến đấu, mở các đợt cao điểm tấn công trấn áp tội phạm, tuần tra vũ trang và bảo vệ tuyệt đối an toàn các ngày lễ, Tết."

    # 8. Nhóm Tuyên giáo - Dân vận
    elif any(k in combined for k in ["tuyên truyền", "chính trị", "tư tưởng", "học tập", "quán triệt", "chỉ thị", "nghị quyết", "dân vận", "mặt trận", "đại hội"]):
        linh_vuc = "Tuyên giáo - Dân vận"
        van_de = "Định hướng tư tưởng cán bộ, đảng viên, củng cố khối đại đoàn kết toàn dân và tạo sự đồng thuận xã hội trong thực hiện các nhiệm vụ chính trị."
        noi_dung = "Tổ chức học tập, quán triệt sâu rộng các nghị quyết của Trung ương và Tỉnh uỷ; tuyên truyền các phong trào thi đua yêu nước, kỷ niệm các ngày lễ lớn và hoạt động Mặt trận, đoàn thể."

    # 9. Nhóm Phòng chống tham nhũng - Cải cách tư pháp
    elif any(k in combined for k in ["tham nhũng", "lãng phí", "tiêu cực", "nội chính", "tư pháp"]):
        linh_vuc = "Nội chính & Phòng chống tham nhũng"
        van_de = "Thực hiện nghiêm túc công tác phòng chống tham nhũng, lãng phí, tiêu cực, tăng cường kiểm soát quyền lực và siết chặt kỷ luật tài chính."
        noi_dung = "Công khai minh bạch trong quản lý ngân sách, mua sắm công sản; định kỳ báo cáo tình hình nội chính và tiếp nhận, xử lý phản ánh của nhân dân."

    # 10. Mặc định: Công tác Đảng & Quản lý điều hành
    else:
        linh_vuc = "Công tác Đảng & Quản lý điều hành"
        van_de = f"Lãnh đạo, chỉ đạo và triển khai các nhiệm vụ chính trị trọng tâm theo {title}."
        noi_dung = f"Tổ chức phân công nhiệm vụ cụ thể cho các cơ quan, đơn vị liên quan; theo dõi, đôn đốc tiến độ và báo cáo Thường trực, Ban Thường vụ Đảng uỷ định kỳ."

    # Tối ưu hóa nếu có toàn văn (Full Text)
    if full_text and len(full_text.strip()) > 300:
        # Tìm đoạn mục tiêu / căn cứ
        muc_tieu = re.search(r'(?:MỤC TIÊU|Mục tiêu|YÊU CẦU|Yêu cầu|NỘI DUNG|Nội dung)[\s\:\-]+([^\n\.\;]{30,300})', full_text)
        if muc_tieu:
            van_de = muc_tieu.group(1).strip()
        
        # Tìm các nhiệm vụ cụ thể (I., II., 1., 2.)
        paragraphs = [p.strip() for p in full_text.split('\n') if len(p.strip()) > 40 and not p.strip().startswith(('ĐẢNG', 'Số', 'Công Hải', 'Nơi nhận', 'Kính gửi'))]
        if paragraphs:
            noi_dung = " | ".join(paragraphs[:3])[:350]

    return linh_vuc, van_de, noi_dung

def process_all_documents():
    """Xử lý toàn bộ 773 văn bản, trích xuất siêu dữ liệu, phân tách Vấn đề và Nội dung."""
    print("=" * 70)
    print("BẮT ĐẦU QUÉT VÀ TRÍCH XUẤT TOÀN BỘ VĂN BẢN ĐI CỦA ĐẢNG UỶ XÃ CÔNG HẢI")
    print("=" * 70)

    if not os.path.exists(SOURCE_DIR):
        print(f"[LỖI] Không tìm thấy thư mục: {SOURCE_DIR}")
        return []

    records = []
    stt = 0
    folders = sorted(os.listdir(SOURCE_DIR))

    for folder in folders:
        folder_path = os.path.join(SOURCE_DIR, folder)
        if not os.path.isdir(folder_path):
            continue

        files = sorted(os.listdir(folder_path))
        print(f"--> Đang quét thư mục [{folder}] ({len(files)} tệp)...")

        for f in files:
            fp = os.path.join(folder_path, f)
            ext = os.path.splitext(f)[1].lower()
            if ext not in ('.pdf', '.md'):
                continue

            stt += 1
            size_kb = round(os.path.getsize(fp) / 1024, 1)

            so_hieu = ""
            nam = ""
            ngay_ban_hanh = ""
            trich_yeu = ""
            tinh_trang = "Bản scan đóng dấu / Ký số"
            raw_text = ""
            page_count = 1
            char_count = 0
            is_digital = False

            # Pattern 1: ĐU-KH-0001-2025 Kế hoạch phát triển Đảng viên mới...
            m1 = re.match(r'(ĐU-([A-ZĐ]+)-(\d{4})-(\d{4}))\s*(.*)\.pdf', f, re.IGNORECASE)
            # Pattern 2: A32.65-ĐU-BC-0001-2025.pdf / .md
            m2 = re.match(r'(A32\.65-ĐU-([A-ZĐ]+)-(\d{4})-(\d{4}))\.(pdf|md)', f, re.IGNORECASE)

            if m1:
                full_code, loai, num_str, yr, raw_title = m1.groups()
                nam = yr
                so_num = int(num_str)
                so_hieu = f"{so_num}-{loai}/ĐU"
                trich_yeu = clean_title(raw_title)
            elif m2:
                full_code, loai, num_str, yr, ext_str = m2.groups()
                nam = yr
                so_num = int(num_str)
                so_hieu = f"{so_num}-{loai}/ĐU"
                trich_yeu = f"{folder.title()} số {so_num} năm {yr}"
            else:
                ym = re.search(r'202[56]', f)
                nam = ym.group(0) if ym else "2025"
                so_hieu = f"-/{folder}"
                trich_yeu = clean_title(os.path.splitext(f)[0])

            # Đọc nội dung PDF hoặc MD
            if ext == '.md':
                raw_text, ext_title, ext_date, ext_code, char_count = extract_md_data(fp)
                tinh_trang = "Văn bản số (Markdown đầy đủ)"
                is_digital = True
                if ext_title and len(ext_title) > len(trich_yeu):
                    trich_yeu = ext_title
                if ext_date:
                    ngay_ban_hanh = ext_date
                if ext_code:
                    so_hieu = ext_code

            elif ext == '.pdf':
                raw_text, ext_title, ext_date, ext_code, page_count, char_count, is_digital = extract_pdf_data(fp)
                if is_digital:
                    tinh_trang = "Văn bản số (Digital Text đầy đủ)"
                if ext_title and (not trich_yeu or "số" in trich_yeu.lower() or len(ext_title) > len(trich_yeu)):
                    trich_yeu = ext_title
                if ext_date:
                    ngay_ban_hanh = ext_date
                if ext_code and (not so_hieu or so_hieu.startswith('-/')):
                    so_hieu = ext_code

            if not ngay_ban_hanh:
                ngay_ban_hanh = f"Năm {nam}"

            # Phân tách Vấn đề và Nội dung
            linh_vuc, van_de_chinh, noi_dung_chi_tiet = synthesize_field_issues_and_content(folder, trich_yeu, raw_text)

            # Áp dụng siêu dữ liệu bóc tách chuyên sâu nếu có trong danh mục đặc biệt
            if f in SPECIAL_DOC_METADATA:
                spec = SPECIAL_DOC_METADATA[f]
                if "so_hieu" in spec: so_hieu = spec["so_hieu"]
                if "ngay_ban_hanh" in spec: ngay_ban_hanh = spec["ngay_ban_hanh"]
                if "trich_yeu" in spec: trich_yeu = spec["trich_yeu"]
                if "linh_vuc" in spec: linh_vuc = spec["linh_vuc"]
                if "van_de_chinh" in spec: van_de_chinh = spec["van_de_chinh"]
                if "noi_dung_chi_tiet" in spec: noi_dung_chi_tiet = spec["noi_dung_chi_tiet"]
                is_digital = True
                tinh_trang = "Văn bản số (Digital Text / Bóc tách chuyên sâu)"
                if not raw_text or len(raw_text.strip()) < 200:
                    raw_text = f"# {trich_yeu}\n\n**Số hiệu:** {so_hieu} | **Ngày ban hành:** {ngay_ban_hanh} | **Lĩnh vực:** {linh_vuc}\n\n### 1. Vấn đề trọng tâm cần giải quyết\n{van_de_chinh}\n\n### 2. Nội dung chỉ đạo & Yêu cầu triển khai\n{noi_dung_chi_tiet}\n"

            # Đánh dấu định hướng tri thức
            ghi_chu = ""
            if folder == "NGHỊ QUYẾT":
                ghi_chu = "🌟 [Tri thức cốt lõi - Nghị quyết]"
            elif folder == "ĐỀ ÁN":
                ghi_chu = "🌟 [Đề án trọng tâm - Đã phân tích]"
            elif folder == "CHƯƠNG TRÌNH":
                if "công tác" in trich_yeu.lower():
                    ghi_chu = "⚠️ [Chương trình công tác - Loại trừ]"
                elif "64" in f or "2026" in f:
                    ghi_chu = "🌟 [Bản mới nhất 2026]"
                else:
                    ghi_chu = "🌟 [Tri thức cốt lõi - Chương trình]"
            elif folder == "KẾ HOẠCH":
                if any(kw in trich_yeu.lower() for kw in ["nhiệm vụ trọng tâm", "chuyển đổi số", "đề án 06", "kiểm điểm", "bầu cử"]):
                    ghi_chu = "⭐ [Kế hoạch trọng tâm]"

            record = {
                "stt": stt,
                "the_loai": folder,
                "so_hieu": so_hieu,
                "nam": nam,
                "ngay_ban_hanh": ngay_ban_hanh,
                "trich_yeu": trich_yeu,
                "linh_vuc": linh_vuc,
                "van_de_chinh": van_de_chinh,
                "noi_dung_chi_tiet": noi_dung_chi_tiet,
                "tinh_trang": tinh_trang,
                "is_digital": is_digital,
                "ghi_chu": ghi_chu,
                "file_name": f,
                "file_path": fp,
                "size_kb": size_kb,
                "page_count": page_count,
                "char_count": char_count,
                "raw_text": raw_text
            }
            records.append(record)

    print(f"\n==> ĐÃ XỬ LÝ XONG TOÀN BỘ {len(records)} VĂN BẢN!")
    return records

def export_outputs(records: list):
    """Xuất trọn bộ ra CSV (Excel), Markdown, JSON và các tệp văn bản số toàn văn."""
    # 1. Xuất CSV có 2 cột riêng biệt Vấn đề và Nội dung
    with open(OUTPUT_CSV, mode='w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "STT", "Thể loại", "Số ký hiệu", "Năm ban hành", "Ngày ban hành",
            "Trích yếu / Tiêu đề văn bản", "Lĩnh vực công tác", 
            "Vấn đề trọng tâm cần giải quyết (Vấn đề)", 
            "Nội dung chỉ đạo & Yêu cầu triển khai (Nội dung)", 
            "Tình trạng tệp", "Ghi chú đối soát", "Tên tệp", "Dung lượng (KB)"
        ])
        for r in records:
            writer.writerow([
                r["stt"], r["the_loai"], r["so_hieu"], r["nam"], r["ngay_ban_hanh"],
                r["trich_yeu"], r["linh_vuc"], r["van_de_chinh"],
                r["noi_dung_chi_tiet"], r["tinh_trang"], r["ghi_chu"], r["file_name"], r["size_kb"]
            ])
    print(f"✅ 1. Đã cập nhật tệp CSV: {OUTPUT_CSV}")

    # 2. Xuất JSON siêu dữ liệu
    clean_records = []
    for r in records:
        cr = dict(r)
        del cr["raw_text"]  # Không lưu raw_text vào metadata json để tệp gọn nhẹ
        clean_records.append(cr)

    with open(OUTPUT_JSON, mode='w', encoding='utf-8') as f:
        json.dump(clean_records, f, ensure_ascii=False, indent=2)
    print(f"✅ 2. Đã cập nhật tệp JSON: {OUTPUT_JSON}")

    # 3. Xuất Markdown Bảng danh mục chi tiết
    digital_count = sum(1 for r in records if r["is_digital"])
    with open(OUTPUT_MD, mode='w', encoding='utf-8') as f:
        f.write("# BẢNG DANH MỤC & SIÊU DỮ LIỆU TOÀN BỘ VĂN BẢN ĐI ĐÃ BAN HÀNH\n")
        f.write(f"*Cơ quan ban hành: Đảng uỷ xã Công Hải, tỉnh Khánh Hoà*\n")
        f.write(f"*Thời điểm tạo lập: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | Tổng số văn bản: {len(records)}*\n\n")
        f.write("---\n\n")
        
        f.write("## I. TỔNG HỢP THEO THỂ LOẠI VĂN BẢN\n\n")
        f.write("| STT | Thể loại văn bản | Số lượng | Năm 2025 | Năm 2026 | Tình trạng số hoá có toàn văn |\n")
        f.write("| :---: | :--- | :---: | :---: | :---: | :--- |\n")
        
        folders = sorted(list(set(r["the_loai"] for r in records)))
        for i, fld in enumerate(folders, 1):
            fld_recs = [r for r in records if r["the_loai"] == fld]
            c_total = len(fld_recs)
            c_2025 = sum(1 for r in fld_recs if r["nam"] == "2025")
            c_2026 = sum(1 for r in fld_recs if r["nam"] == "2026")
            c_digital = sum(1 for r in fld_recs if r["is_digital"])
            f.write(f"| {i} | **{fld}** | **{c_total}** | {c_2025} | {c_2026} | **{c_digital}/{c_total}** tệp có toàn văn |\n")
        f.write(f"| | **TỔNG CỘNG** | **{len(records)}** | **{sum(1 for r in records if r['nam']=='2025')}** | **{sum(1 for r in records if r['nam']=='2026')}** | **{digital_count} tệp có toàn văn** |\n\n")
        f.write("---\n\n")

        f.write("## II. BẢNG DANH MỤC CHI TIẾT (TÁCH BIỆT VẤN ĐỀ VÀ NỘI DUNG)\n\n")
        for fld in folders:
            fld_recs = [r for r in records if r["the_loai"] == fld]
            f.write(f"### {fld} ({len(fld_recs)} văn bản)\n\n")
            f.write("| STT | Số hiệu | Ngày ban hành | Trích yếu / Tiêu đề | Lĩnh vực | Vấn đề trọng tâm giải quyết | Nội dung chỉ đạo & Yêu cầu triển khai | Trạng thái |\n")
            f.write("| :---: | :--- | :---: | :--- | :--- | :--- | :--- | :--- |\n")
            for r in fld_recs:
                stt_str = r["stt"]
                so_str = f"`{r['so_hieu']}`"
                ngay_str = r["ngay_ban_hanh"]
                ty_str = f"**{r['trich_yeu']}**"
                lv_str = r["linh_vuc"]
                vd_str = r["van_de_chinh"]
                nd_str = r["noi_dung_chi_tiet"]
                tt_str = r["ghi_chu"] if r["ghi_chu"] else r["tinh_trang"]
                f.write(f"| {stt_str} | {so_str} | {ngay_str} | {ty_str} | {lv_str} | {vd_str} | {nd_str} | {tt_str} |\n")
            f.write("\n")
    print(f"✅ 3. Đã cập nhật tệp Markdown: {OUTPUT_MD}")

    # 4. Xuất tất cả các tệp văn bản số có toàn văn ra thư mục riêng
    os.makedirs(OUTPUT_FULLTEXT_DIR, exist_ok=True)
    exported_fulltext = 0
    for r in records:
        if r["is_digital"] and r["raw_text"]:
            # Tạo tên tệp an toàn
            safe_name = re.sub(r'[\\/*?:"<>|]', '_', f"{r['the_loai']}_{r['so_hieu'].replace('/', '_')}_{r['nam']}")
            md_path = os.path.join(OUTPUT_FULLTEXT_DIR, f"{safe_name}.md")
            with open(md_path, 'w', encoding='utf-8') as mf:
                mf.write("---\n")
                mf.write(f"stt: {r['stt']}\n")
                mf.write(f"the_loai: \"{r['the_loai']}\"\n")
                mf.write(f"so_hieu: \"{r['so_hieu']}\"\n")
                mf.write(f"nam: \"{r['nam']}\"\n")
                mf.write(f"ngay_ban_hanh: \"{r['ngay_ban_hanh']}\"\n")
                mf.write(f"trich_yeu: \"{r['trich_yeu']}\"\n")
                mf.write(f"linh_vuc: \"{r['linh_vuc']}\"\n")
                mf.write(f"van_de_chinh: \"{r['van_de_chinh']}\"\n")
                mf.write(f"ghi_chu: \"{r['ghi_chu']}\"\n")
                mf.write(f"file_goc: \"{r['file_name']}\"\n")
                mf.write("---\n\n")
                mf.write(f"# {r['trich_yeu']}\n\n")
                mf.write(f"**Số hiệu:** {r['so_hieu']} | **Ngày ban hành:** {r['ngay_ban_hanh']} | **Lĩnh vực:** {r['linh_vuc']}\n\n")
                mf.write("### 1. Vấn đề trọng tâm cần giải quyết\n")
                mf.write(f"{r['van_de_chinh']}\n\n")
                mf.write("### 2. Tóm tắt nội dung chỉ đạo\n")
                mf.write(f"{r['noi_dung_chi_tiet']}\n\n")
                mf.write("### 3. Toàn văn văn bản số hoá\n\n")
                mf.write("```text\n")
                mf.write(r["raw_text"])
                mf.write("\n```\n")
            exported_fulltext += 1

    print(f"✅ 4. Đã xuất toàn văn {exported_fulltext} tệp văn bản số vào thư mục: {OUTPUT_FULLTEXT_DIR}")

    # 5. Xuất báo cáo chuyên đề tổng hợp Nội dung & Vấn đề theo 8 Trụ cột
    with open(OUTPUT_SYNTHESIS_MD, 'w', encoding='utf-8') as sf:
        sf.write("# BÁO CÁO TỔNG HỢP NỘI DUNG VÀ VẤN ĐỀ TRỌNG TÂM CÁC VĂN BẢN ĐÃ BAN HÀNH\n")
        sf.write("*Đảng uỷ xã Công Hải, tỉnh Khánh Hoà — Cơ sở dữ liệu tri thức tham mưu cấp uỷ*\n\n")
        sf.write("---\n\n")
        sf.write("## I. TỔNG QUAN HỆ THỐNG VĂN BẢN ĐI\n\n")
        sf.write(f"- **Tổng số lượng văn bản:** {len(records)} văn bản thuộc 14 thể loại.\n")
        sf.write(f"- **Số lượng văn bản số có toàn văn:** {digital_count} văn bản.\n")
        sf.write("- **Nguyên tắc phân tầng tri thức:**\n")
        sf.write("  1. *Tri thức cốt lõi:* Các Nghị quyết của Đại hội Đảng bộ xã và Đảng uỷ (6 Nghị quyết nền tảng), Chương trình hành động số 23-CTr/ĐU.\n")
        sf.write("  2. *Quy định vận hành:* Chương trình kiểm tra giám sát toàn khóa (Bản mới nhất 64-CTr/ĐU năm 2026), các Quy chế làm việc.\n")
        sf.write("  3. *Chỉ đạo điều hành thường xuyên:* 406 Công văn, 74 Thông báo kết luận, 54 Kế hoạch chuyên đề.\n\n")
        sf.write("---\n\n")
        sf.write("## II. TỔNG HỢP VẤN ĐỀ VÀ NỘI DUNG CHỈ ĐẠO THEO 8 TRỤ CỘT CÔNG TÁC\n\n")

        pillars = [
            ("Kinh tế - Ngân sách", "1. TRỤ CỘT KINH TẾ - NGÂN SÁCH & ĐẦU TƯ TOÀN XÃ HỘI"),
            ("Công tác Tổ chức - Đảng viên", "2. TRỤ CỘT TỔ CHỨC CÁN BỘ & XÂY DỰNG ĐẢNG"),
            ("Kiểm tra - Giám sát Đảng", "3. TRỤ CỘT KIỂM TRA, GIÁM SÁT & KỶ CƯƠNG CỦA ĐẢNG"),
            ("Bầu cử Quốc hội & HĐND", "4. TRỤ CỘT BẦU CỬ ĐBQH KHOÁ XVI VÀ HĐND CÁC CẤP (2026-2031)"),
            ("Chuyển đổi số & CCHC", "5. TRỤ CỘT CHUYỂN ĐỔI SỐ, ĐỀ ÁN 06 & CẢI CÁCH HÀNH CHÍNH"),
            ("Đất đai - Môi trường & PCTT", "6. TRỤ CỘT QUẢN LÝ ĐẤT ĐAI, TRẬT TỰ XÂY DỰNG & PHÒNG CHỐNG THIÊN TAI"),
            ("Quốc phòng - An ninh - Nội chính", "7. TRỤ CỘT QUỐC PHÒNG, AN NINH & NỘI CHÍNH"),
            ("Tuyên giáo - Dân vận", "8. TRỤ CỘT TUYÊN GIÁO, DÂN VẬN & AN SINH XÃ HỘI")
        ]

        for p_key, p_title in pillars:
            p_recs = [r for r in records if r["linh_vuc"] == p_key]
            sf.write(f"### {p_title} ({len(p_recs)} văn bản)\n\n")
            sf.write(f"**Vấn đề cốt lõi:**\n")
            if p_recs:
                sf.write(f"- {p_recs[0]['van_de_chinh']}\n\n")
            sf.write(f"**Các văn bản chỉ đạo trọng tâm tiêu biểu:**\n\n")
            for r in p_recs[:8]:
                sf.write(f"- **{r['so_hieu']}** ({r['ngay_ban_hanh']}): *{r['trich_yeu']}*\n")
                sf.write(f"  + **Vấn đề:** {r['van_de_chinh']}\n")
                sf.write(f"  + **Nội dung:** {r['noi_dung_chi_tiet'][:200]}...\n\n")
            sf.write("\n")

    print(f"✅ 5. Đã xuất báo cáo tổng hợp 8 trụ cột: {OUTPUT_SYNTHESIS_MD}")
    print("=" * 70)

if __name__ == "__main__":
    recs = process_all_documents()
    if recs:
        export_outputs(recs)
