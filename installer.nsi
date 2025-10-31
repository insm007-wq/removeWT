; NSIS Installer Script for Watermark Removal System
; 자동 설치 (GPU 라이브러리 포함)

!include "MUI2.nsh"
!include "x64.nsh"
!include "WinVer.nsh"

; 기본 설정
Name "Watermark Removal System"
OutFile "WatermarkRemover_Installer.exe"
InstallDir "$PROGRAMFILES\WatermarkRemover"
InstallDirRegKey HKCU "Software\WatermarkRemover" ""

; 관리자 권한 요청
RequestExecutionLevel admin

; MUI Settings
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "Korean"

; 설치 섹션
Section "Install"
  SetOutPath "$INSTDIR"

  ; 프로그램 파일 복사
  File "dist\WatermarkRemover\*.*"
  File /r "dist\WatermarkRemover\*"

  ; 시작 메뉴 바로가기 생성
  CreateDirectory "$SMPROGRAMS\WatermarkRemover"
  CreateShortcut "$SMPROGRAMS\WatermarkRemover\Watermark Remover.lnk" "$INSTDIR\WatermarkRemover.exe"
  CreateShortcut "$SMPROGRAMS\WatermarkRemover\Uninstall.lnk" "$INSTDIR\Uninstall.exe"

  ; 바탕화면 바로가기
  CreateShortcut "$DESKTOP\Watermark Remover.lnk" "$INSTDIR\WatermarkRemover.exe"

  ; 제거 프로그램 등록
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WatermarkRemover" "DisplayName" "Watermark Removal System"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WatermarkRemover" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WatermarkRemover" "DisplayVersion" "1.0"

  ; GPU 의존성 자동 설치 스크립트 실행
  DetailPrint "Installing GPU dependencies... (This may take several minutes)"
  ExecWait "$INSTDIR\install_gpu_deps.bat"

  ; 언제성 메시지
  DetailPrint "Installation complete!"

SectionEnd

; 제거 섹션
Section "Uninstall"
  RMDir /r "$INSTDIR"
  RMDir /r "$SMPROGRAMS\WatermarkRemover"
  Delete "$DESKTOP\Watermark Remover.lnk"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WatermarkRemover"
SectionEnd
