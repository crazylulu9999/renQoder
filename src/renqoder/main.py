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

import customtkinter as ctk
from PIL import Image

# 모듈 경로 문제 해결
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from hardware_detector import HardwareDetector, check_ffmpeg
from encoder import VideoEncoder

# 테마 설정
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

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
        self.encoding_in_progress = False
        
        # 설정 파일 경로
        self.config_file = Path.home() / '.renqoder_config.json'
        
        # UI 초기화
        self.init_ui()
        
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
        self.title("renQoder - Smart Video Transcoder")
        self.geometry("700x850")
        
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

        # 메인 스크롤 가능한 프레임
        self.main_frame = ctk.CTkScrollableFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # 1. 헤더 (타이틀 & 슬로건)
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, pady=(0, 20), sticky="ew")
        
        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="renQoder", 
            font=ctk.CTkFont(size=32, weight="bold")
        )
        self.title_label.pack()
        
        self.slogan_label = ctk.CTkLabel(
            self.header_frame, 
            text="Smart Render, Slim Storage.", 
            text_color="#888888",
            font=ctk.CTkFont(size=14)
        )
        self.slogan_label.pack()

        # 2. GPU 정보
        encoder_info = self.detector.get_encoder_info()
        self.gpu_info_label = ctk.CTkLabel(
            self.main_frame,
            text=f"🎮 감지된 GPU: {encoder_info['vendor']} ({encoder_info['name']})",
            text_color=self.accent_color,
            font=ctk.CTkFont(weight="bold")
        )
        self.gpu_info_label.grid(row=1, column=0, pady=(0, 20))

        # 3. 파일 선택 섹션
        self.file_frame = ctk.CTkFrame(self.main_frame)
        self.file_frame.grid(row=2, column=0, padx=10, pady=(0, 20), sticky="ew")
        self.file_frame.grid_columnconfigure(0, weight=1)
        
        self.file_label = ctk.CTkLabel(
            self.file_frame, 
            text="파일을 선택하세요", 
            height=60,
            fg_color="#2B2B2B",
            corner_radius=6
        )
        self.file_label.grid(row=0, column=0, padx=(15, 10), pady=15, sticky="ew")
        
        self.select_btn = ctk.CTkButton(
            self.file_frame, 
            text="파일 선택", 
            width=100,
            height=40,
            command=self.select_file
        )
        self.select_btn.grid(row=0, column=1, padx=(0, 15), pady=15)

        # 4. 화질 설정 (슬라이더)
        self.quality_frame = ctk.CTkFrame(self.main_frame)
        self.quality_frame.grid(row=3, column=0, padx=10, pady=(0, 20), sticky="ew")
        self.quality_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.quality_frame, text="화질 설정", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")
        
        self.slider_labels_frame = ctk.CTkFrame(self.quality_frame, fg_color="transparent")
        self.slider_labels_frame.grid(row=1, column=0, padx=20, sticky="ew")
        ctk.CTkLabel(self.slider_labels_frame, text="초고화질").pack(side="left")
        ctk.CTkLabel(self.slider_labels_frame, text="저용량").pack(side="right")

        self.quality_slider = ctk.CTkSlider(
            self.quality_frame, 
            from_=18, 
            to=35, 
            number_of_steps=17,
            command=self.on_slider_change
        )
        self.quality_slider.set(23)
        self.quality_slider.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        
        self.quality_value_label = ctk.CTkLabel(self.quality_frame, text="현재 값: 23 (권장)", text_color="#888")
        self.quality_value_label.grid(row=3, column=0, pady=(0, 5))
        
        self.quality_desc = ctk.CTkLabel(
            self.quality_frame,
            text="💡 CQ 값이 낮을수록 고화질/대용량, 높을수록 저화질/저용량\n"
                 "18-20: 초고화질 (거의 무손실) | 23: 균형 (권장) | 28-30: 저용량",
            font=ctk.CTkFont(size=11),
            text_color="#666666",
            justify="left"
        )
        self.quality_desc.grid(row=4, column=0, padx=20, pady=(0, 15))

        # 5. 오디오 설정
        self.audio_frame = ctk.CTkFrame(self.main_frame)
        self.audio_frame.grid(row=4, column=0, padx=10, pady=(0, 20), sticky="ew")
        self.audio_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.audio_frame, text="오디오 설정", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")
        
        self.audio_option = ctk.CTkOptionMenu(
            self.audio_frame,
            values=["원본 유지 (Copy) - 빠름, MKV 권장", "AAC 변환 (192kbps) - 호환성 우선"],
            command=self.on_audio_change
        )
        self.audio_option.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.audio_mode_map = {
            "원본 유지 (Copy) - 빠름, MKV 권장": "copy",
            "AAC 변환 (192kbps) - 호환성 우선": "aac"
        }

        # 6. 출력 파일명
        self.output_frame = ctk.CTkFrame(self.main_frame)
        self.output_frame.grid(row=5, column=0, padx=10, pady=(0, 20), sticky="ew")
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
            width=80,
            state="disabled",
            command=self.edit_output_filename
        )
        self.edit_output_btn.grid(row=0, column=1)
        
        self.drive_space_label = ctk.CTkLabel(self.output_frame, text="", font=ctk.CTkFont(size=11), text_color="#888")
        self.drive_space_label.grid(row=2, column=0, padx=20, pady=(0, 15), sticky="w")

        # 7. FFmpeg 미리보기
        self.ffmpeg_frame = ctk.CTkFrame(self.main_frame)
        self.ffmpeg_frame.grid(row=6, column=0, padx=10, pady=(0, 20), sticky="ew")
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

        # 8. 진행률 및 시작 버튼
        self.action_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.action_frame.grid(row=7, column=0, pady=(0, 20), sticky="ew")
        self.action_frame.grid_columnconfigure(0, weight=1)
        
        # 진행률 정보 (상태 + 퍼센트)
        self.progress_info_frame = ctk.CTkFrame(self.action_frame, fg_color="transparent")
        self.progress_info_frame.grid(row=0, column=0, padx=10, sticky="ew")
        
        self.status_label = ctk.CTkLabel(self.progress_info_frame, text="대기 중", font=ctk.CTkFont(size=12))
        self.status_label.pack(side="left")
        
        self.progress_label = ctk.CTkLabel(self.progress_info_frame, text="0%", font=ctk.CTkFont(size=12, weight="bold"))
        self.progress_label.pack(side="right")
        
        self.progress_bar = ctk.CTkProgressBar(self.action_frame)
        self.progress_bar.set(0)
        self.progress_bar.configure(progress_color=self.accent_color)
        self.progress_bar.grid(row=1, column=0, padx=10, pady=(5, 5), sticky="ew")
        
        # 예상 용량 표시 레이블
        self.estimated_size_label = ctk.CTkLabel(
            self.action_frame, 
            text="", 
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#AAAAAA"
        )
        self.estimated_size_label.grid(row=2, column=0, pady=(0, 15))
        
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
        self.run_btn.grid(row=3, column=0, padx=10, sticky="ew")

        # 9. 로그
        self.log_text = ctk.CTkTextbox(
            self.main_frame, 
            height=120, 
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color="#00FF00",
            fg_color="#1A1A1A"
        )
        self.log_text.grid(row=8, column=0, padx=10, pady=(0, 20), sticky="ew")

        # 종료 시 이벤트 바인딩
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

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
        if val == 23:
            self.quality_value_label.configure(text=f"현재 값: {val} (권장)")
        else:
            self.quality_value_label.configure(text=f"현재 값: {val}")
        self.update_ui_state()

    def on_audio_change(self, _):
        self.update_ui_state()

    def update_ui_state(self):
        """파일 선택이나 설정 변경 시 UI 업데이트"""
        if not self.input_file:
            return

        quality = int(self.quality_slider.get())
        audio_display_mode = self.audio_option.get()
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

    def update_drive_space_label(self):
        if not self.output_file:
            return
            
        try:
            path = Path(self.output_file)
            drive = path.drive if path.drive else path.parts[0]
            total, used, free = shutil.disk_usage(drive)
            free_gb = free / (1024 ** 3)
            total_gb = total / (1024 ** 3)
            
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
            filetypes=(("Video Files", "*.mkv *.mp4 *.mov *.avi"), ("All Files", "*.*"))
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
            filetypes=(("Video Files", "*.mkv *.mp4 *.mov *.avi"), ("All Files", "*.*"))
        )
        
        if new_output:
            self.output_file = new_output
            self.auto_naming = False
            self.update_ui_state()
            self.log(f"출력 파일명 변경: {Path(new_output).name}")

    def copy_ffmpeg_command(self):
        if not self.input_file or not self.output_file:
            return
            
        quality = int(self.quality_slider.get())
        audio_mode = self.audio_mode_map.get(self.audio_option.get(), "copy")
        
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
            if not messagebox.askyesno("파일 중복", f"이미 파일이 존재합니다:\n{Path(self.output_file).name}\n\n덮어쓰시겠습니까?"):
                self.log("인코딩 취소: 파일이 이미 존재함")
                return
            else:
                self.log("덮어쓰기 승인됨")
                overwrite = True
        else:
            overwrite = False

        self.encoding_in_progress = True
        self.run_btn.configure(state="disabled", text="⏳ 인코딩 중...")
        self.select_btn.configure(state="disabled")
        self.edit_output_btn.configure(state="disabled")
        self.status_label.configure(text="인코딩 중...")
        self.progress_label.configure(text="0%")
        self.progress_bar.set(0)
        
        quality = int(self.quality_slider.get())
        audio_mode = self.audio_mode_map.get(self.audio_option.get(), "copy")
        
        # 인코딩 스레드 시작
        thread = threading.Thread(
            target=self.encoding_worker,
            args=(quality, audio_mode, overwrite),
            daemon=True
        )
        thread.start()

    def encoding_worker(self, quality, audio_mode, overwrite):
        try:
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

    def on_progress_callback(self, value):
        self.after(0, lambda: self._update_progress_ui(value))

    def _update_progress_ui(self, value):
        self.progress_bar.set(value / 100)
        self.progress_label.configure(text=f"{int(value)}%")

    def on_log_callback(self, message):
        self.after(0, lambda: self.log(message))

    def encoding_finished(self, output_file):
        self.encoding_in_progress = False
        self.log(f"✓ 인코딩 완료: {Path(output_file).name}")
        
        input_size = Path(self.input_file).stat().st_size / (1024**3)
        output_size = Path(output_file).stat().st_size / (1024**3)
        reduction = ((input_size - output_size) / input_size) * 100 if input_size > 0 else 0
        
        self.log(f"원본: {input_size:.2f}GB → 결과: {output_size:.2f}GB (절감: {reduction:.1f}%)")
        
        messagebox.showinfo(
            "완료",
            f"인코딩이 완료되었습니다!\n\n"
            f"원본: {input_size:.2f}GB\n"
            f"결과: {output_size:.2f}GB\n"
            f"절감: {reduction:.1f}%"
        )
        
        self.run_btn.configure(state="normal", text="🚀 START")
        self.select_btn.configure(state="normal")
        self.edit_output_btn.configure(state="normal")
        self.status_label.configure(text="완료")
        self.progress_label.configure(text="100%")
        self.progress_bar.set(1.0)

    def encoding_error(self, error_msg):
        self.encoding_in_progress = False
        self.log(f"✗ 오류: {error_msg}")
        messagebox.showerror("오류", f"인코딩 중 오류가 발생했습니다:\n{error_msg}")
        
        self.run_btn.configure(state="normal", text="🚀 START")
        self.select_btn.configure(state="normal")
        self.edit_output_btn.configure(state="normal")
        self.status_label.configure(text="오류 발생")

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
