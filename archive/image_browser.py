import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import os

class ImageBrowser:
    def __init__(self, root):
        self.root = root
        self.root.title("图片浏览器")

        # 创建主框架
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 左边的图片列表框
        self.image_listbox = tk.Listbox(self.main_frame, width=20)
        self.image_listbox.pack(side=tk.LEFT, fill=tk.Y)
        self.image_listbox.bind("<<ListboxSelect>>", self.on_image_select)

        # 右边的图片显示区域
        self.image_label: tk.Label = tk.Label(self.main_frame)  # 添加类型注解
        self.image_label.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 下方的缩略图区域
        self.thumbnail_frame = tk.Frame(root)
        self.thumbnail_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # 加载图片按钮
        self.load_button = tk.Button(root, text="加载图片", command=self.load_images)
        self.load_button.pack(side=tk.TOP)

        # 存储图片路径
        self.image_paths = []

    def load_images(self):
        # 选择图片文件夹
        folder = filedialog.askdirectory()
        if folder:
            # 清空列表框和缩略图区域
            self.image_listbox.delete(0, tk.END)
            for widget in self.thumbnail_frame.winfo_children():
                widget.destroy()

            # 获取文件夹中的所有图片文件
            self.image_paths = []
            for filename in os.listdir(folder):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    self.image_paths.append(os.path.join(folder, filename))
                    self.image_listbox.insert(tk.END, filename)

            # 显示缩略图
            # 遍历所有图片路径
            for i, path in enumerate(self.image_paths):
                # 打开图片文件
                thumbnail = Image.open(path)
                # 将图片缩放到最大尺寸为 100x100 的缩略图
                thumbnail.thumbnail((100, 100))
                # 将缩略图转换为 Tkinter 可以显示的 PhotoImage 对象
                photo = ImageTk.PhotoImage(thumbnail)
                # 创建一个 Label 组件用于显示缩略图
                label: tk.Label = tk.Label(self.thumbnail_frame, image=photo)  # 添加类型注解
                # 为 Label 组件设置 image 属性，防止图片被垃圾回收
                label.image = photo
                # 将 Label 组件添加到缩略图区域的左侧
                label.pack(side=tk.LEFT)
                # 为 Label 组件绑定鼠标点击事件，点击时调用 on_thumbnail_click 方法
                label.bind("<Button-1>", lambda event, index=i: self.on_thumbnail_click(index))

    def on_image_select(self, event):
        # 获取选中的图片索引
        index = self.image_listbox.curselection()
        if index:
            index = index[0]
            path = self.image_paths[index]
            # 打开并显示图片
            image = Image.open(path)
            photo = ImageTk.PhotoImage(image)
            self.image_label.config(image=photo)
            self.image_label.image = photo

    def on_thumbnail_click(self, index):
        # 选中缩略图对应的图片
        self.image_listbox.selection_clear(0, tk.END)
        self.image_listbox.selection_set(index)
        self.on_image_select(None)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageBrowser(root)
    root.mainloop()