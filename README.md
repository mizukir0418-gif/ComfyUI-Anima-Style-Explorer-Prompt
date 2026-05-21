# ComfyUI Anima Style Explorer Prompt

一个专为二次元画师风格探索打造的 ComfyUI 辅助侧边栏插件。内置高能安全防御流与自动化交互按钮，完美对接外网风格检索。

## ✨ 核心特性

- **🌐 嵌入式风格浏览器**：在 ComfyUI 内部一键唤出风格侧边栏，丝滑浏览大触作品。
- **🔍 智能双站并排检索**：一键自动提取剪贴板画师 ID。自动过滤 Stable Diffusion 权重转义符 `\`，在 Danbooru 与 E-Hentai 之间智能转换规范（如自动处理空格与下划线）并排双屏搜索。
- **✍️ 自动化寻轨填入**：点击侧边栏复制画师后，一键自动在选中的 Anima 模板节点中寻找空槽位，按顺序自动填入（artist_1 至 artist_10）。
- **🛡️ 工业级安全沙箱**：
  - **SSRF 深度拦截**：自动解算 DNS 封杀内网、回环、本地链路及云端元数据地址，防止内网穿透。
  - **图片 DNA 字节审计**：强行读取二进制魔术字节（Magic Bytes），彻底拦截木马/脚本伪装成的假图片。
  - **流式下载控制**：硬限制最大 30MB 缓冲区，免疫文件大弹头撑爆硬盘。
  -**使用教程**：https://www.bilibili.com/video/BV1pWLt6sET9/?share_source=copy_web&vd_source=9198fc46d1ce8dbbf2f5c607bbc4f354

## 🚀 安装方法

### 方法一：Git 克隆（推荐）
打开终端进入你的 ComfyUI 插件目录 `ComfyUI/custom_nodes/`，执行：
```bash
git clone https://github.com/mizukir0418-gif/ComfyUI-Anima-Style-Explorer-Prompt.git
