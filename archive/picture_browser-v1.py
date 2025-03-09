import re
import os
import time
from PIL import Image, ImageTk
import exiftool
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD

SUPPORT_TYPES = ('.png', '.jpg', '.jpeg')

class ImageBrowser:
    def __init__(self, root):
        self.root = root
        self.root.title("图片浏览器")
        # 设置窗口最小宽度和高度
        self.root.minsize(width=800, height=600)

        # 左侧缩略图框架，包含滚动条
        self.thumbnail_frame = tk.Frame(root)
        self.thumbnail_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.thumbnail_canvas = tk.Canvas(self.thumbnail_frame)
        self.thumbnail_inner_frame = tk.Frame(self.thumbnail_canvas)
        self.thumbnail_scrollbar = tk.Scrollbar(self.thumbnail_frame, orient="vertical", command=self.thumbnail_canvas.yview)
        self.thumbnail_canvas.configure(yscrollcommand=self.thumbnail_scrollbar.set)

        self.thumbnail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.thumbnail_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.thumbnail_canvas.create_window((0, 0), window=self.thumbnail_inner_frame, anchor="nw")

        self.thumbnail_inner_frame.bind("<Configure>", lambda e: self.thumbnail_canvas.configure(scrollregion=self.thumbnail_canvas.bbox("all")))

        # 新增一个列表来存储 PhotoImage 对象
        self.thumbnail_images = []

        # 右侧主显示区域
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 中间图片显示框架
        self.image_frame = tk.Frame(self.main_frame)
        self.image_frame.pack(pady=10)

        # 左右按钮
        self.prev_button = tk.Button(self.image_frame, text="上一张", command=self.prev_image)
        self.prev_button.pack(side=tk.LEFT)

        self.image_label = tk.Label(self.image_frame)
        self.image_label.pack(side=tk.LEFT)

        self.next_button = tk.Button(self.image_frame, text="下一张", command=self.next_image)
        self.next_button.pack(side=tk.LEFT)

        # 底部信息框架
        self.info_frame = tk.Frame(self.main_frame)
        self.info_frame.pack(fill=tk.X, pady=10, expand=False, side=tk.TOP)
        self.info_label = tk.Label(self.info_frame, text="")
        self.info_label.pack()

        # 新增可复制文本框
        self.copyable_text = tk.StringVar()
        self.copyable_entry = tk.Entry(self.info_frame, textvariable=self.copyable_text, state='readonly', justify='center')
        self.copyable_entry.pack(fill=tk.X)

        # 初始化图片列表和当前索引
        self.image_list = []
        self.current_index = 0

        # 绑定拖放事件
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.on_drop)

    def on_drop(self, event):
        file_paths = event.data.split()
        file_path = file_paths[0].strip('{}')  # 只取第一个并去除路径字符串的大括号
        if file_path.lower().endswith(SUPPORT_TYPES):
            try:
                # 检查文件是否存在
                if os.path.exists(file_path):
                    # 避免重新加载整个文件夹
                    if file_path not in self.image_list:
                        self.image_list.append(file_path)
                        self.show_thumbnails()
                    self.current_index = self.image_list.index(file_path)
                    self.show_image()
                    self.load_images(os.path.dirname(file_path))
                    self.show_thumbnails()
                else:
                    messagebox.showerror("错误", f"文件不存在: {file_path}")
            except ValueError:
                messagebox.showerror("错误", f"文件未在列表中: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"处理文件时出错: {e}")

    def select_image(self, event):
        file_path = filedialog.askopenfilename(filetypes=[("图片文件", "*.png;*.jpg;*.jpeg")])
        if file_path:
            self.load_images(os.path.dirname(file_path))
            self.current_index = self.image_list.index(file_path)
            self.show_image()

    def load_images(self, folder):
        self.image_list = []
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.lower().endswith(SUPPORT_TYPES):
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        self.image_list.append(file_path)

    def show_thumbnails(self):
        # 清空之前的缩略图
        for widget in self.thumbnail_inner_frame.winfo_children():
            widget.destroy()
        # 清空之前的 PhotoImage 对象列表
        self.thumbnail_images = []

        for index, image_path in enumerate(self.image_list):
            try:
                image = Image.open(image_path)
                image.thumbnail((100, 100))
                photo = ImageTk.PhotoImage(image)
                # 将 PhotoImage 对象添加到列表中
                self.thumbnail_images.append(photo)
                thumbnail_label = tk.Label(self.thumbnail_inner_frame, image=photo)
                thumbnail_label.image = photo
                thumbnail_label.pack(side=tk.TOP)
                thumbnail_label.bind("<Button-1>", lambda e, idx=index: self.on_thumbnail_click(idx))
                print(f"成功加载缩略图: {image_path}")
            except Exception as e:
                print(f"无法加载缩略图: {image_path}, 错误: {e}")

        self.thumbnail_inner_frame.update_idletasks()
        self.thumbnail_canvas.configure(scrollregion=self.thumbnail_canvas.bbox("all"))

    def show_image(self):
        if self.image_list:
            try:
                image_path = self.image_list[self.current_index]
                image = Image.open(image_path)
                width, height = image.size
                aspect_ratio = f"{width}:{height}"
                file_format = image.format
                creation_time = time.ctime(os.path.getctime(image_path))

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
                self.image_label.config(image=photo)
                self.image_label.image = photo

                # Display image information
                info_text = f"长宽比: {aspect_ratio}, 格式: {file_format}, 创建时间: {creation_time}"
                self.info_label.config(text=info_text)

                # 更新可复制文本框内容
                self.copyable_text.set(self.extract_text_values())

            except Exception as e:
                messagebox.showerror("错误", f"无法加载图片: {e}")

    def prev_image(self):
        if self.image_list:
            self.current_index = (self.current_index - 1) % len(self.image_list)
            self.show_image()

    def next_image(self):
        if self.image_list:
            self.current_index = (self.current_index + 1) % len(self.image_list)
            self.show_image()

    def extract_text_values(self):
        with exiftool.ExifToolHelper() as et:
            metadata = et.get_metadata(self.image_list[self.current_index])
            pattern = r'"text"\s*:\s*"([^"]+)"'
            cleaned_text = re.findall(pattern, str(metadata))
            if cleaned_text:
                return "|||".join(cleaned_text).strip()
            else:
                return "未找到提示词（可能是图生图?）"

    def on_thumbnail_click(self, index):
        self.current_index = index
        self.show_image()

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = ImageBrowser(root)
    root.mainloop()