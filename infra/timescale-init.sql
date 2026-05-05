-- 初始化 TimescaleDB 扩展
-- 该脚本在 docker 首次创建数据库时自动执行

CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 时区
SET TIME ZONE 'Asia/Shanghai';
