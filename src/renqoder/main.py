"""
renQoder - Smart Video Transcoder
0.4.0 버전
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
from searcher import VideoSearcher
from metadata_utils import format_duration

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
        
        # 마우스 위치 기반 또는 위젯 기반 좌표 계산
        if event:
            x = event.x_root + 15
            y = event.y_root + 10
        else:
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
        
        # 검색기 초기화
        self.searcher = VideoSearcher()
        
        # 변수
        self.input_file = None
        self.output_file = None
        self.estimated_size_bytes = 0
        self.encoding_in_progress = False
        self.taskbar = None
        
        # 검색 관련 상태
        self.all_search_results = []
        self.metadata_thread_running = False
        self.sort_column = None
        self.sort_descending = False
        
        # 설정 파일 경로
        self.config_file = Path.home() / '.renqoder_config.json'
        
        # UI 초기화
        self.init_ui()
        
        # 툴팁 인스턴스 초기화 (Treeview용 동적 툴팁)
        self.tree_tooltip = ToolTip(self.results_tree, "")
        self.results_tree.bind("<Motion>", self.on_tree_motion)
        self.results_tree.bind("<Leave>", lambda e: self.tree_tooltip.hide_tooltip())
        
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
        self.grid_rowconfigure(1, weight=1)  # Changed to row 1 for tabview

        # 공통 헤더 (로고, 타이틀 & 슬로건)
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(10, 0))
        
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
        
        # Everything 링크 버튼
        self.everything_btn = ctk.CTkButton(
            self.links_frame,
            text="Everything",
            width=100,
            height=22,
            font=ctk.CTkFont(size=11),
            fg_color="#333",
            hover_color="#444",
            command=lambda: webbrowser.open("https://www.voidtools.com/")
        )
        self.everything_btn.pack(side="top")

        # 탭뷰 생성 (탭 버튼 크기 증가)
        self.tabview = ctk.CTkTabview(
            self, 
            corner_radius=0,
            width=660,  # 전체 너비 설정
            segmented_button_fg_color="#1A1A1A",
            segmented_button_selected_color=self.accent_color,
            segmented_button_unselected_color="#2B2B2B"
        )
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 10))
        
        # 탭 추가
        self.tabview.add("Encoding")
        self.tabview.add("Search")
        
        # 탭 버튼 크기 및 스타일 설정
        try:
            # 세그먼트 버튼 전체 높이 증가
            self.tabview._segmented_button.configure(height=40, font=ctk.CTkFont(size=14, weight="bold"))
            
            # 각 개별 버튼이 동일한 너비를 차지하도록 설정
            for button in self.tabview._segmented_button._buttons_dict.values():
                button.configure(width=300)  # 각 버튼에 충분한 너비 설정
        except Exception as e:
            print(f"탭 버튼 설정 오류: {e}")
        
        # Encoding 탭 초기화
        self.init_encoding_tab()
        
        # Search 탭 초기화
        self.init_search_tab()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def init_encoding_tab(self):
        """인코딩 탭 UI 구성"""
        encoding_tab = self.tabview.tab("Encoding")
        encoding_tab.grid_columnconfigure(0, weight=1)

        # GPU 정보
        encoder_info = self.detector.get_encoder_info()
        self.gpu_info_label = ctk.CTkLabel(
            encoding_tab,
            text=f"🎮 감지된 GPU: {encoder_info['vendor']} ({encoder_info['name']})",
            text_color=self.accent_color,
            font=ctk.CTkFont(weight="bold")
        )
        self.gpu_info_label.grid(row=0, column=0, pady=(10, 15))

        # 3. 입력 파일 및 출력 파일 섹션
        self.files_container = ctk.CTkFrame(encoding_tab, fg_color="transparent")
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

        # 4. 설정 섹션 (화질 & 오디오 가로 배치)
        self.settings_container = ctk.CTkFrame(encoding_tab, fg_color="transparent")
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

        self.summary_frame = ctk.CTkFrame(encoding_tab)
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

        self.ffmpeg_frame = ctk.CTkFrame(encoding_tab)
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
        self.action_frame = ctk.CTkFrame(encoding_tab, fg_color="transparent")
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
            encoding_tab, 
            height=100, 
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color="#00FF00",
            fg_color="#1A1A1A"
        )
        self.log_text.grid(row=7, column=0, padx=10, pady=(0, 10), sticky="nsew")
        encoding_tab.grid_rowconfigure(7, weight=1)  # Log area expands

    def init_search_tab(self):
        """검색 탭 UI 구성"""
        search_tab = self.tabview.tab("Search")
        search_tab.grid_columnconfigure(0, weight=1)
        search_tab.grid_rowconfigure(4, weight=1)  # Results area expands

        # Everything 감지 정보
        everything_status = self.searcher.get_everything_status()
        self.everything_info_label = ctk.CTkLabel(
            search_tab,
            text=everything_status['status_text'],
            text_color=everything_status['color'],
            font=ctk.CTkFont(weight="bold")
        )
        self.everything_info_label.grid(row=0, column=0, pady=(10, 5))

        # Everything 다운로드 버튼 (미설치 시에만 표시)
        if not everything_status['installed']:
            self.everything_download_btn = ctk.CTkButton(
                search_tab,
                text="Everything 다운로드",
                width=150,
                height=28,
                font=ctk.CTkFont(size=12),
                fg_color="#0071c5",
                hover_color="#005a9e",
                command=lambda: webbrowser.open("https://www.voidtools.com/")
            )
            self.everything_download_btn.grid(row=1, column=0, pady=(0, 15))

        # 검색 컨트롤 프레임
        search_control_frame = ctk.CTkFrame(search_tab)
        search_control_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        search_control_frame.grid_columnconfigure(1, weight=1)

        # 드라이브 카드 컨테이너 (Canvas + Scrollbar)
        import tkinter as tk
        canvas_container = ctk.CTkFrame(search_control_frame, fg_color="transparent")
        canvas_container.grid(row=0, column=0, columnspan=3, padx=20, pady=(15, 15), sticky="ew")
        
        # Canvas for horizontal scrolling
        drive_canvas = tk.Canvas(canvas_container, bg="#1A1A1A", height=90, highlightthickness=0)
        drive_canvas.pack(side="top", fill="x")
        
        # Horizontal scrollbar
        h_scrollbar = ctk.CTkScrollbar(canvas_container, orientation="horizontal", command=drive_canvas.xview)
        h_scrollbar.pack(side="bottom", fill="x", pady=(2, 0))
        drive_canvas.configure(xscrollcommand=h_scrollbar.set)
        
        # Frame inside canvas
        drive_container = ctk.CTkFrame(drive_canvas, fg_color="transparent")
        canvas_window = drive_canvas.create_window((0, 0), window=drive_container, anchor="nw")
        
        # 마우스 휠로 가로 스크롤
        def on_mousewheel(event):
            # Windows: event.delta, Linux: event.num
            if event.delta:
                drive_canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
            elif event.num == 4:
                drive_canvas.xview_scroll(-1, "units")
            elif event.num == 5:
                drive_canvas.xview_scroll(1, "units")
        
        # 마우스 휠 이벤트 바인딩 (Windows/Mac)
        drive_canvas.bind("<MouseWheel>", on_mousewheel)
        # Linux 지원
        drive_canvas.bind("<Button-4>", on_mousewheel)
        drive_canvas.bind("<Button-5>", on_mousewheel)
        
        # Shift + 마우스 휠로도 가로 스크롤 가능
        def on_shift_mousewheel(event):
            if event.delta:
                drive_canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
        
        drive_canvas.bind("<Shift-MouseWheel>", on_shift_mousewheel)
        
        # 드라이브 정보 가져오기
        drives_info = self.searcher.get_drives_with_info()
        self.selected_drive = ctk.StringVar(value=drives_info[0]['letter'] if drives_info else "C:\\")
        self.drive_cards = {}
        
        # 드라이브 카드 생성 (고정 너비, 가로로 나열)
        for idx, drive_info in enumerate(drives_info):
            # 드라이브 카드 프레임 (고정 너비)
            card = ctk.CTkFrame(
                drive_container,
                fg_color="#2B2B2B",
                border_width=2,
                border_color="#3B3B3B",
                corner_radius=6,
                width=200,
                height=70
            )
            card.grid(row=0, column=idx, padx=3, pady=3, sticky="w")
            card.grid_propagate(False)  # 고정 크기 유지
            
            # 드라이브 타입별 아이콘
            icon_map = {
                'local': '💾',
                'removable': '🔌',
                'network': '🌐',
                'cdrom': '💿',
                'ramdisk': '⚡'
            }
            icon = icon_map.get(drive_info['type'], '💾')
            
            # 아이콘 + 드라이브 레터
            header_frame = ctk.CTkFrame(card, fg_color="transparent")
            header_frame.pack(fill="x", padx=8, pady=(8, 3))
            
            header_label = ctk.CTkLabel(
                header_frame,
                text=f"{icon} {drive_info['label']} ({drive_info['letter'][0]}:)",
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w"
            )
            header_label.pack(side="left", fill="x", expand=True)
            
            # 용량 정보
            total_gb = drive_info['total'] / (1024**3)
            free_gb = drive_info['free'] / (1024**3)
            used_gb = drive_info['used'] / (1024**3)
            usage_percent = (drive_info['used'] / drive_info['total'] * 100) if drive_info['total'] > 0 else 0
            
            capacity_text = f"{free_gb:.0f}GB / {total_gb:.0f}GB 사용 가능"
            capacity_label = ctk.CTkLabel(
                card,
                text=capacity_text,
                font=ctk.CTkFont(size=10),
                text_color="#AAAAAA",
                anchor="w"
            )
            capacity_label.pack(fill="x", padx=8, pady=(0, 3))
            
            # 용량 바
            progress_bar = ctk.CTkProgressBar(
                card,
                height=6,
                progress_color="#E74856" if usage_percent > 90 else "#FFA500" if usage_percent > 75 else self.accent_color
            )
            progress_bar.pack(fill="x", padx=8, pady=(0, 8))
            progress_bar.set(usage_percent / 100)
            
            # 드래그 데이터 저장
            drag_info = {"start_x": 0, "dragging": False, "drive_letter": drive_info['letter']}
            
            def on_card_press(event, info=drag_info):
                info["start_x"] = event.x_root
                info["dragging"] = False
            
            def on_card_drag(event, info=drag_info):
                # 5픽셀 이상 움직이면 드래그로 간주
                if abs(event.x_root - info["start_x"]) > 5:
                    info["dragging"] = True
                    # Canvas 스크롤
                    delta = event.x_root - info["start_x"]
                    current_x = drive_canvas.xview()[0]
                    canvas_width = drive_canvas.winfo_width()
                    scroll_region_width = drive_canvas.bbox("all")[2] if drive_canvas.bbox("all") else canvas_width
                    
                    # 스크롤 비율 계산
                    scroll_amount = -delta / scroll_region_width
                    drive_canvas.xview_moveto(max(0, min(1, current_x + scroll_amount)))
                    info["start_x"] = event.x_root
            
            def on_card_release(event, info=drag_info):
                # 드래그하지 않았으면 클릭으로 처리
                if not info["dragging"]:
                    self.select_drive_card(info["drive_letter"])
            
            # 모든 위젯에 드래그 이벤트 바인딩
            for widget in [card, header_frame, header_label, capacity_label, progress_bar]:
                widget.bind("<ButtonPress-1>", on_card_press)
                widget.bind("<B1-Motion>", on_card_drag)
                widget.bind("<ButtonRelease-1>", on_card_release)
            
            self.drive_cards[drive_info['letter']] = card
        
        # Canvas 스크롤 영역 업데이트
        drive_container.update_idletasks()
        drive_canvas.configure(scrollregion=drive_canvas.bbox("all"))
        
        # 첫 번째 드라이브 선택
        if drives_info:
            self.select_drive_card(drives_info[0]['letter'])


        # 검색 버튼 (드라이브 카드 아래에 배치)
        self.search_btn = ctk.CTkButton(
            search_control_frame,
            text="🔍 검색 시작",
            width=200,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.accent_color,
            hover_color=self.adjust_color_brightness(self.accent_color, 1.2),
            command=self.start_search
        )
        self.search_btn.grid(row=2, column=0, columnspan=3, padx=20, pady=(0, 15))

        # 필터 프레임
        filter_frame = ctk.CTkFrame(search_tab)
        filter_frame.grid(row=3, column=0, padx=10, pady=(0, 5), sticky="ew")

        ctk.CTkLabel(filter_frame, text="필터", font=ctk.CTkFont(weight="bold", size=13)).grid(row=0, column=0, columnspan=8, padx=20, pady=(15, 10), sticky="w")

        # 컨테이너 필터
        ctk.CTkLabel(filter_frame, text="컨테이너:").grid(row=1, column=0, padx=(20, 5), pady=(0, 15), sticky="w")
        self.container_var = ctk.StringVar(value="전체")
        self.container_combo = ctk.CTkComboBox(
            filter_frame,
            variable=self.container_var,
            values=["전체", "mp4", "mkv", "avi", "ts", "m2ts", "mov", "wmv", "flv", "webm"],
            width=100
        )
        self.container_combo.grid(row=1, column=1, padx=(0, 15), pady=(0, 15), sticky="w")

        # 최소 크기 필터
        ctk.CTkLabel(filter_frame, text="최소 크기:").grid(row=1, column=2, padx=(0, 5), pady=(0, 15), sticky="w")
        self.min_size_var = ctk.StringVar(value="1MB")
        self.min_size_combo = ctk.CTkComboBox(
            filter_frame,
            variable=self.min_size_var,
            values=["제한 없음", "1MB", "100MB", "500MB", "1GB", "5GB", "10GB"],
            width=100,
            command=lambda _: self.apply_filters()
        )
        self.min_size_combo.grid(row=1, column=3, padx=(0, 15), pady=(0, 15), sticky="w")

        # 코덱 필터
        ctk.CTkLabel(filter_frame, text="코덱:").grid(row=1, column=4, padx=(0, 5), pady=(0, 15), sticky="w")
        self.search_codec_var = ctk.StringVar(value="전체")
        self.search_codec_combo = ctk.CTkComboBox(
            filter_frame,
            variable=self.search_codec_var,
            values=["전체", "h264", "hevc", "vp9", "av1", "h263", "mpeg4"],
            width=100,
            command=lambda _: self.apply_filters()
        )
        self.search_codec_combo.grid(row=1, column=5, padx=(0, 15), pady=(0, 15), sticky="w")

        # 비트레이트 필터
        ctk.CTkLabel(filter_frame, text="최소 비트레이트:").grid(row=1, column=6, padx=(0, 5), pady=(0, 15), sticky="w")
        self.min_bitrate_var = ctk.StringVar(value="제한 없음")
        self.min_bitrate_combo = ctk.CTkComboBox(
            filter_frame,
            variable=self.min_bitrate_var,
            values=["제한 없음", "1 Mbps", "5 Mbps", "10 Mbps", "20 Mbps", "50 Mbps"],
            width=100,
            command=lambda _: self.apply_filters()
        )
        self.min_bitrate_combo.grid(row=1, column=7, padx=(0, 20), pady=(0, 15), sticky="w")

        # 비정상 파일 필터 (체크박스)
        self.abnormal_only_var = ctk.BooleanVar(value=False)
        self.abnormal_only_check = ctk.CTkCheckBox(
            filter_frame,
            text="비정상 파일만",
            variable=self.abnormal_only_var,
            width=100,
            command=self.apply_filters
        )
        self.abnormal_only_check.grid(row=1, column=8, padx=(0, 20), pady=(0, 15), sticky="w")

        # 결과 프레임
        results_frame = ctk.CTkFrame(search_tab)
        results_frame.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="nsew")
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_rowconfigure(0, weight=1)

        # Treeview 스타일 설정을 위한 프레임
        tree_container = ctk.CTkFrame(results_frame, fg_color="#2B2B2B")
        tree_container.grid(row=0, column=0, padx=20, pady=(10, 10), sticky="nsew")
        tree_container.grid_columnconfigure(0, weight=1)
        tree_container.grid_rowconfigure(0, weight=1)

        # Treeview 생성
        import tkinter.ttk as ttk
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview",
                       background="#2B2B2B",
                       foreground="white",
                       fieldbackground="#2B2B2B",
                       borderwidth=0)
        style.configure("Treeview.Heading",
                       background="#1A1A1A",
                       foreground="white",
                       borderwidth=1)
        style.map('Treeview', background=[('selected', self.accent_color)])
        style.map('Treeview.Heading',
                 background=[('active', self.accent_color)],
                 foreground=[('active', 'black')])

        # 스크롤바
        tree_scroll = ctk.CTkScrollbar(tree_container)
        tree_scroll.grid(row=0, column=1, sticky="ns")

        self.results_tree = ttk.Treeview(
            tree_container,
            columns=("name", "abnormal", "codec", "res", "fps", "size", "bitrate", "length", "ext", "path"),
            show="headings",
            yscrollcommand=tree_scroll.set,
            selectmode="browse"
        )
        self.results_tree.tag_configure("loading", foreground="#666666")
        self.results_tree.tag_configure("estimated", foreground="#FFA500") # Orange for estimated fields
        tree_scroll.configure(command=self.results_tree.yview)

        # 컬럼 설정
        self.column_headings = {
            "name": "파일명",
            "abnormal": "상태",
            "codec": "코덱",
            "res": "해상도",
            "fps": "FPS",
            "size": "크기",
            "bitrate": "비트레이트",
            "length": "길이",
            "ext": "확장자",
            "path": "경로"
        }
        
        widths = {
            "name": 200,
            "abnormal": 40,
            "codec": 80,
            "res": 100,
            "fps": 60,
            "size": 100,
            "bitrate": 100,
            "length": 80,
            "ext": 70,
            "path": 300
        }

        for col, head in self.column_headings.items():
            self.results_tree.heading(col, text=head, command=lambda _c=col: self.on_column_click(_c))
            self.results_tree.column(col, width=widths[col], minwidth=50)

        self.results_tree.grid(row=0, column=0, sticky="nsew")

        # 우클릭 메뉴 정의
        self.results_context_menu = tk.Menu(self, tearoff=0, bg="#2B2B2B", fg="white", activebackground="#0071c5")
        self.results_context_menu.add_command(label="➡️ 인코딩 탭으로 보내기", command=self.send_to_encoder)
        self.results_context_menu.add_separator()
        self.results_context_menu.add_command(label="📂 폴더 열기", command=lambda: self.context_menu_action("open_folder"))
        self.results_context_menu.add_command(label="🔗 파일 경로 복사", command=lambda: self.context_menu_action("copy_path"))
        self.results_context_menu.add_command(label="📄 파일 이름 복사", command=lambda: self.context_menu_action("copy_name"))
        self.results_context_menu.add_separator()
        self.results_context_menu.add_command(label="🔄 재분석", command=lambda: self.context_menu_action("clear_cache"))
        self.results_context_menu.add_command(label="❌ 파일 삭제 (휴지통)", command=lambda: self.context_menu_action("delete"))

        self.results_tree.bind("<Button-3>", self.show_context_menu)
        self.results_tree.bind("<Home>", self.on_home_key)
        self.results_tree.bind("<End>", self.on_end_key)

        # 메타데이터 진행바 및 상태 라벨
        self.metadata_progress = ctk.CTkProgressBar(
            results_frame, 
            height=6, 
            fg_color="#333333",
            progress_color="#0071c5"
        )
        self.metadata_progress.grid(row=3, column=0, padx=20, pady=(0, 5), sticky="ew")
        self.metadata_progress.set(0)

        self.metadata_status_label = ctk.CTkLabel(
            results_frame, 
            text="", 
            font=ctk.CTkFont(size=11),
            text_color="#888888"
        )
        self.metadata_status_label.grid(row=2, column=0, padx=20, pady=(5, 2), sticky="w")

        # 액션 프레임
        action_frame = ctk.CTkFrame(search_tab, fg_color="transparent")
        action_frame.grid(row=5, column=0, padx=10, pady=(0, 10), sticky="ew")
        action_frame.grid_columnconfigure(0, weight=1)

        self.send_to_encoder_btn = ctk.CTkButton(
            action_frame,
            text="➡️ 선택한 파일을 인코딩 탭으로 보내기",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#0071c5",
            hover_color="#005a9e",
            state="disabled",
            command=self.send_to_encoder
        )
        self.send_to_encoder_btn.grid(row=0, column=0, padx=(10, 5), sticky="ew")

        self.clear_cache_btn = ctk.CTkButton(
            action_frame,
            text="🗑️ 캐시 초기화",
            width=120,
            height=40,
            fg_color="#444444",
            hover_color="#555555",
            command=self.clear_search_cache
        )
        self.clear_cache_btn.grid(row=0, column=1, padx=(5, 10), sticky="e")

        # Treeview 선택 이벤트
        self.results_tree.bind('<<TreeviewSelect>>', self.on_search_result_select)

    def select_drive_card(self, drive_letter):
        """드라이브 카드 선택 처리"""
        self.selected_drive.set(drive_letter)
        
        # 모든 카드의 테두리 초기화
        for card in self.drive_cards.values():
            card.configure(border_color="#3B3B3B")
        
        # 선택된 카드 강조
        if drive_letter in self.drive_cards:
            self.drive_cards[drive_letter].configure(border_color=self.accent_color)
    
    def start_search(self):
        """검색 시작"""
        drive = self.selected_drive.get()
        min_size_str = self.min_size_var.get()

        # UI 비활성화
        self.search_btn.configure(state="disabled", text="🔍 검색 중...")
        self.results_tree.delete(*self.results_tree.get_children())
        self.metadata_status_label.configure(text="")
        self.metadata_progress.set(0)
        
        # 기존 메타데이터 추출 중단
        self.metadata_thread_running = False

        # 백그라운드 스레드에서 검색 실행
        import threading
        thread = threading.Thread(
            target=self.search_worker,
            args=(drive, min_size_str),
            daemon=True
        )
        thread.start()

    def search_worker(self, drive, min_size_str):
        """검색 작업 스레드"""
        try:
            # 1. 파일 검색 (빠름)
            results = self.searcher.search(drive)
            self.all_search_results = results
            
            # 2. UI 업데이트
            self.after(0, lambda: self.on_search_complete(results))
            
            # 3. 메타데이터 추출 대상 필터링 (최소 크기 조건 적용)
            size_map = {
                "1MB": 1024 * 1024,
                "100MB": 100 * 1024 * 1024,
                "500MB": 500 * 1024 * 1024,
                "1GB": 1024 * 1024 * 1024,
                "5GB": 5 * 1024 * 1024 * 1024,
                "10GB": 10 * 1024 * 1024 * 1024
            }
            # "제한 없음"이라도 최소 1바이트 이상인 파일만 대상으로 함 (0바이트 파일 제외)
            min_size = max(size_map.get(min_size_str, 0), 1)
            
            # 지정된 크기 이상의 파일만 상세 정보 추출 대상으로 선정
            extraction_targets = [item for item in results if item['size'] >= min_size]
            
            # 4. 메타데이터 추출 시작 (느림)
            self.start_metadata_extraction(extraction_targets)
            
        except Exception as e:
            self.after(0, lambda: self.log(f"검색 오류: {e}"))
            self.after(0, lambda: self.search_btn.configure(state="normal", text="🔍 검색 시작"))

    def on_search_complete(self, results):
        """기본 검색 완료 시 호출"""
        self.search_btn.configure(state="normal", text="🔍 검색 시작")
        self.apply_filters()
        self.log(f"검색 완료: {len(results)}개 파일 발견")
        
    def start_metadata_extraction(self, results):
        """메타데이터 추출 스레드 시작"""
        self.metadata_thread_running = True
        import threading
        thread = threading.Thread(
            target=self.metadata_worker,
            args=(results,),
            daemon=True
        )
        thread.start()

    def metadata_worker(self, results):
        """메타데이터 추출 작업 스레드 (2단계 추출 방식)"""
        total = len(results)
        
        # --- Stage 1: 빠른 헤더 분석 (Fast Scan) ---
        self.after(0, lambda: self.metadata_status_label.configure(text=f"상세 정보 추출 중 (1단계: 빠른 스캔)... (0/{total})"))
        
        for i, item in enumerate(results):
            if not self.metadata_thread_running:
                return
            
            if not item.get('metadata_loaded'):
                # Stage 1: fast_only=True
                metadata = self.searcher.extract_metadata(item['path'], fast_only=True)
                item.update(metadata)
            
            # 주기적으로 UI 업데이트 (5개마다 혹은 마지막에)
            if (i + 1) % 5 == 0 or (i + 1) == total:
                self.after(0, lambda count=i+1: self.update_metadata_progress(count, total, stage=1))
        
        # --- Stage 2: 정밀 스캔 (Deep Scan for damaged files) ---
        # 재생 시간이 0인 파일들만 골라냄
        damaged_files = [item for item in results if item.get('metadata_loaded') and item.get('duration', 0) <= 0 and not item.get('invalid')]
        
        if damaged_files:
            total_damaged = len(damaged_files)
            self.after(0, lambda: self.metadata_status_label.configure(text=f"손상된 파일 정밀 분석 중 (2단계)... (0/{total_damaged})"))
            
            for i, item in enumerate(damaged_files):
                if not self.metadata_thread_running:
                    return
                
                filename = Path(item['path']).name
                
                # Progress callback for real-time duration updates
                def progress_update(current_duration):
                    h = int(current_duration // 3600)
                    m = int((current_duration % 3600) // 60)
                    s = int(current_duration % 60)
                    time_str = f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"
                    self.after(0, lambda: self.metadata_status_label.configure(
                        text=f"정밀 분석 중 (2단계): {filename} - {time_str} ({i+1}/{total_damaged})"
                    ))
                
                # Stage 2: fast_only=False (ffmpeg 스캔 포함) with progress callback
                metadata = self.searcher.extract_metadata(item['path'], fast_only=False, progress_callback=progress_update)
                item.update(metadata)
                
                # 매 파일마다 UI 업데이트
                self.after(0, lambda count=i+1: self.update_metadata_progress(count, total_damaged, stage=2))
        
        self.metadata_thread_running = False
        self.after(0, lambda: self.metadata_status_label.configure(text=f"상세 정보 추출 완료 ({total}개 파일)"))
        self.after(0, lambda: self.metadata_progress.set(1.0))

    def update_metadata_progress(self, current, total, stage=1):
        """메타데이터 추출 진행률 업데이트"""
        progress_val = current / total if total > 0 else 0
        self.metadata_progress.set(progress_val)
        
        if stage == 1:
            self.metadata_status_label.configure(text=f"상세 정보 추출 중 (1단계: 빠른 스캔)... ({current}/{total})")
        else:
            self.metadata_status_label.configure(text=f"손상된 파일 정밀 분석 중 (2단계)... ({current}/{total})")
            
        # 현재 필터 상태에 맞춰 테이블 새로고침
        self.apply_filters()

    def apply_filters(self):
        """필터 및 정렬 적용하여 Treeview 업데이트"""
        container = self.container_var.get()
        min_size_str = self.min_size_var.get()
        codec_filter = self.search_codec_var.get()
        min_bitrate_str = self.min_bitrate_var.get()
        abnormal_only = self.abnormal_only_var.get()

        # 크기 필터 값 변환
        size_map = {
            "1MB": 1024 * 1024,
            "100MB": 100 * 1024 * 1024,
            "500MB": 500 * 1024 * 1024,
            "1GB": 1024 * 1024 * 1024,
            "5GB": 5 * 1024 * 1024 * 1024,
            "10GB": 10 * 1024 * 1024 * 1024
        }
        # "제한 없음"이라도 최소 1바이트 이상인 파일만 표시 (0바이트 파일 제외)
        min_size = max(size_map.get(min_size_str, 0), 1)

        # 비트레이트 필터 값 변환 (bps)
        bitrate_map = {
            "1 Mbps": 1 * 1000 * 1000,
            "5 Mbps": 5 * 1000 * 1000,
            "10 Mbps": 10 * 1000 * 1000,
            "20 Mbps": 20 * 1000 * 1000,
            "50 Mbps": 50 * 1000 * 1000
        }
        min_bitrate = bitrate_map.get(min_bitrate_str, 0)

        filtered = []
        for item in self.all_search_results:
            # 분석 결과 동영상이 아닌 파일은 아예 제외
            if item.get('invalid'):
                continue
                
            # 컨테이너 필터
            if container != "전체" and item['extension'].lstrip('.') != container:
                continue
            
            # 크기 필터
            if item['size'] < min_size:
                continue
            
            # 코덱 필터
            if codec_filter != "전체" and item.get('metadata_loaded'):
                if codec_filter.lower() not in item.get('codec', '').lower():
                    continue
            
            # 비트레이트 필터
            if min_bitrate > 0 and item.get('metadata_loaded'):
                if item.get('bitrate', 0) < min_bitrate:
                    continue
            
            # 비정상 파일 필터 (추정된 필드가 하나라도 있는 경우)
            if abnormal_only:
                if not item.get('estimated_fields'):
                    continue
            
            filtered.append(item)

        # 정렬 적용
        if self.sort_column:
            def sort_key(x):
                if self.sort_column == "res":
                    # 해상도는 전체 픽셀 수 기준으로 정렬 (캐시된 값 우선 사용)
                    pixels = x.get('pixels')
                    if pixels is None:
                        pixels = x.get('width', 0) * x.get('height', 0)
                    # 동일 픽셀 수일 경우 해상도 문자열(예: "1920x1080")로 2차 비교
                    return (pixels, x.get('resolution', ""))
                if self.sort_column == "length":
                    # 길이는 초 단위 duration으로 정렬
                    return x.get('duration', 0.0)
                if self.sort_column == "abnormal":
                    # 상태별 정렬 우선순위: 비정상(3) > 미분석(2) > 분석 중(1) > 정상(0)
                    if x.get('estimated_fields'):
                        return 3
                    if not x.get('metadata_loaded'):
                        return 2
                    # 기초 정보는 있으나 정밀 분석(Stage 2) 대기/진행 중인 경우
                    if self.metadata_thread_running and x.get('duration', 0) <= 0 and not x.get('invalid'):
                        return 1
                    return 0
                val = x.get(self.sort_column)
                if val is None:
                    return 0 if self.sort_column in ['size', 'bitrate', 'fps', 'width', 'height', 'duration'] else ""
                return val
            
            filtered.sort(key=sort_key, reverse=self.sort_descending)

        self.update_treeview(filtered)

    def on_column_click(self, col):
        """Treeview 컬럼 클릭 시 정렬"""
        if self.sort_column == col:
            self.sort_descending = not self.sort_descending
        else:
            self.sort_column = col
            self.sort_descending = True  # 새로운 컬럼은 내림차순부터 시작
        
        self.update_column_headers()
        self.apply_filters()

    def update_column_headers(self):
        """컬럼 헤더에 정렬 표시 업데이트"""
        for col, base_text in self.column_headings.items():
            if col == self.sort_column:
                # 현재 정렬 중인 컬럼에 화살표 추가
                indicator = " ▼" if self.sort_descending else " ▲"
                self.results_tree.heading(col, text=base_text + indicator)
            else:
                # 다른 컬럼은 기본 텍스트만 표시
                self.results_tree.heading(col, text=base_text)

    def update_treeview(self, results):
        """Treeview에 데이터 표시"""
        # 현재 선택된 아이템 기억
        selected = self.results_tree.selection()
        selected_path = None
        if selected:
            curr_values = self.results_tree.item(selected[0])['values']
            if len(curr_values) > 9:
                selected_path = curr_values[9]

        # 데이터 업데이트
        self.results_tree.delete(*self.results_tree.get_children())
        
        for item in results:
            size_mb = item['size'] / (1024 * 1024)
            size_str = f"{size_mb:.1f} MB" if size_mb < 1024 else f"{size_mb/1024:.2f} GB"
            
            bitrate = item.get('bitrate', 0)
            # 비트레이트 표시 (미디어 표준인 1000 단위를 사용)
            bitrate_kbps = f"{bitrate / 1000:,.0f} kbps" if item.get('metadata_loaded') and bitrate > 0 else "-"

            # 상태 아이콘 결정
            if item.get('estimated_fields'):
                status_icon = "⚠️"
            elif not item.get('metadata_loaded'):
                status_icon = "⏳"
            elif self.metadata_thread_running and item.get('duration', 0) <= 0 and not item.get('invalid'):
                status_icon = "🔍"
            else:
                status_icon = "✅"
            
            values = (
                item['name'],
                status_icon,
                item.get('codec', '-').upper(),
                item.get('resolution', '-'),
                item.get('fps', '-'),
                size_str,
                bitrate_kbps,
                item.get('duration_str', '-') if item.get('metadata_loaded') else '-',
                item['extension'].upper(),
                item['path']
            )
            # 하이라이트 태그 설정 (1단계 미완료이거나, 2단계 분석 대기 중인 경우)
            is_loading = not item.get('metadata_loaded')
            if not is_loading and self.metadata_thread_running:
                # 1단계는 완료되었으나 재생 시간이 '0'이고 분석이 진행 중이면 2단계 대기 상태로 간주
                if item.get('duration', 0) <= 0 and not item.get('invalid'):
                    is_loading = True
            
            tags = ()
            if is_loading:
                tags = ("loading",)
            elif item.get('estimated_fields'):
                tags = ("estimated",)
            
            node = self.results_tree.insert("", "end", values=values, tags=tags)
            
            # 선택 상태 복원
            if selected_path and item['path'] == selected_path:
                self.results_tree.selection_set(node)
                self.results_tree.see(node)

    def update_search_results(self, results):
        """이전 방식 호환성 유지용"""
        pass

    def on_tree_motion(self, event):
        """Treeview 마우스 이동 시 툴팁 처리"""
        item_id = self.results_tree.identify_row(event.y)
        if not item_id:
            self.tree_tooltip.hide_tooltip()
            return

        # 해당 아이템의 태그 확인
        tags = self.results_tree.item(item_id, "tags")
        if "estimated" in tags:
            # 원본 데이터 찾기 (아이템 인덱스로 추적)
            # Treeview의 모든 아이템을 순회하며 찾거나, update_treeview 시 map을 만들 수도 있지만
            # 여기서는 path를 기준으로 all_search_results에서 찾음
            values = self.results_tree.item(item_id, "values")
            if len(values) > 9:
                filepath = values[9]
                # 최적화를 위해 캐시된 데이터에서 찾기
                target_item = next((i for i in self.all_search_results if i['path'] == filepath), None)
                
                if target_item and target_item.get('estimated_fields'):
                    reasons = []
                    for field, reason in target_item['estimated_fields'].items():
                        field_name = "재생 시간" if field == "duration" else "비트레이트" if field == "bitrate" else field
                        reasons.append(f"• {field_name}: {reason}")
                    
                    tooltip_text = "⚠️ 추정된 메타데이터 정보:\n" + "\n".join(reasons)
                    
                    # 툴팁 텍스트 업데이트 및 표시
                    if self.tree_tooltip.text != tooltip_text:
                        self.tree_tooltip.text = tooltip_text
                        if self.tree_tooltip.tooltip_window:
                            # 이미 열려있으면 내용만 변경은 어려우므로 일단 닫고 다시 열거나Label 업데이트
                            # 여기서는 간단히 새로 고침
                            self.tree_tooltip.hide_tooltip()
                    
                    self.tree_tooltip.show_tooltip(event)
                    return

        self.tree_tooltip.hide_tooltip()

    def show_context_menu(self, event):
        """우클릭 시 메뉴 표시"""
        item = self.results_tree.identify_row(event.y)
        if item:
            self.results_tree.selection_set(item)
            self.results_context_menu.post(event.x_root, event.y_root)

    def on_home_key(self, event):
        """HOME 키: 첫 번째 항목으로 이동"""
        children = self.results_tree.get_children()
        if children:
            first_item = children[0]
            self.results_tree.selection_set(first_item)
            self.results_tree.see(first_item)
            self.results_tree.focus(first_item)
        return "break"  # 기본 동작 방지

    def on_end_key(self, event):
        """END 키: 마지막 항목으로 이동"""
        children = self.results_tree.get_children()
        if children:
            last_item = children[-1]
            self.results_tree.selection_set(last_item)
            self.results_tree.see(last_item)
            self.results_tree.focus(last_item)
        return "break"  # 기본 동작 방지

    def context_menu_action(self, action):
        """우클릭 메뉴 액션 처리"""
        selected = self.results_tree.selection()
        if not selected:
            return
            
        values = self.results_tree.item(selected[0])['values']
        if len(values) < 9:
            return
            
        filename = values[0]
        filepath = values[9]
        
        if action == "open_folder":
            self.open_folder(filepath)
        elif action == "copy_path":
            self.clipboard_clear()
            self.clipboard_append(filepath)
            self.log(f"경로 복사됨: {filepath}")
        elif action == "copy_name":
            self.clipboard_clear()
            self.clipboard_append(filename)
            self.log(f"파일명 복사됨: {filename}")
        elif action == "clear_cache":
            if self.searcher.clear_cache_item(filepath):
                # 해당 파일의 메타데이터를 초기화
                target_item = None
                for item in self.all_search_results:
                    if item['path'] == filepath:
                        target_item = item
                        item['metadata_loaded'] = False
                        item['duration'] = 0
                        item.pop('duration_str', None)
                        item.pop('codec', None)
                        item.pop('resolution', None)
                        item.pop('fps', None)
                        item.pop('bitrate', None)
                        item.pop('pixels', None)
                        break
                
                if target_item:
                    self.log(f"재분석 시작: {filename}")
                    self.apply_filters()  # UI 업데이트 (회색 표시)
                    
                    # 백그라운드에서 즉시 재분석 수행
                    def reanalyze():
                        # Stage 1: Fast scan
                        metadata = self.searcher.extract_metadata(filepath, fast_only=True)
                        target_item.update(metadata)
                        self.after(0, self.apply_filters)
                        
                        # Stage 2: Deep scan if needed
                        if target_item.get('metadata_loaded') and target_item.get('duration', 0) <= 0 and not target_item.get('invalid'):
                            def progress_update(current_duration):
                                h = int(current_duration // 3600)
                                m = int((current_duration % 3600) // 60)
                                s = int(current_duration % 60)
                                time_str = f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"
                                self.after(0, lambda: self.metadata_status_label.configure(
                                    text=f"재분석 중: {filename} - {time_str}"
                                ))
                            
                            metadata = self.searcher.extract_metadata(filepath, fast_only=False, progress_callback=progress_update)
                            target_item.update(metadata)
                            self.after(0, lambda: self.metadata_status_label.configure(text=""))
                            self.after(0, self.apply_filters)
                            self.after(0, lambda: self.log(f"재분석 완료: {filename}"))
                    
                    import threading
                    threading.Thread(target=reanalyze, daemon=True).start()
        elif action == "delete":
            if messagebox.askyesno("파일 삭제", f"정말로 이 파일을 휴지통으로 보내시겠습니까?\n\n{filename}"):
                try:
                    import send2trash
                    send2trash.send2trash(filepath)
                    self.log(f"파일 삭제됨 (휴지통): {filename}")
                    # 리스트에서 제거
                    self.all_search_results = [i for i in self.all_search_results if i['path'] != filepath]
                    self.apply_filters()
                except Exception as e:
                    messagebox.showerror("오류", f"파일 삭제 실패: {e}")

    def on_search_result_select(self, event):
        """검색 결과 선택 시"""
        selection = self.results_tree.selection()
        if selection:
            self.send_to_encoder_btn.configure(state="normal")
        else:
            self.send_to_encoder_btn.configure(state="disabled")

    def send_to_encoder(self):
        """선택한 파일을 인코딩 탭으로 전송"""
        selection = self.results_tree.selection()
        if not selection:
            return
        
        item = self.results_tree.item(selection[0])
        file_path = item['values'][9]  # path column is index 9
        
        # 인코딩 탭으로 전환
        self.tabview.set("Encoding")
        
        # 파일 설정
        self.input_file = file_path
        self.auto_naming = True
        
        file_name = Path(file_path).name
        self.file_label.configure(text=f"📁 {file_name}")
        
        # 비디오 정보
        video_info = self.encoder.get_video_info(file_path)
        duration_str = format_duration(video_info['duration'])
        
        self.log(f"검색 탭에서 파일 선택됨: {file_name}")
        self.log(f"정보: {video_info['codec'].upper()} | {video_info['width']}x{video_info['height']} | {duration_str} | {video_info['fps']:.2f}fps")
        
        self.update_ui_state()

    def clear_search_cache(self):
        """메타데이터 캐시 초기화"""
        self.searcher.clear_cache()
        self.log("메타데이터 캐시가 초기화되었습니다. 다음 검색 시 모든 파일을 새로 분석합니다.")
        self.metadata_status_label.configure(text="캐시 초기화 완료")

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
            duration_str = format_duration(video_info['duration'])
            
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
