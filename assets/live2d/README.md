# Live2D 模型存放规则

`assets/live2d/` 既是渲染 Live2D 的前端运行时目录，也是模型的存放目录。约定如下。

## 目录结构

```
assets/live2d/
├── index.html                 # 渲染页面（运行时，勿删 / 勿移）
├── main.js                    # 通用渲染逻辑（运行时）
├── cubism4.min.js             # pixi-live2d-display 插件（运行时）
├── live2dcubismcore.min.js    # Cubism Core（运行时）
├── pixi.min.js                # PixiJS（运行时）
└── <模型名>/                  # 每个模型一个子目录，目录名即模型名
    ├── *.model3.json          # 入口（必需，也支持旧版 *.model.json）
    ├── *.moc3                 # 模型网格（必需）
    ├── *.physics3.json        # 物理（可选）
    ├── texture_*.png          # 贴图（必需）
    ├── expressions/           # 表情 *.exp3.json（可选）
    ├── motions/               # 动作 *.motion3.json（可选）
    └── sounds/                # 音效（可选）
```

## 核心约定

1. **一个模型 = 一个子目录**，目录名就是「模型名」：
   - 出现在右键「切换模型」菜单里；
   - 记在根目录 `config.json` 的 `live2d_model` 字段。
2. **入口文件名不固定**：只要匹配 `*.model3.json`（或旧版 `*.model.json`）即可，程序会自动发现，无需改名。
3. **运行时文件别动**：`index.html`、`main.js`、三个 `*.min.js` 是所有模型共享的渲染运行时，不要删除或移动；它们不是模型目录，也不会出现在模型列表里。

## 添加模型

- **对话框导入（推荐）**：右键桌面宠物 →「添加 Live2D 模型…」→ 选择含 `*.model3.json` 的 Cubism 4 模型文件夹 → 填模型名（默认取文件夹名）→「导入」。程序会把它复制到 `assets/live2d/<模型名>/` 并自动切换。
- **手动放置**：直接把模型文件夹复制到 `assets/live2d/` 下，重启后右键「切换模型」即可看到。

## 切换模型

右键 →「切换模型」→ 点选要用的模型；当前模型前有 √ 标记。切换结果写入 `config.json` 的 `live2d_model`，重启后仍生效。
