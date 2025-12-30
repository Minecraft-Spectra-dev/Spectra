# Spectra

一个现代化的 Minecraft 资源包管理工具，提供直观的图形界面来浏览、配置和管理 Minecraft 资源包。

## 功能特点

- **资源包管理**：浏览和管理 Minecraft 各版本的资源包
- **实例支持**：支持多版本 Minecraft 实例，可分别管理各版本的资源包
- **收藏功能**：快速访问收藏的资源包和版本
- **下载中心**：从 Modrinth 平台搜索和下载资源包
- **Packset 支持**：支持可配置的 Packset 资源包系统
- **自定义界面**：
  - 多种背景模式（纯色、图片、黑色）
  - 背景模糊效果
  - 可自定义字体
  - 多语言支持（内置简体中文）
- **控制台**：内置开发控制台，支持多种调试命令

## 系统要求

- Python 3.14+
- Windows 操作系统
- PyQt6
- 支持 FFmpeg（用于视频背景）

## 安装

```bash
# 克隆项目
git clone <repository-url>
cd spectra

# 安装依赖
pip install -r requirements.txt
```

## 运行

```bash
python main.py
```

## 构建可执行文件

使用 PyInstaller 构建独立的可执行文件：

```bash
pyinstaller Spectra.spec --clean --noconfirm
```

构建完成后，可执行文件位于 `dist/Spectra/` 目录下。

## 配置

配置文件位于 `config.json`，主要配置项包括：

- `background_mode`：背景模式（solid/image/black）
- `background_image_path`：背景图片路径
- `background_color`：背景颜色
- `language`：界面语言（zh_CN/en_US 等）
- `minecraft_path`：Minecraft 安装目录
- `blur_opacity`：背景模糊不透明度
- `font_mode`：字体模式（系统字体/自定义）
- `version_isolation`：版本隔离开关

## 控制台命令

控制台页面支持以下命令：

| 命令 | 功能 |
|------|------|
| `restart` | 重启程序 |
| `exit` / `quit` | 退出程序 |
| `clear` | 清空控制台显示 |
| `reload` | 重新加载日志文件 |
| `info` | 显示程序信息（Python版本、窗口大小、DPI缩放、背景设置等） |
| `help` | 显示所有可用指令的帮助信息 |

## 项目结构

```
Spectra/
├── main.py                 # 程序入口
├── config.json             # 配置文件
├── requirements.txt        # Python 依赖
├── styles.py              # 样式定义
├── splash_screen.py       # 启动画面
├── window.py             # 主窗口
├── widgets/              # 自定义组件
├── ui/                   # UI 构建
├── managers/             # 管理器
│   ├── config.py         # 配置管理
│   ├── language.py       # 语言管理
│   ├── log_manager.py    # 日志管理
│   ├── background.py     # 背景管理
│   └── modrinth_manager.py # Modrinth API 管理
├── utils/                # 工具函数
├── lang/                 # 语言文件
└── svg/                  # SVG 图标
```

## 示例资源包

项目包含一个示例资源包（`example_resourcepack/`），展示了 Packset 配置系统的使用方法，支持：

- 功能分类
- 开关类型配置（bool）
- 状态切换配置（toggle）
- 自定义本地化

详细的配置说明请查看 [example_resourcepack/README.md](example_resourcepack/README.md)。

## 许可证

本项目采用开源许可证，详见 [LICENSE](LICENSE) 文件。