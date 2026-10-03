# -*- coding: utf-8 -*-
"""
scripts/generate_tham_dinh_outputs.py
Tạo 2 tệp văn bản Word (.docx) chuẩn thể thức Đảng theo HD 05-HD/VPTW:
1. Báo cáo Thẩm định của Văn phòng Đảng uỷ xã Công Hải
2. Dự thảo Thông báo Kết luận kiểm tra Chi bộ thôn Suối Giếng đã được chuẩn hóa
"""

import os
import sys
from pathlib import Path

# Thiết lập encoding UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from scripts.export_docx import PartyDocumentBuilder
except ImportError:
    from export_docx import PartyDocumentBuilder


def generate_bao_cao_tham_dinh():
    """Tạo tệp Báo cáo Thẩm định của Văn phòng Đảng uỷ."""
    data_bc = {
        "doc_type": "BC",
        "so_hieu": "Số       -BC/VPĐU",
        "co_quan_cap_tren": "ĐẢNG UỶ XÃ CÔNG HẢI",
        "co_quan_ban_hanh": "VĂN PHÒNG",
        "dia_danh_ngay": "Công Hải, ngày   tháng   năm 2026",
        "ten_loai": "BÁO CÁO",
        "trich_yeu": "kết quả thẩm định dự thảo Thông báo Kết luận kiểm tra việc lãnh đạo, chỉ đạo triển khai thực hiện công tác phòng, chống tham nhũng, lãng phí, tiêu cực đối với Chi bộ thôn Suối Giếng",
        "can_cu": [
            "Căn cứ Quy chế làm việc số 01-QC/ĐU ngày 02/7/2025 của Ban Chấp hành Đảng bộ xã Công Hải khoá I, nhiệm kỳ 2025 - 2030;",
            "Thực hiện phân công của Thường trực Đảng uỷ, Văn phòng Đảng uỷ tiến hành thẩm định dự thảo Thông báo Kết luận kiểm tra việc lãnh đạo, chỉ đạo triển khai thực hiện công tác phòng, chống tham nhũng, lãng phí, tiêu cực đối với Chi bộ thôn Suối Giếng do Đoàn kiểm tra Ban Thường vụ Đảng uỷ trình. Kết quả thẩm định cụ thể như sau:"
        ],
        "noi_dung": [
            "I. TỔNG QUAN HỒ SƠ THẨM ĐỊNH",
            "- Cơ quan trình: Đoàn kiểm tra Ban Thường vụ Đảng uỷ (Uỷ ban Kiểm tra Đảng uỷ chủ trì tham mưu).",
            "- Tên văn bản dự thảo: Thông báo Kết luận kiểm tra việc lãnh đạo, chỉ đạo triển khai thực hiện công tác phòng, chống tham nhũng, lãng phí, tiêu cực đối với chi bộ thôn Suối Giếng.",
            "- Thể loại và thẩm quyền ban hành đề xuất: Thông báo kết luận của Ban Thường vụ Đảng uỷ (-TB/ĐU), do đồng chí Bí thư Đảng uỷ ký ban hành thay mặt Ban Thường vụ Đảng uỷ (T/M BAN THƯỜNG VỤ).",
            "- Thành phần hồ sơ gửi kèm: Tờ trình đề nghị ban hành kết luận kiểm tra; dự thảo Thông báo Kết luận; Báo cáo kết quả kiểm tra của Đoàn kiểm tra; các biên bản làm việc và hồ sơ tài liệu liên quan.",
            "II. KẾT QUẢ THẨM ĐỊNH",
            "**1. Thể thức văn bản:** Văn phòng Đảng uỷ đã rà soát, chỉnh sửa trực tiếp trên dự thảo văn bản các lỗi chính tả, chỉnh sửa thể thức văn bản theo đúng Hướng dẫn số 05-HD/VPTW ngày 12/01/2026 của Văn phòng Trung ương Đảng.",
            "Tuy nhiên, đề nghị cơ quan tham mưu soạn thảo rút kinh nghiệm một số hạn chế về kỹ thuật thể thức trong hồ sơ ban đầu như sau:",
            "- Về chính tả khối Đảng: Văn bản còn mắc lỗi đặt dấu thanh chưa chuẩn theo phong cách chính luận Đảng (ghi 'HÒA', 'ỦY', 'Thùy' thay vì 'HOÀ', 'UỶ', 'Thuỳ'). Văn phòng Đảng uỷ đã chỉnh sửa thống nhất trên toàn bộ văn bản.",
            "- Về khối Header và Tiêu đề: Khối tiêu ngữ bên phải thiếu đường kẻ nét liền màu đen chuẩn (chiều dài 186pt, độ dày 3/4pt); phần trích yếu bị phân cắt dòng rời rạc và sử dụng đường gạch nối ('-----') không đúng quy cách thể loại Thông báo. Văn phòng Đảng uỷ đã chuẩn hóa tiêu đề và trích yếu cân đối, trang trọng.",
            "- Về định dạng đoạn văn bản (Paragraph Spacing): Toàn bộ các đoạn thân bài chưa áp dụng đúng thông số bắt buộc của Đảng uỷ xã (Before 6pt, After 6pt, Line spacing Exactly 18pt); mức thụt lề đầu dòng chưa đồng bộ (đoạn thụt 10mm, đoạn 12.7mm, đoạn không thụt lề). Văn phòng Đảng uỷ đã căn chỉnh đồng nhất thụt đầu dòng đúng 1cm (10mm) cho toàn bộ các đoạn và đề mục.",
            "- Về quy chuẩn in đậm chỉ mục: Các dấu gạch đầu dòng ('-') tại phần yêu cầu bị bôi đậm sai quy chuẩn Cấp 4 của Hướng dẫn số 05-HD/VPTW; cụm từ mốc thời gian ('trước ngày 30/11/2026') vừa in nghiêng vừa in đậm. Văn phòng Đảng uỷ đã chuẩn hóa các dấu gạch đầu dòng in thường đứng và cụm mốc thời gian in đứng đậm theo đúng quy cách.",
            "- Về khối Footer: Khoảng cách từ chức danh ký ('BÍ THƯ') đến họ tên người ký chưa chuẩn 5 dòng cỡ 14pt (dự thảo để 6 dòng rỗng); văn bản còn tồn tại 01 bảng rỗng thừa ở cuối trang. Văn phòng Đảng uỷ đã xóa bảng thừa và thiết lập chuẩn 5 dòng cách ký.",
            "**2. Nội dung và số liệu chuyên môn:**",
            "- Về căn cứ pháp lý và quy trình kiểm tra: Dự thảo mở đầu ghi chung chung 'Thực hiện Chương trình kiểm tra, giám sát năm 2026, Ban Thường vụ Đảng ủy đã tiến hành kiểm tra...' mà chưa viện dẫn đầy đủ các căn cứ có tính pháp lý bắt buộc: Quyết định thành lập Đoàn kiểm tra, Kế hoạch kiểm tra, Báo cáo kết quả kiểm tra của Đoàn kiểm tra, và phiên họp của Ban Thường vụ Đảng uỷ ngày xem xét kết luận. Cần bổ sung để bảo đảm giá trị pháp lý chặt chẽ của Thông báo kết luận.",
            "- Về tính khách quan giữa đánh giá ưu điểm và khuyết điểm: Dự thảo đánh giá 'Trách nhiệm của người đứng đầu được phát huy... trong thời gian kiểm tra, chưa phát hiện vụ việc... phải xem xét, xử lý'. Tuy nhiên, tại mục hạn chế lại chỉ rõ: Chi bộ chưa ban hành Quy chế làm việc; chưa có Quy chế chi tiêu nội bộ; việc thu nộp đảng phí chưa đúng quy định; việc bàn giao sau sáp nhập chi bộ về tài chính, tài sản chưa đầy đủ; và đặc biệt là chưa khắc phục dứt điểm tồn tại theo Thông báo số 20-TB/UBKTĐU ngày 29/4/2026 của UBKT Đảng uỷ. Đây là những hạn chế, thiếu sót rất nghiêm trọng về nguyên tắc tổ chức, kỷ luật Đảng và trách nhiệm của người đứng đầu cấp uỷ sau sáp nhập. Do đó, phần đánh giá ưu điểm cần diễn đạt thận trọng, khách quan, sát với thực chất tình hình.",
            "- Về phân công trách nhiệm tổ chức thực hiện (Nguyên tắc '5 Rõ'): Dự thảo chỉ yêu cầu chung chung Chi bộ thôn Suối Giếng khắc phục và báo cáo kết quả trước ngày 30/11/2026, hoàn toàn chưa giao trách nhiệm cho các cơ quan tham mưu chuyên môn của Đảng uỷ để theo dõi, hướng dẫn, kiểm tra, đôn đốc. Cụ thể: cần giao Uỷ ban Kiểm tra Đảng uỷ chủ trì theo dõi việc khắc phục sau kiểm tra; giao Ban Xây dựng Đảng hướng dẫn xây dựng Quy chế làm việc và chấn chỉnh công tác đảng phí; giao đồng chí Đảng uỷ viên phụ trách thôn Suối Giếng trực tiếp chỉ đạo, giám sát.",
            "- Về phân kỳ lộ trình, thời hạn thực hiện (Deadline): Mốc thời gian 'trước ngày 30/11/2026' là thời hạn báo cáo toàn diện. Tuy nhiên, đối với các công việc cấp bách như hoàn thành dứt điểm việc bàn giao tài chính, tài sản sau sáp nhập và ban hành Quy chế làm việc, nếu để đến cuối tháng 11/2026 mới giải quyết là quá muộn, dễ phát sinh phức tạp. Cần phân kỳ thời hạn hoàn thành các nhiệm vụ cấp bách này trước ngày 31/10/2026.",
            "- Về thành phần Nơi nhận: Cần bổ sung gửi Ban Xây dựng Đảng và đồng chí Đảng uỷ viên phụ trách thôn Suối Giếng để phối hợp triển khai và giám sát.",
            "III. ĐỀ XUẤT, KIẾN NGHỊ",
            "Trên cơ sở kết quả thẩm định, Văn phòng Đảng uỷ kính trình Thường trực Đảng uỷ xem xét, chỉ đạo một số nội dung sau:",
            "1. Đối với thể thức văn bản: Thống nhất áp dụng bản dự thảo Thông báo Kết luận đã được Văn phòng Đảng uỷ trực tiếp rà soát, chỉnh sửa, chuẩn hóa kỹ thuật toàn diện theo đúng Hướng dẫn số 05-HD/VPTW ngày 12/01/2026 của Văn phòng Trung ương Đảng.",
            "2. Đối với nội dung và số liệu chuyên môn: Đề nghị Thường trực Đảng uỷ chỉ đạo Đoàn kiểm tra / Uỷ ban Kiểm tra Đảng uỷ:",
            "- Bổ sung đầy đủ căn cứ: Quyết định thành lập Đoàn kiểm tra, Kế hoạch kiểm tra, Báo cáo kết quả kiểm tra của Đoàn kiểm tra và ngày họp của Ban Thường vụ Đảng uỷ xem xét kết luận.",
            "- Rà soát, điều chỉnh phần đánh giá ưu điểm bảo đảm khách quan, phù hợp với tính chất, mức độ các tồn tại, khuyết điểm được chỉ ra tại mục 2.",
            "- Bổ sung trách nhiệm của các cơ quan tham mưu theo nguyên tắc '5 Rõ': Giao Uỷ ban Kiểm tra Đảng uỷ chủ trì đôn đốc, giám sát; giao Ban Xây dựng Đảng trực tiếp hướng dẫn Chi bộ thôn Suối Giếng ban hành Quy chế làm việc, chấn chỉnh nộp đảng phí; giao đồng chí Đảng uỷ viên phụ trách thôn trực tiếp chỉ đạo chi bộ thực hiện.",
            "- Phân kỳ tiến độ khắc phục: Yêu cầu Chi bộ thôn Suối Giếng hoàn thành dứt điểm việc bàn giao tài chính, tài sản sau sáp nhập và ban hành Quy chế làm việc trước ngày 31/10/2026; xây dựng kế hoạch khắc phục và báo cáo kết quả toàn diện về Ban Thường vụ Đảng uỷ trước ngày 30/11/2026.",
            "- Bổ sung thành phần Nơi nhận: Ban Xây dựng Đảng, đồng chí Đảng uỷ viên phụ trách thôn Suối Giếng.",
            "3. Về điều kiện trình: Kính đề nghị Thường trực Đảng uỷ xem xét, thống nhất các nội dung điều chỉnh trên để hoàn thiện dự thảo Thông báo Kết luận, trình đồng chí Bí thư Đảng uỷ ký ban hành chính thức./."
        ],
        "noi_nhan": [
            "- Thường trực Đảng uỷ;",
            "- Ban Thường vụ Đảng uỷ;",
            "- Uỷ ban Kiểm tra Đảng uỷ;",
            "- Lưu VPĐU (BC-2026)."
        ],
        "tham_quyen": "K/T CHÁNH VĂN PHÒNG",
        "chuc_vu": "PHÓ CHÁNH VĂN PHÒNG",
        "nguoi_ky": "Ngô Hoàng Việt"
    }

    builder = PartyDocumentBuilder(data_bc)
    builder.build_header()
    builder.build_title_section()
    builder.build_body()
    builder.build_footer()
    
    out_file = str(BASE_DIR / "van_ban_du_thao" / "BC_tham_dinh_du_thao_TBKL_kiem_tra_Chi_bo_Suoi_Gieng.docx")
    builder.save(out_file)
    print(f"Đã xuất Báo cáo Thẩm định: {out_file}")
    return out_file


def generate_thong_bao_ket_luan_chuan_hoa():
    """Tạo tệp Dự thảo Thông báo Kết luận đã được chỉnh sửa, chuẩn hóa kỹ thuật thể thức."""
    data_tb = {
        "doc_type": "TB",
        "so_hieu": "Số       -TB/ĐU",
        "co_quan_cap_tren": "ĐẢNG BỘ TỈNH KHÁNH HOÀ",
        "co_quan_ban_hanh": "ĐẢNG UỶ XÃ CÔNG HẢI",
        "dia_danh_ngay": "Công Hải, ngày   tháng   năm 2026",
        "ten_loai": "THÔNG BÁO",
        "trich_yeu": "Kết luận kiểm tra việc lãnh đạo, chỉ đạo triển khai thực hiện công tác phòng, chống tham nhũng, lãng phí, tiêu cực đối với Chi bộ thôn Suối Giếng",
        "can_cu": [
            "Căn cứ Điều lệ Đảng Cộng sản Việt Nam;",
            "Căn cứ Quy chế làm việc số 01-QC/ĐU ngày 02/7/2025 của Ban Chấp hành Đảng bộ xã Công Hải khoá I, nhiệm kỳ 2025 - 2030;",
            "Thực hiện Chương trình kiểm tra, giám sát năm 2026 của Ban Thường vụ Đảng uỷ xã; xét Báo cáo kết quả kiểm tra của Đoàn kiểm tra theo Quyết định số ...-QĐ/ĐU và ý kiến thảo luận của Ban Thường vụ Đảng uỷ tại phiên họp ngày .../.../2026,",
            "Ban Thường vụ Đảng uỷ thông báo kết luận kiểm tra đối với Chi bộ thôn Suối Giếng như sau:"
        ],
        "noi_dung": [
            "**1. Ưu điểm:** Chi bộ đã quan tâm quán triệt, tuyên truyền về công tác phòng, chống tham nhũng, lãng phí, tiêu cực; chấp hành các chủ trương, quy định của Đảng, chính sách, pháp luật của Nhà nước; bước đầu thực hiện các biện pháp phòng ngừa, công khai trong sinh hoạt chi bộ. Trong thời gian kiểm tra, chưa phát hiện vụ việc tham nhũng, lãng phí thuộc phạm vi lãnh đạo của chi bộ phải xử lý kỷ luật.",
            "**2. Về hạn chế, tồn tại:**",
            "- Chưa cụ thể hóa, ban hành kịp thời văn bản lãnh đạo, chỉ đạo triển khai thực hiện công tác phòng, chống tham nhũng, lãng phí, tiêu cực của chi bộ; công tác tự kiểm tra, tự giám sát chưa được thực hiện thường xuyên.",
            "- Công tác lãnh đạo, chỉ đạo và tổ chức thực hiện nhiệm vụ sau sáp nhập chi bộ chưa thật sự đồng bộ, thống nhất; việc tiếp nhận, bàn giao nhiệm vụ, hồ sơ, tài liệu, tài chính và tài sản từ chi bộ thôn Suối Giếng (cũ) sang chi bộ thôn Suối Giếng (mới) chưa đầy đủ, chặt chẽ.",
            "- Việc thực hiện khắc phục các nội dung tồn tại, hạn chế đã được chỉ ra tại Thông báo số 20-TB/UBKTĐU ngày 29/4/2026 của Uỷ ban Kiểm tra Đảng uỷ về việc thực hiện nhiệm vụ kiểm tra, giám sát và thi hành kỷ luật Đảng chưa đầy đủ và chưa báo cáo kết quả khắc phục theo quy định (đối với chi bộ thôn Suối Giếng cũ).",
            "- Chi bộ chưa xây dựng, ban hành Quy chế làm việc, Quy chế chi tiêu nội bộ; Chương trình kiểm tra, giám sát toàn khoá và năm 2026 chưa bảo đảm nội dung; việc thực hiện thu, trích nộp đảng phí chưa bảo đảm đúng theo quy định hiện hành.",
            "**3. Ban Thường vụ Đảng uỷ yêu cầu:**",
            "Chi bộ thôn Suối Giếng tiếp tục phát huy những ưu điểm, tập trung chấn chỉnh, khắc phục triệt để những hạn chế, tồn tại nêu trên và thực hiện nghiêm túc các nội dung sau:",
            "- Tiếp tục quán triệt, triển khai thực hiện nghiêm các chủ trương, quy định của Đảng, chính sách, pháp luật của Nhà nước về công tác phòng, chống tham nhũng, lãng phí, tiêu cực; nâng cao nhận thức của cấp uỷ, người đứng đầu, cán bộ, đảng viên và Nhân dân về vai trò, ý nghĩa, tầm quan trọng của công tác phòng, chống tham nhũng, lãng phí, tiêu cực gắn với công tác xây dựng Đảng và thực hiện nhiệm vụ chính trị của địa phương; cụ thể hóa, ban hành các văn bản triển khai thực hiện phù hợp với tình hình thực tế của chi bộ và địa bàn dân cư.",
            "- Khẩn trương rà soát, bổ sung, hoàn thiện và tổ chức thực hiện nghiêm Quy chế làm việc, Quy chế chi tiêu nội bộ, Chương trình kiểm tra, giám sát toàn khoá và năm 2026 của chi bộ; thực hiện thu, trích nộp đảng phí đầy đủ, đúng quy định.",
            "- Tăng cường công tác tự kiểm tra, tự giám sát đối với các lĩnh vực có nguy cơ phát sinh tham nhũng, lãng phí, tiêu cực, nhất là trong quản lý tài chính, tài sản và các khoản thu, chi; kịp thời chấn chỉnh những hạn chế, thiếu sót trong quá trình thực hiện.",
            "- Xây dựng Kế hoạch khắc phục đầy đủ các nội dung đã được chỉ ra qua các cuộc kiểm tra trước đây và báo cáo kết quả khắc phục theo quy định. Đồng thời, chỉ đạo rà soát, hoàn tất dứt điểm việc tổ chức bàn giao và tiếp nhận nhiệm vụ, hồ sơ, tài liệu, tài chính và tài sản từ chi bộ thôn Suối Giếng (cũ) bảo đảm đầy đủ, chặt chẽ, đúng quy định.",
            "- Phát huy dân chủ, thực hiện công khai, minh bạch trong hoạt động của chi bộ, nhất là đối với các nội dung liên quan đến tài chính, tài sản và các khoản thu, chi; thực hiện nghiêm trách nhiệm nêu gương của cán bộ, đảng viên, nhất là người đứng đầu cấp uỷ, chi bộ.",
            "- Người đứng đầu chi bộ nâng cao tinh thần trách nhiệm trong lãnh đạo, chỉ đạo, kiểm tra, đôn đốc việc thực hiện công tác phòng, chống tham nhũng, lãng phí, tiêu cực tại địa bàn dân cư.",
            "**4. Tổ chức thực hiện:**",
            "- Giao Chi bộ thôn Suối Giếng hoàn thành dứt điểm việc bàn giao tài chính, tài sản sau sáp nhập và ban hành Quy chế làm việc của chi bộ **trước ngày 31/10/2026**; xây dựng kế hoạch khắc phục tổng thể và báo cáo kết quả về Ban Thường vụ Đảng uỷ **trước ngày 30/11/2026**.",
            "- Giao Uỷ ban Kiểm tra Đảng uỷ xã chủ trì theo dõi, hướng dẫn, kiểm tra và đôn đốc Chi bộ thôn Suối Giếng triển khai thực hiện nghiêm túc Thông báo kết luận này; định kỳ báo cáo Ban Thường vụ Đảng uỷ.",
            "- Giao Ban Xây dựng Đảng hướng dẫn Chi bộ thôn Suối Giếng củng cố công tác tổ chức, xây dựng Quy chế làm việc, nâng cao chất lượng sinh hoạt chi bộ và chấn chỉnh công tác thu, trích nộp đảng phí.",
            "- Đề nghị đồng chí Đảng uỷ viên phụ trách thôn Suối Giếng thường xuyên theo dõi, dự sinh hoạt chi bộ và trực tiếp chỉ đạo việc khắc phục các hạn chế, khuyết điểm của chi bộ.",
            "Ban Thường vụ Đảng uỷ thông báo để Chi bộ thôn Suối Giếng và các cơ quan, đơn vị liên quan biết, nghiêm túc triển khai thực hiện./."
        ],
        "noi_nhan": [
            "- Uỷ ban Kiểm tra Tỉnh uỷ;",
            "- Các đồng chí UVTV Đảng uỷ;",
            "- Uỷ ban Kiểm tra Đảng uỷ;",
            "- Ban Xây dựng Đảng;",
            "- Đồng chí ĐUV phụ trách thôn Suối Giếng;",
            "- Chi bộ thôn Suối Giếng;",
            "- Lưu VPĐU, HSKT (TB-2026)."
        ],
        "tham_quyen": "T/M BAN THƯỜNG VỤ",
        "chuc_vu": "BÍ THƯ",
        "nguoi_ky": "Vũ Thị Thuỳ Trang"
    }

    builder = PartyDocumentBuilder(data_tb)
    builder.build_header()
    builder.build_title_section()
    builder.build_body()
    builder.build_footer()
    
    out_file = str(BASE_DIR / "van_ban_du_thao" / "TBKL_kiem_tra_chi_bo_thon_Suoi_Gieng_chuan_hoa.docx")
    builder.save(out_file)
    print(f"Đã xuất Thông báo Kết luận chuẩn hóa: {out_file}")
    return out_file


if __name__ == "__main__":
    generate_bao_cao_tham_dinh()
    generate_thong_bao_ket_luan_chuan_hoa()
