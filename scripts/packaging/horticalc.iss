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

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
Name: "{app}\user"; Flags: uninsneveruninstall

[Icons]
Name: "{group}\Horticalc"; Filename: "{app}\Horticalc.exe"; WorkingDir: "{app}"

[Run]
Filename: "{app}\Horticalc.exe"; Description: "Launch Horticalc"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"
