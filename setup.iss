[Setup]
AppName=PyEaseRecoiler
AppVersion=2.0.1
DefaultDirName={pf}\PyEaseRecoiler
OutputDir=installer
OutputBaseFilename=PyEaseRecoiler_Setup
Compression=lzma2
PrivilegesRequired=admin

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
; 将所在文件夹下的所有文件复制到目标安装目录
Source: "*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs


[Icons]
; 为 PyEaseRecoiler.exe 做快捷方式
Name: "{userdesktop}\PyEaseRecoiler"; Filename: "{app}\PyEaseRecoiler\dist\PyEaseRecoiler.exe"

[Run]
; 在安装过程中运行 VC_redist.x64.exe
Filename: "{app}\VC_redist.x64.exe"; Parameters: "/install /quiet /norestart"; StatusMsg: "正在安装 Visual C++ 运行库..."; Flags: runhidden