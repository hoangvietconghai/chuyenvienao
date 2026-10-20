# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.export_docx import export_party_document

tb_data = {
    'doc_type': 'TB',
    'so_hieu': 'Số      -TB/ĐU',
    'co_quan_cap_tren': 'ĐẢNG BỘ TỈNH KHÁNH HOÀ',
    'co_quan_ban_hanh': 'ĐẢNG UỶ XÃ CÔNG HẢI',
    'dia_danh_ngay': 'Công Hải, ngày 19 tháng 10 năm 2026',
    'ten_loai': 'THÔNG BÁO',
    'trich_yeu': 'Kết luận của Thường trực Đảng uỷ\ntại cuộc họp giao ban tuần 42 (ngày 19/10/2026)',
    'noi_dung': [
        'Ngày 19/10/2026, Thường trực Đảng uỷ xã Công Hải tổ chức cuộc họp giao ban tuần để nghe Văn phòng Đảng uỷ, Uỷ ban nhân dân xã và các cơ quan tham mưu báo cáo tình hình thực hiện công tác tuần 41 (từ ngày 12/10/2026 - 16/10/2026) và phương hướng, nhiệm vụ trọng tâm tuần 42. Đồng chí Vũ Thị Thuỳ Trang - Bí thư Đảng uỷ xã chủ trì cuộc họp. Tham dự cuộc họp có các đồng chí Thường trực Đảng uỷ, lãnh đạo HĐND, UBND xã, lãnh đạo Ban Xây dựng Đảng, Cơ quan Uỷ ban Kiểm tra, Cơ quan Uỷ ban MTTQ Việt Nam xã và Văn phòng Đảng uỷ.',
        'Sau khi nghe Văn phòng Đảng uỷ báo cáo tổng hợp tình hình công tác tuần 41, ý kiến phát biểu bổ sung của Uỷ ban nhân dân xã và các cơ quan, đơn vị, Thường trực Đảng uỷ kết luận như sau:',
        'I. ĐÁNH GIÁ TÌNH HÌNH CÔNG TÁC TUẦN 41',
        'Thường trực Đảng uỷ cơ bản thống nhất với nội dung dự thảo Báo cáo số 89-BC/VPĐU ngày 16/10/2026 của Văn phòng Đảng uỷ về tình hình công tác tuần 41 và Báo cáo số 342/BC-UBND ngày 16/10/2026 của Uỷ ban nhân dân xã. Trong tuần, Thường trực Đảng uỷ, Ban Thường vụ Đảng uỷ đã tập trung lãnh đạo, chỉ đạo toàn diện hệ thống chính trị triển khai các nhiệm vụ trọng tâm; quán triệt kịp thời các văn bản chỉ đạo của Trung ương, Tỉnh uỷ; triển khai Kế hoạch số 144-KH/ĐU về làm sạch, chuẩn hóa dữ liệu tổ chức đảng, đảng viên. Uỷ ban nhân dân xã đã nỗ lực chỉ đạo điều hành thu ngân sách vượt dự toán cả năm (đạt 117,4%), triển khai tốt công tác sản xuất vụ Mùa, đẩy mạnh cấp CCCD, Đề án 06 và dịch vụ công trực tuyến đạt 100%. An ninh chính trị, trật tự an toàn xã hội trên địa bàn được giữ vững.',
        'Bên cạnh kết quả đạt được, vẫn còn một số tồn tại, hạn chế: Tỷ lệ giải ngân vốn đầu tư công năm 2026 còn thấp (mới đạt 68,88%); công tác phối hợp giải quyết khiếu nại, phản ánh của nhân dân liên quan đến đường dân sinh thôn Bình Tiên và ô nhiễm khói bụi tại các mỏ đá chưa kịp thời; công tác hành chính, văn thư của một số cơ quan còn xuất hiện sai sót về địa danh, thuật ngữ bộ máy (còn nhắc tên cấp huyện cũ), đặc biệt là việc đưa thông tin bảo mật tài khoản vào báo cáo công khai.',
        'II. NHIỆM VỤ TRỌNG TÂM TUẦN 42 (TỪ NGÀY 19/10 - 23/10/2026)',
        'Thường trực Đảng uỷ yêu cầu các cơ quan tham mưu, giúp việc Đảng uỷ, HĐND, UBND, Uỷ ban Mặt trận Tổ quốc Việt Nam xã và các chi bộ trực thuộc tập trung triển khai thực hiện tốt các nhiệm vụ trọng tâm sau:',
        '1. Uỷ ban nhân dân xã:',
        '- Tập trung chỉ đạo quyết liệt các giải pháp tháo gỡ điểm nghẽn, đẩy nhanh tiến độ giải ngân vốn đầu tư công các dự án năm 2026 (hiện mới đạt 68,88%), phấn đấu hoàn thành 100% kế hoạch vốn được giao trước ngày 31/12/2026. Khẩn trương hoàn thiện, ban hành Kế hoạch triển khai thực hiện Nghị quyết số 17-NQ/ĐU ngày 30/9/2026 của Ban Chấp hành Đảng bộ xã về các Chương trình mục tiêu quốc gia giai đoạn 2026 - 2030, hoàn thành trước ngày 23/10/2026.',
        '- Tập trung xử lý dứt điểm các vấn đề dân sinh nóng tại cơ sở: Chủ trì, phối hợp với các đơn vị liên quan và 02 hộ dân làm việc để thống nhất phương án làm đường dân sinh tại khu vực thôn Bình Tiên, giải quyết dứt điểm các kiến nghị của Công ty Đường sắt theo đúng thẩm quyền; tăng cường kiểm tra, kiên quyết xử lý tình trạng bụi phát sinh từ hoạt động của các cơ sở khai thác khoáng sản (mỏ đá) gây ảnh hưởng đến sức khoẻ, sinh hoạt của Nhân dân; chủ động rà soát, kiểm tra các khu vực xung yếu có nguy cơ sạt lở, ngập úng trước mùa mưa lũ, sẵn sàng phương án ứng phó theo phương châm "4 tại chỗ".',
        '- Phối hợp đẩy nhanh tiến độ bồi thường, giải phóng mặt bằng Dự án Đường sắt tốc độ cao trên trục Bắc - Nam (Hạng mục: Khu tái định cư thôn Hiệp Kiết theo Quyết định số 988/QĐ-UBND ngày 10/10/2026); tiếp tục tổ chức kê khai, đăng ký đất đai cho hộ gia đình, cá nhân theo Kế hoạch số 335/KH-UBND bảo đảm tiến độ, chất lượng.',
        '- Lĩnh vực Quốc phòng - An ninh: Chỉ đạo Ban Chỉ huy Quân sự xã tham mưu triển khai hiệu quả Kế hoạch thực hiện Chiến dịch 500 ngày đêm quy tập, tìm kiếm và xác định danh tính hài cốt liệt sĩ trên địa bàn xã. Chỉ đạo Công an xã chủ trì tổ chức Hội nghị triển khai công tác phòng cháy, chữa cháy và cứu nạn, cứu hộ trên địa bàn toàn xã; duy trì nghiêm chế độ tuần tra kiểm soát bảo đảm trật tự an toàn xã hội.',
        '- Rà soát, chấn chỉnh ngay công tác văn thư, soạn thảo văn bản: Tuyệt đối không đưa các thông tin nhạy cảm, mật khẩu tài khoản vào văn bản báo cáo công khai; kiểm tra, rà soát triệt để không để xuất hiện tên gọi cấp huyện cũ và cơ quan huyện cũ trong văn bản chỉ đạo, điều hành theo đúng mô hình chính quyền địa phương 02 cấp của tỉnh Khánh Hoà.',
        '2. Ban Xây dựng Đảng:',
        '- Chủ trì, phối hợp với Văn phòng Đảng uỷ và các cơ quan liên quan khẩn trương tiếp thu ý kiến kết luận của Ban Thường vụ Đảng uỷ tại Thông báo số 163-TB/ĐU, hoàn thiện danh mục sản phẩm công việc chuẩn của Ban Thường vụ Đảng uỷ và danh mục sản phẩm công việc của các đồng chí Thường trực Đảng uỷ quý IV/2026; trình Thường trực Đảng uỷ phê duyệt trước ngày 22/10/2026.',
        '- Tiếp tục theo dõi, hướng dẫn, đôn đốc các chi bộ trực thuộc khẩn trương triển khai thực hiện Kế hoạch số 144-KH/ĐU ngày 13/10/2026 của Ban Thường vụ Đảng uỷ xã về rà soát, làm sạch, chuẩn hóa, đối soát dữ liệu tổ chức đảng, đảng viên; tổng hợp tiến độ báo cáo Thường trực Đảng uỷ định kỳ thứ Sáu hằng tuần. Tham mưu hoàn thiện hồ sơ xếp loại chất lượng sinh hoạt chi bộ tháng 10/2026.',
        '3. Uỷ ban Kiểm tra Đảng uỷ:',
        '- Tiếp tục triển khai thực hiện toàn diện chương trình kiểm tra, giám sát năm 2026 của Đảng uỷ và Uỷ ban Kiểm tra Đảng uỷ; thực hiện nghiêm quy trình, quy định các cuộc giám sát chuyên đề đang tiến hành.',
        '- Bám sát lịch công tác tuần từ ngày 19/10 đến ngày 23/10/2026; chủ động nắm chắc tình hình tổ chức đảng, đảng viên, kịp thời báo cáo Thường trực Đảng uỷ xem xét, xử lý các dấu hiệu vi phạm ngay từ cơ sở.',
        '4. Cơ quan Uỷ ban Mặt trận Tổ quốc Việt Nam xã:',
        '- Tiếp tục tuyên truyền, vận động đoàn viên, hội viên và các tầng lớp Nhân dân đẩy mạnh phong trào thi đua "Dân vận khéo", tích cực tham gia các cuộc vận động toàn dân đoàn kết xây dựng nông thôn mới, đô thị văn minh.',
        '- Chủ trì, phối hợp với UBND xã chuẩn bị chu đáo nội dung, điều kiện tổ chức Lễ phát động Tháng cao điểm "Vì người nghèo" năm 2026 và phối hợp tổ chức thành công Hội nghị gặp mặt Doanh nghiệp trên địa bàn xã Công Hải.',
        '5. Văn phòng Đảng uỷ:',
        '- Tiếp thu ý kiến kết luận của Thường trực Đảng uỷ, rà soát, hoàn thiện và phát hành Thông báo kết luận này; đồng thời chỉnh lý, lưu hành Báo cáo tuần 41 của Đảng uỷ xã bảo đảm đầy đủ số liệu, chuẩn xác thể thức.',
        '- Theo dõi, đôn đốc các cơ quan, đơn vị, các chi bộ trực thuộc triển khai thực hiện nghiêm túc các nội dung kết luận; chuẩn bị chu đáo nội dung, tài liệu và các điều kiện phục vụ chương trình công tác tuần 42 của Thường trực và Ban Thường vụ Đảng uỷ.',
        '6. Các chi bộ trực thuộc Đảng uỷ:',
        '- Cụ thể hóa các nhiệm vụ công tác quý IV/2026 sát với tình hình thực tế của chi bộ, cơ quan, đơn vị, thôn xóm. Tập trung lãnh đạo hoàn thành tốt các chỉ tiêu chuyên môn và công tác xây dựng Đảng năm 2026.',
        '- Khẩn trương hoàn thành công tác rà soát, đối soát, chuẩn hóa dữ liệu đảng viên theo đúng Kế hoạch số 144-KH/ĐU của Ban Thường vụ Đảng uỷ, bảo đảm tiến độ và thời hạn quy định.',
        'Căn cứ Thông báo này, yêu cầu các cơ quan tham mưu, giúp việc Đảng uỷ, Uỷ ban nhân dân xã, Cơ quan Uỷ ban Mặt trận Tổ quốc Việt Nam xã và các chi bộ trực thuộc nghiêm túc triển khai thực hiện./.'
    ],
    'noi_nhan': [
        '- Thường trực Đảng uỷ;',
        '- Các đồng chí UV BTV Đảng uỷ;',
        '- HĐND, UBND xã;',
        '- Cơ quan UBMTTQVN xã;',
        '- Ban Xây dựng Đảng, Cơ quan UBKT Đảng uỷ;',
        '- Các chi bộ trực thuộc;',
        '- Lưu VPĐU.'
    ],
    'tham_quyen': 'T/M BAN THƯỜNG VỤ',
    'chuc_vu': 'BÍ THƯ',
    'nguoi_ky': 'Vũ Thị Thuỳ Trang'
}

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out_path = os.path.join(base_dir, 'van_ban_du_thao', '2026', 'Thong_bao', 'TB_ket_luan_giao_ban_tuan_42.docx')
export_party_document(tb_data, out_path)
