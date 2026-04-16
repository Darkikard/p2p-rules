# p2p-rules

> BT / PT / 下载 直连规则集，适用于 [Clash](https://github.com/Dreamacro/clash) / [Mihomo](https://github.com/MetaCubeX/mihomo) / Clash Meta

自动解析 [pre-dessert-sites](https://github.com/mantou568/pre-dessert-sites) 的 PT 站点配置，
结合公共 BT Tracker 与国内外下载工具、网盘域名，生成统一规则集。

## 📦 规则集一览

| 文件 | 用途 | 条数 |
|------|------|------:|
| `pt-direct.txt` | PT 站点域名 → 直连 | 220 |
| `pt-tracker-direct.txt` | PT Tracker 域名 → 直连 | 219 |
| `bt-tracker-direct.txt` | BT 公共 Tracker → 直连 | 47 |
| `download-direct.txt` | 下载工具 & 网盘 → 直连 | 107 |
| `all-download-rules.txt` | 以上全部合并 → 直连 | 592 |
| `all-download-fakeip.txt` | 以上全部合并 → FakeIP | 588 |

## 🔧 使用方法

### 方式一：合并版（推荐，一条规则搞定）

```yaml
rule-providers:
  p2p:
    type: http
    url: "https://raw.githubusercontent.com/Darkikard/p2p-rules/main/rules/all-download-rules.txt"
    path: ./rules/all-download-rules.txt
    format: text
    behavior: domain
    interval: 2592000  # 30天

rules:
  - RULE-SET,p2p,DIRECT
  - MATCH,PROXY
```

### 方式二：分类使用（按需精细控制）

```yaml
rule-providers:
  pt:
    type: http
    url: "https://raw.githubusercontent.com/Darkikard/p2p-rules/main/rules/pt-direct.txt"
    path: ./rules/pt-direct.txt
    format: text
    behavior: domain
    interval: 2592000

  pt-tracker:
    type: http
    url: "https://raw.githubusercontent.com/Darkikard/p2p-rules/main/rules/pt-tracker-direct.txt"
    path: ./rules/pt-tracker-direct.txt
    format: text
    behavior: domain
    interval: 2592000

  bt:
    type: http
    url: "https://raw.githubusercontent.com/Darkikard/p2p-rules/main/rules/bt-tracker-direct.txt"
    path: ./rules/bt-tracker-direct.txt
    format: text
    behavior: domain
    interval: 2592000

  download:
    type: http
    url: "https://raw.githubusercontent.com/Darkikard/p2p-rules/main/rules/download-direct.txt"
    path: ./rules/download-direct.txt
    format: text
    behavior: domain
    interval: 2592000

rules:
  - RULE-SET,pt,DIRECT
  - RULE-SET,pt-tracker,DIRECT
  - RULE-SET,bt,DIRECT
  - RULE-SET,download,DIRECT
  - MATCH,PROXY
```

### FakeIP 模式

使用 `all-download-fakeip.txt`，配合 Mihomo 的 `fake-ip` DNS 模式：

```yaml
dns:
  fake-ip-filter:
    - RULE-SET,p2p  # 引用 fakeip 规则集

rule-providers:
  p2p:
    type: http
    url: "https://raw.githubusercontent.com/Darkikard/p2p-rules/main/rules/all-download-fakeip.txt"
    path: ./rules/all-download-fakeip.txt
    format: text
    behavior: domain
    interval: 2592000

rules:
  - RULE-SET,p2p,DIRECT
  - MATCH,PROXY
```

## 📋 覆盖范围

### PT 站点（220+）
自动从 [pre-dessert-sites](https://github.com/mantou568/pre-dessert-sites) 解析，
涵盖国内外主流 PT 站点及其对应 Tracker 域名。

### BT 公共 Tracker（47）
`opentrackr.org` `stealth.si` `demonii.com` `coppersurfer.tk` `bittorrent.com` `debian.org` `ubuntu.com` 等

### BT 客户端
qBittorrent · Transmission · Deluge · μTorrent · aria2 · Motrix

### 迅雷生态
xunlei.com · sandai.net · P2P CDN 节点 · 迅雷云盘

### 下载工具
IDM · FDM · JDownloader · EagleGet

### DHT / P2P 网络
router.bittorrent.com · dht.transmissionbt.com · PEX 节点

### BT 搜索引擎
1337x · ThePirateBay · Nyaa · 动漫花园 · 萌番组 · AC.G.rip · dmhy.org

### 网盘服务

| 国际 | 国内 |
|------|------|
| Mega · MediaFire · Pixeldrain · GoFile · Bunkr · KrakenFiles · 1fichier · Uploaded | 百度网盘 · 阿里云盘 · 夸克 · 迅雷云盘 · 天翼云盘 · 115 · 蓝奏云 · 123云盘 · 坚果云 · 城通 · 奶牛快传 · 文叔叔 · 微云 |

## 🔄 自动更新

每月 1 号通过 GitHub Actions 自动运行，无需手动维护。

手动触发：进入 Actions → **Build BT/PT/Download Rules** → Run workflow

## 🛠 本地生成

```bash
# 完整生成
python3 generate-rules.py

# 指定输出目录
python3 generate-rules.py --output ./rules/

# 跳过 PT 站点抓取（离线 / 网络受限时）
python3 generate-rules.py --skip-pt
```

## 📄 License

[MIT](LICENSE)
