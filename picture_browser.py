import re
import os
import time
import requests  # 新增库用于与 Ollama API 交互
from PIL import Image, ImageTk
import exiftool
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import threading

SUPPORT_TYPES = ('.png', '.jpg', '.jpeg')

# 新增 ToolTip 类用于显示完整文件名提示
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip, text=self.text, background="#ffffff", relief="solid", borderwidth=1)
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

class ImageBrowser:
    def __init__(self, root):
        self.root = root
        self.root.title("图片浏览器")
        # 设置窗口最小宽度和高度
        self.root.minsize(width=1000, height=600)
        # 配置根窗口的网格布局
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=3)  # 让右侧主显示区域占比更大

        # 左侧缩略图框架，包含滚动条
        self.thumbnail_frame = tk.Frame(root)
        self.thumbnail_frame.grid(row=0, column=0, sticky="nsew")
        self.thumbnail_frame.grid_rowconfigure(0, weight=1)
        self.thumbnail_frame.grid_columnconfigure(0, weight=1)
        # 为整个缩略图框架绑定滚轮事件
        self.bind_mouse_wheel_events(self.thumbnail_frame)
        self.thumbnail_canvas = tk.Canvas(self.thumbnail_frame)
        self.thumbnail_canvas.grid(row=0, column=0, sticky="nsew")
        self.thumbnail_scrollbar = tk.Scrollbar(self.thumbnail_frame, orient="vertical", command=self.thumbnail_canvas.yview)
        self.thumbnail_scrollbar.grid(row=0, column=1, sticky="ns")
        self.thumbnail_inner_frame = tk.Frame(self.thumbnail_canvas)
        self.thumbnail_inner_frame.bind("<Configure>", lambda e: self.thumbnail_canvas.configure(scrollregion=self.thumbnail_canvas.bbox("all")))
        self.thumbnail_canvas.create_window((0, 0), window=self.thumbnail_inner_frame, anchor="nw")      
        self.thumbnail_canvas.configure(yscrollcommand=self.thumbnail_scrollbar.set)
        # 新增一个列表来存储 PhotoImage 对象
        self.thumbnail_images = []
        # 设置缩略图列数
        self.thumbnail_columns = 3

        # 右侧主显示区域
        self.main_frame = tk.Frame(root)
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        # self.main_frame.grid_rowconfigure(0, weight=1)
        # self.main_frame.grid_rowconfigure(1, weight=4)  # 让图片显示区域占比更大
        # self.main_frame.grid_rowconfigure(2, weight=1)
        # # 调整滚动显示区域的权重，降低其高度占比
        # self.main_frame.grid_rowconfigure(2, weight=1)  # 原代码未设置或权重过大，可调整为合适值
        # self.main_frame.grid_columnconfigure(0, weight=1)

        # 按钮框架，用于放置前后张按钮
        self.button_frame = tk.Frame(self.main_frame)
        self.button_frame.grid(row=0, column=0, sticky="ew")
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)

        # 左右按钮
        self.prev_button = tk.Button(self.button_frame, text="上一张", command=self.prev_image)
        self.prev_button.grid(row=0, column=0, sticky="ew")

        self.next_button = tk.Button(self.button_frame, text="下一张", command=self.next_image)
        self.next_button.grid(row=0, column=1, sticky="ew")

        # 中间图片显示框架
        self.image_frame = tk.Frame(self.main_frame)
        self.image_frame.grid(row=1, column=0, sticky="nsew")
        self.image_frame.grid_rowconfigure(0, weight=1)  # 让图片显示区域占比更大
        self.image_frame.grid_columnconfigure(0, weight=1)  # 只需要一列来显示图片

        self.image_label = tk.Label(self.image_frame, text="请拖放图片于此处")
        self.image_label.grid(row=0, column=0, sticky="nsew")

        # 底部信息框架
        self.info_frame = tk.Frame(self.main_frame)
        self.info_frame.grid(row=2, column=0, sticky="ew")
        self.info_frame.grid_rowconfigure(0, weight=1)
        self.info_frame.grid_rowconfigure(1, weight=1)
        self.info_frame.grid_columnconfigure(0, weight=1)

        self.info_label = tk.Label(self.info_frame, text="")
        self.info_label.grid(row=0, column=0, sticky="ew")

        # 新增可复制文本框
        self.copyable_text = tk.StringVar()
        self.copyable_text.set("")  # 初始化文本变量
        self.copyable_entry = tk.Text(self.info_frame, state='disabled', wrap='word', height=4)
        self.copyable_entry.grid(row=1, column=0, sticky="ew")
       
        # 加载提示标签
        self.loading_label = tk.Label(self.main_frame, text="正在加载...", fg="red")
        self.loading_label.grid(row=0, column=0, sticky="n")
        self.loading_label.grid_remove()  # 初始时隐藏

        # 初始化图片列表和当前索引
        self.image_list = []
        self.current_index = 0
        self.exiftool_lock = threading.Lock()  # 添加锁来避免并发调用 exiftool
        self.is_ollama_request_running = False  # 新增标志变量
        self.cancel_ollama_request = False  # 新增取消标志变量
        self.current_loading_folder = None  # 新增属性，用于记录当前正在加载的文件夹

        # 绑定拖放事件
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.on_drop)

    def update_copyable_text(self, text):
        self.copyable_entry.config(state='normal')
        self.copyable_entry.delete(1.0, tk.END)
        self.copyable_entry.insert(tk.END, text)
        self.copyable_entry.config(state='disabled')


    def bind_mouse_wheel_events(self, widget):
        widget.bind("<MouseWheel>", self.on_mouse_wheel)
        widget.bind("<Button-4>", self.on_mouse_wheel)
        widget.bind("<Button-5>", self.on_mouse_wheel)

    def on_drop(self, event):
        print(event.data)
        if event.data.startswith('{'):
            file_path = re.findall(r'{([^}]+)}', event.data)[0]
        else:
            file_path = event.data.strip()
        if file_path.lower().endswith(SUPPORT_TYPES):
            try:
                # 检查文件是否存在
                if os.path.exists(file_path):
                    folder = os.path.dirname(file_path)
                    # 检查是否需要重新加载文件夹
                    if folder != self.current_loading_folder:
                        self.current_loading_folder = folder
                        # 避免重新加载整个文件夹
                        if file_path not in self.image_list:
                            self.image_list.append(file_path)
                            self.show_thumbnails()
                        self.current_index = self.image_list.index(file_path)
                        self.show_image()
                        # 使用线程来加载图片
                        self.show_loading()
                        threading.Thread(target=self.load_images_thread, args=(folder,)).start()
                    else:
                        # 文件夹相同，只需显示当前图片
                        if file_path not in self.image_list:
                            self.image_list.append(file_path)
                            self.show_thumbnails()
                        self.current_index = self.image_list.index(file_path)
                        self.show_image()
                else:
                    messagebox.showerror("错误", f"文件不存在: {file_path}")
            except ValueError:
                messagebox.showerror("错误", f"文件未在列表中: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"处理文件时出错: {e}")

    def load_images_thread(self, folder):
        def load_images():
            self.image_list = []
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(SUPPORT_TYPES):
                        file_path = os.path.join(root, file)
                        if os.path.exists(file_path):
                            self.image_list.append(file_path)
                            # 更新 loading_label 显示加载进度
                            progress_text = f"正在加载 {os.path.basename(file_path)}"
                            self.root.after(0, lambda: self.loading_label.config(text=progress_text))
            # 加载完成后更新缩略图
            self.root.after(0, self.show_thumbnails)
            # 确保隐藏加载提示
            self.root.after(0, self.hide_loading)
            self.current_loading_folder = None  # 加载完成后重置当前加载文件夹

        threading.Thread(target=load_images).start()

    def show_thumbnails(self):
        def update_thumbnails():
            # 清空之前的缩略图
            for widget in self.thumbnail_inner_frame.winfo_children():
                widget.destroy()
            # 清空之前的 PhotoImage 对象列表
            self.thumbnail_images = []

            row = 0
            col = 0
            for index, image_path in enumerate(self.image_list):
                try:
                    image = Image.open(image_path)
                    image.thumbnail((100, 100))
                    photo = ImageTk.PhotoImage(image)
                    # 将 PhotoImage 对象添加到列表中
                    self.thumbnail_images.append(photo)
                    thumbnail_label = tk.Label(self.thumbnail_inner_frame, image=photo)
                    # 新增：为缩略图标签绑定滚轮事件
                    self.bind_mouse_wheel_events(thumbnail_label)
                    thumbnail_label.image = photo
                    thumbnail_label.grid(row=row * 2, column=col, padx=5, pady=5)
                    thumbnail_label.bind("<Button-1>", lambda e, idx=index: self.on_thumbnail_click(idx))
                    #print(f"成功加载缩略图: {image_path}")
                    # 更新 loading_label 显示加载进度
                    progress_text = f"正在加载 {os.path.basename(image_path)}"
                    self.root.after(0, lambda: self.loading_label.config(text=progress_text))
                    # 显示文件名
                    file_name = os.path.basename(image_path)
                    ToolTip(thumbnail_label, file_name)
                    col += 1
                    if col >= self.thumbnail_columns:
                        col = 0
                        row += 1
                except Exception as e:
                    print(f"无法加载缩略图: {image_path}, 错误: {e}")

            self.thumbnail_inner_frame.update_idletasks()
            self.thumbnail_canvas.configure(scrollregion=self.thumbnail_canvas.bbox("all"))
            # 移除全局滚轮事件绑定
            # self.thumbnail_canvas.unbind_all("<MouseWheel>")
            # self.thumbnail_canvas.unbind_all("<Button-4>")
            # self.thumbnail_canvas.unbind_all("<Button-5>")
            # 仅在缩略图画布和缩略图内部框架上绑定滚轮事件
            self.bind_mouse_wheel_events(self.thumbnail_canvas)
            self.bind_mouse_wheel_events(self.thumbnail_inner_frame)
            # 加载完成后隐藏加载提示
            self.root.after(0, self.hide_loading)

        # 显示加载提示
        self.show_loading()
        # 使用线程来更新缩略图
        threading.Thread(target=update_thumbnails).start()

    def select_image(self, event):
        file_path = filedialog.askopenfilename(filetypes=[("图片文件", "*.png;*.jpg;*.jpeg")])
        if file_path:
            # 使用线程来加载图片
            self.show_loading()
            threading.Thread(target=self.load_images_thread, args=(os.path.dirname(file_path),)).start()
            self.current_index = self.image_list.index(file_path)
            self.show_image()

    def show_loading(self):
        self.loading_label.grid()

    def hide_loading(self):
        self.loading_label.grid_remove()

    def check_ollama_request(self):
        if self.is_ollama_request_running:
            self.root.after(100, self.check_ollama_request)
        else:
            self.cancel_ollama_request = False

    def on_mouse_wheel(self, event):
        # 检查事件发生的部件是否为缩略图画布
        if event.widget == self.thumbnail_canvas:
            # 处理不同操作系统的滚轮事件处理
            if event.delta:
                # Windows 和 macOS 系统
                self.thumbnail_canvas.yview_scroll(-1 * (event.delta // 60), "units")
            elif event.num == 4:
                # Linux 系统向上滚动
                self.thumbnail_canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                # Linux 系统向下滚动
                self.thumbnail_canvas.yview_scroll(1, "units")

    def show_image(self):
        if self.image_list:
            try:
                # 取消正在进行的 Ollama 请求
                if self.is_ollama_request_running:
                    self.cancel_ollama_request = True
                    self.check_ollama_request()
                image_path = self.image_list[self.current_index]
                image = Image.open(image_path)
                width, height = image.size
                aspect_ratio = f"{width}:{height}"
                file_format = image.format
                creation_time = time.ctime(os.path.getctime(image_path))
                file_name = os.path.basename(image_path)  # 获取文件名

                # Resize the image to fit the window
                max_width = 800
                max_height = 600
                if width > max_width or height > max_height:
                    ratio = min(max_width / width, max_height / height)
                    new_width = int(width * ratio)
                    new_height = int(height * ratio)
                    # Replace ANTIALIAS with LANCZOS
                    image = image.resize((new_width, new_height), Image.LANCZOS)

                photo = ImageTk.PhotoImage(image)
                self.image_label.config(image=photo, text="")
                self.image_label.image = photo

                # Display image information
                info_text = f"文件名: {file_name}, 长宽比: {aspect_ratio}, 格式: {file_format}, 创建时间: {creation_time}"
                self.info_label.config(text=info_text)

                # 更新可复制文本框内容
                #self.copyable_text.set(self.extract_text_values())
                self.update_copyable_text(self.extract_text_values())

            except Exception as e:
                messagebox.showerror("错误", f"无法加载图片: {e}")
        else:
            self.image_label.config(text="请拖放图片于此处", image="")

    def prev_image(self):
        if self.image_list:
            self.current_index = (self.current_index - 1) % len(self.image_list)
            self.show_image()

    def next_image(self):
        if self.image_list:
            self.current_index = (self.current_index + 1) % len(self.image_list)
            self.show_image()

    def extract_text_values(self):
        with self.exiftool_lock:  # 使用锁来避免并发调用
            try:
                with exiftool.ExifToolHelper() as et:
                    metadata = et.get_metadata(self.image_list[self.current_index])
                    pattern1 = r'"text"\s*:\s*"([^"]+)"'
                    cleaned_text1 = re.findall(pattern1, str(metadata))
                    if cleaned_text1:
                        return "|||".join(cleaned_text1).strip()
                    else:
                        if not self.is_ollama_request_running:  # 检查标志
                            self.is_ollama_request_running = True  # 设置标志为True
                            # 显示加载提示
                            self.show_loading()
                            # 启动线程进行猜测提示词
                            threading.Thread(target=self.guess_prompt_thread, args=(metadata,)).start()
                        return "正在通过Ollama猜测提示词..."
            except Exception as e:
                return "未找到提示词（可能并非是文生图？）"

    def guess_prompt_thread(self, metadata):
        guessed_prompt = self.guess_prompt_from_metadata(metadata)
        # 在主线程中更新可复制文本框内容
        self.root.after(0, lambda: self.update_copyable_text(guessed_prompt))
        # 隐藏加载提示
        self.root.after(0, self.hide_loading)
        self.is_ollama_request_running = False  # 请求完成，设置标志为False

    def guess_prompt_from_metadata(self, metadata):
        try:
            self.is_ollama_request_running = True
            # 将 metadata 转换为适合发送给 Ollama 的文本格式
            metadata_text = str(metadata)
            # 构建请求体
            prompt = '''
                请猜测上述元数据字符串中哪句最可能是提示词？
            '''
            payload = {
                "model": "deepseek-r1:8b",        # 替换你的模型名称，如deepseek-r1:8b
                "stream": False,          # 关键参数：关闭流式传输
                "prompt": f"元数据为：{metadata_text},{prompt}",
                "options": {
                    "temperature": 1.0    # 其他参数（可选）
                }
            }
            headers = {
                "Content-Type": "application/json",
            }
            ollama_api_url = "http://localhost:11434/api/generate"
            with requests.Session() as session:
                req = requests.Request('POST', ollama_api_url, json=payload, headers=headers)
                prepared = req.prepare()
                resp = session.send(prepared, timeout=90)  # 适当延长超时时间
                while self.cancel_ollama_request:
                    resp.close()
                    session.close()
                    self.is_ollama_request_running = False
                    return "请求已取消"
            resp.raise_for_status()  # 检查 HTTP 错误
        except requests.RequestException as e:
            return f"网络请求错误: {e}"
        except Exception as e:
            return f"Ollama错误: {e}"
        else:
            if resp.status_code == 200:
                try:
                    full_response = resp.json()
                    print(full_response["response"])  # 实际生成内容
                    # 尝试分割响应                    
                    parts = full_response["response"].split("</think>")
                    if len(parts) > 1:
                        answer = parts[1].strip()
                        return answer
                    else:
                        return full_response["response"].strip()
                except ValueError:
                    return "Ollama错误，响应不是有效的JSON格式"
            else:
                return f"Ollama错误，状态码: {resp.status_code}"
        finally:
            self.is_ollama_request_running = False
            
    def on_thumbnail_click(self, index):
        self.current_index = index
        self.show_image()

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = ImageBrowser(root)
    root.mainloop()
