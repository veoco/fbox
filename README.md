# fbox

文件快递柜：匿名储存文件，通过取件码获取文件。

此处为后端源码，实际效果请访问 [演示站点](https://dbox.cf/)

## Docker 使用方法

1. 快速启动

```
docker run -d \
  -p 8000:8000 \
  -v /host_path/data:/app/data \
  -v /host_path/logs:/app/logs \
  -e SECRET_KEY=yourownsecretkey \
  -- name fbox \
  ghcr.io/veoco/fbox
```

2. 可配置选项

2.1 所有选项都可以通过环境变量配置，主要配置为：

```
# 站点标题
SITE_TITLE: "DBox"
# API 文档，开启后可访问 /api/docs 查看 API 文档
SITE_API_DOCS: true
# 管理密码，用于签发会员卡
ADMIN_PASSWORD: "password"

# 数据存放目录
DATA_ROOT: "data"
# 过期数据归档目录
LOGS_ROOT: "logs"
# 前端文件目录
WWW_ROOT: "www"
```

2.2 默认使用文件系统储存，可以配置使用 s3 兼容的对象储存：

```
STORAGE_ENGINE: "s3remote"

S3_ENDPOINT_URL: "https://s3.dbox.cf/"
S3_ACCESS_KEY: "yourownaccesskey"
S3_SECRET_KEY: "yourownsecretkey"

S3_DATA_BUCKET: "data"
S3_LOGS_BUCKET: "logs"
```

注意！对象储存与文件系统不同，有以下区别：

1. 文件上传和下载不经过服务器，用户可能上传无效文件块占用空间，需要手动配置储存桶过期策略。
2. 没有为请求数特别优化，且由于上传下载不经过服务器，可能导致对象储存被刷！
3. 由于当前实现限制，大于 5G 的单个文件无法实现归档。
4. 不要频繁重启，由于没有外部数据库，每次重启都需要大量请求。

2.3 会员及容量限制相关配置：

```
# box 过期时间，以秒为单位
BOX_EXPIRE: 86400
# 过期 box 清理间隔
BOX_CLEAN_PERIOD: 60

# 用户单次可上传文件数量
FILE_MAX_COUNT: 5
# 用户单次可上传文件大小，以 B 为单位
FILE_MAX_SIZE: 100000000
# 会员单次可上传文件数量
FILE_RED_MAX_COUNT: 10
# 会员单次可上传文件大小
FILE_RED_MAX_SIZE: 1000000000

# 会员卡过期时间，0 为永久有效
CARD_EXPIRE: 0
# 会员卡可用次数
CARD_VALID_COUNT: 10
```

2.4 频率相关限制：

```
# 可上传 box 数量限制
RATE_BOX_COUNT_LIMIT: 10
# 可尝试 box 取件码次数限制
RATE_BOX_ERROR_LIMIT: 10
# 可上传文件总大小限制，以 B 为单位
RATE_FILE_SIZE_LIMIT: 10000000000
```

频率限制基于用户 IP，计算周期为 1 小时。

