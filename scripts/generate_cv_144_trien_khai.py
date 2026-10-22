# -*- coding: utf-8 -*-
"""
Script tạo file docx Công văn của Thường trực Đảng uỷ triển khai Kế hoạch 144-KH/ĐU
"""
import os
import sys

# Thêm đường dẫn thư mục gốc để import scripts.export_docx
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from scripts.export_docx import export_party_document

def generate_cv():
    output_docx = os.path.join(BASE_DIR, "van_ban_du_thao", "2026", "Cong_van", "CV triển khai KH 144 ĐU chuẩn hoá dữ liệu ĐV.docx")
    
    cv_data = {
        "doc_type": "CV",
        "so_hieu": "Số      -CV/ĐU",
        "dia_danh_ngay": "Công Hải, ngày 16 tháng 10 năm 2026",
        "co_quan_cap_tren": "ĐẢNG BỘ TỈNH KHÁNH HOÀ",
        "co_quan_ban_hanh": "ĐẢNG UỶ XÃ CÔNG HẢI",
        "trich_yeu": "Triển khai Kế hoạch số 144-KH/ĐU của\nBan Thường vụ Đảng uỷ về làm sạch,\nchuẩn hoá dữ liệu tổ chức đảng, đảng viên",
        "kinh_gui": [
            "Các cơ quan tham mưu, giúp việc Đảng uỷ xã;",
            "Uỷ ban nhân dân xã;",
            "Các chi bộ trực thuộc Đảng uỷ xã;",
            "Tổ hỗ trợ công nghệ thông tin và chuyển đổi số xã."
        ],
        "noi_dung": [
            "Thực hiện Kế hoạch số 144-KH/ĐU ngày 13/10/2026 của Ban Thường vụ Đảng uỷ xã về triển khai rà soát, làm sạch, chuẩn hóa, đối soát dữ liệu tổ chức đảng, đảng viên trong Đảng bộ xã Công Hải. Để bảo đảm hoàn thành chỉ tiêu tối thiểu 98% dữ liệu tổ chức đảng, đảng viên được làm sạch, chuẩn hóa, đối soát, đồng bộ trên Phần mềm Cơ sở dữ liệu đảng viên và Ứng dụng Sổ tay đảng viên điện tử trước ngày 20/11/2026; Thường trực Đảng uỷ yêu cầu các cơ quan, đơn vị, các chi bộ trực thuộc và các tổ chức, cá nhân liên quan khẩn trương triển khai thực hiện tốt một số nội dung trọng tâm sau:",
            
            "**1. Các chi bộ trực thuộc Đảng uỷ xã:**",
            "- Bí thư chi bộ trực tiếp lãnh đạo, chỉ đạo, tổ chức quán triệt sâu sắc mục đích, yêu cầu và các mốc tiến độ của Kế hoạch số 144-KH/ĐU đến 100% đảng viên trong chi bộ; chịu trách nhiệm toàn diện trước Thường trực, Ban Thường vụ Đảng uỷ xã về tiến độ, chất lượng và tính chính xác của dữ liệu đảng viên thuộc phạm vi quản lý.",
            "- Khẩn trương phối hợp với Ban Xây dựng Đảng hoàn thành việc phân loại 05 nhóm đảng viên trên hệ thống; đôn đốc 100% đảng viên đủ điều kiện (thuộc Nhóm 1) hoàn thành tự kê khai, cập nhật, bổ sung thông tin trên Ứng dụng Sổ tay đảng viên điện tử trước ngày 20/10/2026.",
            "- Phân công cấp uỷ viên, đảng viên có kỹ năng sử dụng thiết bị số trực tiếp hỗ trợ các trường hợp đảng viên cao tuổi, sức khoẻ yếu, miễn công tác và sinh hoạt đảng hoặc không có điều kiện sử dụng thiết bị số (Nhóm 2, 3, 4); trường hợp cần thiết bố trí đến hỗ trợ trực tiếp tại nơi cư trú, bảo đảm an toàn và bảo mật thông tin cá nhân.",
            "- Chi bộ tổ chức kiểm tra, đối chiếu thông tin đảng viên kê khai với hồ sơ đảng viên gốc, thực hiện xác nhận dữ liệu trên hệ thống trước ngày 30/10/2026; Bí thư chi bộ hoàn thành phê duyệt (hoặc ký số) dữ liệu trước ngày 10/11/2026.",
            "- Đối với Chi bộ Quân sự xã và Chi bộ Công an xã: Quán triệt thực hiện nghiêm túc quy định về bảo mật; hướng dẫn đảng viên bổ sung lý lịch theo Mẫu SYLL-2c/TW-2026 (ban hành kèm theo Quy định số 211-QĐ/TW ngày 07/8/2026 của Ban Bí thư); cử cấp uỷ viên hoặc đảng viên tổng hợp hồ sơ đến trực tiếp Ban Xây dựng Đảng để rà soát, cập nhật, tuyệt đối không kê khai trực tiếp trên ứng dụng công cộng.",
            "- Thực hiện nghiêm túc chế độ báo cáo tiến độ định kỳ về Ban Xây dựng Đảng trước 15 giờ 00 thứ Tư hằng tuần (trong tháng 10 và tháng 11/2026).",
            
            "**2. Đối với các chi bộ thôn:**",
            "- Phối hợp chặt chẽ, đồng bộ với Tổ hỗ trợ công nghệ thông tin và chuyển đổi số Đảng uỷ xã theo Lịch trình triển khai tại từng địa bàn thôn (cụ thể: Thôn Kà Rôm ngày 24/10; Thôn Suối Vang ngày 25/10; Thôn Bình Tiên ngày 26/10; Thôn Hiệp Kiết ngày 27 - 28/10; Thôn Suối Giếng ngày 29 - 30/10; Thôn Ma Trai ngày 02/11; Thôn Phước Chiến ngày 03 - 04/11; Thôn Động Thông ngày 05 - 06/11/2026).",
            "- Bí thư chi bộ chủ động chuẩn bị đầy đủ cơ sở vật chất tại Nhà văn hoá thôn (hoặc Nhà sinh hoạt cộng đồng); thông báo lịch làm việc cụ thể và huy động toàn thể đảng viên trong chi bộ có mặt theo đúng khung giờ để Tổ hỗ trợ trực tiếp hướng dẫn cài đặt ứng dụng, chuẩn hoá dữ liệu, đối soát thẻ Đảng, căn cước công dân và chụp ảnh thẻ đúng quy chuẩn phông trắng.",
            "- Đối với các thôn sau sáp nhập (Kà Rôm, Hiệp Kiết, Suối Giếng, Phước Chiến, Động Thông): Chi uỷ chi bộ tập trung rà soát kỹ danh sách biến động đảng viên, phối hợp xử lý khớp nối giữa hồ sơ giấy và tài khoản đảng viên điện tử, bảo đảm 100% đảng viên sau sáp nhập được kích hoạt tài khoản và phân quyền sinh hoạt đúng quy định.",
            "- Huy động lực lượng đoàn viên thanh niên chi đoàn thôn phối hợp với thành viên Tổ hỗ trợ thành lập các nhóm lưu động đến tận nhà hỗ trợ đối với đảng viên già yếu, neo đơn, đi lại khó khăn.",
            
            "**3. Giao Tổ hỗ trợ công nghệ thông tin và chuyển đổi số Đảng uỷ xã:**",
            "- Căn cứ Quyết định số 98-QĐ/ĐU ngày 30/6/2026 của Ban Thường vụ Đảng uỷ xã và Bảng phân công nhiệm vụ đã được phê duyệt, khẩn trương kích hoạt 03 Tổ công tác; phân công nhiệm vụ cụ thể cho từng thành viên, chủ động liên hệ với Chi uỷ các chi bộ thôn để thống nhất phương án, chuẩn bị hạ tầng kỹ thuật phục vụ hướng dẫn trực tiếp.",
            "- Chuẩn bị đầy đủ thiết bị kỹ thuật (máy tính xách tay, thiết bị phát wifi di động 4G/5G, phông chụp ảnh thẻ...), tài liệu hướng dẫn trực quan; trực tiếp hướng dẫn \"cầm tay chỉ việc\", hỗ trợ đảng viên cài đặt ứng dụng, thao tác cập nhật dữ liệu; kiểm tra sơ bộ tính đầy đủ, chính xác của thông tin trước khi chuyển chi bộ xác nhận.",
            "- Đặc biệt tăng cường lực lượng cho Tổ công tác số 3 phụ trách khối 03 thôn miền núi, đồng bào dân tộc thiểu số Raglai (Ma Trai, Phước Chiến, Động Thông); bố trí cán bộ biết tiếng Raglai phối hợp hướng dẫn, giải quyết khó khăn về thiết bị thông minh và đường truyền internet.",
            "- Phối hợp chặt chẽ với Ban Xây dựng Đảng xử lý kịp thời các lỗi kỹ thuật phần mềm, vướng mắc phát sinh trong quá trình đồng bộ và ký số dữ liệu.",
            
            "**4. Ban Xây dựng Đảng Đảng uỷ xã:**",
            "- Chủ trì theo dõi, đôn đốc tiến độ thực hiện Kế hoạch số 144-KH/ĐU; hướng dẫn nghiệp vụ công tác đảng viên, quy trình thẩm định, đối soát giữa dữ liệu số với hồ sơ đảng viên gốc cho các chi bộ và Tổ hỗ trợ CNTT & CĐS.",
            "- Thiết lập biểu theo dõi tiến độ chi tiết từng ngày của 23 chi bộ trực thuộc; tham mưu Thường trực Đảng uỷ xã tổ chức kiểm tra chéo, kiểm tra đột xuất đối với những đơn vị có tiến độ chậm hoặc tỷ lệ sai lệch cao; định kỳ tổng hợp báo cáo Thường trực Đảng uỷ và Ban Tổ chức Tỉnh uỷ theo quy định.",
            "- Hoàn thành công tác thẩm định, phê duyệt và đồng bộ 100% dữ liệu tổ chức đảng, đảng viên của toàn Đảng bộ xã trước ngày 20/11/2026.",
            
            "**5. Uỷ ban nhân dân xã và các tổ chức chính trị - xã hội xã:**",
            "- Uỷ ban nhân dân xã chỉ đạo các bộ phận chuyên môn phối hợp với Công an xã rà soát, đối soát thông tin dữ liệu dân cư (VNeID mức 2) phục vụ việc chuẩn hoá thông tin đảng viên theo Đề án 06 của Chính phủ; bảo đảm điều kiện cơ sở vật chất tại Nhà văn hoá các thôn phục vụ Tổ hỗ trợ làm việc.",
            "- Đoàn Thanh niên xã cử lực lượng đoàn viên thanh niên nòng cốt, am hiểu công nghệ tham gia phối hợp với Tổ hỗ trợ CNTT & CĐS và các chi bộ thôn để hỗ trợ người cao tuổi, đảng viên khó khăn về thao tác kỹ thuật số.",
            
            "**6. Văn phòng Đảng uỷ xã:**",
            "- Bảo đảm đầy đủ kinh phí, phương tiện di chuyển, văn phòng phẩm và hạ tầng kỹ thuật cần thiết cho Tổ hỗ trợ CNTT & CĐS hoàn thành tốt nhiệm vụ được giao.",
            "- Theo dõi, giám sát chặt chẽ việc chấp hành chế độ thông tin, báo cáo của các chi bộ; kịp thời tham mưu Thường trực Đảng uỷ chỉ đạo, chấn chỉnh các trường hợp thực hiện chưa nghiêm túc.",
            
            "Thường trực Đảng uỷ yêu cầu các cơ quan, đơn vị, các chi bộ trực thuộc và Tổ hỗ trợ công nghệ thông tin và chuyển đổi số Đảng uỷ xã nghiêm túc, khẩn trương triển khai thực hiện./.",
            
            "*(Đính kèm Kế hoạch số 144-KH/ĐU ngày 13/10/2026 của Ban Thường vụ Đảng uỷ xã và Bảng phân công nhiệm vụ Tổ hỗ trợ CNTT và CĐS)./.*"
        ],
        "noi_nhan": [
            "- Ban Tổ chức Tỉnh uỷ (b/c);",
            "- Ban Thường vụ Đảng uỷ (b/c);",
            "- Đ/c Lương Đức Hải - UVTV Tỉnh uỷ phụ trách địa bàn (b/c);",
            "- Các đ/c Đảng uỷ viên phụ trách địa bàn (để đôn đốc);",
            "- Như kính gửi (để t/h);",
            "- Lưu VPĐU."
        ],
        "tham_quyen": "T/M BAN THƯỜNG VỤ",
        "chuc_vu": "PHÓ BÍ THƯ",
        "nguoi_ky": "Nguyễn Xuân Hoàng"
    }

    res_path = export_party_document(cv_data, output_docx)
    print(f"File created successfully at: {res_path}")

if __name__ == "__main__":
    generate_cv()
