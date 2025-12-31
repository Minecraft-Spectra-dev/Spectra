# Spectra 项目结构

```
Spectra/
├── main.py                         # 程序入口
├── config.json                     # 配置文件
├── requirements.txt                # 依赖包列表
├── icon.png                        # 应用图标
├── icon-old.png                    # 旧版应用图标
├── styles.py                       # 样式定义
├── splash_screen.py                # 启动画面
├── window.py                       # 主窗口
├── Spectra.spec / main.spec        # PyInstaller 打包配置
├── widgets/                        # 自定义组件
│   ├── __init__.py
│   ├── buttons.py                  # 按钮组件（JellyButton, CardButton等）
│   ├── cards.py                    # 卡片组件
│   ├── file_explorer.py            # 文件浏览器组件
│   ├── labels.py                   # 标签组件（ClickableLabel）
│   ├── modrinth_cards.py           # Modrinth 项目卡片
│   ├── resourcepack_config_editor.py     # 资源包配置编辑器
│   ├── resourcepack_config_editor_page.py # 资源包配置编辑页面
│   └── text_renderer.py            # 文本渲染器
├── ui/                             # UI 构建与页面
│   ├── __init__.py
│   ├── builder.py                  # UI 构建器
│   ├── components.py              # 通用 UI 组件
│   ├── console_page.py             # 控制台页面
│   ├── download_thread.py          # 下载线程
│   ├── downloads_page.py           # 下载页面
│   ├── instances_page.py           # 实例页面
│   ├── settings_page.py            # 设置页面
│   └── styles.py                   # UI 样式定义
├── managers/                       # 管理器
│   ├── __init__.py
│   ├── background.py               # 背景管理器
│   ├── config.py                   # 配置管理器
│   ├── language.py                 # 语言管理器
│   ├── log_manager.py              # 日志管理器
│   ├── modrinth_manager_async.py   # Modrinth 异步管理器
│   └── modrinth_manager.py         # Modrinth 管理器
├── utils/                          # 工具函数
│   ├── __init__.py
│   ├── icons.py                    # 图标工具
│   └── path_helper.py              # 路径辅助工具
├── tools/                          # 工具
│   ├── __init__.py
│   └── log_viewer.py               # 日志查看器
├── svg/                            # SVG 图标资源（50个图标）
├── png/                            # PNG 图标资源
│   ├── block.png
│   ├── fabric.png
│   ├── forge.png
│   ├── neoforged.png
│   └── unknown_pack.png
├── lang/                           # 语言文件
│   ├── en_US.json                  # 英文翻译
│   └── zh_CN.json                  # 中文翻译
├── example_resourcepack/           # 示例资源包
│   ├── pack.mcmeta                 # 资源包元数据
│   ├── packset.json                # 资源包集配置
│   ├── README.md                   # 说明文档
│   ├── packset_lang/               # 资源包语言文件
│   └── assets/                     # 资源包资源
├── .github/                        # GitHub 配置
│   └── workflows/
│       └── build.yml               # CI/CD 构建配置
├── build/                          # 构建输出目录
├── dist/                           # 打包输出目录
├── logs/                           # 日志目录
├── __pycache__/                    # Python 缓存
├── .gitignore                      # Git 忽略配置
├── LICENSE                         # 许可证
├── README.md                       # 项目说明
└── PROJECT_STRUCTURE.md            # 项目结构文档
```

## 模块说明

### 核心文件
- **main.py**: 程序入口文件，负责初始化应用、显示启动画面和主窗口
- **styles.py**: 定义所有UI样式常量，包括按钮、滑块等组件的样式
- **splash_screen.py**: 启动画面类，显示应用图标
- **window.py**: 主窗口类，包含窗口初始化、事件处理、页面切换等核心逻辑
- **config.json**: 应用配置文件
- **requirements.txt**: Python 依赖包列表

### widgets/ - 自定义组件
- **buttons.py**: 自定义按钮组件
  - `JellyButton`: 带动画效果的按钮
  - `CardButton`: 卡片式按钮
- **cards.py**: 卡片相关组件
- **file_explorer.py**: 文件浏览器组件，支持目录导航和文件选择
- **labels.py**: 自定义标签组件
  - `ClickableLabel`: 可点击的标签
- **modrinth_cards.py**: Modrinth 项目展示卡片
- **resourcepack_config_editor.py**: 资源包配置编辑器组件
- **resourcepack_config_editor_page.py**: 资源包配置编辑页面
- **text_renderer.py**: 文本渲染工具

### ui/ - UI 构建与页面
- **builder.py**: UI 构建器，负责创建各种UI组件
  - 导航按钮
  - 标题栏按钮
  - 背景选项卡片
  - 可展开菜单
  - 设置页面
- **components.py**: 通用 UI 组件集合
- **console_page.py**: 控制台输出页面
- **download_thread.py**: 下载任务线程处理
- **downloads_page.py**: 下载管理页面
- **instances_page.py**: Minecraft 实例管理页面
- **settings_page.py**: 应用设置页面
- **styles.py**: 页面级别的样式定义

### managers/ - 管理器
- **config.py**: 配置管理器
  - 加载/保存配置
  - 提供配置访问接口
- **background.py**: 背景管理器
  - 管理背景图片和视频
  - 处理视频播放
  - 背景切换逻辑
- **language.py**: 语言管理器
  - 多语言支持
  - 语言切换
- **log_manager.py**: 日志管理器
  - 日志记录
  - 日志文件管理
- **modrinth_manager.py**: Modrinth API 管理器
  - 项目搜索
  - 版本获取
  - 下载功能
- **modrinth_manager_async.py**: Modrinth 异步 API 管理器

### utils/ - 工具函数
- **icons.py**: 图标工具
  - 加载 SVG 图标
  - 转换图标颜色
- **path_helper.py**: 路径辅助工具
  - 路径处理
  - 文件操作辅助

### tools/ - 工具
- **log_viewer.py**: 日志查看器工具

### 资源文件
- **svg/**: 50 个 SVG 图标文件，包含各种 UI 元素的矢量图标
- **png/**: Minecraft 相关的 PNG 图标（block, fabric, forge, neoforged 等）
- **lang/**: 多语言支持
  - `en_US.json`: 英文翻译
  - `zh_CN.json`: 中文翻译

### example_resourcepack/ - 示例资源包
包含一个完整的示例资源包，展示资源包结构和配置格式：
- `pack.mcmeta`: 资源包元数据
- `packset.json`: 资源包集配置
- `packset_lang/`: 资源包语言文件
- `assets/minecraft/textures/gui/`: GUI 纹理和配置

### 构建与部署
- **Spectra.spec / main.spec**: PyInstaller 打包配置文件
- **.github/workflows/build.yml**: GitHub Actions CI/CD 构建配置
- **build/**: 构建过程中的临时文件
- **dist/**: 打包后的可执行文件

### 其他
- **LICENSE**: 项目许可证
- **README.md**: 项目说明文档
- **.gitignore**: Git 版本控制忽略规则
- **logs/**: 运行时日志文件目录

## 使用方法

直接运行 `python main.py` 即可启动应用。

## 打包

使用 PyInstaller 打包：
```bash
pyinstaller Spectra.spec
# 或
pyinstaller main.spec
```

打包后的可执行文件位于 `dist/` 目录中。
