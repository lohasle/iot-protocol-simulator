# 贡献指南

感谢您考虑为 IoT Protocol Simulator 做出贡献！

## 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发环境设置](#开发环境设置)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [Pull Request 流程](#pull-request-流程)

## 行为准则

请尊重所有贡献者，保持友好和建设性的讨论氛围。

## 如何贡献

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 进行更改并确保测试通过
4. 提交更改 (`git commit -m 'feat: add amazing feature'`)
5. 推送到分支 (`git push origin feature/AmazingFeature`)
6. 创建一个 Pull Request

## 开发环境设置

### 前置要求

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose

### 后端设置

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.main:app --reload
```

### 前端设置

```bash
cd frontend
npm install
npm run dev
```

### 运行测试

```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
npm test
```

## 代码规范

### Python

- 使用 Ruff 进行代码检查
- 遵循 PEP 8 规范
- 使用类型注解
- 编写文档字符串

```bash
# 运行 lint
ruff check src/
```

### TypeScript/React

- 使用 ESLint 进行代码检查
- 使用函数式组件和 Hooks
- 遵循项目现有的代码风格

```bash
# 运行 lint
npm run lint
```

## 提交规范

使用约定式提交格式：

- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档更新
- `style:` 代码格式（不影响功能）
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建/工具相关

示例：
```
feat: add CoAP protocol support
fix: resolve WebSocket connection issue
docs: update API documentation
```

## Pull Request 流程

1. 确保代码通过所有测试
2. 更新相关文档
3. 添加必要的测试用例
4. 等待 CI 检查通过
5. 等待代码审查

## 添加新协议

要添加新的协议支持，请：

1. 在 `backend/src/protocols/` 创建新文件
2. 实现协议基类接口
3. 在 `backend/src/routers/` 添加对应的 API 路由
4. 更新前端协议配置界面
5. 添加测试用例
6. 更新文档

## 需要帮助？

如有问题，请创建 Issue 或在 Discussions 中提问。

---

*由 OpenClaw 自动生成 - 2026-02-15*
