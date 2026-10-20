param([string]$DocumentDirectory = (Join-Path $PSScriptRoot '..\whitepapers'))
$ErrorActionPreference = 'Stop'
$wordApp = $null
try {
    $wordApp = New-Object -ComObject Word.Application
    $wordApp.Visible = $false
    $wordApp.DisplayAlerts = 0
    foreach ($inputFile in (Get-ChildItem -LiteralPath $DocumentDirectory -Filter '*.docx')) {
        $wordDoc = $null
        try {
            $wordDoc = $wordApp.Documents.Open($inputFile.FullName, $false, $false)
            $wordDoc.Fields.Update() | Out-Null
            $wordDoc.Repaginate()
            foreach ($toc in $wordDoc.TablesOfContents) {
                $toc.Update()
                $toc.Range.Font.Size = 10
                $toc.Range.ParagraphFormat.SpaceBefore = 0
                $toc.Range.ParagraphFormat.SpaceAfter = 2
                $toc.Range.ParagraphFormat.LineSpacingRule = 4
                $toc.Range.ParagraphFormat.LineSpacing = 14
            }
            $wordDoc.Repaginate()
            foreach ($toc in $wordDoc.TablesOfContents) { $toc.UpdatePageNumbers() }
            $wordDoc.Save()
            $pdfPath = [System.IO.Path]::ChangeExtension($inputFile.FullName, '.pdf')
            $wordDoc.ExportAsFixedFormat($pdfPath, 17)
            Write-Output $pdfPath
        } finally {
            if ($null -ne $wordDoc) { $wordDoc.Close(0) }
        }
    }
} finally {
    if ($null -ne $wordApp) { $wordApp.Quit() }
}
