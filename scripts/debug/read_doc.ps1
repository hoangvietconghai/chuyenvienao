$docPath = "D:\Chuyên viên ảo\van_ban_den\2026\12. TB KẾT LUẬN KIỂM TRA PCTNLPTC ĐỐI VỚI CB THÔN SUỐI GIẾNG.doc"
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $doc = $word.Documents.Open($docPath, $false, $true)
    $text = $doc.Content.Text
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    Write-Output $text
    
    # Also save as docx in a temp location for easy inspection with python-docx if needed
    $docxPath = "D:\Chuyên viên ảo\van_ban_den\2026\temp_converted.docx"
    $doc.SaveAs2($docxPath, 16) # 16 = wdFormatXMLDocument (docx)
    $doc.Close()
} catch {
    Write-Error $_
} finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
