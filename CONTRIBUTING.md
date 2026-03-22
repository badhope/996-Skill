# 贡献指南

感谢您对 Auto-SignIn 项目的关注！我们欢迎各种形式的贡献。

## 🚀 如何贡献

### 1. 提交 Issue

- 报告 Bug
- 提出新功能建议
- 询问问题

### 2. 提交 Pull Request

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

## 📝 代码规范

- 遵循 PEP 8 规范
- 使用类型注解
- 编写清晰的文档字符串
- 添加适当的日志记录

## 🧪 测试

- 为新功能编写测试
- 确保所有测试通过
- 保持代码覆盖率

## 📋 添加新平台

1. 在 `platforms/` 目录创建新文件
2. 继承 `BasePlatform` 类
3. 实现 `sign_in()` 方法
4. 在 `__init__.py` 中注册

## 💬 联系我们

如有问题，欢迎通过 Issue 与我们联系。
