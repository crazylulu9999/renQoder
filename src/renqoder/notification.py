import subprocess
import sys
import os
import traceback

# 개발 모드인지 확인 (exe로 빌드되면 sys.frozen이 True가 됨)
# 따라서 frozen이 없으면 개발 모드(True), 있으면 배포 모드(False)
IS_DEV = not getattr(sys, 'frozen', False)

def show_toast(title, message, icon_path=None):
    """
    윈도우 10/11에서 Toast 알림을 표시합니다.
    win10toast 라이브러리를 우선 사용하고, 실패 시 PowerShell로 폴백합니다.
    """
    if sys.platform != "win32":
        return

    # 1. win10toast 라이브러리 시도
    try:
        from win10toast import ToastNotifier
        
        toaster = ToastNotifier()
        
        # 아이콘 경로 설정
        # win10toast는 .ico 파일만 지원하므로 .png를 .ico로 변경
        icon = None
        if icon_path:
            # Path 객체를 문자열로 변환
            icon_path_str = str(icon_path)
            if os.path.exists(icon_path_str):
                if icon_path_str.endswith('.png'):
                    # .png를 .ico로 변경 시도
                    ico_path = icon_path_str.replace('.png', '.ico')
                    if os.path.exists(ico_path):
                        icon = ico_path
                    else:
                        icon = icon_path_str  # .ico가 없으면 .png 시도 (실패할 수 있음)
                else:
                    icon = icon_path_str
        
        # Toast 알림 표시
        # threaded=True로 설정하여 비동기 실행
        toaster.show_toast(
            title=title,
            msg=message,
            icon_path=icon,
            duration=5,  # 5초간 표시
            threaded=True
        )
        return
        
    except ImportError:
        # win10toast가 설치되지 않은 경우 PowerShell 폴백
        print("win10toast가 설치되지 않은 경우 PowerShell로 폴백합니다.")
        pass
    except Exception as e:
        # win10toast 실행 실패 시 PowerShell 폴백
        if IS_DEV:
            traceback.print_exc()
        print(f"win10toast 실패: {e}, PowerShell로 폴백합니다.")
    
    # 2. PowerShell 폴백
    template_type = "ToastText02"
    image_logic = ""
    
    if icon_path:
        # Path 객체를 문자열로 변환
        icon_path_str = str(icon_path)
        if os.path.exists(icon_path_str):
            abs_path = os.path.abspath(icon_path_str).replace("\\", "/")
            if not abs_path.startswith("/"):
                abs_path = "/" + abs_path
            icon_uri = f"file://{abs_path}"
            
            template_type = "ToastImageAndText02"
            image_logic = f"""
            $imageNodes = $template.GetElementsByTagName("image")
            if ($imageNodes.Count -gt 0) {{
                $imageNodes[0].SetAttribute("src", "{icon_uri}") | Out-Null
            }}
            """

    ps_script = f"""
    $ErrorActionPreference = 'SilentlyContinue'
    
    try {{
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null
        
        $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::{template_type})
        
        $textNodes = $template.GetElementsByTagName("text")
        $textNodes[0].AppendChild($template.CreateTextNode("{title}")) | Out-Null
        $textNodes[1].AppendChild($template.CreateTextNode("{message}")) | Out-Null
        
        {image_logic}
        
        $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
        $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Microsoft.Windows.PowerShell")
        $notifier.Show($toast)
    }} catch {{
        # Toast 실패 시 BalloonTip 폴백
        Add-Type -AssemblyName System.Windows.Forms
        $notify = New-Object System.Windows.Forms.NotifyIcon
        $notify.Icon = [System.Drawing.SystemIcons]::Information
        $notify.Visible = $true
        $notify.ShowBalloonTip(5000, "{title}", "{message}", [System.Windows.Forms.ToolTipIcon]::Info)
        Start-Sleep -Seconds 1
        $notify.Dispose()
    }}
    """

    startupinfo = None
    if sys.platform == 'win32':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    try:
        subprocess.run(
            ["powershell", "-Command", ps_script],
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
            check=False
        )
    except Exception as e:
        print(f"알림 오류: {e}")
