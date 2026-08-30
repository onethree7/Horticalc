#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

#ifndef SourceDir
  #define SourceDir "..\..\dist\Horticalc"
#endif

#ifndef OutputDir
  #define OutputDir "..\.."
#endif

#ifndef OutputBaseFilename
  #define OutputBaseFilename "horticalc-windows-setup"
#endif

[Setup]
AppId={{50DF7813-DAE5-4976-8B13-6D677CF44660}
AppName=Horticalc
AppVersion={#AppVersion}
AppPublisher=Horticalc Open Source Project
AppPublisherURL=https://github.com/onethree7/Horticalc
AppSupportURL=https://github.com/onethree7/Horticalc/issues
AppUpdatesURL=https://github.com/onethree7/Horticalc/releases
DefaultDirName={localappdata}\Programs\Horticalc
DefaultGroupName=Horticalc
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir={#OutputDir}
OutputBaseFilename={#OutputBaseFilename}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
MinVersion=10.0
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile={#SourceDir}\..\..\assets\horticalc.ico
CloseApplications=yes
RestartApplications=no
UsePreviousAppDir=yes
DisableDirPage=auto
UsePreviousTasks=yes
Uninstallable=yes
CreateUninstallRegKey=yes
UninstallDisplayIcon={app}\Horticalc.exe
SetupLogging=yes

[InstallDelete]
Type: filesandordirs; Name: "{app}\_internal"
Type: filesandordirs; Name: "{app}\frontend"
Type: filesandordirs; Name: "{app}\data"
Type: filesandordirs; Name: "{app}\recipes"
Type: filesandordirs; Name: "{app}\user\webview\EBWebView\Default\Cache"
Type: filesandordirs; Name: "{app}\user\webview\EBWebView\Default\Code Cache"
Type: files; Name: "{app}\Horticalc.exe"
Type: files; Name: "{app}\README.txt"
Type: files; Name: "{app}\LICENSE"
Type: files; Name: "{group}\Horticalc.lnk"; Tasks: not startmenuicon
Type: files; Name: "{autodesktop}\Horticalc.lnk"; Tasks: not desktopicon

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
Name: "{app}\user"; Flags: uninsneveruninstall

[Tasks]
Name: "startmenuicon"; Description: "Create a Start Menu shortcut"; GroupDescription: "Shortcuts:"
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: unchecked

[Icons]
Name: "{group}\Horticalc"; Filename: "{app}\Horticalc.exe"; WorkingDir: "{app}"; Tasks: startmenuicon
Name: "{autodesktop}\Horticalc"; Filename: "{app}\Horticalc.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\Horticalc.exe"; Description: "Launch Horticalc"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"

[Code]
const
  UninstallKey = 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{50DF7813-DAE5-4976-8B13-6D677CF44660}_is1';

var
  MaintenancePage: TInputOptionWizardPage;
  ExistingInstallFound: Boolean;
  ExistingInstallPath: string;
  ExistingUninstaller: string;
  ExistingVersion: string;
  ExitAfterUninstall: Boolean;

function ExistingInstallation: Boolean;
begin
  ExistingInstallPath := '';
  ExistingUninstaller := '';
  ExistingVersion := '';
  Result := RegQueryStringValue(HKCU, UninstallKey, 'InstallLocation', ExistingInstallPath) and
    (ExistingInstallPath <> '');
  if Result then begin
    RegQueryStringValue(HKCU, UninstallKey, 'UninstallString', ExistingUninstaller);
    ExistingUninstaller := RemoveQuotes(ExistingUninstaller);
    RegQueryStringValue(HKCU, UninstallKey, 'DisplayVersion', ExistingVersion);
  end;
end;

procedure InitializeWizard;
var
  ExistingDescription: string;
begin
  ExistingInstallFound := ExistingInstallation;
  if not ExistingInstallFound then
    Exit;

  if ExistingVersion = '' then
    ExistingVersion := 'an earlier version';

  ExistingDescription :=
    'Setup found Horticalc ' + ExistingVersion + ' installed at:' + #13#10 +
    ExistingInstallPath + #13#10#13#10 +
    'Installing this version or uninstalling preserves the user folder and its saved data.';
  MaintenancePage := CreateInputOptionPage(wpWelcome,
    'Horticalc maintenance', 'Choose an installation action',
    ExistingDescription, True, False);
  MaintenancePage.Add('Install Horticalc version {#AppVersion}');
  MaintenancePage.Add('Uninstall Horticalc and close Setup');
  MaintenancePage.SelectedValueIndex := 0;
  WizardForm.DirEdit.Text := ExistingInstallPath;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := ExistingInstallFound and
    ((PageID = wpSelectDir) or
      ((MaintenancePage <> nil) and (PageID = MaintenancePage.ID) and
        WizardSilent));
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  if ExistingInstallFound then
    WizardForm.DirEdit.Text := ExistingInstallPath;
  if (MaintenancePage = nil) or (CurPageID <> MaintenancePage.ID) or
    (MaintenancePage.SelectedValueIndex <> 1) then
    Exit;

  Result := False;
  if (ExistingUninstaller = '') or not FileExists(ExistingUninstaller) then
  begin
    MsgBox('The registered Horticalc uninstaller could not be found. ' +
      'Installation remains available.', mbError, MB_OK);
    Exit;
  end;
  if MsgBox('Horticalc will be uninstalled from:' + #13#10 +
    ExistingInstallPath + #13#10#13#10 +
    'The user folder and its saved data will be preserved. Continue?',
    mbConfirmation, MB_YESNO) <> IDYES then
    Exit;

  ResultCode := 0;
  if not Exec(ExistingUninstaller, '/SILENT /NORESTART',
    ExistingInstallPath, SW_SHOWNORMAL, ewWaitUntilTerminated,
    ResultCode) then
  begin
    MsgBox('The Horticalc uninstaller could not be started.' + #13#10 +
      SysErrorMessage(ResultCode), mbError, MB_OK);
    Exit;
  end;
  if ResultCode <> 0 then
  begin
    MsgBox('Horticalc was not uninstalled. The uninstaller returned exit code ' +
      IntToStr(ResultCode) + '. Installation remains available.', mbError, MB_OK);
    Exit;
  end;

  ExitAfterUninstall := True;
  WizardForm.Close;
end;

procedure CancelButtonClick(CurPageID: Integer; var Cancel, Confirm: Boolean);
begin
  if ExitAfterUninstall then
  begin
    Cancel := True;
    Confirm := False;
  end;
end;
