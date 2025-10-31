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

class WatermarkRemovalGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Watermark Removal System")
        self.root.geometry("1200x1000")
        self.root.resizable(True, True)

        self.input_file = tk.StringVar()
        self.output_folder = tk.StringVar(value="output")
        self.method = tk.StringVar(value="replicate")  # Default: Replicate API
        self.is_processing = False
        self.process = None

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
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(8, weight=1)

        self.title_label = ttk.Label(main_frame, text="Watermark Removal System", font=("Arial", 18, "bold"))
        self.title_label.grid(row=0, column=0, columnspan=3, pady=(0, 15))

        input_frame = ttk.LabelFrame(main_frame, text="Input Video", padding="10")
        input_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        input_frame.columnconfigure(1, weight=1)

        ttk.Label(input_frame, text="Video File:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(input_frame, textvariable=self.input_file, state="readonly").grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 10))
        ttk.Button(input_frame, text="Browse", command=self.select_input_file).grid(row=0, column=2)

        output_frame = ttk.LabelFrame(main_frame, text="Output", padding="10")
        output_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        output_frame.columnconfigure(1, weight=1)

        ttk.Label(output_frame, text="Output Folder:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(output_frame, textvariable=self.output_folder).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 10))
        ttk.Button(output_frame, text="Browse", command=self.select_output_folder).grid(row=0, column=2)

        method_frame = ttk.LabelFrame(main_frame, text="Processing Method (Replicate API)", padding="10")
        method_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)

        ttk.Radiobutton(method_frame, text="Replicate API - Sora2 Watermark Remover (1-2 minutes)", variable=self.method, value="replicate").pack(anchor=tk.W, pady=5)

        info_frame = ttk.LabelFrame(main_frame, text="실시간 로그 (Live Logs)", padding="10")
        info_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(0, weight=1)

        # 로그 텍스트 위젯 (스크롤바 포함)
        # state="disabled"여도 드래그 선택과 복사는 가능!
        info_text = tk.Text(info_frame, height=15, width=80, wrap=tk.WORD,
                           font=("Courier", 9), bg="black", fg="white", state="disabled")

        # disabled 상태에서도 드래그 선택 가능하도록 설정
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

        info_text.config(state="normal")
        info_text.insert("1.0", info_content)
        info_text.config(state="disabled")

        # 테그 설정 (색상)
        info_text.tag_config("error", foreground="red", background="black")
        info_text.tag_config("success", foreground="lime", background="black")
        info_text.tag_config("warning", foreground="yellow", background="black")
        info_text.tag_config("info", foreground="cyan", background="black")

        # 로그 텍스트에 우클릭 메뉴 바인딩 및 Ctrl+C 바인딩
        info_text.bind("<Button-3>", self.show_log_context_menu)
        info_text.bind("<Control-c>", self.copy_log_from_binding)  # Ctrl+C로 복사

        progress_frame = ttk.LabelFrame(main_frame, text="상태 (Status)", padding="10")
        progress_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        progress_frame.columnconfigure(0, weight=1)

        # 상태 표시 레이블 (드래그 가능, 복사 가능)
        self.status_label = tk.Label(progress_frame, text="Ready", foreground="blue",
                                     font=("Arial", 10), wraplength=700, justify=tk.LEFT,
                                     bg="white", relief=tk.SUNKEN, padx=5, pady=5)
        self.status_label.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # 상태 레이블에 드래그 기능 추가
        self.status_label.bind("<Button-1>", self.start_drag_status)
        self.status_label.bind("<B1-Motion>", self.on_drag_status)
        self.status_label.bind("<Button-3>", self.show_context_menu)  # 우클릭
        self.status_label.config(cursor="hand2")

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(20, 0))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        self.start_button = ttk.Button(button_frame, text="Start Processing", command=self.start_processing)
        self.start_button.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_processing, state="disabled")
        self.stop_button.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0))

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

    def select_output_folder(self):
        folder_path = filedialog.askdirectory(title="Select Output Folder")
        if folder_path:
            self.output_folder.set(folder_path)
            self.save_config()

    def save_config(self):
        config = {
            "input_file": self.input_file.get(),
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
                    if config.get("output_folder"):
                        self.output_folder.set(config["output_folder"])
                    if config.get("method"):
                        self.method.set(config["method"])
        except Exception as e:
            print(f"Error loading config: {e}")

    def validate_inputs(self):
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input video file")
            return False

        if not os.path.exists(self.input_file.get()):
            messagebox.showerror("Error", "Input file does not exist")
            return False

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
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.update_status("Processing started...", "blue")

        # 로그 초기화
        try:
            self.info_text.config(state="normal")
            self.info_text.delete("1.0", tk.END)
            self.info_text.insert(tk.END, "=" * 80 + "\n")
            self.info_text.config(state="disabled")
        except:
            try:
                self.info_text.config(state="disabled")
            except:
                pass

        self.add_log(f"처리 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "info")
        self.add_log(f"입력 파일: {self.input_file.get()}", "info")
        self.add_log(f"출력 폴더: {self.output_folder.get()}", "info")
        self.add_log("=" * 80, "info")

        thread = threading.Thread(target=self.process_video)
        thread.daemon = True
        thread.start()

    def process_video(self):
        try:
            input_file = self.input_file.get()
            output_folder = self.output_folder.get()
            method = self.method.get()

            # 입력 파일 검증
            if not os.path.exists(input_file):
                error_msg = f"입력 파일을 찾을 수 없습니다: {input_file}"
                self.add_log(error_msg, "error")
                self.update_status(error_msg, "red")
                messagebox.showerror("오류", error_msg)
                self.is_processing = False
                self.start_button.config(state="normal")
                self.stop_button.config(state="disabled")
                return

            # 출력 폴더 생성
            os.makedirs(output_folder, exist_ok=True)

            # 출력 파일 경로 설정 (사용자 선택 폴더에 저장)
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
                # WatermarkRemover 초기화 및 실행
                remover = WatermarkRemover()

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

            finally:
                # Handler 제거
                logger.removeHandler(gui_handler)

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

    def stop_processing(self):
        if self.process:
            try:
                self.process.terminate()
                self.update_status("Processing stopped by user", "orange")
                messagebox.showinfo("Info", "Processing has been stopped")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to stop processing: {e}")

    def add_log(self, message, tag="info"):
        """로그를 Info 텍스트 창에 추가 (메인 스레드에서만 실행!)"""
        def update_log():
            try:
                # disabled 상태여도 insert 가능
                self.info_text.config(state="normal")
                self.info_text.insert(tk.END, message + "\n", tag)
                self.info_text.see(tk.END)
                self.info_text.config(state="disabled")  # 다시 disabled로 복원
            except Exception as e:
                try:
                    self.info_text.config(state="disabled")
                except:
                    pass

        # 메인 스레드에서만 실행 (스레드 안전)
        self.root.after(0, update_log)

    def copy_log_from_binding(self, event=None):
        """Ctrl+C 키 바인딩으로 선택된 텍스트 복사 (빠른 복사)"""
        try:
            selected_text = self.info_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected_text:
                self.root.clipboard_clear()
                self.root.clipboard_append(selected_text)
                self.root.update()
                return "break"  # 기본 동작 방지
        except tk.TclError:
            pass

    def show_log_context_menu(self, event):
        """로그 우클릭 메뉴 - 복사 기능"""
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label="선택된 텍스트 복사", command=self.copy_log_selected)
        context_menu.add_command(label="전체 로그 복사", command=self.copy_log_all)
        context_menu.add_separator()
        context_menu.add_command(label="로그 지우기", command=self.clear_log)
        context_menu.post(event.x_root, event.y_root)

    def copy_log_selected(self):
        """선택된 로그 텍스트 복사"""
        try:
            selected_text = self.info_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected_text:
                self.root.clipboard_clear()
                self.root.clipboard_append(selected_text)
                self.root.update()
                messagebox.showinfo("복사 완료", "선택된 로그가 클립보드에 복사되었습니다.")
            else:
                messagebox.showwarning("알림", "복사할 텍스트를 먼저 선택하세요.")
        except tk.TclError:
            messagebox.showwarning("알림", "복사할 텍스트를 먼저 선택하세요.")

    def copy_log_all(self):
        """전체 로그 복사"""
        try:
            all_text = self.info_text.get("1.0", tk.END)
            if all_text.strip():
                self.root.clipboard_clear()
                self.root.clipboard_append(all_text)
                self.root.update()
                messagebox.showinfo("복사 완료", "전체 로그가 클립보드에 복사되었습니다.")
            else:
                messagebox.showwarning("알림", "복사할 로그가 없습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"복사 실패: {str(e)}")

    def clear_log(self):
        """로그 지우기"""
        try:
            self.info_text.config(state="normal")
            self.info_text.delete("1.0", tk.END)
            self.info_text.config(state="disabled")
            messagebox.showinfo("완료", "로그가 지워졌습니다.")
        except Exception as e:
            try:
                self.info_text.config(state="disabled")
            except:
                pass
            messagebox.showerror("오류", f"로그 지우기 실패: {str(e)}")

    def update_status(self, message, color="black"):
        def update_label():
            timestamp = datetime.now().strftime("%H:%M:%S")
            status_msg = f"[{timestamp}] {message}"
            self.status_label.config(text=status_msg, foreground=color)

            # 오류 메시지면 배경색도 변경
            if color == "red":
                self.status_label.config(bg="#ffe6e6")  # 연한 빨강
            elif color == "green":
                self.status_label.config(bg="#e6ffe6")  # 연한 초록
            elif color == "orange":
                self.status_label.config(bg="#fff0e6")  # 연한 주황
            else:
                self.status_label.config(bg="white")

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
