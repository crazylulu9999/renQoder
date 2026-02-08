"""
renQoder - Smart Video Transcoder
PoC 버전
"""

import sys
import os
import webbrowser
import json
import shutil
import threading
import ctypes
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
import send2trash

import customtkinter as ctk
from PIL import Image

IS_DEV = not getattr(sys, 'frozen', False)

# 모듈 경로 문제 해결
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from hardware_detector import HardwareDetector, check_ffmpeg
from encoder import VideoEncoder
from taskbar import TaskbarController
from notification import show_toast
from __init__ import __version__

# 테마 설정
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ToolTip:
    """마우스 오버 시 정보를 보여주는 툴팁 클래스"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return
        
        # 툴팁 위치 계산 (위젯 하단)
        x = self.widget.winfo_rootx() + 10
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
        
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True) # 테두리 제거
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True) # 항상 위에
        
        # 배경색과 폰트 설정
        label = tk.Label(tw, text=self.text, justify='left',
                       background="#2b2b2b", foreground="#dddddd",
                       relief='solid', borderwidth=1,
                       font=("Malgun Gothic", 9), padx=10, pady=8)
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

class MainWindow(ctk.CTk):
    """메인 윈도우"""
    
    def __init__(self):
        super().__init__()
        
        # Windows에서 작업표시줄 아이콘이 올바르게 표시되도록 설정
        if sys.platform == "win32":
            myappid = 'crazylulu.renqoder.transcoder.v1'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        
        # 하드웨어 감지
        self.detector = HardwareDetector()
        self.detector.detect_gpu()
        
        # 인코더 초기화
        encoder_info = self.detector.get_encoder_info()
        self.encoder = VideoEncoder(encoder_info['encoder'])
        self.accent_color = self.detector.get_accent_color()
        
        # 변수
        self.input_file = None
        self.output_file = None
        self.estimated_size_bytes = 0
        self.encoding_in_progress = False
        self.taskbar = None
        
        # 설정 파일 경로
        self.config_file = Path.home() / '.renqoder_config.json'
        
        # UI 초기화
        self.init_ui()
        
        # 작업표시줄 컨트롤러 초기화 (Windows 전용)
        if sys.platform == "win32":
            self.after(500, self.init_taskbar)
        
        # 설정 로드 및 적용
        self.load_settings()
        
        self.log("renQoder 초기화 완료")
        self.log(f"감지된 인코더: {encoder_info['name']}")

    def get_resource_path(self, relative_path):
        """리소스 파일의 실제 경로를 가져옵니다"""
        if hasattr(sys, '_MEIPASS'):
            return Path(sys._MEIPASS) / relative_path
        return Path(__file__).parent / relative_path

    def init_ui(self):
        """UI 구성"""
        self.title(f"renQoder v{__version__} - Smart Video Transcoder")
        self.geometry("700x800")
        
        # 아이콘 설정 (.ico 파일 우선 사용)
        ico_rel_path = "resources/icon.ico"
        icon_path = self.get_resource_path(ico_rel_path)
        if icon_path.exists():
            try:
                self.after(200, lambda: self.wm_iconbitmap(str(icon_path)))
                print(f"✓ 윈도우 아이콘 로드 성공: {icon_path}")
            except Exception as e:
                print(f"✗ 아이콘 로드 오류: {e}")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 메인 프레임 (스크롤바 제거를 위해 일반 프레임으로 변경)
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(7, weight=1)

        # 1. 헤더 (로고, 타이틀 & 슬로건)
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, pady=(0, 15))
        
        # 로고 아이콘 추가
        icon_png_path = self.get_resource_path("resources/icon.png")
        if icon_png_path.exists():
            try:
                img = Image.open(icon_png_path)
                # 고해상도 이미지를 적절한 크기(64x64)로 변환
                self.logo_image = ctk.CTkImage(light_image=img, dark_image=img, size=(64, 64))
                self.logo_label = ctk.CTkLabel(self.header_frame, image=self.logo_image, text="")
                self.logo_label.pack(side="left", padx=(0, 20))
            except Exception as e:
                print(f"헤더 로고 로드 오류: {e}")

        # 텍스트 프레임 (타이틀 & 슬로건)
        self.header_text_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.header_text_frame.pack(side="left", padx=0)
        
        self.title_label = ctk.CTkLabel(
            self.header_text_frame, 
            text="renQoder", 
            font=ctk.CTkFont(size=32, weight="bold"),
            anchor="w"
        )
        self.title_label.pack(fill="x")
        
        self.slogan_label = ctk.CTkLabel(
            self.header_text_frame, 
            text="Smart Render, Slim Storage.", 
            text_color="#888888",
            font=ctk.CTkFont(size=14),
            anchor="w"
        )
        self.slogan_label.pack(fill="x")

        # 링크 버튼 프레임 (우측 끝, 2행 배치)
        self.links_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.links_frame.pack(side="right", padx=(40, 0))
        
        # GitHub 링크 버튼
        self.github_btn = ctk.CTkButton(
            self.links_frame,
            text="GitHub",
            width=100,
            height=22,
            font=ctk.CTkFont(size=11),
            fg_color="#333",
            hover_color="#444",
            command=lambda: webbrowser.open("https://github.com/crazylulu9999/renQoder")
        )
        self.github_btn.pack(side="top", pady=(0, 5))
        
        # FFmpeg 링크 버튼
        self.ffmpeg_site_btn = ctk.CTkButton(
            self.links_frame,
            text="FFmpeg",
            width=100,
            height=22,
            font=ctk.CTkFont(size=11),
            fg_color="#333",
            hover_color="#444",
            command=lambda: webbrowser.open("https://www.ffmpeg.org/")
        )
        self.ffmpeg_site_btn.pack(side="top", pady=(0, 5))

        # 알림 테스트 버튼
        if IS_DEV:
            self.test_notify_btn = ctk.CTkButton(
                self.links_frame,
                text="🔔 알림 테스트",
                width=100,
                height=22,
                font=ctk.CTkFont(size=11),
                fg_color="#333",
                hover_color="#444",
                command=self.test_notification
            )
            self.test_notify_btn.pack(side="top")

        # 2. GPU 정보
        encoder_info = self.detector.get_encoder_info()
        self.gpu_info_label = ctk.CTkLabel(
            self.main_frame,
            text=f"🎮 감지된 GPU: {encoder_info['vendor']} ({encoder_info['name']})",
            text_color=self.accent_color,
            font=ctk.CTkFont(weight="bold")
        )
        self.gpu_info_label.grid(row=2, column=0, pady=(0, 15))

        # 3. 입력 파일 및 출력 파일 섹션
        self.files_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.files_container.grid(row=1, column=0, pady=(0, 15), sticky="ew")
        self.files_container.grid_columnconfigure(0, weight=1)

        # 입력 파일
        self.file_frame = ctk.CTkFrame(self.files_container)
        self.file_frame.grid(row=0, column=0, padx=10, pady=(0, 5), sticky="ew")
        self.file_frame.grid_columnconfigure(0, weight=1)
        
        self.file_label = ctk.CTkLabel(
            self.file_frame, 
            text="파일을 선택하세요", 
            height=40,
            fg_color="#2B2B2B",
            corner_radius=6
        )
        self.file_label.grid(row=0, column=0, padx=(15, 10), pady=10, sticky="ew")
        
        self.select_btn = ctk.CTkButton(
            self.file_frame, 
            text="파일 선택", 
            width=80,
            height=32,
            command=self.select_file
        )
        self.select_btn.grid(row=0, column=1, padx=(0, 5), pady=10)

        self.input_folder_btn = ctk.CTkButton(
            self.file_frame,
            text="📂",
            width=40,
            height=32,
            fg_color="#444",
            hover_color="#555",
            state="disabled",
            command=lambda: self.open_folder(self.input_file)
        )
        self.input_folder_btn.grid(row=0, column=2, padx=(0, 15), pady=10)

        # 출력 파일명
        self.output_frame = ctk.CTkFrame(self.files_container)
        self.output_frame.grid(row=1, column=0, padx=10, sticky="ew")
        self.output_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.output_frame, text="출력 파일명", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")
        
        self.output_entry_frame = ctk.CTkFrame(self.output_frame, fg_color="transparent")
        self.output_entry_frame.grid(row=1, column=0, padx=20, pady=(0, 5), sticky="ew")
        self.output_entry_frame.grid_columnconfigure(0, weight=1)
        
        self.output_filename_entry = ctk.CTkEntry(
            self.output_entry_frame, 
            placeholder_text="파일을 선택하면 자동으로 생성됩니다",
            state="readonly"
        )
        self.output_filename_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        self.edit_output_btn = ctk.CTkButton(
            self.output_entry_frame, 
            text="✏️ 수정", 
            width=60,
            state="disabled",
            command=self.edit_output_filename
        )
        self.edit_output_btn.grid(row=0, column=1, padx=(0, 5))

        self.output_folder_btn = ctk.CTkButton(
            self.output_entry_frame,
            text="📂",
            width=40,
            fg_color="#444",
            hover_color="#555",
            state="disabled",
            command=lambda: self.open_folder(self.output_file)
        )
        self.output_folder_btn.grid(row=0, column=2)
        
        self.output_folder_btn.grid(row=0, column=2)

        # 4. 설정 섹션 (화질 & 오디오 가로 배치)
        self.settings_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.settings_container.grid(row=3, column=0, pady=(0, 15), sticky="ew")
        self.settings_container.grid_columnconfigure((0, 1), weight=1)

        # 화질 설정
        self.quality_frame = ctk.CTkFrame(self.settings_container)
        self.quality_frame.grid(row=0, column=0, padx=(10, 5), sticky="nsew")
        self.quality_frame.grid_columnconfigure(0, weight=1)

        # 화질 설정 타이틀 + 툴팁
        self.quality_title_frame = ctk.CTkFrame(self.quality_frame, fg_color="transparent")
        self.quality_title_frame.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")
        
        ctk.CTkLabel(self.quality_title_frame, text="화질 설정", font=ctk.CTkFont(weight="bold")).pack(side="left")
        
        self.help_icon = ctk.CTkLabel(
            self.quality_title_frame, 
            text=" ⓘ", 
            text_color="#888",
            font=ctk.CTkFont(size=14, weight="bold"),
            cursor="hand2"
        )
        self.help_icon.pack(side="left", padx=2)
        
        tooltip_text = (
            "화질 설정 (CQ/CQP)\n\n"
            "- 숫자가 낮을수록 고화질(대용량), 높을수록 저화질(저용량)입니다.\n"
            "- 기술적인 전체 범위는 0~51이며, 본 자동화 툴은 실용적인 범위인 18~30을 제공합니다.\n"
            "- 18~20: 초고화질 (20 권장, 육안으로 원본과 거의 구분 불가능)\n"
            "- 23: 균형점 (화질과 용량의 조화)\n"
            "- 28~30: 저용량 (용량 절감이 최우선인 경우)\n\n"
            "* CQ(Constant Quality)는 목표 화질을 일정하게 유지하기 위해\n"
            "  영상의 복잡도에 따라 비트레이트를 자동으로 조절하는 방식입니다."
        )
        ToolTip(self.help_icon, tooltip_text)
        
        self.slider_labels_frame = ctk.CTkFrame(self.quality_frame, fg_color="transparent")
        self.slider_labels_frame.grid(row=1, column=0, padx=20, sticky="ew")
        ctk.CTkLabel(self.slider_labels_frame, text="초고화질").pack(side="left")
        ctk.CTkLabel(self.slider_labels_frame, text="저용량").pack(side="right")

        self.quality_slider = ctk.CTkSlider(
            self.quality_frame, 
            from_=18, 
            to=30, 
            number_of_steps=12,
            command=self.on_slider_change
        )
        self.quality_slider.set(20)
        self.quality_slider.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        
        self.quality_value_label = ctk.CTkLabel(self.quality_frame, text="현재 값: 20 (권장)", text_color="#888")
        self.quality_value_label.grid(row=3, column=0, pady=(0, 5))
        
        # 오디오 설정
        self.audio_frame = ctk.CTkFrame(self.settings_container)
        self.audio_frame.grid(row=0, column=1, padx=(5, 10), sticky="nsew")
        self.audio_frame.grid_columnconfigure(0, weight=1)
        
        # 오디오 설정 타이틀 + 툴팁
        self.audio_title_frame = ctk.CTkFrame(self.audio_frame, fg_color="transparent")
        self.audio_title_frame.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")
        
        ctk.CTkLabel(self.audio_title_frame, text="오디오 설정", font=ctk.CTkFont(weight="bold")).pack(side="left")
        
        self.audio_help_icon = ctk.CTkLabel(
            self.audio_title_frame, 
            text=" ⓘ", 
            text_color="#888",
            font=ctk.CTkFont(size=14, weight="bold"),
            cursor="hand2"
        )
        self.audio_help_icon.pack(side="left", padx=2)
        
        audio_tooltip_text = (
            "오디오 설정 안내\n\n"
            "- 원본 유지 (Copy): 오디오 트랙을 재인코딩 없이 그대로 복사합니다.\n"
            "  음질 변화가 전혀 없고 속도가 매우 빠르지만, MKV 컨테이너 사용을 권장합니다.\n"
            "- AAC 변환 (192kbps): 오디오를 범용적인 AAC 코덱으로 변환합니다.\n"
            "  대부분의 플레이어 및 기기에서 원활하게 재생되는 높은 호환성을 제공합니다."
        )
        ToolTip(self.audio_help_icon, audio_tooltip_text)
        
        # 라디오 버튼 변수
        self.audio_var = ctk.StringVar(value="원본 유지 (Copy) - 빠름, MKV 권장")
        
        self.audio_radio_copy = ctk.CTkRadioButton(
            self.audio_frame,
            text="원본 유지 (Copy) - 빠름",
            variable=self.audio_var,
            value="원본 유지 (Copy) - 빠름, MKV 권장",
            command=self.on_audio_change
        )
        self.audio_radio_copy.grid(row=1, column=0, padx=20, pady=5, sticky="w")
        
        self.audio_radio_aac = ctk.CTkRadioButton(
            self.audio_frame,
            text="AAC 변환 (192kbps) - 호환성",
            variable=self.audio_var,
            value="AAC 변환 (192kbps) - 호환성 우선",
            command=self.on_audio_change
        )
        self.audio_radio_aac.grid(row=2, column=0, padx=20, pady=(0, 15), sticky="w")

        self.audio_mode_map = {
            "원본 유지 (Copy) - 빠름, MKV 권장": "copy",
            "AAC 변환 (192kbps) - 호환성 우선": "aac"
        }

        self.summary_frame = ctk.CTkFrame(self.main_frame)
        self.summary_frame.grid(row=4, column=0, padx=10, pady=(0, 15), sticky="ew")
        self.summary_frame.grid_columnconfigure(0, weight=1)

        self.estimated_size_label = ctk.CTkLabel(
            self.summary_frame, 
            text="파일을 선택하면 예상 용량이 표시됩니다", 
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#AAAAAA"
        )
        self.estimated_size_label.pack(pady=(15, 5))
        
        self.drive_space_label = ctk.CTkLabel(self.summary_frame, text="", font=ctk.CTkFont(size=12), text_color="#888")
        self.drive_space_label.pack(pady=(0, 15))

        self.ffmpeg_frame = ctk.CTkFrame(self.main_frame)
        self.ffmpeg_frame.grid(row=5, column=0, padx=10, pady=(0, 15), sticky="ew")
        self.ffmpeg_frame.grid_columnconfigure(0, weight=1)
        
        self.ffmpeg_header = ctk.CTkFrame(self.ffmpeg_frame, fg_color="transparent")
        self.ffmpeg_header.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="ew")
        
        ctk.CTkLabel(self.ffmpeg_header, text="🔧 FFmpeg 명령어 미리보기", font=ctk.CTkFont(weight="bold")).pack(side="left")
        
        self.copy_btn = ctk.CTkButton(
            self.ffmpeg_header, 
            text="📋 한 줄로 복사", 
            width=100, 
            height=25,
            font=ctk.CTkFont(size=11),
            fg_color="#444",
            hover_color="#555",
            state="disabled",
            command=self.copy_ffmpeg_command
        )
        self.copy_btn.pack(side="right")
        
        self.ffmpeg_preview = ctk.CTkTextbox(
            self.ffmpeg_frame, 
            height=100, 
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#00FF00",
            fg_color="#1A1A1A"
        )
        self.ffmpeg_preview.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.ffmpeg_preview.insert("1.0", "파일을 선택하면 실행될 FFmpeg 명령어가 표시됩니다")
        self.ffmpeg_preview.configure(state="disabled")

        # 7. 실행 섹션
        self.action_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.action_frame.grid(row=6, column=0, pady=(0, 15), sticky="ew")
        self.action_frame.grid_columnconfigure(0, weight=1)

        self.run_btn = ctk.CTkButton(
            self.action_frame, 
            text="🚀 START", 
            height=60,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color=self.accent_color,
            hover_color=self.adjust_color_brightness(self.accent_color, 1.2),
            text_color_disabled="white",
            state="disabled",
            command=self.start_encoding
        )
        self.run_btn.grid(row=0, column=0, padx=10, sticky="ew")

        self.progress_bar = ctk.CTkProgressBar(self.action_frame)
        self.progress_bar.set(0)
        self.progress_bar.configure(progress_color=self.accent_color)
        self.progress_bar.grid(row=1, column=0, padx=10, pady=(15, 5), sticky="ew")

        # 8. 로그
        self.log_text = ctk.CTkTextbox(
            self.main_frame, 
            height=100, 
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color="#00FF00",
            fg_color="#1A1A1A"
        )
        self.log_text.grid(row=7, column=0, padx=10, pady=(0, 10), sticky="nsew")

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def open_folder(self, file_path):
        """파일이 위치한 폴더를 시스템 탐색기로 엽니다"""
        if not file_path:
            return
            
        folder_path = str(Path(file_path).parent)
        if not os.path.exists(folder_path):
            return

        try:
            if sys.platform == "win32":
                os.startfile(folder_path)
            else:
                # macOS/Linux 호환성
                import subprocess
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.Popen([opener, folder_path])
        except Exception as e:
            self.log(f"폴더 열기 실패: {e}")

    def init_taskbar(self):
        """Windows 작업표시줄 진행바 연동 초기화"""
        try:
            # Tkinter의 winfo_id()는 Windows에서 HWND를 반환함
            self.taskbar = TaskbarController(self.winfo_id())
            # self.log("작업표시줄 연동 완료")
        except Exception as e:
            print(f"Taskbar initialization error: {e}")

    def adjust_color_brightness(self, hex_color, factor):
        """색상 밝기 조정"""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r = min(255, int(r * factor))
        g = min(255, int(g * factor))
        b = min(255, int(b * factor))
        return f'#{r:02x}{g:02x}{b:02x}'

    def log(self, message):
        """로그 출력"""
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"> {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def on_slider_change(self, value):
        val = int(value)
        label_map = {
            18: "(초고화질)",
            19: "(고화질)",
            20: "(권장)",
            23: "(균형점)"
        }
        
        suffix = label_map.get(val, "")
        if 28 <= val <= 30:
            suffix = "(저용량)"
            
        self.quality_value_label.configure(text=f"현재 값: {val} {suffix}".strip())
        self.update_ui_state()

    def on_audio_change(self):
        self.update_ui_state()

    def update_ui_state(self):
        """파일 선택이나 설정 변경 시 UI 업데이트"""
        if not self.input_file:
            return

        quality = int(self.quality_slider.get())
        audio_display_mode = self.audio_var.get()
        audio_mode = self.audio_mode_map.get(audio_display_mode, "copy")
        
        if not self.output_file or self.auto_naming:
            self.output_file = self.encoder.generate_output_filename(
                self.input_file,
                quality,
                audio_mode
            )
        
        self.output_filename_entry.configure(state="normal")
        self.output_filename_entry.delete(0, "end")
        self.output_filename_entry.insert(0, Path(self.output_file).name)
        self.output_filename_entry.configure(state="readonly")
        
        # FFmpeg 미리보기
        cmd_preview = self.encoder.get_command_preview(
            self.input_file,
            self.output_file,
            quality,
            audio_mode
        )
        self.ffmpeg_preview.configure(state="normal")
        self.ffmpeg_preview.delete("1.0", "end")
        self.ffmpeg_preview.insert("1.0", cmd_preview)
        self.ffmpeg_preview.configure(state="disabled")
        
        # 드라이브 용량
        self.update_drive_space_label()
        
        # 예상 용량 계산 및 표시
        self.update_estimated_size(quality, audio_mode)
        
        # 버튼 활성화
        if not self.encoding_in_progress:
            self.run_btn.configure(state="normal")
            self.edit_output_btn.configure(state="normal")
            self.copy_btn.configure(state="normal")
            self.input_folder_btn.configure(state="normal")
            self.output_folder_btn.configure(state="normal")

    def update_drive_space_label(self):
        if not self.output_file:
            return
            
        try:
            path = Path(self.output_file)
            drive = path.drive if path.drive else path.parts[0]
            total, used, free = shutil.disk_usage(drive)
            free_gb = free / (1024 ** 3)
            total_gb = total / (1024 ** 3)
            
            # 용량 경고 로직 개선 (예상 용량 기준)
            if self.estimated_size_bytes > 0:
                # 예상 용량의 N% 기준
                if free < self.estimated_size_bytes * 1.25:
                    color = "#FF4444"
                    warning = " ⚠️ 공간 부족"
                elif free < self.estimated_size_bytes * 2.0:
                    color = "#FFAA00"
                    warning = " ⚠️ 공간 여유 적음"
                else:
                    color = "#888888"
                    warning = ""
            else:
                # 폴백: 절대량 기준 (10GB/50GB)
                if free_gb < 10:
                    color = "#FF4444"
                    warning = " ⚠️ 공간 부족"
                elif free_gb < 50:
                    color = "#FFAA00"
                    warning = ""
                else:
                    color = "#888888"
                    warning = ""
                
            self.drive_space_label.configure(
                text=f"💾 {drive} 드라이브: {free_gb:.1f}GB / {total_gb:.1f}GB 사용 가능{warning}",
                text_color=color
            )
        except:
            self.drive_space_label.configure(text="")
            
    def update_estimated_size(self, quality, audio_mode):
        if not self.input_file:
            return
            
        try:
            video_info = self.encoder.get_video_info(self.input_file)
            orig_size = video_info.get('size', 0)
            
            est_data = self.encoder.estimate_output_size(video_info, quality, audio_mode)
            est_size = est_data['total']
            self.estimated_size_bytes = est_size
            
            if est_size > 0:
                est_gb = est_size / (1024 ** 3)
                reduction = ((orig_size - est_size) / orig_size * 100) if orig_size > 0 else 0
                
                reduction_text = f" (약 {reduction:.1f}% 절감 예상)" if reduction > 0 else ""
                self.estimated_size_label.configure(
                    text=f"📊 예상 결과 용량: {est_gb:.2f} GB{reduction_text}",
                    text_color=self.accent_color
                )
                
                # 로그에 상세 정보 추가
                v_mb = est_data['video'] / (1024 * 1024)
                a_mb = est_data['audio'] / (1024 * 1024)
                t_mb = est_size / (1024 * 1024)
                codec_name = self.encoder.encoder_type.upper()
                self.log(f"예상 용량 ({codec_name}, CQ{quality}): 총 {t_mb:.1f}MB (비디오 {v_mb:.1f}MB, 오디오 {a_mb:.1f}MB)")
            else:
                self.estimated_size_label.configure(text="")
        except Exception as e:
            print(f"예상 용량 계산 오류: {e}")
            self.estimated_size_label.configure(text="")

    def select_file(self):
        file_path = filedialog.askopenfilename(
            initialdir=self.last_directory,
            title="비디오 파일 선택",
            filetypes=(
                ("Video Files", "*.mkv *.mp4 *.mov *.avi *.ts *.m2ts *.wmv *.flv *.webm *.vob *.3gp *.m4v"),
                ("All Files", "*.*")
            )
        )
        
        if file_path:
            self.input_file = file_path
            self.last_directory = str(Path(file_path).parent)
            self.auto_naming = True
            
            file_name = Path(file_path).name
            self.file_label.configure(text=f"📁 {file_name}")
            
            # 비디오 정보
            video_info = self.encoder.get_video_info(file_path)
            d = video_info['duration']
            duration_str = f"{int(d // 60)}분 {int(d % 60)}초" if d > 0 else "알 수 없음"
            
            self.log(f"파일 선택됨: {file_name}")
            self.log(f"정보: {video_info['codec'].upper()} | {video_info['width']}x{video_info['height']} | {duration_str} | {video_info['fps']:.2f}fps")
            
            self.update_ui_state()

    def edit_output_filename(self):
        if not self.input_file:
            return
            
        new_output = filedialog.asksaveasfilename(
            initialfile=Path(self.output_file).name,
            initialdir=Path(self.output_file).parent,
            title="출력 파일명 지정",
            filetypes=(
                ("MP4 Files", "*.mp4"),
                ("All Files", "*.*")
            )
        )
        
        if new_output:
            # 확장자가 .mp4가 아니면 강제로 추가
            if not new_output.lower().endswith(".mp4"):
                new_output += ".mp4"
                
            self.output_file = new_output
            self.auto_naming = False
            self.update_ui_state()
            self.log(f"출력 파일명 변경: {Path(new_output).name}")

    def copy_ffmpeg_command(self):
        if not self.input_file or not self.output_file:
            return
            
        quality = int(self.quality_slider.get())
        audio_mode = self.audio_mode_map.get(self.audio_var.get(), "copy")
        
        cmd = self.encoder.build_command(self.input_file, self.output_file, quality, audio_mode)
        
        safe_cmd = []
        for arg in cmd:
            if ' ' in arg or '\\' in arg or '/' in arg:
                safe_cmd.append(f'"{arg}"')
            else:
                safe_cmd.append(arg)
        
        command_str = ' '.join(safe_cmd)
        self.clipboard_clear()
        self.clipboard_append(command_str)
        
        self.log("FFmpeg 명령어가 클립보드에 복사되었습니다.")
        messagebox.showinfo("복사 완료", "FFmpeg 명령어가 클립보드에 복사되었습니다.")

    def start_encoding(self):
        if not self.input_file or self.encoding_in_progress:
            return
            
        if Path(self.output_file).exists():
            if not messagebox.askyesno("파일 중복", f"이미 파일이 존재합니다:\n{Path(self.output_file).name}\n\n파일을 덮어쓰시겠습니까?\n(기존 파일은 휴지통으로 안전하게 이동됩니다)"):
                self.log("인코딩 취소: 파일이 이미 존재함")
                return
            else:
                self.log("덮어쓰기 승인됨")
                overwrite = True
        else:
            overwrite = False

        self.encoding_in_progress = True
        self.run_btn.configure(state="disabled", text="⏳ 인코딩 중... (0%)\n남은 시간: 계산 중...")
        self.select_btn.configure(state="disabled")
        self.edit_output_btn.configure(state="disabled")
        self.progress_bar.set(0)
        
        quality = int(self.quality_slider.get())
        audio_mode = self.audio_mode_map.get(self.audio_var.get(), "copy")
        
        # 인코딩 스레드 시작
        thread = threading.Thread(
            target=self.encoding_worker,
            args=(quality, audio_mode, overwrite),
            daemon=True
        )
        thread.start()

    def encoding_worker(self, quality, audio_mode, overwrite):
        try:
            # 덮어쓰기인 경우 기존 파일을 휴지통으로 이동
            if overwrite and Path(self.output_file).exists():
                try:
                    send2trash.send2trash(self.output_file)
                    self.log(f"기존 파일을 휴지통으로 이동했습니다: {Path(self.output_file).name}")
                except Exception as e:
                    self.log(f"휴지통 이동 실패 (영구 삭제될 수 있음): {e}")

            result = self.encoder.encode(
                self.input_file,
                quality,
                audio_mode,
                self.output_file,
                self.on_progress_callback,
                self.on_log_callback,
                overwrite
            )
            
            if result:
                self.after(0, self.encoding_finished, result)
            else:
                self.after(0, self.encoding_error, "인코딩 실패")
        except Exception as e:
            self.after(0, self.encoding_error, str(e))

    def on_progress_callback(self, data):
        self.after(0, lambda: self._update_progress_ui(data))

    def _update_progress_ui(self, data):
        if isinstance(data, dict):
            progress = data.get('progress', 0)
            remaining = data.get('remaining', "")
            
            self.progress_bar.set(progress / 100)
            self.run_btn.configure(text=f"⏳ 인코딩 중... ({int(progress)}%)\n남은 시간: {remaining}")
            
            # 작업표시줄 연동
            if self.taskbar:
                self.taskbar.set_value(progress)
        else:
            # 하위 호환성 유지
            self.progress_bar.set(data / 100)
            self.run_btn.configure(text=f"⏳ 인코딩 중... ({int(data)}%)")
            
            # 작업표시줄 연동
            if self.taskbar:
                self.taskbar.set_value(data)

    def on_log_callback(self, message):
        self.after(0, lambda: self.log(message))

    def encoding_finished(self, output_file):
        self.encoding_in_progress = False
        self.run_btn.configure(state="normal", text="🚀 START")
        self.log(f"✓ 인코딩 완료: {Path(output_file).name}")
        
        input_size = Path(self.input_file).stat().st_size / (1024**3)
        output_size = Path(output_file).stat().st_size / (1024**3)
        reduction = ((input_size - output_size) / input_size) * 100 if input_size > 0 else 0
        
        self.log(f"원본: {input_size:.2f}GB → 결과: {output_size:.2f}GB (절감: {reduction:.1f}%)")
        
        # OS Toast 알림 (팝업 대신 사용)
        icon_path = self.get_resource_path("resources/icon.png")
        show_toast(
            "renQoder 변환 완료",
            f"성공적으로 변환되었습니다!\n절감률: {reduction:.1f}% ({output_size:.2f}GB)",
            icon_path=str(icon_path)
        )
        
        self.run_btn.configure(state="normal", text="🚀 START")
        self.select_btn.configure(state="normal")
        self.edit_output_btn.configure(state="normal")
        self.progress_bar.set(1.0)
        
        # 작업표시줄 상태 리셋
        if self.taskbar:
            self.taskbar.stop()

    def test_notification(self):
        """OS 알림 기능 테스트"""
        # icon_path = self.get_resource_path("resources/icon.png")
        # 리소스 폴더의 icon.png 경로 찾기
        # 실행 위치(run.py) 기준 상대 경로 혹은 절대 경로 계산
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir, "resources", "icon.png")
        show_toast(
            "renQoder 알림 테스트",
            "알림 기능이 정상적으로 작동하고 있습니다!",
            icon_path
        )
        self.log(f"알림 테스트를 실행했습니다. {icon_path}")

    def encoding_error(self, message):
        self.encoding_in_progress = False
        self.log(f"✗ 오류 발생: {message}")
        messagebox.showerror("오류", f"인코딩 중 오류가 발생했습니다:\n{message}")
        
        self.run_btn.configure(state="normal", text="🚀 START")
        self.select_btn.configure(state="normal")
        self.edit_output_btn.configure(state="normal")
        
        # 작업표시줄 에러 상태 (빨간색)
        if self.taskbar:
            self.taskbar.set_error()

    def load_settings(self):
        """설정 로드"""
        self.last_directory = str(Path.home())
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.last_directory = config.get('last_directory', self.last_directory)
                    
                    # 윈도우 위치/크기 복원 (CustomTkinter는 geometry 문자열 사용)
                    geom = config.get('window_geometry_ctk')
                    if geom:
                        self.geometry(geom)
        except Exception as e:
            print(f"설정 로드 중 오류: {e}")

    def on_closing(self):
        """종료 시 설정 저장"""
        try:
            config = {}
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config['last_directory'] = self.last_directory
            config['window_geometry_ctk'] = self.geometry()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"설정 저장 중 오류: {e}")
        
        self.destroy()

def main():
    # FFmpeg 확인
    if not check_ffmpeg():
        if messagebox.askyesno(
            "FFmpeg 미설치", 
            "FFmpeg가 설치되어 있지 않습니다.\nrenQoder는 FFmpeg가 필요합니다.\n공식 사이트에서 다운로드하시겠습니까?"
        ):
            webbrowser.open("https://www.ffmpeg.org/download.html")
        sys.exit(1)
        
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()
