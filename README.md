# ImagePromptViewer

📷 一个用于查看AI生成图像提示词的工具

## 概述

ImagePromptViewer 是一个用于提取和展示AI生成图像提示词的工具。它可以自动从图片元数据中获取生成参数，或在元数据不可用时尝试推测可能的提示词。

## 主要功能

- 🖥️ 简洁的图形界面
- 🔍 自动解析常见AI生成工具的元数据
- 🤖 理论支持多种AI生成模型（FLUX、Stable Diffusion、MidJourney等）生成的图片
- 🔄 支持多种图片格式（PNG、JPEG、WEBP等）

## 配置
- 需要安装[Exiftools](https://exiftool.org/)，并把它加到系统路径中；
- 如果安装了Ollama，就可以使用LLM猜测解析元数据的功能了，可以根据自己的模型名称更新源码后使用，默认是'deepseek-r1:8b'。

## 安装

```bash
git clone https://github.com/highwindmx/ImagePromptViewer.git
cd ImagePromptViewer
pip install -r requirements.txt
python picture_browser.py
```
```windows
如果你使用windows x64系统，我已经build好了一个exe文件，可以用快捷方式直接打开
```

## 感谢
1. TRAE 创建和修订代码
2. DeepSeek 回答代码问题，撰写本Readme文件
3. 本人 熬夜地从AI幻觉中爬出来
   
## 许可证
MIT License - 详见 [LICENSE](LICENSE)

## 未来计划
完全没有
