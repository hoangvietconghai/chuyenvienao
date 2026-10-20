import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.export_docx import export_party_document

bc_data = {
    'doc_type': 'BC',
    'so_hieu': 'Số      -BC/VPĐU',
    'co_quan_cap_tren': 'ĐẢNG UỶ XÃ CÔNG HẢI',
    'co_quan_ban_hanh': 'VĂN PHÒNG',
    'dia_danh_ngay': 'Công Hải, ngày   tháng 10 năm 2026',
    'ten_loai': 'BÁO CÁO',
    'trich_yeu': 'tình hình thực hiện công tác tuần 41 (từ ngày 12/10/2026 - 16/10/2026)\nvà một số nhiệm vụ trọng tâm tuần 42',
    'noi_dung': [
        'Thực hiện Chương trình công tác của Thường trực, Ban Thường vụ Đảng uỷ tuần 41 (từ ngày 12/10/2026 - 16/10/2026), Văn phòng Đảng uỷ xã báo cáo tình hình công tác tuần 41 và nhiệm vụ trọng tâm tuần 42 như sau:',
        'I. KẾT QUẢ TRIỂN KHAI NHIỆM VỤ',
        '1. Công tác lãnh đạo, chỉ đạo của Thường trực, Ban Thường vụ Đảng uỷ:',
        '- Về quán triệt, tuyên truyền và triển khai các văn bản của cấp trên: Ban Thường vụ Đảng uỷ đã ban hành Kế hoạch tổ chức nghiên cứu, học tập, quán triệt, tuyên truyền và triển khai thực hiện Nghị quyết Hội nghị lần thứ tư Ban Chấp hành Trung ương Đảng khóa XIV; triển khai Hướng dẫn số 07-HD/BTGTU ngày 23/9/2026 của Ban Tuyên giáo Tỉnh uỷ về công tác tuyên truyền miệng tháng 10 năm 2026; triển khai Hướng dẫn số 03-HD/BTGTU ngày 14/9/2026 của Ban Tuyên giáo Tỉnh uỷ thực hiện Đề án phổ biến, bồi dưỡng, cập nhật kiến thức lý luận chính trị cho cán bộ, đảng viên trên Internet; triển khai Thông báo số 218-TB/TU ngày 02/10/2026 của Thường trực Tỉnh uỷ tại Hội nghị công tác nội chính, phòng, chống tham nhũng, lãng phí, tiêu cực và cải cách tư pháp 9 tháng năm 2026; triển khai Kết luận số 353-KL/TU ngày 02/10/2026 của Ban Chấp hành Đảng bộ tỉnh về tình hình thực hiện nhiệm vụ 9 tháng đầu năm và nhiệm vụ trọng tâm quý IV năm 2026.',
        '- Chỉ đạo các cơ quan, đơn vị, các chi bộ trực thuộc và các tổ chức, cá nhân liên quan triển khai thực hiện Kế hoạch số 144-KH/ĐU ngày 13/10/2026 của Ban Thường vụ Đảng uỷ xã về triển khai rà soát, làm sạch, chuẩn hóa, đối soát dữ liệu tổ chức đảng, đảng viên trong Đảng bộ xã Công Hải.',
        '- Chỉ đạo triển khai thực hiện Hướng dẫn số 01-HD/ĐUMTTQCĐTT ngày 08/10/2026 của Đảng uỷ Mặt trận Tổ quốc, các đoàn thể tỉnh về Xây dựng, đánh giá, công nhận mô hình, điển hình "Dân vận khéo" cấp tỉnh, giai đoạn 2026 - 2030; chỉ đạo triển khai thực hiện Công văn số 1902-CV/TU ngày 08/10/2026 của Ban Thường vụ Tỉnh uỷ về việc tăng cường lãnh đạo, chỉ đạo công tác số hóa hồ sơ đảng viên; chỉ đạo triển khai thực hiện Đề án số 21-ĐA/TU ngày 30/9/2026 của Ban Thường vụ Tỉnh uỷ về nâng cao chất lượng hoạt động của Hội đồng nhân dân 02 cấp trên địa bàn tỉnh Khánh Hoà nhiệm kỳ 2026 - 2031.',
        '- Trong tuần, Thường trực, Ban Thường vụ Đảng uỷ họp cho ý kiến danh mục, sản phẩm công việc của tập thể Ban Thường vụ Đảng uỷ và cá nhân các đồng chí cán bộ lãnh đạo diện Ban Thường vụ Tỉnh uỷ quản lý quý IV/2026; làm việc với ba chi bộ thôn (Động Thông, Phước Chiến, Ma Trai) về tình hình, kết quả thực hiện nhiệm vụ Quý III năm 2026, định hướng công tác Quý IV/2026; tổ chức họp mặt kỷ niệm ngày truyền thống các cơ quan Đảng, tổ chức chính trị - xã hội.',
        '- Thường trực Đảng uỷ tham dự Hội nghị toàn quốc nghiên cứu, học tập, quán triệt và triển khai thực hiện Nghị quyết Hội nghị lần thứ tư Ban Chấp hành Trung ương Đảng khóa XIV; dự Họp mặt kỷ niệm 96 năm Ngày thành lập Hội Nông dân Việt Nam; dự Đại hội Hội Khuyến học xã Công Hải lần thứ I, nhiệm kỳ 2026 - 2031.',
        '2. Công tác chỉ đạo, điều hành của Uỷ ban nhân dân xã:',
        '- Về kinh tế, ngân sách và đầu tư công: Thu ngân sách trong tuần đạt 119 triệu đồng, lũy kế từ đầu năm đạt 16.572 triệu đồng / 14.115 triệu đồng (đạt 117,4% dự toán năm). Chi trong tuần đạt 5.256 triệu đồng, lũy kế từ đầu năm đạt 126.979 triệu đồng. Về đầu tư công: Đã giải ngân 37.651 triệu đồng / 50.527 triệu đồng (đạt 74,51% kế hoạch); trong đó vốn năm 2025 chuyển sang đạt 99,47%, riêng vốn giao năm 2026 giải ngân đạt 28.395 triệu đồng / 41.221 triệu đồng (đạt 68,88%).',
        '- Về nông nghiệp, nông thôn mới và quản lý đất đai: Duy trì chăm sóc 1.262,1 ha cây trồng vụ Mùa (lúa 507,3 ha, màu 754,8 ha); kiểm soát tốt dịch bệnh trên cây trồng và đàn gia súc, gia cầm; có 7/8 thôn hoàn thành kê khai động vật nuôi. Hoàn thiện dự thảo Kế hoạch thực hiện Nghị quyết số 17-NQ/ĐU ngày 30/9/2026 của Ban Chấp hành Đảng bộ xã về các Chương trình mục tiêu quốc gia giai đoạn 2026 - 2030. Ban hành Kế hoạch số 335/KH-UBND ngày 09/10/2026 về kê khai đăng ký đất đai cho hộ gia đình, cá nhân (đã thực hiện khoảng 400 thửa tại 03 thôn Kà Rôm, Suối Giếng, Suối Vang); hoàn thành đăng ký đất đai đối với 687 thửa đất do UBND xã quản lý (đợt 4); ban hành Quyết định phê duyệt giá khởi điểm đấu giá cho thuê đất nông nghiệp công ích trên địa bàn xã.',
        '- Về xây dựng, công thương và các dự án trọng điểm: Ban hành Quyết định số 988/QĐ-UBND ngày 10/10/2026 phê duyệt Phương án và kinh phí di dời trụ điện Kà Rôm 2/B07 phục vụ Dự án thành phần 3: Bồi thường, hỗ trợ, tái định cư phục vụ dự án Đường sắt tốc độ cao trên trục Bắc - Nam (Hạng mục: Khu tái định cư thôn Hiệp Kiết). Phê duyệt Báo cáo kinh tế - kỹ thuật 02 dự án: Nâng cấp đường giao thông thôn Suối Vang và Hệ thống điện chiếu sáng đường 706 thôn Kà Rôm. Xây dựng Kế hoạch tổ chức Hội nghị gặp mặt Doanh nghiệp trên địa bàn xã Công Hải.',
        '- Về văn hoá - xã hội và chính sách an sinh: Lập danh sách truy lĩnh trợ cấp xã hội theo Nghị định số 335/2026/NĐ-CP ngày 21/8/2026 của Chính phủ cho 519 đối tượng với kinh phí 79,36 triệu đồng. Đề xuất kế hoạch và bổ sung dự toán kinh phí hỗ trợ đào tạo nghề cho thanh niên hoàn thành nghĩa vụ quân sự, công an năm 2026. Đề xuất điều chuyển, bố trí 08 máy tính phục vụ hoạt động của Tổ Công nghệ số cộng đồng tại 08 thôn.',
        '- Về cải cách hành chính và giải quyết thủ tục hành chính: Tại Trung tâm Phục vụ hành chính công của xã, đã tiếp nhận 142 hồ sơ TTHC (122 hồ sơ trực tuyến trong kỳ, 20 hồ sơ kỳ trước chuyển qua, không có hồ sơ trực tiếp; tỷ lệ nộp trực tuyến đạt 100%). Đã giải quyết 124 hồ sơ (trước hạn 101 hồ sơ, đúng hạn 23 hồ sơ, không có hồ sơ trễ hạn); đang giải quyết trong hạn 18 hồ sơ.',
        '- Về quốc phòng - an ninh: Duy trì nghiêm chế độ trực sẵn sàng chiến đấu. Lực lượng Công an xã tổ chức tuần tra, kiểm soát địa bàn 14 ca với 32 lượt cán bộ, chiến sĩ và lực lượng ANTT cơ sở tham gia; gọi hỏi, răn đe 01 lượt thanh thiếu niên hư (hiện quản lý 06 đối tượng); phối hợp làm việc với Đoàn kiểm tra PCCC và CNCH của Công an tỉnh Khánh Hoà tại địa phương. Tiếp nhận, hướng dẫn 54 trường hợp TTHC về an ninh trật tự, thu nhận 12 hồ sơ và kích hoạt 18 tài khoản định danh điện tử.',
        'II. NHIỆM VỤ TRỌNG TÂM TUẦN TỚI (TUẦN 42)',
        'Thường trực, Ban Thường vụ Đảng uỷ tập trung lãnh đạo, chỉ đạo triển khai thực hiện các nhiệm vụ trọng tâm quý IV/2026; đôn đốc các cơ quan, đơn vị, chi bộ trực thuộc thực hiện nhiệm vụ được giao, bảo đảm tiến độ, chất lượng. Trọng tâm lãnh đạo, chỉ đạo các khối cơ quan tuần 42:',
        '1. Uỷ ban nhân dân xã:',
        '- Tập trung các giải pháp đẩy nhanh tiến độ giải ngân vốn đầu tư công năm 2026 (hiện mới đạt 68,88%), phấn đấu hoàn thành 100% kế hoạch vốn được giao. Khẩn trương hoàn thiện, ban hành Kế hoạch triển khai thực hiện Nghị quyết số 17-NQ/ĐU ngày 30/9/2026 của Ban Chấp hành Đảng bộ xã về các Chương trình mục tiêu quốc gia giai đoạn 2026 - 2030.',
        '- Quyết liệt chỉ đạo giải quyết các vấn đề thực tiễn, điểm nóng cơ sở: Chủ trì làm việc với các đơn vị liên quan và 02 hộ dân để giải quyết việc làm đường dân sinh tại khu vực thôn Bình Tiên và giải quyết dứt điểm các kiến nghị của Công ty Đường sắt; tăng cường kiểm tra, xử lý tình trạng bụi phát sinh từ các cơ sở khai thác khoáng sản (mỏ đá) gây ảnh hưởng đến đời sống nhân dân; khẩn trương kiểm tra các khu vực xung yếu có nguy cơ sạt lở, ngập úng trước mùa mưa lũ, chủ động phương án bảo vệ an toàn tính mạng, tài sản của nhân dân.',
        '- Tiếp tục phối hợp thực hiện công tác bồi thường, giải phóng mặt bằng Dự án Đường sắt tốc độ cao Bắc - Nam (Khu tái định cư thôn Hiệp Kiết). Tiếp tục triển khai Kế hoạch số 335/KH-UBND về kê khai, đăng ký đất đai cho hộ gia đình, cá nhân bảo đảm tiến độ và chất lượng.',
        '- Về quốc phòng - an ninh: Chỉ đạo Ban Chỉ huy Quân sự xã tham mưu triển khai hiệu quả Chiến dịch 500 ngày đêm quy tập, tìm kiếm và xác định danh tính hài cốt liệt sĩ. Tổ chức Hội nghị triển khai công tác phòng cháy, chữa cháy và cứu nạn, cứu hộ trên địa bàn toàn xã; duy trì nghiêm chế độ trực sẵn sàng chiến đấu và tuần tra bảo đảm an ninh trật tự.',
        '- Rà soát, chấn chỉnh công tác văn thư, hành chính: Tuyệt đối không đưa các thông tin bảo mật, nhạy cảm (như mật khẩu tài khoản) vào văn bản báo cáo công khai; kiểm tra, chuẩn hóa triệt để thuật ngữ bộ máy theo mô hình chính quyền địa phương 02 cấp của tỉnh Khánh Hoà (hoàn toàn không còn cấp huyện).',
        '2. Ban Xây dựng Đảng: Chủ trì, phối hợp với Văn phòng Đảng uỷ và các cơ quan liên quan tiếp thu ý kiến tại Thông báo số 163-TB/ĐU, hoàn thiện danh mục sản phẩm công việc chuẩn của Ban Thường vụ Đảng uỷ và danh mục sản phẩm công việc của các đồng chí Thường trực Đảng uỷ quý IV/2026, tham mưu trình phê duyệt; tiếp tục đôn đốc thực hiện Kế hoạch số 144-KH/ĐU về rà soát, chuẩn hóa dữ liệu tổ chức đảng, đảng viên; tham mưu hoàn thiện hồ sơ xếp loại chất lượng sinh hoạt chi bộ tháng 10/2026.',
        '3. Uỷ ban Kiểm tra Đảng uỷ: Tiếp tục thực hiện chương trình kiểm tra, giám sát năm 2026; tổ chức các nội dung giám sát theo kế hoạch, bảo đảm đúng quy trình, quy định; triển khai các nội dung theo lịch công tác tuần từ ngày 19/10 đến ngày 23/10/2026; kịp thời báo cáo Thường trực Đảng uỷ những vấn đề phát sinh và đề xuất hướng xử lý.',
        '4. Uỷ ban Mặt trận Tổ quốc Việt Nam xã: Đẩy mạnh tuyên truyền, vận động đoàn viên, hội viên và Nhân dân thực hiện các chủ trương của Đảng, chính sách, pháp luật của Nhà nước; triển khai hiệu quả các phong trào thi đua, cuộc vận động và mô hình "Dân vận khéo"; phối hợp chuẩn bị, tổ chức Lễ phát động Tháng cao điểm "Vì người nghèo" năm 2026 và Hội nghị gặp mặt doanh nghiệp.',
        '5. Văn phòng Đảng uỷ: Phối hợp Ban Xây dựng Đảng hoàn thiện danh mục sản phẩm công việc quý IV/2026; theo dõi, đôn đốc các cơ quan, đơn vị triển khai thực hiện, tổng hợp báo cáo Thường trực Đảng uỷ. Tham mưu chuẩn bị chu đáo nội dung, tài liệu phục vụ cuộc họp Thường trực Đảng uỷ tuần 42.',
        '6. Các chi bộ trực thuộc Đảng uỷ: Tiếp tục triển khai các nhiệm vụ chính trị, công tác xây dựng Đảng theo chương trình công tác năm 2026; rà soát, cụ thể hóa các nhiệm vụ quý IV/2026 theo chức năng, nhiệm vụ được giao. Khẩn trương thực hiện Kế hoạch số 144-KH/ĐU về rà soát, làm sạch, chuẩn hóa dữ liệu tổ chức đảng, đảng viên, bảo đảm thời hạn theo kế hoạch.',
        'Trên đây là Báo cáo tình hình công tác tuần 41 (từ ngày 12/10/2026 - 16/10/2026) và một số nhiệm vụ trọng tâm tuần 42. Văn phòng Đảng uỷ báo cáo Thường trực Đảng uỷ xem xét, chỉ đạo./.'
    ],
    'noi_nhan': [
        '- Thường trực Đảng uỷ;',
        '- UBND xã;',
        '- Uỷ ban Mặt trận Tổ quốc Việt Nam xã;',
        '- Các cơ quan tham mưu, giúp việc Đảng uỷ;',
        '- Lưu VPĐU.'
    ],
    'chuc_vu': 'PHÓ CHÁNH VĂN PHÒNG',
    'nguoi_ky': 'Ngô Hoàng Việt'
}

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out_path = os.path.join(base_dir, 'van_ban_du_thao', '2026', 'Bao_cao', 'BC_tuan_41_VPDU_Toi_uu.docx')
export_party_document(bc_data, out_path)
