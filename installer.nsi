; NSIS Installer Script for Watermark Removal System
; Full Installer with all dependencies included

!include "MUI2.nsh"
!include "x64.nsh"

; Basic Settings
Name "Watermark Removal System"
OutFile "WatermarkRemover_Installer.exe"
InstallDir "$PROGRAMFILES\WatermarkRemover"
InstallDirRegKey HKLM "Software\WatermarkRemover" ""
RequestExecutionLevel admin

; MUI Settings
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

; Constants
!define PRODUCT_NAME "Watermark Removal System"
!define PRODUCT_VERSION "1.0"
!define PRODUCT_PUBLISHER "WatermarkRemover"
!define PRODUCT_WEB_SITE "https://github.com/linkedlist771/SoraWatermarkCleaner"

; Installer Sections
Section "Install"
  SetOutPath "$INSTDIR"

  ; Check if dist folder exists
  ${If} ${FileExists} "dist\WatermarkRemover\WatermarkRemover.exe"
    ; Copy main executable
    File "dist\WatermarkRemover\WatermarkRemover.exe"

    ; Copy _internal folder with all dependencies
    SetOutPath "$INSTDIR\_internal"
    File /r "dist\WatermarkRemover\_internal\*.*"

    ; Go back to install dir for other folders
    SetOutPath "$INSTDIR"
  ${Else}
    MessageBox MB_ICONEXCLAMATION "Error: WatermarkRemover.exe not found!$\n$\nPlease run PyInstaller first:$\npython -m PyInstaller watermark_remover.spec"
    Abort
  ${EndIf}

  ; Copy FFmpeg binaries
  ${If} ${FileExists} "ffmpeg\ffmpeg.exe"
    SetOutPath "$INSTDIR\ffmpeg"
    File "ffmpeg\ffmpeg.exe"
    File "ffmpeg\ffprobe.exe"
  ${Else}
    MessageBox MB_ICONEXCLAMATION "Warning: FFmpeg binaries not found!$\n$\nFFmpeg is required for video processing.$\nPlease run install.bat to download FFmpeg."
  ${EndIf}

  ; Copy YOLO model
  ${If} ${FileExists} "models\best.pt"
    SetOutPath "$INSTDIR\models"
    File "models\best.pt"
  ${Else}
    MessageBox MB_ICONEXCLAMATION "Warning: YOLO model not found!$\n$\nLocal GPU mode will not be available.$\nYou can still use API mode (Replicate)."
  ${EndIf}

  ; Create empty runtime directories
  CreateDirectory "$INSTDIR\output"
  CreateDirectory "$INSTDIR\temp"
  CreateDirectory "$INSTDIR\logs"

  ; Create Start Menu Shortcuts
  CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\Watermark Remover.lnk" "$INSTDIR\WatermarkRemover.exe" "" "$INSTDIR\WatermarkRemover.exe" 0
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk" "$INSTDIR\uninstall.exe"

  ; Create Desktop Shortcut
  CreateShortCut "$DESKTOP\Watermark Remover.lnk" "$INSTDIR\WatermarkRemover.exe" "" "$INSTDIR\WatermarkRemover.exe" 0

  ; Write uninstaller
  WriteUninstaller "$INSTDIR\uninstall.exe"

  ; Write registry keys for Add/Remove Programs
  WriteRegStr HKLM "Software\${PRODUCT_NAME}" "" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "UninstallString" "$INSTDIR\uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "Publisher" "${PRODUCT_PUBLISHER}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "InstallLocation" "$INSTDIR"

  ; Show success message
  MessageBox MB_OK "Installation completed successfully!$\n$\nWatermark Removal System is ready to use.$\n$\nYou can launch it from:$\n- Start Menu$\n- Desktop Shortcut"

SectionEnd

; Uninstaller Section
Section "Uninstall"

  ; Remove shortcuts
  Delete "$SMPROGRAMS\${PRODUCT_NAME}\Watermark Remover.lnk"
  Delete "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk"
  RMDir "$SMPROGRAMS\${PRODUCT_NAME}"
  Delete "$DESKTOP\Watermark Remover.lnk"

  ; Remove all installed files and folders
  RMDir /r "$INSTDIR"

  ; Remove registry keys
  DeleteRegKey HKLM "Software\${PRODUCT_NAME}"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"

  MessageBox MB_OK "Uninstall completed!"

SectionEnd
