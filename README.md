# 电商评价情绪分析系统

对电商用户评价做自动情绪分析：提交文本 → 输出**正向 / 负面 / 中性**标签 + **置信度** → 原文、结果、时间存入 MySQL。

- 后端：Python 3.12 + FastAPI（自带 Swagger 文档 `/docs`）
- 分析引擎：内置中文情感词典 + 规则打分（本地运行，无需外网）
- 存储：MySQL 8（Docker 容器）
- 前端：单页 Demo（FastAPI 静态托管）
- 部署：Docker Compose（api + mysql 两个容器）

## 本地运行

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt          # Windows
.venv/bin/pip install -r requirements.txt              # Linux
# 需要一个 MySQL，或临时用 SQLite：
set DATABASE_URL=sqlite+aiosqlite:///./dev.db          # Windows
uvicorn app.main:app --reload
```

打开 http://127.0.0.1:8000 即为 Demo 页；http://127.0.0.1:8000/docs 为接口文档。

## 虚拟机部署（Ubuntu + Docker）

```bash
# 1. 首次部署前：把用户加入 docker 组（避免 permission denied）
echo '<sudo密码>' | sudo -S usermod -aG docker $USER
# 重新登录后生效

# 2. 准备配置
cp .env.example .env    # 修改两个密码

# 3. 一键起停
./deploy/ops.sh start    # 构建并启动（首次会拉取镜像，走国内源）
./deploy/ops.sh logs     # 看 api 日志
./deploy/ops.sh backup   # 备份数据库到 .runtime/
./deploy/ops.sh stop
```

启动后访问 `http://<虚拟机IP>:8000`。

> 说明：虚拟机直连 Docker Hub 不通，Dockerfile 基础镜像与 mysql 镜像均已配置国内镜像代理（docker.1ms.run），pip 走阿里云源。如网络环境变化，可改回官方镜像名。

## API 一览（前缀 /api/v1）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /health | 健康检查（含数据库状态） |
| POST | /analyze | `{text}` → 情绪标签 + 置信度 + 命中词，并落库 |
| GET | /records | 分页列表，支持 `polarity` / `date_from` / `date_to` / `q` 筛选 |
| GET | /records/{id} | 单条详情（含原文与命中词） |
| DELETE | /records/{id} | 删除记录 |

## 分析引擎说明

1. 预处理去掉 URL/空白；按标点切句
2. 句内对情感词做**正向最大匹配**（最长优先）
3. 情感词前 6 字窗内的**程度副词**加权（如"非常好"= 好 × 1.75），**否定词**翻转极性（双否定翻回）
4. 汇总得到 `raw_score`：> 0.5 → 正向；< -0.5 → 负面；否则中性
5. 置信度：正/负 `1 - e^(-|raw|/1.5)`（封顶 0.99）；中性 `1/(1+|raw|)`

调参：阈值与斜率在 `app/core/config.py`（可用环境变量 `POS_THRESHOLD` / `NEG_THRESHOLD` / `CONF_SCALE` 覆盖）；词表在 `app/lexicon/*.txt`，一行一词，随时可扩充，无需改代码。

## 测试

```bash
pip install -r requirements-dev.txt
pytest
```
