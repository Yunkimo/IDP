# 贡献指南

## 代码风格

- 统一使用 [Ruff](https://docs.astral.sh/ruff/) 检查与格式化（配置见 `pyproject.toml`）。
- 行宽 ≤ 100；启用规则 `E`/`F`/`I`/`W`（忽略 E501 由 ruff-format 处理）。
- 所有函数/方法使用类型注解；模块职责单一。

```bash
ruff check .            # 静态检查
ruff format .           # 格式化
```

## 提交规范（Conventional Commits）

提交信息统一为 `type: 中文描述`，一个提交只做一件事：

| type | 用途 |
|---|---|
| feat | 新功能 |
| fix | 修复缺陷 |
| refactor | 重构（不改行为） |
| test | 测试 |
| docs | 文档 |
| ci | CI/构建脚本 |
| chore | 杂项（脚手架、依赖） |

示例：`feat: 实现语音识别引擎`、`test: 补充记忆裁剪用例`。

## 分支与协作流程

1. 从 `main` 拉取最新代码。
2. 创建功能分支：`git checkout -b feat/xxx`。
3. 开发并按上面的规范提交。
4. 推送到远端并创建 **Pull Request**，通过 CI 与评审后合并。

## 测试要求

- 新增或修改逻辑必须补充/更新对应单元测试。
- 提交前本地跑通：`ruff check . && pytest`。

## 本地开发

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
```
