import os
import tkinter as tk
from PIL import ImageTk, Image

class ImageBrowser:
    def __init__(self, root, folder_path):
        self.root = root
        self.folder_path = folder_path
        self.image_files = []
        self.current_index = 0
        
        # 获取文件夹中所有图片文件
        self.load_images()
        
        # 创建界面
        self.create_widgets()
        
        # 绑定键盘事件
        self.root.bind("<Left>", self.prev_image)
        self.root.bind("<Right>", self.next_image)
        
        # 显示第一张图片
        self.show_image()

    def load_images(self):
        """加载文件夹中的图片文件"""
        valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        for filename in os.listdir(self.folder_path):
            if filename.lower().endswith(valid_extensions):
                self.image_files.append(filename)
        self.image_files.sort()  # 按文件名排序

    def create_widgets(self):
        """创建界面元素"""
        self.root.title("图片浏览器")
        self.image_label = tk.Label(self.root)
        self.image_label.pack()
        
        # 状态栏
        self.status = tk.StringVar()
        status_bar = tk.Label(self.root, textvariable=self.status, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.update_status()

    def show_image(self):
        """显示当前图片"""
        if not self.image_files:
            self.status.set("文件夹中没有图片")
            return
            
        image_path = os.path.join(self.folder_path, self.image_files[self.current_index])
        try:
            img = Image.open(image_path)
            # 调整图片尺寸以适应窗口（可选）
            img.thumbnail((800, 600))
            self.tk_img = ImageTk.PhotoImage(img)
            self.image_label.config(image=self.tk_img)
        except Exception as e:
            self.status.set(f"无法加载图片: {str(e)}")

    def update_status(self):
        """更新状态栏"""
        total = len(self.image_files)
        if total == 0:
            self.status.set("没有找到图片文件")
        else:
            self.status.set(f"图片 {self.current_index + 1}/{len(self.image_files)} ｜ 文件名: {self.image_files[self.current_index]}")

    def next_image(self, event=None):
        """下一张图片"""
        if self.current_index < len(self.image_files) - 1:
            self.current_index += 1
            self.show_image()
            self.update_status()

    def prev_image(self, event=None):
        """上一张图片"""
        if self.current_index > 0:
            self.current_index -= 1
            self.show_image()
            self.update_status()

if __name__ == "__main__":
    # 设置要浏览的图片文件夹路径
    image_folder = r"C:\Users\Administrator\Desktop\新建文件夹"  # 替换为你的图片文件夹路径
    
    root = tk.Tk()
    browser = ImageBrowser(root, image_folder)
    root.mainloop()