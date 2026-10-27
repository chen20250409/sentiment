-- MySQL 容器首次初始化时由 docker-entrypoint-initdb.d 自动执行
-- 库与用户已由镜像环境变量(MYSQL_DATABASE/MYSQL_USER)创建，这里仅兜底保证字符集
CREATE DATABASE IF NOT EXISTS sentiment
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;
