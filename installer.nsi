; NSIS Installer Script for Watermark Removal System
; Simplified version to avoid compiler issues

!include "MUI2.nsh"

Name "Watermark Removal System"
OutFile "WatermarkRemover_Installer.exe"
InstallDir "$PROGRAMFILES\WatermarkRemover"
RequestExecutionLevel admin

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

Section "Install"
  SetOutPath "$INSTDIR"

  ; Copy executable
  File "dist\WatermarkRemover\WatermarkRemover.exe"

  ; Copy _internal dependencies
  SetOutPath "$INSTDIR\_internal"
  File /r "dist\WatermarkRemover\_internal"

  SetOutPath "$INSTDIR"

  ; Copy FFmpeg if exists
  ${If} ${FileExists} "ffmpeg\ffmpeg.exe"
    SetOutPath "$INSTDIR\ffmpeg"
    File "ffmpeg\ffmpeg.exe"
    File "ffmpeg\ffprobe.exe"
  ${EndIf}

  ; Copy models if exists
  ${If} ${FileExists} "models\best.pt"
    SetOutPath "$INSTDIR\models"
    File "models\best.pt"
  ${EndIf}

  ; Create directories
  SetOutPath "$INSTDIR"
  CreateDirectory "$INSTDIR\output"
  CreateDirectory "$INSTDIR\temp"
  CreateDirectory "$INSTDIR\logs"

  ; Create shortcuts
  CreateDirectory "$SMPROGRAMS\WatermarkRemover"
  CreateShortCut "$SMPROGRAMS\WatermarkRemover\Watermark Remover.lnk" "$INSTDIR\WatermarkRemover.exe"
  CreateShortCut "$SMPROGRAMS\WatermarkRemover\Uninstall.lnk" "$INSTDIR\uninstall.exe"
  CreateShortCut "$DESKTOP\Watermark Remover.lnk" "$INSTDIR\WatermarkRemover.exe"

  ; Create uninstaller
  WriteUninstaller "$INSTDIR\uninstall.exe"

  ; Registry
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\WatermarkRemover" "DisplayName" "Watermark Removal System"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\WatermarkRemover" "UninstallString" "$INSTDIR\uninstall.exe"

  MessageBox MB_OK "Installation completed!"

SectionEnd

Section "Uninstall"
  Delete "$SMPROGRAMS\WatermarkRemover\*.*"
  RMDir "$SMPROGRAMS\WatermarkRemover"
  Delete "$DESKTOP\Watermark Remover.lnk"
  RMDir /r "$INSTDIR"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\WatermarkRemover"
  MessageBox MB_OK "Uninstall completed!"
SectionEnd
