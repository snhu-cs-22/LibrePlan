;--------------------------------

; Includes

!include "MUI2.nsh"
!include "logiclib.nsh"

;--------------------------------

; Custom defines

!define NAME "LibrePlan"
!define APPFILE "$INSTDIR\${NAME}.exe"
!define VERSION ""
!define SLUG "${NAME} v${VERSION}"

!define INSTALLERFILE "dist\${NAME}-${VERSION}-windows.exe"
!define UNINSTALLERFILE "$INSTDIR\uninstall.exe"

;--------------------------------

; Defines

Name "${NAME}"
OutFile "${INSTALLERFILE}"
RequestExecutionLevel admin
Unicode True
InstallDir $PROGRAMFILES\${NAME}
InstallDirRegKey HKLM "Software\${NAME}" "Install_Dir"

;--------------------------------

; UI

; !define MUI_ICON "resources\icon.png"
; !define MUI_HEADERIMAGE
; !define MUI_HEADERIMAGE_BITMAP "${MUI_ICON}"
!define MUI_ABORTWARNING
!define MUI_WELCOMEPAGE_TITLE "Welcome to the ${SLUG} Setup!"

;--------------------------------

; Pages

; Installer pages
!insertmacro MUI_PAGE_WELCOME
; !insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Set UI language
!insertmacro MUI_LANGUAGE "English"

;--------------------------------

; Sections

Section "${NAME}" Package

  SectionIn RO

  ; Set output path to the installation directory.
  SetOutPath $INSTDIR

  ; Put files under dist\${NAME} in the install directory
  File /r "dist\${NAME}\*"

  ; Create directories in AppData
  CreateDirectory "$APPDATA\${NAME}"
  CreateDirectory "$APPDATA\${NAME}\backups"

  ; Write the installation path into the registry
  WriteRegStr HKLM SOFTWARE\${NAME} "Install_Dir" "$INSTDIR"

  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NAME}" "DisplayName" "${NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NAME}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NAME}" "UninstallString" '"${UNINSTALLERFILE}"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NAME}" "QuietUninstallString" '"${UNINSTALLERFILE}" /S'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NAME}" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NAME}" "NoRepair" 1

  WriteUninstaller "${UNINSTALLERFILE}"

SectionEnd

Section /o "Start Menu Shortcuts" StartShort

  CreateDirectory "$SMPROGRAMS\${NAME}"
  CreateShortcut "$SMPROGRAMS\${NAME}\${NAME}.lnk" "${APPFILE}"
  CreateShortcut "$SMPROGRAMS\${NAME}\Uninstall ${NAME}.lnk" "${UNINSTALLERFILE}"

SectionEnd

Section /o "Desktop Shortcut" DeskShort

  CreateShortcut "$DESKTOP\${NAME}.lnk" "${APPFILE}"

SectionEnd

;--------------------------------

; Descriptions

; Language strings
LangString DESC_Package ${LANG_ENGLISH} "The full ${NAME} package."
LangString DESC_DeskShort ${LANG_ENGLISH} "Create a shortcut to ${NAME} on the Desktop."
LangString DESC_StartShort ${LANG_ENGLISH} "Create $\"${NAME}$\" and $\"Uninstall ${NAME}$\" shortcuts in the Start Menu."

; Assign language strings to sections
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
!insertmacro MUI_DESCRIPTION_TEXT ${Package} $(DESC_Package)
!insertmacro MUI_DESCRIPTION_TEXT ${DeskShort} $(DESC_DeskShort)
!insertmacro MUI_DESCRIPTION_TEXT ${StartShort} $(DESC_StartShort)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

;--------------------------------

; Uninstaller

Section "Uninstall"

  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NAME}"
  DeleteRegKey HKLM SOFTWARE\${NAME}

  Delete "$DESKTOP\${NAME}.lnk" ; Remove desktop shortcut
  RMDir /r "$SMPROGRAMS\${NAME}" ; Remove Start Menu folder
  RMDir /r "$INSTDIR" ; Remove files and uninstaller

SectionEnd
