#!/usr/bin/env python3
"""
p2p-rules Generator — IYUU 生态数据源
===================================
数据源：
  1. pre-dessert-sites（IYUU 生态 PT 站点配置库）
  2. 内置 BT 公共 Tracker / 下载工具 / 网盘域名

生成物：
  - pt-site-direct.txt          PT 站点域名 → 直连
  - pt-tracker-direct.txt       PT Tracker 域名 → 直连
  - bt-tracker-direct.txt       BT 公共 Tracker → 直连
  - download-direct.txt         下载工具 & 网盘 → 直连
  - all-direct-rules.txt        全部合并 → 直连
  - all-fakeip-filter.txt       全部合并 → FakeIP Filter

用法：
  python3 generate.py --output ./rules/
  python3 generate.py --output ./rules/ --skip-pt  # 离线模式
"""

import argparse
import io
import json
import os
import sys
import urllib.request
import zipfile
from urllib.parse import urlparse
from datetime import datetime

# ─── BT Public Trackers ───────────────────────────────────────────────
BT_TRACKERS = [
    "opentrackr.org", "stealth.si", "demonii.com", "coppersurfer.tk",
    "bittorrent.com", "tracker.opentrackr.org", "tracker.coppersurfer.tk",
    "tracker.leechers-paradise.org", "tracker.internetwarriors.net",
    "tracker.skyts.net", "tracker.pirateparty.gr", "tracker.breizh.pm",
    "tracker.tiny-vps.com", "tracker.fastcast.nz", "tracker.zer0day.to",
    "tracker.publictorrent.net", "open.stealth.si",
    "udp.tracker.opentrackr.org", "tracker.openbittorrent.com",
    "udp.tracker.openbittorrent.com", "tracker.publicbt.com",
    "tracker.istole.it", "tracker.ccc.de", "tracker.pomf.se",
    "explodie.org", "retracker.local", "tracker.uw0.xyz",
    "retracker.mooo.com", "tracker.torrent.eu.org", "tracker.dler.org",
    "tracker.zemojia.love", "tracker.nanoha.org", "tracker.moeking.me",
    "tracker.tamersunion.org", "tracker.ipv4.download.windowsupdate.com",
    "bt1.archive.org", "bt2.archive.org", "debian.org", "ubuntu.com",
    "torrent.ubuntu.com", "ipv4.tracker.harry.lu", "tracker.filemail.com",
    "tracker2.itzmx.com", "tracker3.itzmx.com", "tracker4.itzmx.com",
    "tracker.ali213.net", "tracker.joybomb.cn",
]

# ─── PT Tracker 硬编码（pre-dessert-sites 可能没有覆盖的）──────────────
PT_TRACKER_EXTRA = [
    "tracker.mteam.cc", "tracker.hdsky.me", "tracker.ourbits.club",
    "tracker.pthome.net", "tracker.chdbits.co", "tracker.lemonhd.org",
    "tracker.hdcity.org", "tracker.totheglory.im", "tracker.piggo.me",
    "tracker.hdfans.org", "tracker.wintersakura.net", "tracker.hdatmos.club",
    "tracker.leaves.red", "tracker.audiences.me", "tracker.open.cd",
    "tracker.springsunday.net", "tracker.beitai.pt", "tracker.btschool.club",
    "tracker.hdhome.org", "tracker.hdzone.me", "tracker.gainbound.net",
    "tracker.nicept.net", "tracker.cyanbug.net",
]

# ─── Download Tools ────────────────────────────────────────────────────
DOWNLOAD_TOOL_DOMAINS = [
    # qBittorrent / Transmission / Deluge / μTorrent
    "api.qbittorrent.org", "releases.qbittorrent.org",
    "www.transmissionbt.com", "download.transmissionbt.com",
    "ftp.osuosl.org", "deluge-torrent.org",
    "www.bittorrent.com", "bt.utorrent.com",
    "download.utorrent.com", "download.bittorrent.com",
    # aria2 / Motrix
    "api.github.com", "github.com", "objects.githubusercontent.com",
    # 迅雷
    "xunlei.com", "www.xunlei.com", "sandai.net", "www.sandai.net",
    "hub5btmain.sandai.net", "hub5emu.sandai.net", "hub5pr.sandai.net",
    "api.cloud.xunlei.com", "xluser-ssl.xunlei.com",
    "vip.xunlei.com", "dynamic.cloud.vip.xunlei.com",
    "cloud.xunlei.com", "xlyunpan.xunlei.com",
    # IDM / FDM / JDownloader / EagleGet
    "www.internetdownloadmanager.com", "tonec.com",
    "www.freedownloadmanager.org", "freedownloadmanager.org",
    "jdownloader.org", "my.jdownloader.org",
    "update.jdownloader.org", "eagleget.com",
]

# ─── Cloud Storage / 网盘 ─────────────────────────────────────────────
CLOUD_DOMAINS = [
    # 国内
    "pan.baidu.com", "yun.baidu.com", "pcs.baidu.com",
    "issuecdn.baidupcs.com", "pan.xunlei.com",
    "www.aliyundrive.com", "aliyundrive.com",
    "api.aliyundrive.com", "openapi.alipan.com",
    "www.quark.cn", "drive-pc.quark.cn",
    "cloud.189.cn", "h5.cloud.189.cn", "m.cloud.189.cn",
    "115.com", "115cdn.com", "anxia.com",
    "wwa.lanzoui.com", "lanzoui.com", "lanzoux.com", "lanzouy.com",
    "www.123pan.com", "123pan.com",
    "www.jianguoyun.com", "www.jianguoyun.net",
    "ctfile.com", "www.ctfile.com", "ftn.ctfile.com",
    "cowtransfer.com", "www.cowtransfer.com",
    "wen-shu.com", "www.wen-shu.com",
    "weiyun.com", "www.weiyun.com", "filehelper.115.com",
    # 国际
    "mega.nz", "mediafire.com", "www.mediafire.com",
    "pixeldrain.com", "gofile.io", "bunkr.to", "bunkr.la",
    "krakenfiles.com", "1fichier.com", "uploaded.net",
    "files.catbox.moe", "litterbox.catbox.moe",
    "tempfiles.ninja", "tmpfiles.org",
]

# ─── BT/PT Search Sites ───────────────────────────────────────────────
SEARCH_DOMAINS = [
    "1337x.to", "www.1337x.to",
    "thepiratebay.org", "www.thepiratebay.org",
    "nyaa.si", "sukebei.nyaa.si",
    "bangumi.moe", "acg.rip", "dmhy.org", "www.dmhy.org",
    "hdvbits.com", "btdig.com", "www.btdig.com",
    "www.torrentgalaxy.to", "www.torlock.com", "www.limetorrents.info",
]

# ─── DHT / PEX ─────────────────────────────────────────────────────────
DHT_DOMAINS = [
    "router.bittorrent.com", "router.utorrent.com",
    "dht.transmissionbt.com", "dht.aelitis.com", "demonoid.com",
]


def fetch_pt_sites():
    """从 pre-dessert-sites 拉取 PT 站点配置（IYUU 生态上游数据源）"""
    zip_url = "https://github.com/mantou568/pre-dessert-sites/archive/refs/heads/main.zip"

    try:
        print("[IYUU] 正在下载 pre-dessert-sites 站点配置...")
        req = urllib.request.Request(zip_url, headers={"User-Agent": "iyuu-mihomo-gen/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            zip_data = resp.read()
        print(f"[IYUU] 下载完成: {len(zip_data) // 1024}KB")
    except Exception as e:
        print(f"[WARN] 下载失败: {e}", file=sys.stderr)
        return set()

    domains = set()
    prefix = "pre-dessert-sites-main/site_config/sites/"

    try:
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            site_files = [n for n in zf.namelist() if n.startswith(prefix) and n.endswith(".json")]
            print(f"[IYUU] 发现 {len(site_files)} 个站点配置")

            for name in site_files:
                try:
                    content = zf.read(name)
                    site_data = json.loads(content)
                    domain_url = site_data.get("domain", "")
                    if domain_url:
                        parsed = urlparse(domain_url)
                        host = parsed.hostname or domain_url
                        host = host.lower().strip()
                        if host:
                            domains.add(host)
                            # 同时生成 tracker 子域名
                            domains.add(f"tracker.{host}")
                except Exception as e:
                    short = name.split("/")[-1]
                    print(f"  [WARN] 解析 {short} 失败: {e}", file=sys.stderr)
    except Exception as e:
        print(f"[WARN] 读取 zip 失败: {e}", file=sys.stderr)

    print(f"[IYUU] 提取了 {len(domains)} 个 PT 站点 + Tracker 域名")
    return domains


def write_rules(filepath, domains, comment=""):
    """写入规则文件"""
    sorted_domains = sorted(set(d.lower().strip() for d in domains if d.strip()))
    with open(filepath, "w", encoding="utf-8") as f:
        if comment:
            f.write(f"# {comment}\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        for d in sorted_domains:
            f.write(f"{d}\n")
    return len(sorted_domains)


def main():
    parser = argparse.ArgumentParser(description="p2p-rules Generator")
    parser.add_argument("--output", "-o", default="./rules", help="输出目录")
    parser.add_argument("--skip-pt", action="store_true", help="跳过 PT 站点抓取（离线模式）")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    # 1. 获取 PT 站点
    if args.skip_pt:
        print("[SKIP] 跳过 PT 站点抓取")
        pt_sites = set()
    else:
        pt_sites = fetch_pt_sites()

    # 2. PT Tracker（硬编码 + 自动生成的 tracker 子域名）
    pt_tracker = set(PT_TRACKER_EXTRA)
    for d in pt_sites.copy():
        # 如果域名本身不是 tracker.xxx 格式，生成 tracker.xxx
        if not d.startswith("tracker."):
            pt_tracker.add(f"tracker.{d}")
    pt_tracker -= pt_sites  # 去重

    # 3. 合并 BT + DHT
    bt_all = set(BT_TRACKERS) | set(DHT_DOMAINS)

    # 4. 合并下载工具 + 网盘 + 搜索
    download_all = set(DOWNLOAD_TOOL_DOMAINS) | set(CLOUD_DOMAINS) | set(SEARCH_DOMAINS)

    # 5. 写入各个规则文件
    stats = {}

    stats["pt-site"] = write_rules(
        os.path.join(args.output, "pt-site-direct.txt"),
        pt_sites,
        "IYUU PT Site Domains → Direct (from pre-dessert-sites)"
    )

    stats["pt-tracker"] = write_rules(
        os.path.join(args.output, "pt-tracker-direct.txt"),
        pt_tracker,
        "IYUU PT Tracker Domains → Direct"
    )

    stats["bt"] = write_rules(
        os.path.join(args.output, "bt-tracker-direct.txt"),
        bt_all,
        "BT Public Trackers + DHT/PEX → Direct"
    )

    stats["download"] = write_rules(
        os.path.join(args.output, "download-direct.txt"),
        download_all,
        "Download Tools + Cloud Storage + Search → Direct"
    )

    # 6. 合并全部
    all_domains = pt_sites | pt_tracker | bt_all | download_all

    stats["all-direct"] = write_rules(
        os.path.join(args.output, "all-direct-rules.txt"),
        all_domains,
        "All IYUU PT/BT/Download Rules → Direct"
    )

    stats["all-fakeip"] = write_rules(
        os.path.join(args.output, "all-fakeip-filter.txt"),
        all_domains,
        "All IYUU PT/BT/Download Rules → FakeIP Filter"
    )

    # 汇总
    print(f"\n{'='*55}")
    print(f"  IYUU Mihomo 规则生成完毕 → {args.output}/")
    print(f"{'='*55}")
    print(f"  pt-site-direct.txt    : {stats['pt-site']:>5} domains  (PT 站点)")
    print(f"  pt-tracker-direct.txt : {stats['pt-tracker']:>5} domains  (PT Tracker)")
    print(f"  bt-tracker-direct.txt : {stats['bt']:>5} domains  (BT Tracker + DHT)")
    print(f"  download-direct.txt   : {stats['download']:>5} domains  (下载工具 + 网盘)")
    print(f"  all-direct-rules.txt  : {stats['all-direct']:>5} domains  (直连汇总)")
    print(f"  all-fakeip-filter.txt : {stats['all-fakeip']:>5} domains  (FakeIP 汇总)")
    print(f"{'='*55}")


if __name__ == "__main__":
    main()
