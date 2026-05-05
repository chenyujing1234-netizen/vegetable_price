# 公共 API（v1）

供 B 端开发者集成的只读价格查询 API。

## 鉴权

通过 `X-API-Key` Header 传 API Key。

```bash
curl -H "X-API-Key: vk_live_xxxxxxxxxxxxxxxx" \
     https://api.example.com/api/v1/public/prices/latest?product=tomato
```

## 申请 API Key

1. 在前端 `/alerts` 页面注册并登录
2. 调用 `POST /api/auth/api-keys?name=my-app`，注意：
   返回值中的 `secret` 字段只在创建时出现一次，请妥善保存

## 速率限制

| 套餐 | 速率（每分钟） |
|---|---|
| Free | 60 |
| Pro | 600 |
| Enterprise | 6000 |

超出返回 `429 Too Many Requests`。

## 端点

### `GET /api/v1/public/products`
返回支持的产品列表。

### `GET /api/v1/public/markets`
返回支持的市场列表。

### `GET /api/v1/public/prices/latest`

| 参数 | 必填 | 说明 |
|---|---|---|
| `product` | ✓ | 产品 code（tomato/cucumber/chili/potato） |
| `market` | ✗ | 市场 code，留空返回所有市场 |

### `GET /api/v1/public/prices/series`

| 参数 | 必填 | 说明 |
|---|---|---|
| `product` | ✓ | 产品 code |
| `market` | ✓ | 市场 code |
| `days` | ✗ | 历史天数，1-1825，默认 90 |

返回格式：

```json
{
  "product": "tomato",
  "market": "shouguang",
  "points": [
    {"date": "2026-04-01", "avg": 3.21, "low": 2.95, "high": 3.50},
    ...
  ]
}
```

## 后续规划

- `GET /api/v1/public/predictions/forecast` - 价格预测（Pro 套餐）
- `GET /api/v1/public/factors/correlation` - 影响因子相关性
- WebSocket 实时推送
