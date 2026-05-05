# 模型层

## 模块

| 目录 | 模型 | 用途 |
|---|---|---|
| `prophet/` | Facebook Prophet | 主序列预测（季节性 + 节假日） |
| `deeplearn/` | LSTM / N-BEATS (Darts) | 多变量预测（价格 + 天气 + CPI） |
| `nlp/` | bge-base-zh + 词典 | 新闻情感分析、关键词聚类 |

## 运行

```bash
cd ml
pip install -r requirements.txt

export SYNC_DATABASE_URL="postgresql+psycopg://veg:vegpass@localhost:5432/vegdb"

# 训练并落盘 Prophet 模型
python -m prophet.train --product tomato --market shouguang --horizon 30

# 训练 LSTM 多变量
python -m deeplearn.train_lstm --product tomato --market shouguang \
    --features weather,cpi --horizon 30

# 评估并集成
python -m ensemble.evaluate --product tomato --market shouguang
```

模型 artifact 保存在 `ml/checkpoints/<model>/<market>_<product>.pkl`，
后端推理时优先读取最新 artifact，否则在线 fit。
