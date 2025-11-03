#!/usr/bin/env python3
"""
Watermark Removal System - GUI
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os
import sys
import subprocess
from pathlib import Path
import json
from datetime import datetime
import logging

# Import WatermarkRemover
from watermark_remover import WatermarkRemover
from utils.logger import logger
import config


class SelectableText(tk.Text):
    """normal 상태에서 드래그/선택 가능하지만 편집 불가능한 Text 위젯"""
    # 차단할 키 목록 (메모리 효율성)
    BLOCKED_KEYS = ("<Delete>", "<BackSpace>", "<Control-x>", "<Control-v>")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind("<1>", self._focus_click)
        self.bind("<Control-a>", self._select_all)

        # 특정 편집 키만 바인딩 (모든 키 체크 대신)
        for key in self.BLOCKED_KEYS:
            self.bind(key, self._block_edit)

        # 드래그 선택 색상 명시적 설정
        self.config(
            selectbackground="#0078d4",
            selectforeground="white",
            highlightthickness=0,
            insertbackground="white",
            insertwidth=0
        )

        # 로그 라인 수 제한
        self.max_lines = 1000
        self.line_count = 0

    def _focus_click(self, event):
        self.focus_set()

    def _select_all(self, event):
        self.tag_add("sel", "1.0", "end")
        return "break"

    def _block_edit(self, event):
        """편집 시도 차단"""
        return "break"

    def insert_with_limit(self, index, text, tags=None):
        """로그 라인 수 제한과 함께 insert"""
        lines = text.count('\n')
        self.line_count += lines

        # 최대 라인 수 초과 시 오래된 로그 삭제
        if self.line_count > self.max_lines:
            excess = self.line_count - self.max_lines
            self.delete("1.0", f"{excess}.0")
            self.line_count = self.max_lines

        if tags:
            self.insert(index, text, tags)
        else:
            self.insert(index, text)

        # 자동으로 맨 아래로 스크롤
        self.see(tk.END)


class WatermarkRemovalGUI:
    # 상태 색상 매핑 (최적화)
    STATUS_COLORS = {
        "red": "#ffe6e6",
        "green": "#e6ffe6",
        "blue": "white",
        "orange": "#fff0e6",
        "black": "white"
    }

    def __init__(self, root):
        self.root = root
        self.root.title("Watermark Removal System")
        self.root.geometry("1200x1000")
        self.root.resizable(True, True)

        self.input_file = tk.StringVar()
        self.input_folder = tk.StringVar()  # 폴더 선택용
        self.output_folder = tk.StringVar(value="output")
        self.input_mode = tk.StringVar(value="single")  # "single" 또는 "batch"
        self.method = tk.StringVar(value="replicate")  # Default: Replicate API
        self.is_processing = False
        self.stop_event = threading.Event()  # 처리 중지 플래그

        self.config_file = "gui_config.json"
        self.load_config()

        # Dragging variables
        self.drag_data = {"x": 0, "y": 0}

        self.setup_ui()
        self.center_window()

        # Enable dragging from title label (must be after setup_ui)
        self.root.after(100, self.bind_drag_events)

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def bind_drag_events(self):
        """Enable window dragging from title label"""
        if hasattr(self, 'title_label'):
            self.title_label.bind("<Button-1>", self.start_drag)
            self.title_label.bind("<B1-Motion>", self.on_drag)
            self.title_label.config(cursor="hand2")

    def start_drag(self, event):
        """Start window dragging"""
        self.drag_data["x"] = event.x_root - self.root.winfo_x()
        self.drag_data["y"] = event.y_root - self.root.winfo_y()

    def on_drag(self, event):
        """Handle window dragging"""
        x = event.x_root - self.drag_data["x"]
        y = event.y_root - self.drag_data["y"]
        self.root.geometry(f"+{x}+{y}")

    def start_drag_status(self, event):
        """Start dragging status label"""
        self.drag_data["x"] = event.x_root - self.root.winfo_x()
        self.drag_data["y"] = event.y_root - self.root.winfo_y()

    def on_drag_status(self, event):
        """Handle status label window dragging"""
        x = event.x_root - self.drag_data["x"]
        y = event.y_root - self.drag_data["y"]
        self.root.geometry(f"+{x}+{y}")

    def show_context_menu(self, event):
        """상태 레이블 우클릭 메뉴 표시 및 복사 기능"""
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label="복사 (Copy)", command=self.copy_status_text)
        context_menu.add_command(label="전체 선택 (Select All)", command=self.select_all_status)
        context_menu.post(event.x_root, event.y_root)

    def copy_status_text(self):
        """상태 메시지를 클립보드에 복사"""
        try:
            status_text = self.status_label.cget("text")
            self.root.clipboard_clear()
            self.root.clipboard_append(status_text)
            self.root.update()
            messagebox.showinfo("복사 완료", "오류 메시지가 클립보드에 복사되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"복사 실패: {str(e)}")

    def select_all_status(self):
        """상태 메시지 전체 선택"""
        try:
            status_text = self.status_label.cget("text")
            self.root.clipboard_clear()
            self.root.clipboard_append(status_text)
            self.root.update()
            messagebox.showinfo("선택됨", "오류 메시지가 선택되어 클립보드에 복사되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"선택 실패: {str(e)}")

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(8, weight=1)

        self.title_label = ttk.Label(main_frame, text="Watermark Removal System", font=("Arial", 18, "bold"))
        self.title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))

        # ===== Input Mode Selection Frame =====
        mode_frame = ttk.Frame(main_frame)
        mode_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 8))
        mode_frame.columnconfigure(2, weight=1)

        ttk.Label(mode_frame, text="Mode:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W)
        ttk.Radiobutton(mode_frame, text="Single File", variable=self.input_mode, value="single",
                       command=self.on_input_mode_changed).grid(row=0, column=1, sticky=tk.W, padx=(10, 20))
        ttk.Radiobutton(mode_frame, text="Batch (Folder)", variable=self.input_mode, value="batch",
                       command=self.on_input_mode_changed).grid(row=0, column=2, sticky=tk.W)

        # ===== Input Frame (Compact) =====
        input_frame = ttk.LabelFrame(main_frame, text="Input Video", padding="8")
        input_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 8))
        input_frame.columnconfigure(1, weight=1)

        # Single file input
        self.file_label = ttk.Label(input_frame, text="Video File:", font=("Arial", 9))
        self.file_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        self.file_entry = ttk.Entry(input_frame, textvariable=self.input_file, state="readonly")
        self.file_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(8, 8), pady=5)
        self.file_browse_btn = ttk.Button(input_frame, text="Browse...", command=self.select_input_file, width=12)
        self.file_browse_btn.grid(row=0, column=2, padx=(0, 0), pady=5)

        # Batch folder input
        self.folder_label = ttk.Label(input_frame, text="Video Folder:", font=("Arial", 9))
        self.folder_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        self.folder_entry = ttk.Entry(input_frame, textvariable=self.input_folder, state="readonly")
        self.folder_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(8, 8), pady=5)
        self.folder_browse_btn = ttk.Button(input_frame, text="Browse...", command=self.select_input_folder, width=12)
        self.folder_browse_btn.grid(row=0, column=2, padx=(0, 0), pady=5)

        # 초기 상태: folder 숨김
        self.folder_entry.grid_remove()
        self.folder_browse_btn.grid_remove()
        self.folder_label.grid_remove()

        # ===== Output Frame (Compact) =====
        output_frame = ttk.LabelFrame(main_frame, text="Output", padding="8")
        output_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 8))
        output_frame.columnconfigure(1, weight=1)

        ttk.Label(output_frame, text="Output Folder:", font=("Arial", 9)).grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(output_frame, textvariable=self.output_folder).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(8, 8), pady=5)
        ttk.Button(output_frame, text="Browse...", command=self.select_output_folder, width=12).grid(row=0, column=2, pady=5)

        # ===== Method Frame (Compact) =====
        method_frame = ttk.LabelFrame(main_frame, text="Processing Method", padding="8")
        method_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 8))

        ttk.Radiobutton(method_frame, text="Replicate API - Sora2 Watermark Remover",
                       variable=self.method, value="replicate").pack(anchor=tk.W, pady=4)
        ttk.Radiobutton(method_frame, text="Local GPU - YOLOv11 + LAMA (GPU required)",
                       variable=self.method, value="local_gpu").pack(anchor=tk.W, pady=4)

        # ===== Log Frame =====
        info_frame = ttk.LabelFrame(main_frame, text="처리 로그 (Live Logs)", padding="8")
        info_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 8))
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(0, weight=1)

        # 로그 텍스트 위젯 (스크롤바 포함)
        info_text = SelectableText(info_frame, height=13, width=80, wrap=tk.WORD,
                                   font=("Courier", 9), bg="black", fg="white")

        # 드래그 선택 가능하도록 설정
        info_text.tag_config("sel", background="#0078d4", foreground="white")

        scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=info_text.yview)
        info_text.config(yscrollcommand=scrollbar.set)

        info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        self.info_text = info_text

        # 초기 메시지
        info_content = """처리 로그가 여기에 표시됩니다.
════════════════════════════════════════
지원 형식: MP4, MOV, AVI, MKV, WebM
처리 시간: 비디오 길이와 해상도에 따라 다름
────────────────────────────────────────"""

        info_text.insert("1.0", info_content)
        info_text.line_count = info_content.count('\n')  # 초기 라인 수 계산

        # 테그 설정 (색상)
        info_text.tag_config("error", foreground="red", background="black",
                            selectbackground="#0078d4", selectforeground="white")
        info_text.tag_config("success", foreground="lime", background="black",
                            selectbackground="#0078d4", selectforeground="white")
        info_text.tag_config("warning", foreground="yellow", background="black",
                            selectbackground="#0078d4", selectforeground="white")
        info_text.tag_config("info", foreground="cyan", background="black",
                            selectbackground="#0078d4", selectforeground="white")

        # 로그 텍스트에 우클릭 메뉴 바인딩 및 Ctrl+C 바인딩
        info_text.bind("<Button-3>", self.show_log_context_menu)
        info_text.bind("<Control-c>", self.copy_log_from_binding)

        # ===== Status Frame (Compact) =====
        progress_frame = ttk.LabelFrame(main_frame, text="상태 (Status)", padding="8")
        progress_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 8))
        progress_frame.columnconfigure(0, weight=1)

        # 상태 표시 레이블
        self.status_label = tk.Label(progress_frame, text="Ready", foreground="blue",
                                     font=("Arial", 10), wraplength=700, justify=tk.LEFT,
                                     bg="white", relief=tk.SUNKEN, padx=5, pady=5)
        self.status_label.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=4)

        # 상태 레이블에 드래그 기능 추가
        self.status_label.bind("<Button-1>", self.start_drag_status)
        self.status_label.bind("<B1-Motion>", self.on_drag_status)
        self.status_label.bind("<Button-3>", self.show_context_menu)
        self.status_label.config(cursor="hand2")

        # ===== Large Button Frame =====
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        # Create buttons with ttk style
        self.start_button = ttk.Button(button_frame, text="Start Processing", command=self.start_processing)
        self.start_button.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5), pady=5)

        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_processing, state="disabled")
        self.stop_button.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=5)

    def on_input_mode_changed(self):
        """입력 방식 변경 시 UI 업데이트"""
        if self.input_mode.get() == "single":
            # Single file mode
            self.file_label.grid()
            self.file_entry.grid()
            self.file_browse_btn.grid()
            self.folder_label.grid_remove()
            self.folder_entry.grid_remove()
            self.folder_browse_btn.grid_remove()
        else:
            # Batch mode
            self.file_label.grid_remove()
            self.file_entry.grid_remove()
            self.file_browse_btn.grid_remove()
            self.folder_label.grid()
            self.folder_entry.grid()
            self.folder_browse_btn.grid()

    def select_input_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video files", "*.mp4 *.mov *.avi *.mkv *.webm"),
                ("MP4 files", "*.mp4"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.input_file.set(file_path)
            self.save_config()

    def select_input_folder(self):
        """폴더 선택"""
        folder_path = filedialog.askdirectory(title="Select Video Folder for Batch Processing")
        if folder_path:
            self.input_folder.set(folder_path)
            self.save_config()

    def select_output_folder(self):
        folder_path = filedialog.askdirectory(title="Select Output Folder")
        if folder_path:
            self.output_folder.set(folder_path)
            self.save_config()

    def save_config(self):
        config = {
            "input_file": self.input_file.get(),
            "input_folder": self.input_folder.get(),
            "input_mode": self.input_mode.get(),
            "output_folder": self.output_folder.get(),
            "method": self.method.get()
        }
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Error saving config: {e}")

    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    if config.get("input_file"):
                        self.input_file.set(config["input_file"])
                    if config.get("input_folder"):
                        self.input_folder.set(config["input_folder"])
                    if config.get("input_mode"):
                        self.input_mode.set(config["input_mode"])
                    if config.get("output_folder"):
                        self.output_folder.set(config["output_folder"])
                    if config.get("method"):
                        self.method.set(config["method"])
        except Exception as e:
            print(f"Error loading config: {e}")

    def validate_inputs(self):
        mode = self.input_mode.get()

        if mode == "single":
            # Single file mode validation
            if not self.input_file.get():
                messagebox.showerror("Error", "Please select an input video file")
                return False

            if not os.path.exists(self.input_file.get()):
                messagebox.showerror("Error", "Input file does not exist")
                return False
        else:
            # Batch mode validation
            if not self.input_folder.get():
                messagebox.showerror("Error", "Please select an input folder")
                return False

            if not os.path.exists(self.input_folder.get()):
                messagebox.showerror("Error", "Input folder does not exist")
                return False

            # 폴더에 비디오 파일 있는지 확인
            supported_exts = tuple(f'.{ext}' for ext in config.SUPPORTED_FORMATS)
            video_files = [f for f in os.listdir(self.input_folder.get())
                          if f.lower().endswith(supported_exts)]
            if not video_files:
                messagebox.showerror("Error", "No video files found in the selected folder")
                return False

        # Output folder validation (both modes)
        if not self.output_folder.get():
            messagebox.showerror("Error", "Please select an output folder")
            return False

        if not os.path.exists(self.output_folder.get()):
            try:
                os.makedirs(self.output_folder.get())
            except Exception as e:
                messagebox.showerror("Error", f"Cannot create output folder: {e}")
                return False

        return True

    def start_processing(self):
        if not self.validate_inputs():
            return

        if self.is_processing:
            messagebox.showwarning("Warning", "Processing is already running")
            return

        self.is_processing = True
        self.stop_event.clear()  # 중지 플래그 초기화
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.update_status("Processing started...", "blue")

        # 로그 초기화
        try:
            self.info_text.delete("1.0", tk.END)
            self.info_text.insert(tk.END, "=" * 80 + "\n")
            self.info_text.line_count = 1  # 라인 수 리셋
        except:
            pass

        self.add_log(f"처리 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "info")

        # 선택한 모드에 따라 로그 출력
        mode = self.input_mode.get()
        if mode == "single":
            self.add_log(f"모드: 단일 파일 처리 (Single File)", "info")
            self.add_log(f"입력 파일: {self.input_file.get()}", "info")
        else:
            self.add_log(f"모드: 배치 처리 (Batch)", "info")
            self.add_log(f"입력 폴더: {self.input_folder.get()}", "info")

        self.add_log(f"출력 폴더: {self.output_folder.get()}", "info")
        self.add_log("=" * 80, "info")

        thread = threading.Thread(target=self.process_video)
        thread.daemon = True
        thread.start()

    def process_video(self):
        try:
            mode = self.input_mode.get()
            output_folder = self.output_folder.get()
            method = self.method.get()

            # 출력 폴더 생성
            os.makedirs(output_folder, exist_ok=True)

            if mode == "single":
                # Single file processing
                self._process_single_file(output_folder, method)
            else:
                # Batch processing
                self._process_batch_files(output_folder, method)

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.add_log(error_msg, "error")
            self.update_status(error_msg, "red")
            messagebox.showerror("오류", f"오류 발생: {str(e)}")
            import traceback
            self.add_log(traceback.format_exc(), "error")
        finally:
            self.is_processing = False
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.process = None

    def _process_single_file(self, output_folder, method):
        """단일 파일 처리"""
        # 중지 요청 확인
        if self.stop_event.is_set():
            self.add_log("사용자가 처리를 중지했습니다.", "warning")
            self.update_status("Processing stopped by user", "orange")
            return

        input_file = self.input_file.get()

        # 입력 파일 검증
        if not os.path.exists(input_file):
            error_msg = f"입력 파일을 찾을 수 없습니다: {input_file}"
            self.add_log(error_msg, "error")
            self.update_status(error_msg, "red")
            messagebox.showerror("오류", error_msg)
            return

        # 출력 파일 경로 설정
        filename = Path(input_file).stem
        output_path = os.path.join(output_folder, f"{filename}_cleaned.mp4")

        self.add_log(f"입력 파일: {input_file}", "info")
        self.add_log(f"출력 폴더: {output_folder}", "info")
        self.add_log(f"출력 파일: {output_path}", "info")
        self.add_log(f"처리 방법: {method}", "info")
        self.update_status("Processing started...", "blue")

        # Logger handler 추가 (실시간 로그 캡처)
        class GUILogHandler(logging.Handler):
            def __init__(self, gui):
                super().__init__()
                self.gui = gui

            def emit(self, record):
                try:
                    msg = self.format(record)
                    # 로그 레벨에 따라 색상 결정
                    level = record.levelname
                    if level == "ERROR":
                        tag = "error"
                    elif level == "WARNING":
                        tag = "warning"
                    elif level == "INFO":
                        if "✓" in msg or "success" in msg.lower() or "completed" in msg.lower():
                            tag = "success"
                        else:
                            tag = "info"
                    else:
                        tag = "info"

                    self.gui.add_log(msg, tag)
                except:
                    pass

        # GUI handler 추가
        gui_handler = GUILogHandler(self)
        gui_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S'))
        logger.addHandler(gui_handler)

        try:
            # WatermarkRemover 초기화 (stop_event 전달)
            remover = WatermarkRemover(stop_event=self.stop_event)

            # 방법 선택
            success = remover.remove_watermark(input_file, output_path, force_method=method)

            if success:
                # 파일 크기 확인
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path) / (1024 * 1024)
                    self.add_log(f"✓ 처리 완료! 출력 파일: {output_path} ({file_size:.2f} MB)", "success")
                    self.update_status(f"Processing completed successfully! ({file_size:.2f} MB)", "green")
                    messagebox.showinfo("성공", f"비디오 처리가 완료되었습니다!\n\n저장 위치: {output_path}")
                else:
                    error_msg = "출력 파일이 생성되지 않았습니다"
                    self.add_log(error_msg, "error")
                    self.update_status(error_msg, "red")
                    messagebox.showerror("오류", error_msg)
            else:
                error_msg = "비디오 처리 중 오류가 발생했습니다"
                self.add_log(error_msg, "error")
                self.update_status(error_msg, "red")
                messagebox.showerror("오류", error_msg)

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.add_log(error_msg, "error")
            self.update_status(error_msg, "red")
            messagebox.showerror("오류", f"오류 발생: {str(e)}")
            import traceback
            self.add_log(traceback.format_exc(), "error")
        finally:
            # Handler 제거
            logger.removeHandler(gui_handler)

    def _process_batch_files(self, output_folder, method):
        """배치 파일 처리 (폴더의 모든 비디오)"""
        # 중지 요청 확인
        if self.stop_event.is_set():
            self.add_log("사용자가 처리를 중지했습니다.", "warning")
            self.update_status("Processing stopped by user", "orange")
            return

        input_folder = self.input_folder.get()

        # 입력 폴더 검증
        if not os.path.exists(input_folder):
            error_msg = f"입력 폴더를 찾을 수 없습니다: {input_folder}"
            self.add_log(error_msg, "error")
            self.update_status(error_msg, "red")
            messagebox.showerror("오류", error_msg)
            return

        self.add_log(f"입력 폴더: {input_folder}", "info")
        self.add_log(f"출력 폴더: {output_folder}", "info")
        self.add_log(f"처리 방법: {method}", "info")
        self.update_status("Batch processing started...", "blue")

        # Logger handler 추가 (실시간 로그 캡처)
        class GUILogHandler(logging.Handler):
            def __init__(self, gui):
                super().__init__()
                self.gui = gui

            def emit(self, record):
                try:
                    msg = self.format(record)
                    # 로그 레벨에 따라 색상 결정
                    level = record.levelname
                    if level == "ERROR":
                        tag = "error"
                    elif level == "WARNING":
                        tag = "warning"
                    elif level == "INFO":
                        if "✓" in msg or "success" in msg.lower() or "completed" in msg.lower():
                            tag = "success"
                        else:
                            tag = "info"
                    else:
                        tag = "info"

                    self.gui.add_log(msg, tag)
                except:
                    pass

        # GUI handler 추가
        gui_handler = GUILogHandler(self)
        gui_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S'))
        logger.addHandler(gui_handler)

        try:
            # WatermarkRemover 초기화 (stop_event 전달)
            remover = WatermarkRemover(stop_event=self.stop_event)

            # 중지 요청 재확인 (배치 처리 시작 전)
            if self.stop_event.is_set():
                self.add_log("사용자가 처리를 중지했습니다.", "warning")
                self.update_status("Processing stopped by user", "orange")
                return

            # 배치 처리 실행
            results = remover.batch_process(input_folder, output_folder, method=method)

            # 배치 처리 후 중지 요청 확인
            if self.stop_event.is_set():
                self.add_log("사용자가 배치 처리를 중지했습니다.", "warning")
                self.update_status("Processing stopped by user", "orange")
                return

            if results:
                # 결과 표시
                self.add_log(f"\n{'='*80}", "info")
                self.add_log(f"배치 처리 완료", "success")
                self.add_log(f"{'='*80}", "info")
                self.add_log(f"전체: {results['total']}, 성공: {results['success']}, 실패: {results['failed']}", "info")

                if results['success'] > 0:
                    success_rate = (results['success'] / results['total'] * 100)
                    self.add_log(f"성공률: {success_rate:.1f}%", "success")
                    self.update_status(f"Batch processing completed! Success: {results['success']}/{results['total']}", "green")
                    messagebox.showinfo("성공", f"배치 처리가 완료되었습니다!\n\n성공: {results['success']}/{results['total']}\n저장 위치: {output_folder}")
                else:
                    error_msg = "모든 파일 처리가 실패했습니다"
                    self.add_log(error_msg, "error")
                    self.update_status(error_msg, "red")
                    messagebox.showerror("오류", error_msg)
            else:
                error_msg = "배치 처리 중 오류가 발생했습니다"
                self.add_log(error_msg, "error")
                self.update_status(error_msg, "red")
                messagebox.showerror("오류", error_msg)

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.add_log(error_msg, "error")
            self.update_status(error_msg, "red")
            messagebox.showerror("오류", f"오류 발생: {str(e)}")
            import traceback
            self.add_log(traceback.format_exc(), "error")
        finally:
            # Handler 제거
            logger.removeHandler(gui_handler)

    def stop_processing(self):
        """처리 중지 - threading.Event를 사용하여 안전하게 중지"""
        if self.is_processing:
            self.add_log("처리 중지 요청됨... (현재 작업 완료 후 중단됩니다)", "warning")
            self.update_status("Stopping request sent... (will stop after current task)", "orange")
            self.stop_event.set()  # 중지 플래그 설정
        else:
            messagebox.showinfo("알림", "실행 중인 작업이 없습니다.")

    def add_log(self, message, tag="info"):
        """로그를 Info 텍스트 창에 추가 (메인 스레드에서만 실행!)"""
        def update_log():
            try:
                # 로그 라인 수 제한 적용
                self.info_text.insert_with_limit(tk.END, message + "\n", tag)
            except Exception as e:
                pass

        # 메인 스레드에서만 실행 (스레드 안전)
        # 배치 업데이트로 스크롤 성능 향상
        self.root.after(0, update_log)

    def _copy_to_clipboard(self, text, show_message=True, message="복사 완료"):
        """클립보드에 텍스트 복사 (공통 함수)"""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()
            if show_message:
                messagebox.showinfo(message, f"{text[:50]}..." if len(text) > 50 else text)
            return True
        except Exception as e:
            messagebox.showerror("오류", f"복사 실패: {str(e)}")
            return False

    def copy_log_from_binding(self, event=None):
        """Ctrl+C 키 바인딩으로 선택된 텍스트 복사 (빠른 복사)"""
        try:
            selected_text = self.info_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected_text:
                self._copy_to_clipboard(selected_text, show_message=False)
                return "break"  # 기본 동작 방지
        except tk.TclError:
            pass

    def show_log_context_menu(self, event):
        """로그 우클릭 메뉴 - 복사 기능"""
        # Context Menu 캐싱 (매번 생성하지 않음)
        if not hasattr(self, 'log_context_menu'):
            self.log_context_menu = tk.Menu(self.root, tearoff=0)
            self.log_context_menu.add_command(label="선택된 텍스트 복사", command=self.copy_log_selected)
            self.log_context_menu.add_command(label="전체 로그 복사", command=self.copy_log_all)
            self.log_context_menu.add_separator()
            self.log_context_menu.add_command(label="로그 지우기", command=self.clear_log)

        self.log_context_menu.post(event.x_root, event.y_root)

    def copy_log_selected(self):
        """선택된 로그 텍스트 복사"""
        try:
            selected_text = self.info_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected_text:
                self._copy_to_clipboard(selected_text, show_message=True, message="복사 완료")
            else:
                messagebox.showwarning("알림", "복사할 텍스트를 먼저 선택하세요.")
        except tk.TclError:
            messagebox.showwarning("알림", "복사할 텍스트를 먼저 선택하세요.")

    def copy_log_all(self):
        """전체 로그 복사"""
        try:
            all_text = self.info_text.get("1.0", tk.END)
            if all_text.strip():
                self._copy_to_clipboard(all_text, show_message=True, message="복사 완료")
            else:
                messagebox.showwarning("알림", "복사할 로그가 없습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"복사 실패: {str(e)}")

    def clear_log(self):
        """로그 지우기"""
        try:
            self.info_text.delete("1.0", tk.END)
            messagebox.showinfo("완료", "로그가 지워졌습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"로그 지우기 실패: {str(e)}")

    def update_status(self, message, color="black"):
        def update_label():
            timestamp = datetime.now().strftime("%H:%M:%S")
            status_msg = f"[{timestamp}] {message}"
            bg_color = self.STATUS_COLORS.get(color, "white")  # 딕셔너리 맵핑으로 최적화
            self.status_label.config(text=status_msg, foreground=color, bg=bg_color)

        # 메인 스레드에서만 실행 (스레드 안전)
        self.root.after(0, update_label)

def main():
    root = tk.Tk()
    app = WatermarkRemovalGUI(root)
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
