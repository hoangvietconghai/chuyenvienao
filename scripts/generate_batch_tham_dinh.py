# -*- coding: utf-8 -*-
"""
scripts/generate_batch_tham_dinh.py
Tạo 4 tệp Word (.docx) chuẩn thể thức Đảng theo HD 05-HD/VPTW:
1. Báo cáo Thẩm định tổng hợp của Văn phòng Đảng uỷ đối với chùm 03 dự thảo TBKL kiểm tra
2. Dự thảo TBKL kiểm tra Chi bộ thôn Suối Giếng (chuẩn hóa)
3. Dự thảo TBKL kiểm tra Chi bộ Trường Mẫu giáo Công Hải (chuẩn hóa)
4. Dự thảo TBKL kiểm tra Chi bộ Công an xã (chuẩn hóa)
"""

import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.export_docx import PartyDocumentBuilder


def generate_bao_cao_tham_dinh_tong_hop():
    """Tạo Báo cáo Thẩm định tổng hợp của Văn phòng Đảng uỷ."""
    data_bc = {
        "doc_type": "BC",
        "so_hieu": "Số       -BC/VPĐU",
        "co_quan_cap_tren": "ĐẢNG UỶ XÃ CÔNG HẢI",
        "co_quan_ban_hanh": "VĂN PHÒNG",
        "dia_danh_ngay": "Công Hải, ngày   tháng   năm 2026",
        "ten_loai": "BÁO CÁO",
        "trich_yeu": "kết quả thẩm định chùm dự thảo Thông báo Kết luận kiểm tra việc lãnh đạo, chỉ đạo triển khai thực hiện công tác phòng, chống tham nhũng, lãng phí, tiêu cực đối với 03 chi bộ trực thuộc",
        "can_cu": [
            "Căn cứ Quy chế làm việc số 01-QC/ĐU ngày 02/7/2025 của Ban Chấp hành Đảng bộ xã Công Hải khoá I, nhiệm kỳ 2025 - 2030;",
            "Thực hiện phân công của Thường trực Đảng uỷ, Văn phòng Đảng uỷ đã tiến hành thẩm định hồ sơ 03 dự thảo Thông báo Kết luận kiểm tra việc lãnh đạo, chỉ đạo triển khai thực hiện công tác phòng, chống tham nhũng, lãng phí, tiêu cực năm 2026 (đối với: Chi bộ thôn Suối Giếng, Chi bộ Trường Mẫu giáo Công Hải và Chi bộ Công an xã) do Đoàn kiểm tra Ban Thường vụ Đảng uỷ trình. Kết quả thẩm định cụ thể như sau:"
        ],
        "noi_dung": [
            "I. TỔNG QUAN HỒ SƠ THẨM ĐỊNH",
            "- Cơ quan trình: Đoàn kiểm tra Ban Thường vụ Đảng uỷ (Uỷ ban Kiểm tra Đảng uỷ chủ trì tham mưu).",
            "- Danh mục các văn bản dự thảo thẩm định:",
            "+ (1) Dự thảo Thông báo Kết luận kiểm tra đối với Chi bộ thôn Suối Giếng.",
            "+ (2) Dự thảo Thông báo Kết luận kiểm tra đối với Chi bộ Trường Mẫu giáo Công Hải.",
            "+ (3) Dự thảo Thông báo Kết luận kiểm tra đối với Chi bộ Công an xã.",
            "- Thể loại và thẩm quyền ban hành đề xuất: Thông báo kết luận của Ban Thường vụ Đảng uỷ (-TB/ĐU), do đồng chí Bí thư Đảng uỷ thay mặt Ban Thường vụ Đảng uỷ ký ban hành (T/M BAN THƯỜNG VỤ - BÍ THƯ).",
            "- Thành phần hồ sơ gửi kèm: Tờ trình đề nghị ban hành kết luận kiểm tra; 03 bản dự thảo Thông báo Kết luận; các Báo cáo kết quả kiểm tra của Đoàn kiểm tra đối với từng chi bộ; các biên bản làm việc và tài liệu minh chứng liên quan.",
            "II. KẾT QUẢ THẨM ĐỊNH",
            "**1. Thể thức văn bản:** Văn phòng Đảng uỷ đã rà soát, chỉnh sửa trực tiếp trên dự thảo văn bản các lỗi chính tả, chỉnh sửa thể thức văn bản theo đúng Hướng dẫn số 05-HD/VPTW ngày 12/01/2026 của Văn phòng Trung ương Đảng.",
            "Tuy nhiên, đề nghị cơ quan tham mưu soạn thảo rút kinh nghiệm một số hạn chế mang tính hệ thống trong kỹ thuật trình bày của cả 03 dự thảo ban đầu như sau:",
            "- Về chính tả khối Đảng: Cả 03 văn bản đều mắc lỗi đặt dấu thanh chưa chuẩn theo phong cách chính luận Đảng (ghi 'HÒA', 'ỦY', 'Thùy' thay vì 'HOÀ', 'UỶ', 'Thuỳ'). Văn phòng Đảng uỷ đã chuẩn hóa thống nhất toàn bộ.",
            "- Về khối Header và Tiêu đề: Khối tiêu ngữ bên phải thiếu đường kẻ ngang nét liền chuẩn (chiều dài 186pt, độ dày 3/4pt); phần trích yếu bị phân cắt dòng rời rạc và sử dụng đường gạch nối ('-----') không đúng quy cách thể loại Thông báo. Văn phòng Đảng uỷ đã chuẩn hóa tiêu đề và trích yếu cân đối, trang trọng.",
            "- Về định dạng đoạn văn bản (Paragraph Spacing): Các đoạn thân bài chưa áp dụng đúng thông số bắt buộc của Đảng uỷ xã (Before 6pt, After 6pt, Line spacing Exactly 18pt); mức thụt lề đầu dòng chưa đồng bộ (đoạn thụt 10mm, đoạn 12.7mm, đoạn không thụt lề). Văn phòng Đảng uỷ đã căn chỉnh đồng nhất thụt đầu dòng đúng 1cm (10mm) cho toàn bộ các đoạn và đề mục.",
            "- Về quy chuẩn in đậm chỉ mục: Các dấu gạch đầu dòng ('-') tại phần yêu cầu bị bôi đậm sai quy chuẩn Cấp 4 của Hướng dẫn số 05-HD/VPTW; cụm từ mốc thời gian ('trước ngày 30/11/2026') chưa thống nhất quy cách bôi đậm. Văn phòng Đảng uỷ đã chuẩn hóa các dấu gạch đầu dòng in thường đứng và cụm mốc thời gian in đứng đậm theo đúng quy định.",
            "- Về khối Footer: Khoảng cách từ chức danh ký ('BÍ THƯ') đến họ tên người ký chưa chuẩn 5 dòng cỡ 14pt; văn bản còn tồn tại bảng rỗng thừa ở cuối trang; phần Nơi nhận dùng dấu chấm phẩy ngăn cách giữa VPĐU và HSKT chưa chuẩn và thiếu ký hiệu biên soạn (TB-2026). Văn phòng Đảng uỷ đã hoàn thiện chuẩn xác toàn bộ khối chân trang.",
            "**2. Nội dung và số liệu chuyên môn:**",
            "- Về căn cứ pháp lý và quy trình kiểm tra (Chung cả 03 văn bản): Cả 03 dự thảo chỉ ghi chung chung 'Thực hiện Chương trình kiểm tra, giám sát năm 2026, Ban Thường vụ Đảng ủy đã tiến hành kiểm tra...' mà chưa viện dẫn đầy đủ các căn cứ có tính pháp lý bắt buộc: Quyết định thành lập Đoàn kiểm tra, Kế hoạch kiểm tra, Báo cáo kết quả kiểm tra của Đoàn kiểm tra, và phiên họp của Ban Thường vụ Đảng uỷ xem xét kết luận. Cần bổ sung đồng bộ để bảo đảm giá trị pháp lý chặt chẽ.",
            "- Đối với dự thảo kết luận Chi bộ thôn Suối Giếng (Khối thôn dân cư sau sáp nhập):",
            "+ Về tính chất khuyết điểm: Kết quả kiểm tra chỉ ra nhiều tồn tại rất nghiêm trọng (chưa ban hành Quy chế làm việc; chưa có Quy chế chi tiêu nội bộ; việc thu nộp đảng phí chưa đúng quy định; việc bàn giao hồ sơ, tài chính, tài sản sau sáp nhập chưa đầy đủ; chưa khắc phục xong Thông báo số 20-TB/UBKTĐU ngày 29/4/2026 của UBKT Đảng uỷ). Do đó, phần đánh giá ưu điểm cần diễn đạt thận trọng, khách quan, tránh khẳng định 'người đứng đầu phát huy tốt trách nhiệm' trong khi khuyết điểm buông lỏng quản lý, chậm bàn giao sau sáp nhập rất rõ.",
            "+ Về phân kỳ tiến độ: Cần phân kỳ thời hạn thực hiện: yêu cầu hoàn thành dứt điểm bàn giao tài chính, tài sản và ban hành Quy chế làm việc trước ngày 31/10/2026; báo cáo toàn diện kết quả khắc phục trước ngày 30/11/2026.",
            "- Đối với dự thảo kết luận Chi bộ Trường Mẫu giáo Công Hải (Khối đơn vị sự nghiệp giáo dục sau sáp nhập):",
            "+ Phát hiện mâu thuẫn giữa Mục hạn chế và Mục yêu cầu: Tại Mục 2 (Hạn chế, tồn tại), dự thảo chỉ nêu 02 hạn chế (chưa cụ thể hóa văn bản và chưa có chuyên đề KTGS về PCTNLPTC), hoàn toàn không nhắc đến tồn tại về Quy chế làm việc, Quy chế chi tiêu nội bộ sau sáp nhập. Tuy nhiên, tại Mục 3 (Yêu cầu) lại yêu cầu chi bộ 'khẩn trương rà soát, hoàn thiện Quy chế làm việc, Quy chế chi tiêu nội bộ sau sáp nhập' và 'công khai tài chính, tài sản'. Cơ quan soạn thảo cần làm rõ: Nếu chi bộ có hạn chế này thì phải bổ sung vào Mục 2; nếu không có thì phải lược bỏ yêu cầu tại Mục 3 để bảo đảm tính chính xác, chặt chẽ.",
            "+ Về Nơi nhận: Cần bổ sung gửi UBND xã (cơ quan quản lý nhà nước về giáo dục mầm non và ngân sách trường học) và đồng chí Đảng uỷ viên phụ trách lĩnh vực văn hóa - xã hội/giáo dục.",
            "- Đối với dự thảo kết luận Chi bộ Công an xã (Khối lực lượng vũ trang):",
            "+ Về thuật ngữ chính trị - nghiệp vụ: Tại phần yêu cầu (P14), dự thảo ghi 'nâng cao nhận thức của cấp ủy, người đứng đầu, cán bộ, đảng viên và Nhân dân...' là sao chép máy móc từ chi bộ thôn sang, chưa phù hợp với tính chất quản lý nội bộ của lực lượng vũ trang. Cần chỉnh sửa chuẩn xác thành: 'nâng cao nhận thức của cấp uỷ, chỉ huy công an xã, cán bộ, chiến sĩ và đảng viên trong chi bộ'.",
            "+ Về lĩnh vực kiểm tra nhạy cảm: Cần chỉ rõ các lĩnh vực đặc thù có nguy cơ tiêu cực của Công an xã như đăng ký quản lý cư trú, xử lý vi phạm hành chính, quản lý tang vật, tiếp nhận tố giác tội phạm.",
            "+ Về Nơi nhận: Bổ sung gửi UBND xã (quản lý nhà nước) và đồng chí Đảng uỷ viên phụ trách Công an xã/khối nội chính.",
            "- Về phân công trách nhiệm tổ chức thực hiện theo nguyên tắc '5 Rõ' (Chung cả 03 văn bản): Cả 03 dự thảo đều thiếu phân công cụ thể cơ quan theo dõi, đôn đốc. Cần bổ sung phân công rõ: Giao Uỷ ban Kiểm tra Đảng uỷ chủ trì đôn đốc, giám sát việc khắc phục sau kiểm tra; giao Ban Xây dựng Đảng hướng dẫn hoàn thiện Quy chế làm việc, chấn chỉnh nộp đảng phí; giao các đồng chí Đảng uỷ viên phụ trách địa bàn/đơn vị trực tiếp chỉ đạo, giám sát.",
            "III. ĐỀ XUẤT, KIẾN NGHỊ",
            "Trên cơ sở kết quả thẩm định, Văn phòng Đảng uỷ kính trình Thường trực Đảng uỷ xem xét, chỉ đạo một số nội dung sau:",
            "1. Đối với thể thức văn bản: Thống nhất thông qua cả 03 bản dự thảo Thông báo Kết luận kiểm tra đã được Văn phòng Đảng uỷ trực tiếp rà soát, chỉnh sửa, chuẩn hóa kỹ thuật toàn diện theo Hướng dẫn số 05-HD/VPTW ngày 12/01/2026 của Văn phòng Trung ương Đảng.",
            "2. Đối với nội dung và số liệu chuyên môn: Đề nghị Thường trực Đảng uỷ chỉ đạo Đoàn kiểm tra / Uỷ ban Kiểm tra Đảng uỷ:",
            "- Bổ sung đầy đủ căn cứ pháp lý (Quyết định thành lập đoàn kiểm tra, Kế hoạch kiểm tra, Báo cáo kết quả kiểm tra và ngày họp BTV Đảng uỷ) cho cả 03 văn bản.",
            "- Chỉnh lý nội dung từng văn bản theo kết quả thẩm định:",
            "+ Đối với Chi bộ thôn Suối Giếng: Chuẩn hóa phần đánh giá ưu điểm cho khách quan; phân kỳ thời hạn hoàn thành bàn giao tài chính tài sản trước ngày 31/10/2026; báo cáo toàn diện trước ngày 30/11/2026; bổ sung nơi nhận Ban Xây dựng Đảng và ĐUV phụ trách thôn.",
            "+ Đối với Chi bộ Trường Mẫu giáo: Làm rõ tính thống nhất giữa mục Hạn chế và mục Yêu cầu về Quy chế làm việc, chi tiêu nội bộ sau sáp nhập; bổ sung nơi nhận UBND xã và ĐUV phụ trách trường.",
            "+ Đối với Chi bộ Công an xã: Chuẩn hóa thuật ngữ phù hợp lực lượng vũ trang; làm rõ các lĩnh vực nhạy cảm cần tự kiểm tra; bổ sung nơi nhận UBND xã và ĐUV phụ trách đơn vị.",
            "- Bổ sung mục Tổ chức thực hiện theo nguyên tắc '5 Rõ' cho cả 03 văn bản (giao UBKT Đảng uỷ chủ trì đôn đốc; giao Ban Xây dựng Đảng hướng dẫn; giao ĐUV phụ trách trực tiếp chỉ đạo).",
            "3. Về điều kiện trình: Kính đề nghị Thường trực Đảng uỷ xem xét, thống nhất các nội dung hoàn thiện trên để chỉ đạo xuất bản chính thức, trình đồng chí Bí thư Đảng uỷ ký ban hành đồng bộ 03 Thông báo Kết luận kiểm tra./."
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
    
    out_file = os.path.abspath(r"van_ban_du_thao\BC_tham_dinh_chum_03_TBKL_kiem_tra_PCTNLPTC_2026.docx")
    builder.save(out_file)
    print(f"Đã xuất Báo cáo Thẩm định tổng hợp: {out_file}")
    return out_file


def generate_tbkl_suoi_gieng():
    """Tạo tệp Dự thảo TBKL kiểm tra Chi bộ thôn Suối Giếng chuẩn hóa."""
    data = {
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
            "Thực hiện Chương trình kiểm tra, giám sát năm 2026 của Ban Thường vụ Đảng uỷ xã; xét Báo cáo kết quả kiểm tra của Đoàn kiểm tra theo Quyết định số 56-QĐ/ĐU ngày 15/8/2026 và ý kiến thảo luận của Ban Thường vụ Đảng uỷ tại phiên họp ngày .../.../2026,",
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
    b = PartyDocumentBuilder(data)
    b.build_header()
    b.build_title_section()
    b.build_body()
    b.build_footer()
    out = os.path.abspath(r"van_ban_du_thao\TBKL_kiem_tra_Chi_bo_thon_Suoi_Gieng_chuan_hoa.docx")
    b.save(out)
    print(f"Đã xuất TBKL Suối Giếng: {out}")
    return out


def generate_tbkl_truong_mau_giao():
    """Tạo tệp Dự thảo TBKL kiểm tra Chi bộ Trường Mẫu giáo Công Hải chuẩn hóa."""
    data = {
        "doc_type": "TB",
        "so_hieu": "Số       -TB/ĐU",
        "co_quan_cap_tren": "ĐẢNG BỘ TỈNH KHÁNH HOÀ",
        "co_quan_ban_hanh": "ĐẢNG UỶ XÃ CÔNG HẢI",
        "dia_danh_ngay": "Công Hải, ngày   tháng   năm 2026",
        "ten_loai": "THÔNG BÁO",
        "trich_yeu": "Kết luận kiểm tra việc lãnh đạo, chỉ đạo triển khai thực hiện công tác phòng, chống tham nhũng, lãng phí, tiêu cực đối với Chi bộ Trường Mẫu giáo Công Hải",
        "can_cu": [
            "Căn cứ Điều lệ Đảng Cộng sản Việt Nam;",
            "Căn cứ Quy chế làm việc số 01-QC/ĐU ngày 02/7/2025 của Ban Chấp hành Đảng bộ xã Công Hải khoá I, nhiệm kỳ 2025 - 2030;",
            "Thực hiện Chương trình kiểm tra, giám sát năm 2026 của Ban Thường vụ Đảng uỷ xã; xét Báo cáo kết quả kiểm tra của Đoàn kiểm tra theo Quyết định số 57-QĐ/ĐU ngày 15/8/2026 và ý kiến thảo luận của Ban Thường vụ Đảng uỷ tại phiên họp ngày .../.../2026,",
            "Ban Thường vụ Đảng uỷ thông báo kết luận kiểm tra đối với Chi bộ Trường Mẫu giáo Công Hải như sau:"
        ],
        "noi_dung": [
            "**1. Ưu điểm:** Chi bộ đã quan tâm quán triệt, tuyên truyền về công tác phòng, chống tham nhũng, lãng phí, tiêu cực; thực hiện công khai, minh bạch trong hoạt động, quản lý tài chính, tài sản và các chế độ, chính sách; quan tâm giáo dục chính trị tư tưởng, đạo đức, lối sống, trách nhiệm nêu gương của cán bộ, đảng viên, giáo viên và thực hiện kê khai, công khai tài sản, thu nhập theo quy định. Công tác tự kiểm tra, giám sát, nắm tình hình và nhắc nhở, chấn chỉnh việc thực hiện nhiệm vụ được quan tâm. Người đứng đầu đơn vị cơ bản thực hiện tốt chức trách, nhiệm vụ được giao; trong thời gian kiểm tra, chưa phát hiện vụ việc tham nhũng, lãng phí, tiêu cực thuộc phạm vi lãnh đạo, quản lý của chi bộ phải xem xét, xử lý.",
            "**2. Về hạn chế, tồn tại:**",
            "- Chưa cụ thể hóa, ban hành kịp thời văn bản lãnh đạo, chỉ đạo triển khai thực hiện công tác phòng, chống tham nhũng, lãng phí, tiêu cực của chi bộ phù hợp với đặc thù đơn vị sự nghiệp giáo dục.",
            "- Nội dung kiểm tra, giám sát nội bộ chưa xây dựng thành chuyên đề riêng về công tác phòng, chống tham nhũng, lãng phí, tiêu cực.",
            "- Công tác rà soát, điều chỉnh, bổ sung Quy chế làm việc, Quy chế chi tiêu nội bộ và Chương trình kiểm tra, giám sát của chi bộ sau sáp nhập chưa thật sự kịp thời, chặt chẽ.",
            "**3. Ban Thường vụ Đảng uỷ yêu cầu:**",
            "Chi bộ Trường Mẫu giáo Công Hải tiếp tục phát huy những ưu điểm, tập trung khắc phục những hạn chế, tồn tại nêu trên và thực hiện tốt một số nội dung sau:",
            "- Tiếp tục quán triệt, triển khai thực hiện nghiêm các chủ trương, quy định của Đảng, chính sách, pháp luật của Nhà nước về công tác phòng, chống tham nhũng, lãng phí, tiêu cực; nâng cao nhận thức của cấp uỷ, người đứng đầu, cán bộ, đảng viên, giáo viên, nhân viên về vai trò, ý nghĩa, tầm quan trọng của công tác phòng, chống tham nhũng, lãng phí, tiêu cực gắn với công tác xây dựng Đảng và thực hiện nhiệm vụ chính trị, chuyên môn chăm sóc, giáo dục trẻ; kịp thời cụ thể hóa, ban hành các văn bản triển khai thực hiện sát hợp với thực tế nhà trường.",
            "- Khẩn trương rà soát, điều chỉnh, bổ sung, hoàn thiện và tổ chức thực hiện nghiêm Quy chế làm việc, Quy chế chi tiêu nội bộ, Chương trình kiểm tra, giám sát của chi bộ sau sáp nhập bảo đảm công khai, dân chủ, đúng quy định.",
            "- Tập trung kiểm tra, giám sát chuyên đề về công tác phòng, chống tham nhũng, lãng phí, tiêu cực, nhất là trong quản lý các nguồn thu, chi thỏa thuận, bán trú, mua sắm trang thiết bị giáo dục; kịp thời chấn chỉnh những hạn chế, thiếu sót trong quá trình thực hiện.",
            "- Chi bộ nghiêm túc rà soát, xây dựng Kế hoạch khắc phục đầy đủ các hạn chế, khuyết điểm được Đoàn Kiểm tra chỉ ra và báo cáo kết quả khắc phục theo quy định.",
            "- Thực hiện công khai, minh bạch về tài chính, tài sản và các khoản thu, chi của nhà trường và chi bộ; thực hiện nghiêm trách nhiệm nêu gương của cán bộ, đảng viên, nhất là người đứng đầu cấp uỷ, ban giám hiệu.",
            "- Người đứng đầu chi bộ, ban giám hiệu tăng cường lãnh đạo, chỉ đạo việc thực hiện công tác phòng, chống tham nhũng, lãng phí, tiêu cực; chủ động kiểm tra, kịp thời chấn chỉnh những biểu hiện thiếu trách nhiệm, vi phạm quy định của cán bộ, giáo viên, nhân viên thuộc phạm vi quản lý.",
            "**4. Tổ chức thực hiện:**",
            "- Giao Chi bộ Trường Mẫu giáo Công Hải khẩn trương xây dựng Kế hoạch khắc phục và báo cáo kết quả về Ban Thường vụ Đảng uỷ **trước ngày 30/11/2026**.",
            "- Giao Uỷ ban Kiểm tra Đảng uỷ xã chủ trì theo dõi, hướng dẫn, kiểm tra và đôn đốc Chi bộ Trường Mẫu giáo Công Hải triển khai thực hiện nghiêm túc Thông báo kết luận này.",
            "- Đề nghị Uỷ ban nhân dân xã chỉ đạo bộ phận chuyên môn phối hợp hướng dẫn nhà trường hoàn thiện Quy chế chi tiêu nội bộ, quản lý tài sản công đúng quy định pháp luật.",
            "- Đề nghị đồng chí Đảng uỷ viên phụ trách trường học/lĩnh vực văn hóa - xã hội thường xuyên theo dõi, giám sát chi bộ thực hiện khắc phục kết luận kiểm tra.",
            "Ban Thường vụ Đảng uỷ thông báo để Chi bộ Trường Mẫu giáo Công Hải và các cơ quan, đơn vị liên quan biết, nghiêm túc triển khai thực hiện./."
        ],
        "noi_nhan": [
            "- Uỷ ban Kiểm tra Tỉnh uỷ;",
            "- Các đồng chí UVTV Đảng uỷ;",
            "- Uỷ ban Kiểm tra Đảng uỷ;",
            "- Uỷ ban nhân dân xã;",
            "- Ban Xây dựng Đảng;",
            "- Đồng chí ĐUV phụ trách trường học;",
            "- Chi bộ Trường Mẫu giáo Công Hải;",
            "- Lưu VPĐU, HSKT (TB-2026)."
        ],
        "tham_quyen": "T/M BAN THƯỜNG VỤ",
        "chuc_vu": "BÍ THƯ",
        "nguoi_ky": "Vũ Thị Thuỳ Trang"
    }
    b = PartyDocumentBuilder(data)
    b.build_header()
    b.build_title_section()
    b.build_body()
    b.build_footer()
    out = os.path.abspath(r"van_ban_du_thao\TBKL_kiem_tra_Chi_bo_Truong_Mau_giao_chuan_hoa.docx")
    b.save(out)
    print(f"Đã xuất TBKL Trường Mẫu giáo: {out}")
    return out


def generate_tbkl_cong_an_xa():
    """Tạo tệp Dự thảo TBKL kiểm tra Chi bộ Công an xã chuẩn hóa."""
    data = {
        "doc_type": "TB",
        "so_hieu": "Số       -TB/ĐU",
        "co_quan_cap_tren": "ĐẢNG BỘ TỈNH KHÁNH HOÀ",
        "co_quan_ban_hanh": "ĐẢNG UỶ XÃ CÔNG HẢI",
        "dia_danh_ngay": "Công Hải, ngày   tháng   năm 2026",
        "ten_loai": "THÔNG BÁO",
        "trich_yeu": "Kết luận kiểm tra việc lãnh đạo, chỉ đạo triển khai thực hiện công tác phòng, chống tham nhũng, lãng phí, tiêu cực đối với Chi bộ Công an xã",
        "can_cu": [
            "Căn cứ Điều lệ Đảng Cộng sản Việt Nam;",
            "Căn cứ Quy chế làm việc số 01-QC/ĐU ngày 02/7/2025 của Ban Chấp hành Đảng bộ xã Công Hải khoá I, nhiệm kỳ 2025 - 2030;",
            "Thực hiện Chương trình kiểm tra, giám sát năm 2026 của Ban Thường vụ Đảng uỷ xã; xét Báo cáo kết quả kiểm tra của Đoàn kiểm tra theo Quyết định số 58-QĐ/ĐU ngày 15/8/2026 và ý kiến thảo luận của Ban Thường vụ Đảng uỷ tại phiên họp ngày .../.../2026,",
            "Ban Thường vụ Đảng uỷ thông báo kết luận kiểm tra đối với Chi bộ Công an xã như sau:"
        ],
        "noi_dung": [
            "**1. Ưu điểm:** Chi bộ đã quan tâm lãnh đạo, chỉ đạo và tổ chức thực hiện công tác phòng, chống tham nhũng, lãng phí, tiêu cực; thực hiện nghiêm túc các giải pháp phòng ngừa, công khai, minh bạch, kê khai tài sản, thu nhập, chấp hành kỷ luật, kỷ cương, điều lệnh Công an nhân dân và đẩy mạnh cải cách hành chính. Người đứng đầu cơ bản thực hiện tốt trách nhiệm lãnh đạo, chỉ đạo, kiểm tra, đôn đốc về phòng, chống tham nhũng, lãng phí, tiêu cực; đã chủ động khắc phục các tồn tại, hạn chế được chỉ ra tại Thông báo số 26-TB/UBKTĐU ngày 19/8/2026 của Uỷ ban Kiểm tra Đảng uỷ. Trong kỳ kiểm tra, chưa phát hiện vụ việc tham nhũng, lãng phí, tiêu cực thuộc phạm vi lãnh đạo, quản lý của chi bộ phải xem xét, xử lý.",
            "**2. Về hạn chế, tồn tại:** Công tác kiểm tra, giám sát của chi bộ đối với cán bộ, đảng viên trong những lĩnh vực nhạy cảm, có nguy cơ phát sinh tham nhũng, lãng phí, tiêu cực (như đăng ký cư trú, xử lý vi phạm hành chính, trật tự an toàn giao thông, quản lý tang vật) chưa được thực hiện thường xuyên; số cuộc kiểm tra, giám sát chuyên đề về phòng, chống tham nhũng, lãng phí, tiêu cực còn ít.",
            "**3. Ban Thường vụ Đảng uỷ yêu cầu:**",
            "Chi bộ Công an xã tiếp tục phát huy những ưu điểm, tập trung khắc phục những hạn chế, tồn tại nêu trên và thực hiện tốt một số nội dung sau:",
            "- Tiếp tục quán triệt, triển khai thực hiện nghiêm các chủ trương, quy định của Đảng, chính sách, pháp luật của Nhà nước và quy định của ngành Công an về công tác phòng, chống tham nhũng, lãng phí, tiêu cực; nâng cao nhận thức của cấp uỷ, chỉ huy Công an xã, cán bộ, chiến sĩ và đảng viên trong chi bộ về vai trò, ý nghĩa, tầm quan trọng của công tác phòng, chống tham nhũng, lãng phí, tiêu cực gắn với công tác xây dựng Đảng, xây dựng lực lượng Công an nhân dân thật sự trong sạch, vững mạnh và hoàn thành xuất sắc nhiệm vụ bảo đảm an ninh chính trị, trật tự an toàn xã hội trên địa bàn xã.",
            "- Tăng cường lãnh đạo, chỉ đạo công tác kiểm tra, giám sát và tự kiểm tra, tự giám sát, nhất là đối với những lĩnh vực nghiệp vụ nhạy cảm, dễ phát sinh tiêu cực, nhũng nhiễu; thực hiện nghiêm trách nhiệm nêu gương của cán bộ, đảng viên, nhất là người đứng đầu cấp uỷ, chỉ huy đơn vị.",
            "- Người đứng đầu chi bộ tiếp tục tăng cường lãnh đạo, chỉ đạo, kiểm tra, đôn đốc việc thực hiện công tác phòng, chống tham nhũng, lãng phí, tiêu cực; kịp thời chấn chỉnh những biểu hiện thiếu trách nhiệm, vi phạm điều lệnh, quy trình công tác của cán bộ, chiến sĩ trong phạm vi quản lý.",
            "**4. Tổ chức thực hiện:**",
            "- Giao Chi bộ Công an xã xây dựng Kế hoạch khắc phục và báo cáo kết quả về Ban Thường vụ Đảng uỷ **trước ngày 30/11/2026**.",
            "- Giao Uỷ ban Kiểm tra Đảng uỷ xã chủ trì theo dõi, hướng dẫn, kiểm tra và đôn đốc Chi bộ Công an xã triển khai thực hiện nghiêm túc Thông báo kết luận này.",
            "- Đề nghị Uỷ ban nhân dân xã phối hợp tạo điều kiện cơ sở vật chất, hậu cần phục vụ hoạt động của Công an xã đáp ứng yêu cầu nhiệm vụ.",
            "- Đề nghị đồng chí Đảng uỷ viên phụ trách Công an xã/khối Nội chính thường xuyên theo dõi, dự sinh hoạt chi bộ và chỉ đạo việc thực hiện kết luận kiểm tra.",
            "Ban Thường vụ Đảng uỷ thông báo để Chi bộ Công an xã và các cơ quan, đơn vị liên quan biết, nghiêm túc triển khai thực hiện./."
        ],
        "noi_nhan": [
            "- Uỷ ban Kiểm tra Tỉnh uỷ;",
            "- Các đồng chí UVTV Đảng uỷ;",
            "- Uỷ ban Kiểm tra Đảng uỷ;",
            "- Uỷ ban nhân dân xã;",
            "- Ban Xây dựng Đảng;",
            "- Đồng chí ĐUV phụ trách Công an xã;",
            "- Chi bộ Công an xã;",
            "- Lưu VPĐU, HSKT (TB-2026)."
        ],
        "tham_quyen": "T/M BAN THƯỜNG VỤ",
        "chuc_vu": "BÍ THƯ",
        "nguoi_ky": "Vũ Thị Thuỳ Trang"
    }
    b = PartyDocumentBuilder(data)
    b.build_header()
    b.build_title_section()
    b.build_body()
    b.build_footer()
    out = os.path.abspath(r"van_ban_du_thao\TBKL_kiem_tra_Chi_bo_Cong_an_xa_chuan_hoa.docx")
    b.save(out)
    print(f"Đã xuất TBKL Công an xã: {out}")
    return out


if __name__ == "__main__":
    generate_bao_cao_tham_dinh_tong_hop()
    generate_tbkl_suoi_gieng()
    generate_tbkl_truong_mau_giao()
    generate_tbkl_cong_an_xa()
