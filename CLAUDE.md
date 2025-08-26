# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 开发命令

### 构建和安装
```bash
# 以开发模式安装包
make install

# 清理构建产物
make clean

# 安装完整的 mozi 包
pip install git+https://github.com/tonsh/mozi.git@master

# 仅安装 API 依赖
pip install "mozi[api] @ git+https://github.com/tonsh/mozi.git@master"
```

### 代码检查和质量
```bash
# 运行所有代码检查 (pylint + flake8)
make lint

# 运行单独的检查器
make pylint
make flake8
```

### 测试
```bash
# 使用 pytest 运行测试
make test

# 运行代码检查和测试
make check

# 运行单个测试文件
pytest tests/test_logger.py

# 运行特定测试
pytest tests/test_db/test_user.py::TestUser::test_create
```

## 项目架构

这是一个名为 "mozi" 的 Python 工具库，提供数据库操作、日志记录和 FastAPI 应用程序的核心工具。

### 核心组件

- **mozi/db.py**: 基于 SQLModel/SQLAlchemy 的数据库层：
  - `BaseTable`: 具有自动时间戳和不可变字段保护的基础模型
  - `DBMixin`: 提供 CRUD 操作的通用混合类（创建、获取、更新、删除、分页）
  - `BaseModel`: 结合 BaseTable 和 DBMixin 提供完整的 ORM 功能
  - 需要 `POSTGRES_URL` 环境变量

- **mozi/logger.py**: 全面的日志系统：
  - 可配置的处理器（控制台、文件、轮转文件、错误文件）
  - 支持基于 YAML 的配置
  - 自动创建日志目录
  - 支持多种格式化器

- **mozi/api/app.py**: 带内置错误处理的 FastAPI 应用工厂：
  - 自定义 `APIError` 异常处理
  - 请求验证错误格式化
  - 全局异常处理器

- **mozi/utils.py**: 通用操作的工具函数

### 环境配置

环境变量：
- `APP_NAME`: 应用程序名称
- `APP_ENV`: 环境（dev|pro|test）
- `POSTGRES_URL`: PostgreSQL 连接字符串（可选，仅数据库功能需要）

### 依赖关系

核心依赖：PyYAML, pytz, SQLModel
可选依赖：
- `api`: FastAPI 用于 Web API 功能
- `dev`: pytest, httpx 用于开发和测试
- `lint`: flake8, pylint 用于代码质量检查

### 测试配置

测试通过 pytest.ini 配置：
- 自动设置测试环境变量
- 启用 INFO 级别的控制台日志
- 测试位于 `tests/` 目录

项目使用基于 makefile 的构建系统，遵循 Python 打包标准和 pyproject.toml 配置。

### 数据库模型使用方式

继承 `BaseModel` 创建数据库模型：

```python
from mozi.db import BaseModel

class User(BaseModel, table=True):
    name: str
    email: str
    
# 使用
  user = User.create(name="test", email="test@example.com")
  users = User.all()
  user_count = User.count(name="test")
```

### FastAPI 应用使用方式

```python
from mozi.api.app import app

@app.get("/")
async def hello():
    return {"message": "Hello world"}
```
