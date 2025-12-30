# Packset 资源包配置系统示例
本示例展示如何创建一个可配置的资源包，支持通过 Packset 系统控制资源内容。

## 目录结构

```
example_resourcepack/
├── pack.mcmeta                          # Minecraft 资源包元数据
├── packset.json                        # Packset 配置文件（核心配置）
├── packset_lang/                       # 资源包自定义本地化目录（可选）
│   ├── zh_CN.json                      # 简体中文翻译
│   └── en_US.json                      # 英文翻译
├── assets/
│   └── minecraft/
│       └── textures/
│           └── gui/
│               ├── border_overlay.json           # JSON 配置文件示例
│               ├── menu_theme.packset.json     # 子 Packset 配置（bool 类型）
│               ├── background_theme.packset.json # 子 Packset 配置（toggle 类型）
│               ├── borders/
│               │   ├── rounded.png            # 纹理文件
│               │   └── square.png             # 纹理文件
│               └── title_opacity.json
└── ...
```

## 配置文件说明

### 1. packset.json（主配置文件）

主配置文件定义了所有可配置的功能（features）。

#### 配置文件格式

```json
{
  "schema_version": 1,                    // 配置格式版本(请勿修改)
  "feature": {
    "switch_feature": "bool",              // 开关类型功能
    "status_feature": "toggle"              // 切换类型功能
  },
  "category": {                            // 可选项：配置分类（如果不需要分类可省略此字段）
    "list": ["gui", "font"],              // 分类ID列表（定义显示顺序）
    "data": {
      "gui": {
        "name": "GUI Settings",           // 分类显示名称（原始文本，会被本地化覆盖）
        "description": "Configure interface options",
        "list": ["switch_feature"]       // 该分类下的功能列表
      },
      "font": {
        "name": "Font Settings",
        "description": "Configure font options",
        "list": ["status_feature"]
      }
    }
  },
  "config": {
    "switch_feature": {
      "default": "false",                   // 默认值
      "toggle": [...]                         // 关联的配置项
    },
    "status_feature": {
      "default": "classic",                 // 默认状态
      "scope": ["classic", "modern", "minimal"],  // 可选状态列表
      "paths": [...]                           // 关联的配置项
    }
  }
}
```

#### 功能类型

**bool 类型**：开/关类型的配置项
- 在 UI 中显示为切换开关
- 默认值可以是 "true" 或 "false"
- 当值与默认值不同时，执行切换操作

**toggle 类型**：多状态切换类型的配置项
- 在 UI 中显示为下拉选择框
- 可以有多个状态（通过 scope 定义）
- 用户可以在多个选项中切换

### 2. 子 Packset 配置文件（.packset.json）

子 Packset 文件用于定义更复杂的配置结构。

#### bool 类型的子 Packset

```json
{
  "schema_version": 1,
  "type": "bool",
  "assets": [                              // 文件资源配置
    {
      "name": "显示名称",
      "file_path": "assets/xxx/file.ext",  // 文件路径
      "default": "off"                    // 默认状态
    }
  ],
  "toggles": [                             // 文件切换配置
    {
      "name": "显示名称",
      "path": "assets/xxx/file1.ext",        // 默认位置文件
      "toggle_path": "assets/xxx/file2.ext", // 切换位置文件
      "default": "off"                     // 默认状态
    }
  ]
}
```

**assets 配置**：
- `default="off"`：默认情况下文件被隐藏（添加 .packset.old 后缀）
- `default="on"`：默认情况下文件显示

**toggles 配置**：
- `default="off"`：默认情况下显示 path 的文件
- `default="on"`：默认情况下显示 toggle_path 的文件

#### toggle 类型的子 Packset

```json
{
  "schema_version": 1,
  "type": "toggle",
  "states": [                              // 状态列表
    {
      "name": "classic",                     // 状态名称（需在 scope 中定义）
      "file_path": "assets/xxx/file1.ext"
    },
    {
      "name": "modern",
      "file_path": "assets/xxx/file2.ext"
    },
    ...
  ]
}
```

**states 配置**：
- `name`：状态标识符，必须与主配置中的 scope 值对应
- 第一个状态（index 0）被视为默认状态
- 只有一个状态的文件会显示在游戏资源包中，其他状态文件会被移动

### 3. 配置行为说明

#### bool 类型（开关）

当父开关的值与默认值**不同**时：
- `assets` 中的文件会被切换（启用/禁用）
- `toggles` 中的文件会执行切换操作

**示例**：
```
默认值：false
当前值：true

→ 执行切换操作（因为 true != false）
```

#### toggle 类型（状态切换）

**工作原理**：
- 默认状态的文件显示在游戏资源包中
- 切换到其他状态时：
  1. 将当前状态的文件移回原位
  2. 将目标状态的文件移动到默认位置
  3. 默认状态的文件被重命名为 .packset.old

**示例**：
```
状态：classic → modern
1. classic.jpg → classic.jpg.packset.old
2. modern.jpg → classic.jpg
3. 游戏现在使用 modern.jpg 作为经典背景
```

## 使用说明

### 添加自定义本地化（可选）

在资源包根目录下创建 `packset_lang/` 目录，并为每种支持的语言创建 JSON 文件：

```
packset_lang/
├── zh_CN.json    # 简体中文
├── en_US.json    # 美式英语
├── ja_JP.json    # 日语
└── ...
```

#### 本地化文件格式

```json
{
  "category.{分类ID}.name": "分类名称",
  "category.{分类ID}.description": "分类描述",
  "feature.{功能名}": "功能显示名称"
}
```

#### 示例：zh_CN.json

```json
{
  "category.gui.name": "GUI 设置",
  "category.gui.description": "用于配置界面相关的选项",
  "category.font.name": "字体设置",
  "category.font.description": "用于配置字体相关的选项",
  "feature.switch_feature": "开关功能",
  "feature.status_feature": "状态功能"
}
```

#### 示例：en_US.json

```json
{
  "category.gui.name": "GUI Settings",
  "category.gui.description": "Configure interface options",
  "category.font.name": "Font Settings",
  "category.font.description": "Configure font options",
  "feature.switch_feature": "Switch Feature",
  "feature.status_feature": "Status Feature"
}
```

**注意**：
- 本地化是可选的，如果没有翻译文件，会使用 `packset.json` 中的原始文本
- 如果翻译文件中没有对应的键，会回退到原始文本
- 翻译键必须严格匹配格式：`category.{category_id}.name`、`category.{category_id}.description`、`feature.{feature_name}`

### 添加新功能

1. 在 `packset.json` 的 `feature` 中添加新功能名和类型
2. 在 `config` 中添加对应配置
3. 根据需要创建子 Packset 文件（.packset.json）
4. 在 `assets` 中添加对应的资源文件
5. （推荐）在本地化文件中添加对应翻译

### 使用分类功能（可选项）

1. 在 `packset.json` 中添加 `category` 字段（如果不需要分类可省略此字段）
2. 在 `category.list` 中定义分类 ID 的顺序
3. 在 `category.data` 中为每个分类配置：
   - `name`：显示名称
   - `description`：描述文本
   - `list`：该分类下的功能列表
4. 确保 `list` 中的功能在 `feature` 和 `config` 中都有定义

### 文件操作说明

- 文件不会被删除，只是被重命名或移动
- `.packset.old` 后缀用于标记隐藏的文件
- 所有操作都是可逆的，用户可以随时切换回默认状态

### 支持的资源类型

- **纹理文件**：.png, .jpg, .jpeg, .gif 等
- **JSON 配置**：.json 文件用于存储配置
- **模型文件**：.json 或 .obj 等
- **其他资源**：任何 Minecraft 支持的资源类型

## 常见问题

**Q: 可以使用压缩包格式的资源包吗？**

A: 可以！Packset 编辑器同时支持文件夹格式和 .zip 压缩包格式的资源包。

**Q: 文件会被永久删除吗？**

A: 不会。所有文件操作都是可逆的，被隐藏的文件只是添加了 `.packset.old` 后缀。

**Q: 如何设置默认值？**

A: 在配置文件的 `default` 字段中设置。对于 bool 类型，可以是 "true" 或 "false"；对于 toggle 类型，设置为默认状态名称。

**Q: 限制可选项的数量？**

A: 没有限制。你可以定义任意数量的状态或选项。

**Q: 必须使用分类功能吗？**

A: 不是必须的。`category` 字段为可选项，如果不需要分类可以省略此字段，所有配置项会显示在一个卡片中。分类功能有助于组织配置，使界面更清晰。

## 技术细节

- `schema_version`：用于确保配置文件格式的兼容性
- 路径区分大小写（在某些系统上）
- 所有文件操作都会记录日志，便于调试
- 分类 ID 使用下划线替代连字符，以避免属性名问题

## 完整示例

查看本目录中的所有文件以获取完整的示例配置。
