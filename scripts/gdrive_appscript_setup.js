/**
 * GOOGLE APPS SCRIPT UPLOADER CHO THƯ MỤC GOOGLE DRIVE
 * ===================================================
 * Thư mục đích: https://drive.google.com/drive/folders/1IhUuenISqXs_KeSkWqSI_5423DNstxGF?usp=sharing
 * 
 * CÁCH CÀI ĐẶT (chỉ mất 1 phút):
 * 1. Truy cập https://script.google.com và bấm "Dự án mới" (New project).
 * 2. Dán toàn bộ mã nguồn bên dưới vào trình chỉnh sửa.
 * 3. Bấm "Triển khai" (Deploy) -> "Tùy chọn triển khai mới" (New deployment).
 * 4. Chọn loại: "Ứng dụng web" (Web app).
 * 5. Cấu hình:
 *    - Thực thi dưới dạng (Execute as): "Tôi" (Me - tài khoản Google của bạn)
 *    - Ai có quyền truy cập (Who has access): "Bất kỳ ai" (Anyone)
 * 6. Bấm "Triển khai" và cấp quyền truy cập khi được hỏi.
 * 7. Copy URL Ứng dụng web được tạo (dạng https://script.google.com/macros/s/.../exec)
 *    và dán vào biến GDRIVE_WEB_APP_URL trong tệp .env của dự án.
 */

function doPost(e) {
  try {
    const FOLDER_ID = '1IhUuenISqXs_KeSkWqSI_5423DNstxGF';
    const data = JSON.parse(e.postData.contents);
    const fileName = data.filename || ('van_ban_' + new Date().getTime() + '.docx');
    const base64Data = data.base64;
    const mimeType = data.mimetype || 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
    
    const decoded = Utilities.base64Decode(base64Data);
    const blob = Utilities.newBlob(decoded, mimeType, fileName);
    
    const folder = DriveApp.getFolderById(FOLDER_ID);
    const file = folder.createFile(blob);
    
    // Cấp quyền xem cho bất kỳ ai có link
    file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
    
    return ContentService.createTextOutput(JSON.stringify({
      status: 'success',
      file_id: file.getId(),
      file_url: file.getUrl(),
      download_url: 'https://drive.google.com/uc?export=download&id=' + file.getId()
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({
      status: 'error',
      message: err.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  return ContentService.createTextOutput(JSON.stringify({
    status: 'ok',
    message: 'Google Apps Script Uploader for Chuyen Vien Ao is active.'
  })).setMimeType(ContentService.MimeType.JSON);
}
