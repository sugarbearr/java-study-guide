---
title: "07-Nginx"
description: "阶段：中间件篇 ｜ 建议时长：2 天 ｜ 前置：无（了解 HTTP、前后端分离更佳）"
pubDatetime: 2026-08-24T18:00:00
tags:
  - "④ 中间件篇"

draft: false
---

> **阶段**：中间件篇 ｜ **建议时长**：2 天 ｜ **前置**：无（了解 HTTP、前后端分离更佳）

## 它是什么，解决什么问题

Nginx 是高性能的 **HTTP 服务器 / 反向代理服务器**，C 语言编写，单机可轻松支撑数万并发连接。在后端项目里它几乎无处不在：**静态资源服务、反向代理、负载均衡**是三大本职工作。

**为什么它这么能扛？（高频）**

- **epoll 事件驱动 + 异步非阻塞 IO**：一个 worker 进程用 IO 多路复用同时处理成千上万连接，不为每个连接分配线程（对比传统"一连接一线程"模型）；
- **master-worker 架构**：master 读配置、管理 worker；worker 真正处理请求（数量 ≈ CPU 核数，`worker_processes auto`），worker 挂了 master 自动拉起，改配置可平滑 reload 不中断服务。

**正向代理 vs 反向代理（必会）**：

| | 正向代理 | 反向代理 |
| --- | --- | --- |
| 代理谁 | **客户端**（替客户端出去访问） | **服务端**（替服务器接请求） |
| 谁知道谁存在 | 服务端不知道真实客户端 | 客户端不知道真实后端（以为 Nginx 就是服务） |
| 典型例子 | VPN/科学上网 | Nginx 转发到 Spring Boot 集群 |

## 典型使用场景

| 业务场景 | 为什么用它 | 不用的后果 |
| --- | --- | --- |
| 前后端分离部署 | Nginx 托管前端静态包，`/api` 转发后端，同域解决跨域 | 前后端分开部署域名不同，跨域问题频出 |
| 多实例负载均衡 | upstream 把请求分摊到多个 Spring Boot 实例 | 单实例扛不住，宕机全站不可用 |
| 灰度发布 | 按权重把少量流量切到新版本，观察后再全量 | 新版本直接全量上线，出事故影响所有人 |
| 静态资源服务 | 图片/CSS/JS 直接由 Nginx 返回，带缓存头 | 静态请求也打到 Java 应用，浪费 JVM 资源 |

## 快速上手

### 1. 安装与常用命令

```bash
docker run -d --name nginx -p 80:80 nginx:1.26
# 或 Mac：brew install nginx；配置文件通常在 /usr/local/etc/nginx/nginx.conf 或 /etc/nginx/nginx.conf

nginx -t              # 检查配置语法（改完必做）
nginx -s reload       # 平滑重载配置，不断连接
docker exec -it nginx nginx -s reload   # docker 版重载
```

### 2. 核心配置结构（全局块 / events / http / server / location）

```nginx
# ===== 全局块 =====
worker_processes  auto;              # worker 数 = CPU 核数
events {
    worker_connections  10240;       # 每个 worker 的最大连接数
}
http {
    include       mime.types;        # 文件类型映射
    default_type  application/octet-stream;
    access_log    logs/access.log;
    sendfile      on;                # 静态文件零拷贝

    # gzip 压缩：JS/CSS 传输体积减小 70%+
    gzip on;
    gzip_types text/css application/json application/javascript;
    gzip_min_length 1k;

    # ===== 负载均衡：定义后端集群 =====
    upstream backend {
        server 127.0.0.1:8081 weight=2;      # 权重轮询：8081 承担 2 倍流量
        server 127.0.0.1:8082;               # 默认轮询
        # ip_hash;                           # 按客户端 IP 固定分发（会话保持）
        # least_conn;                        # 最少连接优先
        server 127.0.0.1:8083 max_fails=3 fail_timeout=30s;  # 被动健康检查
    }

    server {
        listen 80;
        server_name example.com;

        # 场景1：静态站点（Vue/React 打包产物，history 路由回退 index.html）
        location / {
            root  /usr/share/nginx/html;     # 文件映射到本地目录
            try_files $uri $uri/ /index.html;
        }

        # 场景2：动静分离——静态资源单独 location，直接返回
        location /static/ {
            root /data/www;                  # 实际文件在 /data/www/static/
            expires 7d;                      # 浏览器缓存 7 天
        }

        # 场景3：反向代理——/api 开头转发给后端集群
        location /api/ {
            proxy_pass http://backend/;      # 结尾带 / → 去掉 /api 前缀再转发
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;          # 传真实客户端 IP
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_read_timeout 60s;
        }
    }
}
```

### 3. 限流（令牌桶）与 CORS 跨域

```nginx
http {
    # 每个 IP 每秒 10 个请求，10m 内存约可跟踪 16 万 IP
    limit_req_zone $binary_remote_addr zone=apiLimit:10m rate=10r/s;

    server {
        location /api/ {
            limit_req zone=apiLimit burst=20 nodelay;
            # burst=20 允许突发 20 个排队，nodelay 立即处理不匀速等待

            # 跨域：让前端域名的请求被浏览器放行
            add_header Access-Control-Allow-Origin  $http_origin always;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
            add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
            add_header Access-Control-Allow-Credentials "true" always;
            if ($request_method = OPTIONS) { return 204; }   # 预检请求直接放行
        }
    }
}
```

### 4. WebSocket 反向代理（实时推送场景）

```nginx
location /ws/ {
    proxy_pass http://backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;      # 协议升级头，缺一不可
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 300s;                     # 长连接空闲超时，避免被误断
}
```

### 5. HTTPS 思路与高可用

- HTTPS：用 certbot/云厂商证书拿到 `.pem/.key`，server 块监听 443，配置 `ssl_certificate` 与 `ssl_certificate_key`，再把 80 端口 `return 301 https://$host$request_uri;` 整站跳转；
- **keepalived 高可用**：Nginx 自身是单点，主备两台 Nginx + keepalived 抢占同一个 VIP（虚拟 IP），主挂了 VIP 漂移到备机，客户端无感知。

## 常用命令 / API 速查

| 配置 / 命令 | 作用 |
| --- | --- |
| `root /data/www` | 把 URL 映射到**本地文件**（静态资源） |
| `proxy_pass http://backend` | 把请求**转发到后端服务**（反向代理） |
| `upstream` + `server` | 定义负载均衡后端节点池 |
| `weight / ip_hash / least_conn` | 权重轮询 / IP 会话保持 / 最少连接 |
| `limit_req_zone` + `limit_req` | 令牌桶限流 |
| `gzip on; gzip_types ...` | 响应压缩 |
| `expires 7d` | 静态资源浏览器缓存时间 |
| `nginx -t` / `nginx -s reload` | 语法检查 / 平滑重载 |
| `tail -f logs/access.log` / `error.log` | 排查 502/404 等问题第一现场 |

## 核心进阶

### 1. 负载均衡策略对比

| 策略 | 规则 | 适用 |
| --- | --- | --- |
| 轮询（默认） | 依次分发 | 实例性能相近 |
| weight | 按权重分发（`weight=2`） | 机器配置不均 |
| ip_hash | 客户端 IP 哈希固定到某实例 | 有状态的会话保持（更推荐应用层用 Redis 共享 Session） |
| least_conn | 转发给当前连接数最少的实例 | 请求处理时长差异大 |
- **健康检查**：开源版只有被动检查（`max_fails`/`fail_timeout`：失败 3 次、暂停 30s 不派流量）；主动探测（定期发请求探活）需商业版或第三方模块。

### 2. Nginx 与 Spring Cloud Gateway 的分工（高频）

| | Nginx | Spring Cloud Gateway |
| --- | --- | --- |
| 定位 | 接入层：静态资源、SSL 终止、全局负载均衡 | 业务网关：路由 + 鉴权 + 限流 + 熔断 |
| 能力 | C 语言、性能极高，但不感知微服务 | 与注册中心联动按**服务名**路由，可写 Java 过滤器做业务逻辑 |
| 典型位置 | 最外层入口 | Nginx 之后、微服务之前 |

标准链路：**客户端 → Nginx（负载均衡）→ Gateway（业务网关，做鉴权/限流）→ 微服务**。判断标准：和业务无关的"流量转发"给 Nginx，和微服务体系相关的"路由+治理"给 Gateway。

### 3. 动静分离与灰度

- **动静分离**：静态请求（html/js/css/图片）由 Nginx 直接返回并设置 `expires` 缓存，动态请求走 `proxy_pass` 到应用——减少无效请求占用 JVM；
- **灰度发布**：upstream 中新旧版本配权重（如 `weight=1` vs `weight=9`）放 10% 流量到新版；更精细的按 Cookie/Header 分流用 `map` + 两个 upstream 实现。

### 5. 常见问题排查（实战）

- **502 Bad Gateway**：后端挂了/端口不通/处理超时——先 `curl` 直连后端确认，再查 `error.log`；
- **404**：`root` 与 location 拼接路径不对；前端 history 路由刷新 404 是漏配 `try_files $uri $uri/ /index.html;`；
- **限流不生效**：`limit_req_zone` 必须在 http 块定义、`limit_req` 在 location 块引用，二者缺一；
- **跨域失败**：OPTIONS 预检没放行，或后端也加了 CORS 头导致重复头报错——跨域头只在一处加（推荐 Nginx）。

## 高频面试题

**Q：正向代理和反向代理的区别？**
- 正向代理代理客户端：服务端不知道真实客户端是谁（VPN）；
- 反向代理代理服务端：客户端不知道真实后端是谁，以为代理就是服务本身；
- Nginx 做的是反向代理：隐藏后端、负载均衡、统一入口。

**Q：Nginx 为什么能支撑高并发？**
- master-worker 多进程模型：master 管理，worker 处理请求，worker 数 ≈ CPU 核数，避免线程争抢；
- epoll 事件驱动 + 非阻塞 IO：一个 worker 可同时处理上万连接，不为每个连接创建线程；
- sendfile 零拷贝传输静态文件。

**Q：Nginx 的负载均衡策略有哪些？**
- 轮询（默认）、weight 权重、ip_hash（会话保持）、least_conn（最少连接）；
- 健康检查：开源版被动探测（max_fails/fail_timeout），主动探测要商业版/模块；
- 有状态场景更推荐应用层用 Redis 共享 Session 而不是 ip_hash。

**Q：你写过哪些 Nginx 配置？**
- 静态站点 + `try_files` 支持前端 history 路由；`/api` 反向代理到 Spring Boot 集群（带 X-Real-IP）；
- gzip 压缩、静态资源 `expires` 缓存（动静分离）；
- `limit_req` 接口限流、CORS 跨域头、443 HTTPS + 80 跳转。

**Q：Nginx 和 Spring Cloud Gateway 有什么区别，怎么一起用？**
- Nginx 是接入层反向代理：性能极高，处理静态资源、SSL、全局负载均衡，但不懂微服务；
- Gateway 是业务网关：基于注册中心按服务名动态路由，可用过滤器实现鉴权、限流、熔断等业务治理；
- 典型架构：客户端 → Nginx → Gateway → 微服务，流量入口归 Nginx，服务治理归 Gateway。

## 推荐资料

| 资料 | 说明 | 链接 |
| --- | --- | --- |
| JavaGuide 负载均衡 | 负载均衡原理与分类 | https://javaguide.cn/high-performance/load-balancing.html |
| JavaGuide API 网关 | 网关与 Nginx 的分工 | https://javaguide.cn/distributed-system/api-gateway.html |
| pdai 架构知识体系 | 接入层在整个架构中的位置 | https://pdai.tech/md/arch/arch-z-overview.html |
| JavaGuide 高可用系统设计指南 | 限流、降级等高可用手段 | https://javaguide.cn/high-availability/high-availability-system-design.html |
