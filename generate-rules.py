#!/usr/bin/env python3
"""
BT / PT / 下载 规则集生成器
============================
将 PT 站点、BT 公共 Tracker、下载工具/服务 的域名统一整理为
Clash/Mihomo 格式的规则集文件（txt），支持 domain / domain-suffix / domain-keyword。

输出文件:
  pt-direct.txt             — PT 站点域名 → 直连
  pt-tracker-direct.txt     — PT Tracker 域名 → 直连
  bt-tracker-direct.txt     — BT 公共 Tracker → 直连
  download-direct.txt       — 下载工具/服务 → 直连
  all-download-rules.txt    — 合并版（PT+BT+下载）→ 直连
  all-download-fakeip.txt   — 合并版 → FakeIP

用法:
  python3 generate-rules.py
  python3 generate-rules.py --output ./rules/
"""

import os, json, re, argparse, time
from urllib.parse import urlparse
from urllib.request import urlopen, Request
from collections import defaultdict

# ═══════════════════════════════════════════════════════════════
#  第一部分：PT 站点（从 pre-dessert-sites 自动解析）
# ═══════════════════════════════════════════════════════════════

MULTI_PART_TLDS = {
    "edu.cn", "ac.cn", "com.cn", "net.cn", "org.cn", "gov.cn",
    "co.uk", "ac.uk", "org.uk", "me.uk", "gov.uk",
    "co.jp", "ne.jp", "or.jp", "ac.jp", "ad.jp",
    "co.kr", "ne.kr", "or.kr", "re.kr", "ac.kr",
    "com.au", "net.au", "org.au", "edu.au", "gov.au",
    "co.in", "net.in", "org.in", "ac.in", "edu.in",
    "co.nz", "net.nz", "org.nz",
    "co.za", "net.za", "org.za",
    "com.br", "net.br", "org.br",
    "com.tr", "net.tr", "org.tr", "edu.tr",
    "co.il", "org.il", "net.il",
    "co.th", "net.th", "or.th",
    "co.id", "net.id", "or.id",
    "com.mx", "net.mx", "org.mx",
    "co.hu", "net.hu",
    "co.at", "or.at",
}

EXCLUDE_DOMAINS = {"t.me", "bilibili.download", "github.com"}

def get_tracker_domain(host):
    if host.startswith("www."):
        host = host[4:]
    return f"tracker.{host}"

def extract_hosts(data):
    hosts = []
    for key in ("domain", "domain_url", "api", "api_url"):
        if data.get(key):
            hosts.append(data[key])
    for d in data.get("additional_domain", []):
        if d:
            hosts.append(d)
    for site in data.get("site", []):
        if isinstance(site, dict):
            for k in ("domain", "url"):
                if site.get(k):
                    hosts.append(site[k])
    return hosts

def parse_host(url_str):
    url_str = url_str.strip()
    if not url_str:
        return None
    if "://" not in url_str:
        url_str = "https://" + url_str
    try:
        host = urlparse(url_str).hostname
        if host and not re.match(r'^\d+\.\d+\.\d+\.\d+$', host):
            return host.lower()
    except Exception:
        pass
    return None

def fetch_pt_sites():
    """从 pre-dessert-sites 获取 PT 站点域名"""
    print("📥 正在获取 PT 站点配置...")
    os.makedirs("/tmp/pt-rules-work", exist_ok=True)
    zip_path = "/tmp/pt-rules-work/sites.zip"
    extract_dir = "/tmp/pt-rules-work/sites"

    try:
        req = Request(
            "https://github.com/mantou568/pre-dessert-sites/archive/main.zip",
            headers={"User-Agent": "pt-rules-generator/1.0"}
        )
        with urlopen(req, timeout=30) as resp:
            with open(zip_path, "wb") as f:
                f.write(resp.read())
    except Exception as e:
        print(f"⚠️  下载 pre-dessert-sites 失败: {e}")
        return set(), set()

    import zipfile
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(extract_dir)

    sites_dir = os.path.join(extract_dir, "pre-dessert-sites-main", "site_config", "sites")
    if not os.path.isdir(sites_dir):
        print(f"⚠️  站点目录不存在: {sites_dir}")
        return set(), set()

    site_domains = set()
    tracker_hosts = set()
    errors = 0

    for fname in sorted(os.listdir(sites_dir)):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(sites_dir, fname)) as f:
                data = json.load(f)
        except Exception as e:
            errors += 1
            continue
        for raw in extract_hosts(data):
            host = parse_host(raw)
            if host and host not in EXCLUDE_DOMAINS:
                site_domains.add(host)
                tracker_hosts.add(get_tracker_domain(host))

    print(f"   ✅ PT 站点: {len(site_domains)}, Tracker: {len(tracker_hosts)}")
    if errors:
        print(f"   ⚠️  解析失败: {errors}")
    return site_domains, tracker_hosts


# ═══════════════════════════════════════════════════════════════
#  第二部分：BT 公共 Tracker（静态列表 + 可选在线更新）
# ═══════════════════════════════════════════════════════════════

# 知名公共 Tracker 域名（domain-suffix 级别）
BT_TRACKER_STATIC = [
    # --- Open Trackers ---
    "open.stealth.si",
    "opentracker.i2p.rocks",
    "tracker.opentrackr.org",
    "tracker.openbittorrent.com",
    "tracker.internetwarriors.net",
    "tracker.lelux.fi",
    "tracker.moeking.me",
    "tracker.dler.org",
    "tracker1.bt.moack.co.kr",
    "tracker.zerobytes.xyz",
    "tracker.tamersunion.org",
    "tracker.tiny-vps.com",

    # --- UDP Trackers ---
    "open.demonii.com",
    "tracker.coppersurfer.tk",
    "tracker.skyts.net",
    "tracker4.itzmx.com",
    "tracker2.itzmx.com",
    "tracker.gbitt.info",
    "tracker.filemail.com",
    "tracker.srv00.com",
    "tracker.renfei.net",
    "tracker.beeimg.com",
    "tracker.vanitycore.co",
    "tracker.0x.tf",
    "tracker.ali213.net",
    "tracker.shittygory.xyz",
    "tracker.lilithraws.org",

    # --- HTTP/HTTPS Trackers ---
    "tracker.opentrackr.org",
    "tracker.leechers-paradise.org",
    "9.rarbg.me",
    "9.rarbg.to",
    "9.rarbg.com",
    "open.acgtracker.com",
    "tracker.nanoha.org",
    "tracker.yourbittorrent.com",
    "tracker.tvunderground.org.ru",
    "tracker.swateam.org.uk",
    "tracker.pimpmyhost.net",

    # --- 中国特色 BT Tracker ---
    "tracker.btsync.cc",
    "tracker.tangyuancloud.com",
    "tracker.nicehash.com",

    # --- Transmission / qBittorrent / Aria2 常用 ---
    "bttracker.debian.org",
    "torrent.ubuntu.com",
    "tracker.archlinux.org",
]

BT_TRACKER_KEYWORD = [
    "tracker",        # 兜底，匹配所有含 tracker 的域名
    "announce",
    "bittorrent",
    "bt-tracker",
]


# ═══════════════════════════════════════════════════════════════
#  第三部分：下载工具 & 相关服务
# ═══════════════════════════════════════════════════════════════

# 下载工具 / P2P 服务相关域名
DOWNLOAD_DOMAINS = {
    # --- BT 客户端 WebUI / API ---
    "qBittorrent WebUI": [
        "+.qbittorrent.org",
        "+.github.com/qbittorrent",  # releases
    ],
    "Transmission": [
        "+.transmissionbt.com",
    ],
    "Deluge": [
        "+.deluge-torrent.org",
    ],
    "μTorrent / BitTorrent": [
        "+.utorrent.com",
        "+.bittorrent.com",
        "+.bt.co",
    ],
    "aria2": [
        "+.aria2.github.io",
        "+.github.com/aria2",
    ],
    "Motrix": [
        "+.motrix.app",
        "+.github.com/agalwood/Motrix",
    ],
    "Xunlei (迅雷)": [
        "+.xunlei.com",
        "+.sandai.net",
        "+.kan.xunlei.com",
        "+.hub5btmain.sandai.net",
        "+.hub5emu.sandai.net",
        "+.lv.bilibili.com",  # 迅雷 P2P CDN
    ],
    "IDM (Internet Download Manager)": [
        "+.tonec.com",
        "+.internetdownloadmanager.com",
        "+.idman.com",
    ],
    "FDM (Free Download Manager)": [
        "+.freedownloadmanager.org",
        "+.fdm-foss.org",
    ],
    "EagleGet": [
        "+.eagleget.com",
    ],
    "JDownloader": [
        "+.jdownloader.org",
        "+.appwork.org",
    ],

    # --- BT / P2P 网络辅助 ---
    "DHT Bootstrap": [
        "+.router.bittorrent.com",
        "+.router.utorrent.com",
        "+.dht.transmissionbt.com",
        "+.dht.aelitis.com",
    ],
    "Peer Exchange (PEX)": [
        "+.pex.vuze.com",
    ],
    "BitTorrent DNS (BT-DNS)": [
        "+.btdig.com",
        "+.bteye.org",
        "+.btcache.me",
    ],

    # --- 磁力链接 / 种子搜索引擎 ---
    "BT 搜索引擎": [
        "+.thepiratebay.org",
        "+.1337x.to",
        "+.rarbg.to",
        "+.rarbg.is",
        "+.limetorrents.info",
        "+.torrentgalaxy.to",
        "+.yts.mx",
        "+.eztv.re",
        "+.nyaa.si",
        "+.sukebei.nyaa.si",
        "+.anidex.info",
        "+.acg.rip",
        "+.dmhy.org",
        "+.bangumi.moe",
        "+.nyaa.pt",
    ],

    # --- 网盘 / 直接下载服务 ---
    "Mega": [
        "+.mega.nz",
        "+.mega.co.nz",
        "+.mega.io",
    ],
    "MediaFire": [
        "+.mediafire.com",
    ],
    "Zippyshare": [
        "+.zippyshare.com",
    ],
    "Pixeldrain": [
        "+.pixeldrain.com",
    ],
    "GoFile": [
        "+.gofile.io",
    ],
    "Bunkr": [
        "+.bunkr.ru",
        "+.bunkrr.su",
    ],
    "KrakenFiles": [
        "+.krakenfiles.com",
    ],
    "1fichier": [
        "+.1fichier.com",
    ],
    "Uploaded": [
        "+.uploaded.net",
        "+.ul.to",
    ],

    # --- 国内网盘 ---
    "百度网盘": [
        "+.pan.baidu.com",
        "+.yun.baidu.com",
        "+.d.pcs.baidu.com",
        "+.nj.baidupcs.com",
        "+.qd.baidupcs.com",
        "+.cdn.baidupcs.com",
    ],
    "阿里云盘": [
        "+.aliyundrive.com",
        "+.alipan.com",
        "+.adrive.com",
        "+.cdn.alipan.com",
    ],
    "夸克网盘": [
        "+.pan.quark.cn",
        "+.drive-pc.quark.cn",
        "+.cloud.quark.cn",
    ],
    "迅雷云盘": [
        "+.pan.xunlei.com",
        "+.pan.zwz.xunlei.com",
    ],
    "天翼云盘": [
        "+.cloud.189.cn",
        "+.m.cloud.189.cn",
        "+.h.cloud.189.cn",
    ],
    "115网盘": [
        "+.115.com",
        "+.115cdn.com",
        "+.anxia.com",
    ],
    "蓝奏云": [
        "+.lanzou.com",
        "+.lanzoui.com",
        "+.lanzoux.com",
        "+.wwgz.lanzoup.com",
        "+.wwi.lanzoup.com",
        "+.wwx.lanzoup.com",
    ],
    "123云盘": [
        "+.123pan.com",
        "+.123pan.cn",
        "+.12365.cx",
    ],
    "坚果云": [
        "+.jianguoyun.com",
        "+.nutstore.com",
        "+.nutstore.net",
    ],
    "城通网盘": [
        "+.ctfile.com",
        "+.ctfservice.com",
        "+.pipipan.com",
    ],
    "奶牛快传": [
        "+.cowtransfer.com",
    ],
    "文叔叔": [
        "+.wenjj.com",
        "+.wenshushu.cn",
    ],
    "腾讯微云": [
        "+.weiyun.com",
        "+.share.weiyun.com",
    ],

    # --- 国内下载 / P2P CDN ---
    "Thunder/Xunlei P2P CDN": [
        "+.xlviiirdrdata.com",
        "+.xn--yet82m60b.com",
    ],
    "PPStream/PPTV P2P": [
        "+.ppstream.com",
        "+.pptv.com",
    ],
    "Youku P2P": [
        "+.ykimg.com",
    ],
}


# ═══════════════════════════════════════════════════════════════
#  主逻辑
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="BT/PT/下载规则集生成器")
    parser.add_argument("--output", "-o", default=".", help="输出目录")
    parser.add_argument("--skip-pt", action="store_true", help="跳过 PT 站点获取")
    args = parser.parse_args()

    outdir = args.output
    os.makedirs(outdir, exist_ok=True)

    # ── PT 站点 ──
    pt_site_domains = set()
    pt_tracker_hosts = set()
    if not args.skip_pt:
        pt_site_domains, pt_tracker_hosts = fetch_pt_sites()

    # ── BT 公共 Tracker ──
    bt_trackers = set(BT_TRACKER_STATIC)
    print(f"📥 BT 公共 Tracker: {len(bt_trackers)}")

    # ── 下载工具 & 服务 ──
    dl_direct = set()      # +.domain 格式
    dl_keywords = set()    # keyword 兜底
    for category, domains in DOWNLOAD_DOMAINS.items():
        for d in domains:
            if d.startswith("+."):
                dl_direct.add(d)
            else:
                dl_keywords.add(d)
    print(f"📥 下载服务域名: {len(dl_direct)}, 关键词: {len(dl_keywords)}")

    # ── 写文件 ──
    stats = {}

    # 1) pt-direct.txt
    path = os.path.join(outdir, "pt-direct.txt")
    lines = sorted(f"+.{d}" for d in pt_site_domains)
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n" if lines else "")
    stats["pt-direct"] = len(lines)

    # 2) pt-tracker-direct.txt
    path = os.path.join(outdir, "pt-tracker-direct.txt")
    lines = sorted(f"+.{d}" for d in pt_tracker_hosts)
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
        # PT tracker 关键词兜底
        f.write("tracker\n")
    stats["pt-tracker"] = len(lines)

    # 3) bt-tracker-direct.txt
    path = os.path.join(outdir, "bt-tracker-direct.txt")
    lines = sorted(f"+.{d}" for d in bt_trackers)
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
        for kw in BT_TRACKER_KEYWORD:
            f.write(f"{kw}\n")
    stats["bt-tracker"] = len(lines)

    # 4) download-direct.txt（下载工具/服务）
    path = os.path.join(outdir, "download-direct.txt")
    lines = sorted(dl_direct)
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
        for kw in sorted(dl_keywords):
            f.write(f"{kw}\n")
    stats["download-services"] = len(lines)

    # 5) all-download-rules.txt（合并版 → Direct）
    path = os.path.join(outdir, "all-download-rules.txt")
    all_lines = set()
    all_lines.update(f"+.{d}" for d in pt_site_domains)
    all_lines.update(f"+.{d}" for d in pt_tracker_hosts)
    all_lines.update(f"+.{d}" for d in bt_trackers)
    all_lines.update(dl_direct)
    with open(path, "w") as f:
        f.write("\n".join(sorted(all_lines)) + "\n")
        # 关键词兜底
        all_keywords = {"tracker", "announce", "bittorrent", "bt-tracker"}
        all_keywords.update(dl_keywords)
        for kw in sorted(all_keywords):
            f.write(f"{kw}\n")
    stats["all-merged"] = len(all_lines)

    # 6) all-download-fakeip.txt（合并版 → FakeIP）
    path = os.path.join(outdir, "all-download-fakeip.txt")
    with open(path, "w") as f:
        f.write("\n".join(sorted(all_lines)) + "\n")
    stats["all-fakeip"] = len(all_lines)

    # ── 输出统计 ──
    print()
    print("=" * 50)
    print("  📊 生成完成")
    print("=" * 50)
    print(f"  pt-direct.txt          {stats['pt-direct']:>5} 条 (PT 站点)")
    print(f"  pt-tracker-direct.txt  {stats['pt-tracker']:>5} 条 (PT Tracker)")
    print(f"  bt-tracker-direct.txt  {stats['bt-tracker']:>5} 条 (BT 公共 Tracker)")
    print(f"  download-direct.txt    {stats['download-services']:>5} 条 (下载工具/服务)")
    print(f"  all-download-rules.txt {stats['all-merged']:>5} 条 (合并 Direct)")
    print(f"  all-download-fakeip.txt{stats['all-fakeip']:>5} 条 (合并 FakeIP)")
    print("=" * 50)

    # 写入 GitHub Actions output
    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output:
        with open(gh_output, "a") as f:
            for k, v in stats.items():
                f.write(f"{k}_count={v}\n")


if __name__ == "__main__":
    main()
