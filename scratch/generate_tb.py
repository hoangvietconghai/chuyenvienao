# -*- coding: utf-8 -*-
import os
import sys

# Đảm bảo đường dẫn import thư viện
base_dir = r"d:\Chuyên viên ảo"
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from scripts.export_docx import export_party_document

def generate_doc():
    data = {
        "doc_type": "TB",
        "so_hieu": "Số      -TB/ĐU",
        "co_quan_cap_tren": "ĐẢNG BỘ TỈNH KHÁNH HOÀ",
        "co_quan_ban_hanh": "ĐẢNG UỶ XÃ CÔNG HẢI",
        "dia_danh_ngay": "Công Hải, ngày   tháng 10 năm 2026",
        "ten_loai": "THÔNG BÁO",
        "trich_yeu": "KẾT LUẬN CỦA THƯỜNG TRỰC ĐẢNG UỶ\ntại buổi làm việc với Chi uỷ Chi bộ các thôn:\nĐộng Thông, Ma Trai và Phước Chiến",
        "noi_dung": [
            "Thực hiện Kế hoạch số 136-KH/ĐU ngày 25/9/2026 của Đảng uỷ xã Công Hải về việc tổ chức làm việc với các chi bộ thôn, chi bộ trường học về tình hình, kết quả thực hiện nhiệm vụ Quý III năm 2026; ngày 06/10/2026, Thường trực Đảng uỷ xã đã tổ chức buổi làm việc với Chi uỷ Chi bộ các thôn: Động Thông, Ma Trai và Phước Chiến do đồng chí Bí thư Đảng uỷ xã chủ trì.",
            "Tham dự buổi làm việc có các đồng chí Thường trực Đảng uỷ, Thường trực HĐND xã, lãnh đạo UBND xã; đại diện lãnh đạo Ban Xây dựng Đảng, Uỷ ban Kiểm tra Đảng uỷ, Văn phòng Đảng uỷ, Cơ quan Uỷ ban Mặt trận Tổ quốc Việt Nam xã; các đồng chí Bí thư, Phó Bí thư, Chi uỷ viên và Trưởng Ban Quản lý các thôn: Động Thông, Ma Trai, Phước Chiến.",
            "Sau khi nghe đại diện Chi uỷ Chi bộ 03 thôn báo cáo kết quả thực hiện nhiệm vụ Quý III, phương hướng nhiệm vụ 03 tháng cuối năm 2026 và các đề xuất, kiến nghị; ý kiến phát biểu của các đại biểu tham dự; Thường trực Đảng uỷ xã thống nhất kết luận như sau:",
            "I. ĐÁNH GIÁ TÌNH HÌNH THỰC HIỆN NHIỆM VỤ QUÝ III NĂM 2026",
            "1. Đánh giá chung và kết quả đạt được: Sau khi thực hiện sắp xếp, sáp nhập thôn theo Đề án số 03-ĐA/ĐU ngày 26/6/2026 của Ban Chấp hành Đảng bộ xã, Chi uỷ Chi bộ các thôn Động Thông, Ma Trai và Phước Chiến đã nêu cao tinh thần trách nhiệm, nhanh chóng ổn định tổ chức bộ máy, ban hành quy chế làm việc, phân công nhiệm vụ cụ thể cho từng chi uỷ viên và đảng viên; kịp thời phối hợp kiện toàn Ban Quản lý thôn, Ban Công tác Mặt trận và các chi hội đoàn thể ở cơ sở. Tình hình tư tưởng trong cán bộ, đảng viên và các tầng lớp Nhân dân (trong đó đồng bào dân tộc Raglai chiếm đa số, từ 90% đến 97%) cơ bản ổn định, đồng thuận, chấp hành nghiêm túc chủ trương của Đảng, chính sách, pháp luật của Nhà nước. Về phát triển kinh tế, Nhân dân duy trì diện tích sản xuất nông nghiệp (vụ Mùa, bắp, mì cao sản, đậu, điều) và phát triển chăn nuôi đàn gia súc (bò, dê); thực hiện tốt các chính sách an sinh xã hội, chăm lo cho người có công với cách mạng, hỗ trợ xây dựng, sửa chữa nhà ở và khám sức khoẻ sàng lọc cho bà con; hoàn thành 100% chỉ tiêu giao quân; tình hình an ninh chính trị, trật tự an toàn xã hội trên địa bàn 03 thôn tiếp tục được giữ vững ổn định.",
            "2. Những tồn tại, hạn chế và khó khăn:",
            "- Về công tác xây dựng Đảng và hệ thống chính trị: Tỷ lệ đảng viên cao tuổi được miễn hoãn sinh hoạt tại Chi bộ thôn Phước Chiến (10/34 đảng viên) và Chi bộ thôn Động Thông (11/41 đảng viên từ 70 tuổi trở lên) chiếm tỷ lệ khá lớn; số lượng đảng viên trẻ phải đi làm ăn xa ngoài địa bàn nhiều dẫn đến khó khăn trong việc triệu tập sinh hoạt định kỳ và duy trì quân số. Việc tiếp cận công nghệ thông tin, cài đặt và sử dụng nền tảng Sổ tay đảng viên điện tử còn rất nhiều hạn chế do phần lớn đảng viên lớn tuổi không thành thạo điện thoại thông minh. Công tác tạo nguồn phát triển đảng viên mới tại các thôn còn chậm, chưa đạt tiến độ yêu cầu. Bộ máy chi uỷ sau sắp xếp tại Chi bộ thôn Động Thông và Chi bộ thôn Phước Chiến vẫn chưa được kiện toàn đầy đủ (còn khuyết chức danh Phó Bí thư Chi bộ và cấp uỷ viên). Công tác quản lý sổ sách, chứng từ tài chính Đảng sau sáp nhập còn lúng túng, sai sót đã được UBKT Đảng uỷ chỉ ra nhưng việc khắc phục cần thực hiện bài bản, chặt chẽ hơn.",
            "- Về phát triển kinh tế - xã hội: Tỷ lệ hộ nghèo và hộ cận nghèo tại 03 thôn vẫn còn ở mức rất cao (thôn Phước Chiến tỷ lệ nghèo 9%, cận nghèo 29,8%; thôn Ma Trai tỷ lệ cận nghèo 20,5%; thôn Động Thông hộ cận nghèo chiếm 18,6%). Hoạt động sản xuất còn phụ thuộc nhiều vào điều kiện tự nhiên, thời tiết khô hạn kéo dài ảnh hưởng tiêu cực đến năng suất cây trồng; dịch bệnh trên đàn vật nuôi có thời điểm phát sinh cục bộ (dịch cúm gia cầm tại Phước Chiến). Tỷ lệ người dân tham gia khám sức khoẻ sàng lọc miễn phí còn thấp.",
            "- Về giáo dục, văn hoá - môi trường và hạ tầng: Tình trạng học sinh trong độ tuổi chưa ra lớp hoặc bỏ học cách nhật vẫn còn xảy ra (thôn Động Thông còn 09 học sinh chưa ra lớp; thôn Phước Chiến còn tình trạng học sinh vắng sau khai giảng). Hạ tầng kỹ thuật, công nghệ thông tin tại nhà văn hoá thôn còn thiếu thốn, chưa đồng bộ (thôn Phước Chiến chưa có đường truyền internet, thiếu bàn ghế làm việc và thiết bị số; thôn Ma Trai hệ thống loa truyền thanh chưa phủ sóng toàn thôn). Tỷ lệ hộ dân có nhà tiêu hợp vệ sinh (Ma Trai mới đạt 29,4%) và tỷ lệ thu gom, xử lý chất thải rắn (Ma Trai đạt 20%) còn rất thấp so với tiêu chuẩn nông thôn mới nâng cao. Tình trạng một số thanh thiếu niên chạy xe phân khối lớn, nẹt pô gây mất an toàn giao thông tại thôn Động Thông chưa được xử lý triệt để.",
            "II. NHIỆM VỤ TRỌNG TÂM 03 THÁNG CUỐI NĂM 2026",
            "Để hoàn thành thắng lợi các mục tiêu, nhiệm vụ chính trị năm 2026 của Đảng bộ xã, Thường trực Đảng uỷ yêu cầu cấp uỷ chi bộ 03 thôn và các cơ quan, đơn vị liên quan tập trung lãnh đạo, chỉ đạo triển khai quyết liệt các nhiệm vụ trọng tâm sau:",
            "1. Đối với Chi uỷ, Chi bộ các thôn Động Thông, Ma Trai và Phước Chiến:",
            "a) Về công tác xây dựng Đảng và hệ thống chính trị:",
            "- Tiếp tục nâng cao năng lực lãnh đạo, sức chiến đấu của chi bộ theo tiêu chuẩn mô hình \"Chi bộ bốn tốt\"; duy trì nghiêm nề nếp sinh hoạt chi bộ định kỳ theo Hướng dẫn số 42-HD/BTCTW của Ban Tổ chức Trung ương; phát huy nguyên tắc tập trung dân chủ, tinh thần tự phê bình và phê bình.",
            "- Chủ động phối hợp chặt chẽ với Ban Xây dựng Đảng rà soát nhân sự, chuẩn bị các điều kiện theo quy định để tiến hành bầu bổ sung cấp uỷ viên và chức danh Phó Bí thư Chi bộ còn khuyết tại Chi bộ thôn Động Thông và Chi bộ thôn Phước Chiến, bảo đảm hoàn thành trước ngày 31/10/2026.",
            "- Tăng cường công tác quản lý đảng viên chặt chẽ, đặc biệt là đảng viên đi làm ăn xa; lập sổ theo dõi cụ thể nơi cư trú, nơi làm việc, giữ mối liên hệ thường xuyên và thực hiện việc chuyển sinh hoạt đảng tạm thời đối với trường hợp đủ điều kiện theo Điều lệ Đảng.",
            "- Chủ động phân công các đồng chí đảng viên trẻ, am hiểu công nghệ trực tiếp kèm cặp, hỗ trợ từng đồng chí đảng viên cao tuổi trong việc tiếp cận, khai thác thông tin trên ứng dụng Sổ tay đảng viên điện tử; linh hoạt hình thức triển khai, không gây áp lực nhưng phải từng bước nâng cao tỷ lệ sử dụng.",
            "- Đẩy mạnh công tác tạo nguồn, phát hiện và bồi dưỡng quần chúng ưu tú để phát triển đảng viên mới; khẩn trương hoàn thiện hồ sơ đề nghị kết nạp Đảng đối với các trường hợp đã cử đi học bồi dưỡng nhận thức về Đảng, phấn đấu hoàn thành 100% chỉ tiêu kết nạp đảng viên mới năm 2026 được Đảng uỷ xã giao trước ngày 15/11/2026.",
            "- Chi bộ thôn Phước Chiến tiếp tục thực hiện nghiêm túc việc khắc phục các tồn tại, hạn chế về công tác quản lý thu nộp đảng phí và ghi chép sổ sách kế toán Đảng sau sáp nhập theo đúng kết luận của Đoàn kiểm tra Uỷ ban Kiểm tra Đảng uỷ xã; bảo đảm việc quản lý thu, nộp, sử dụng đảng phí đúng nguyên tắc, công khai, minh bạch.",
            "- Tăng cường công tác dân vận, phát huy vai trò của Ban Công tác Mặt trận, các chi hội đoàn thể và người có uy tín trong đồng bào dân tộc Raglai; kịp thời nắm bắt tâm tư, nguyện vọng chính đáng của Nhân dân để phản ánh, tham mưu cấp uỷ, chính quyền giải quyết, không để phát sinh bức xúc, khiếu kiện phức tạp.",
            "b) Về phát triển kinh tế - xã hội, bảo đảm quốc phòng - an ninh:",
            "- Tập trung lãnh đạo Nhân dân đẩy mạnh sản xuất vụ Mùa năm 2026, chủ động áp dụng các biện pháp kỹ thuật chăm sóc cây trồng thích ứng với tình hình khô hạn; theo dõi sát sao tình hình dịch bệnh trên đàn gia súc, gia cầm, khẩn trương phối hợp khoanh vùng xử lý triệt để, tuyệt đối không để tái phát hoặc lây lan dịch cúm gia cầm.",
            "- Phối hợp với Uỷ ban nhân dân xã và các ngành chuyên môn thực hiện nghiêm túc, chặt chẽ công tác điều tra, rà soát hộ nghèo, hộ cận nghèo cuối năm 2026 bảo đảm công khai, dân chủ, khách quan, đúng thực chất, làm cơ sở thực hiện các chính sách an sinh xã hội.",
            "- Phối hợp chặt chẽ với các trường học (Trường Mầm non Công Hải, Trường Tiểu học Công Hải, Trường THCS Hùng Vương) thành lập các tổ công tác đến từng hộ gia đình để tìm hiểu hoàn cảnh, kiên trì tuyên truyền, vận động 100% học sinh ra lớp, chấm dứt triệt để tình trạng bỏ học cách nhật hoặc chưa ra lớp, hoàn thành trong tháng 10/2026.",
            "- Tích cực vận động đoàn viên, hội viên và Nhân dân tham gia phong trào xây dựng cảnh quan môi trường nông thôn mới; tuyên truyền, hỗ trợ bà con xây dựng nhà tiêu hợp vệ sinh, duy trì nếp sống vệ sinh môi trường, thu gom rác thải định kỳ.",
            "- Lãnh đạo Ban Quản lý thôn và Ban Chỉ huy Quân sự thôn phối hợp với Ban Chỉ huy Quân sự xã rà soát chặt chẽ nguồn thanh niên trong độ tuổi nghĩa vụ quân sự; tổ chức tuyên truyền, vận động thanh niên tham gia khám tuyển nghĩa vụ quân sự năm 2027 bảo đảm hoàn thành 100% chỉ tiêu giao quân; phối hợp Công an xã tăng cường nắm chắc địa bàn, kịp thời ngăn chặn các hành vi vi phạm trật tự an toàn giao thông.",
            "2. Đối với Uỷ ban nhân dân xã:",
            "- Khẩn trương làm việc với các đơn vị cung cấp dịch vụ viễn thông khảo sát, kéo đường truyền mạng cáp quang Internet đến Trụ sở thôn Phước Chiến; đồng thời rà soát, cân đối nguồn ngân sách xã để trang bị bổ sung 01 bộ máy vi tính/máy tính bảng và 01 bộ bàn ghế làm việc phục vụ công tác trực tiếp dân, xử lý văn bản điện tử và thủ tục hành chính tại Trụ sở thôn Phước Chiến trước ngày 15/11/2026.",
            "- Chỉ đạo kiểm tra, bảo dưỡng và nâng cấp cụm loa truyền thanh tại thôn Ma Trai, bảo đảm truyền âm phủ khắp toàn thôn phục vụ kịp thời công tác thông tin, tuyên truyền các chủ trương, chính sách đến Nhân dân trước ngày 30/10/2026.",
            "- Chỉ đạo bộ phận Nông nghiệp, thú y xã thường xuyên cử cán bộ bám sát cơ sở, hướng dẫn người dân phòng chống dịch bệnh trên đàn gia súc, gia cầm (nhất là dịch cúm gia cầm tại thôn Phước Chiến); hướng dẫn lịch thời vụ và biện pháp tưới tiêu tiết kiệm nước trong điều kiện khô hạn.",
            "- Đẩy nhanh tiến độ giải ngân vốn và thực hiện có hiệu quả các dự án thuộc 03 Chương trình mục tiêu quốc gia (phát triển kinh tế - xã hội vùng đồng bào dân tộc thiểu số và miền núi, giảm nghèo bền vững, xây dựng nông thôn mới nâng cao); ưu tiên các chương trình hỗ trợ sinh kế, nhà ở cho hộ nghèo, cận nghèo tại 03 thôn.",
            "- Chỉ đạo Công an xã tăng cường tuần tra vũ trang ban đêm trên các tuyến đường liên thôn; phối hợp với Ban Quản lý thôn Động Thông xử lý nghiêm, triệt để tình trạng thanh thiếu niên điều khiển xe phân khối lớn, nẹt pô, chạy xe tốc độ cao gây mất trật tự an toàn giao thông, báo cáo kết quả xử lý cho Thường trực Đảng uỷ trước ngày 31/10/2026.",
            "- Chỉ đạo Trạm Y tế xã phối hợp với cấp uỷ, Ban Quản lý các thôn đổi mới hình thức tuyên truyền, tăng cường các đợt khám lưu động tại thôn nhằm nâng cao tỷ lệ người dân tham gia khám sức khoẻ sàng lọc miễn phí.",
            "3. Đối với Ban Xây dựng Đảng Đảng uỷ xã:",
            "- Hướng dẫn cụ thể quy trình, thủ tục, thẩm định hồ sơ nhân sự để Chi bộ thôn Động Thông và Chi bộ thôn Phước Chiến tiến hành bầu bổ sung cấp uỷ viên, kiện toàn chức danh Phó Bí thư Chi bộ hoàn thành trước ngày 31/10/2026.",
            "- Chủ trì, phối hợp với Văn phòng Đảng uỷ tham mưu Thường trực Đảng uỷ kế hoạch tổ chức lớp tập huấn nghiệp vụ công tác Đảng năm 2026 cho đội ngũ bí thư, phó bí thư, chi uỷ viên các chi bộ trực thuộc (trọng tâm là kỹ năng điều hành sinh hoạt chi bộ, nghiệp vụ quản lý đảng viên và hướng dẫn sử dụng Sổ tay đảng viên điện tử), thời gian thực hiện trong tháng 10/2026.",
            "- Thường xuyên theo dõi, đôn đốc các chi bộ hoàn thiện hồ sơ kết nạp đảng viên mới; kịp thời tháo gỡ khó khăn về thủ tục xác minh lý lịch người xin vào Đảng đối với các quần chúng ưu tú người đồng bào Raglai.",
            "4. Đối với Uỷ ban Kiểm tra Đảng uỷ xã:",
            "- Tăng cường công tác giám sát thường xuyên đối với các chi bộ trực thuộc, nhất là các chi bộ sau sáp nhập; tiếp tục hướng dẫn nghiệp vụ về công tác thu nộp, quản lý, sử dụng đảng phí và quản lý hồ sơ, sổ sách nghiệp vụ kiểm tra, giám sát bảo đảm chặt chẽ, đúng quy định.",
            "- Theo dõi, kiểm tra việc khắc phục các tồn tại, hạn chế của Chi bộ thôn Phước Chiến theo kết luận kiểm tra tài chính đảng vừa qua.",
            "5. Đối với Cơ quan Uỷ ban Mặt trận Tổ quốc Việt Nam và các tổ chức chính trị - xã hội xã:",
            "- Tiếp tục đổi mới nội dung, phương thức hoạt động; hướng dẫn củng cố, nâng cao chất lượng hoạt động của Ban Công tác Mặt trận và các chi hội đoàn thể tại 03 thôn.",
            "- Giao Đoàn Thanh niên xã khẩn trương xây dựng đội hình tình nguyện phối hợp với Ban Chi uỷ các thôn đến từng hộ gia đình đảng viên lớn tuổi để hướng dẫn, cài đặt, sử dụng Sổ tay đảng viên điện tử; đồng thời phối hợp với các chi hội đoàn thể tích cực vận động học sinh chưa ra lớp trở lại trường học.",
            "6. Đối với các đồng chí Uỷ viên Ban Thường vụ Đảng uỷ phụ trách địa bàn:",
            "- Thường xuyên bám sát địa bàn, chủ động dự sinh hoạt định kỳ tại các chi bộ được phân công phụ trách; kịp thời nắm bắt tình hình tư tưởng cán bộ, đảng viên và Nhân dân; trực tiếp chỉ đạo, tháo gỡ khó khăn, vướng mắc cho cơ sở.",
            "7. Đối với Văn phòng Đảng uỷ xã:",
            "- Đưa toàn bộ các nội dung kết luận nêu trên vào Hệ thống theo dõi, đôn đốc nhiệm vụ của Đảng uỷ xã; định kỳ hằng tuần tổng hợp, báo cáo Thường trực Đảng uỷ về tiến độ thực hiện.",
            "- Phối hợp chuẩn bị tốt các điều kiện tổ chức lớp tập huấn nghiệp vụ công tác Đảng theo phân công.",
            "Căn cứ Thông báo kết luận này, yêu cầu Chi uỷ Chi bộ các thôn: Động Thông, Ma Trai, Phước Chiến, Uỷ ban nhân dân xã, các cơ quan tham mưu, giúp việc Đảng uỷ và các đơn vị liên quan khẩn trương tổ chức triển khai thực hiện nghiêm túc, hiệu quả./."
        ],
        "noi_nhan": [
            "- Thường trực Tỉnh uỷ (để b/c);",
            "- Thường trực HĐND xã;",
            "- UBND xã;",
            "- Ban Xây dựng Đảng, UBKT Đảng uỷ;",
            "- Cơ quan UBMTTQVN và các tổ chức CT-XH xã;",
            "- Chi bộ các thôn: Động Thông, Ma Trai, Phước Chiến;",
            "- Các đồng chí UVBTV Đảng uỷ phụ trách địa bàn;",
            "- Lưu VPĐU."
        ],
        "tham_quyen": "T/M BAN THƯỜNG VỤ",
        "chuc_vu": "BÍ THƯ",
        "nguoi_ky": "Vũ Thị Thuỳ Trang"
    }

    out_path = os.path.join(base_dir, "van_ban_du_thao", "2026", "Thong_bao", "TB_Ket_luan_Thuong_truc_lam_viec_3_chi_bo_thon.docx")
    res = export_party_document(data, out_path)
    print("Exported successfully to:", res)

if __name__ == "__main__":
    generate_doc()
