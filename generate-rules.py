#!/usr/bin/env python3
"""Generate BT/PT/Download direct-connect rule sets for Clash/Mihomo."""

import argparse
import io
import json
import os
import sys
import urllib.request
import urllib.error
import zipfile
from urllib.parse import urlparse

# ─── BT Public Trackers ───────────────────────────────────────────────
BT_TRACKERS = [
    "opentrackr.org",
    "stealth.si",
    "demonii.com",
    "coppersurfer.tk",
    "bittorrent.com",
    "tracker.opentrackr.org",
    "tracker.coppersurfer.tk",
    "tracker.leechers-paradise.org",
    "tracker.internetwarriors.net",
    "tracker.skyts.net",
    "tracker.pirateparty.gr",
    "tracker.breizh.pm",
    "tracker.tiny-vps.com",
    "tracker.fastcast.nz",
    "tracker.zer0day.to",
    "tracker.publictorrent.net",
    "open.stealth.si",
    "udp.tracker.opentrackr.org",
    "tracker.openbittorrent.com",
    "udp.tracker.openbittorrent.com",
    "tracker.publicbt.com",
    "tracker.istole.it",
    "tracker.ccc.de",
    "tracker.pomf.se",
    "explodie.org",
    "retracker.local",
    "tracker.uw0.xyz",
    "retracker.mooo.com",
    "tracker.torrent.eu.org",
    "tracker.dler.org",
    "tracker.zemojia.love",
    "tracker.nanoha.org",
    "tracker.moeking.me",
    "tracker.tamersunion.org",
    "tracker.ipv4.download.windowsupdate.com",
    "bt1.archive.org",
    "bt2.archive.org",
    "debian.org",
    "ubuntu.com",
    "torrent.ubuntu.com",
    "ipv4.tracker.harry.lu",
    "tracker.filemail.com",
    "tracker2.itzmx.com",
    "tracker3.itzmx.com",
    "tracker4.itzmx.com",
    "tracker.ali213.net",
    "tracker.joybomb.cn",
]

# ─── PT Tracker domains ──────────────────────────────────────────────
PT_TRACKER_DOMAINS = [
    "tracker.pterclub.com",
    "tracker.hdsky.me",
    "tracker.mteam.cc",
    "tracker.keepfrds.com",
    "tracker.ourbits.club",
    "tracker.lemonhd.org",
    "tracker.tjupt.org",
    "tracker.npupt.com",
    "tracker.open.cd",
    "tracker.hdfans.org",
    "tracker.pandapt.net",
    "tracker.piggo.me",
    "tracker.yemapt.org",
    "tracker.hhanclub.to",
    "tracker.btschool.club",
    "tracker.springsunday.net",
    "tracker.cilibr.org",
    "tracker.chdbits.co",
    "tracker.hdatmos.club",
    "tracker.nicept.net",
    "tracker.avistaz.to",
    "tracker.cinematik.net",
    "tracker.chdizhi.love",
    "tracker.chdizhi.pub",
    "tracker.beyond-hd.me",
    "tracker.hdbits.org",
    "tracker.passionetorrentr.com",
    "tracker.kamept.com",
    "tracker.discfan.net",
    "tracker.dragonhd.xyz",
    "tracker.nicept.me",
    "tracker.ptcafe.club",
    "tracker.ptlover.com",
    "tracker.nicept.me",
    "tracker.okpt.me",
    "tracker.mypt.me",
    "tracker.dubhe.to",
    "tracker.aither.cc",
    "tracker.blutopia.cc",
    "tracker.hawke.uno",
    "tracker.hdkyl.me",
    "tracker.longpt.com",
    "tracker.luckpt.com",
    "tracker.muxuege.com",
    "tracker.ptfans.me",
    "tracker.ptgtk.me",
    "tracker.ptlgs.me",
    "tracker.ptsbao.com",
    "tracker.ptskit.me",
    "tracker.ptvicomo.com",
    "tracker.ptzone.me",
    "tracker.carpt.me",
    "tracker.ggpt.me",
    "tracker.oshenpt.com",
    "tracker.crabpt.com",
    "tracker.kufei.me",
    "tracker.huabeit.com",
    "tracker.52pt.com",
    "tracker.sukebei.pantsu.cat",
    "tracker.iptorrents.com",
    "tracker.torrentleech.org",
    "tracker.filelist.io",
    "tracker.redacted.ch",
    "tracker.orpheus.network",
    "tracker.broadcasthe.net",
    "tracker.empornium.sx",
    "tracker.javhd.fun",
    "tracker.javzoo.com",
    "tracker.javtrailers.com",
    "tracker.javlib.com",
    "tracker.javdb.com",
    "tracker.javlibrary.com",
    "tracker.jav321.com",
    "tracker.javbus.com",
    "tracker.javbus.me",
    "tracker.javdb.me",
]

# ─── Download Tools ───────────────────────────────────────────────────
DOWNLOAD_TOOL_DOMAINS = [
    # qBittorrent / Transmission / Deluge / μTorrent
    "api.qbittorrent.org",
    "releases.qbittorrent.org",
    "www.transmissionbt.com",
    "download.transmissionbt.com",
    "ftp.osuosl.org",
    "deluge-torrent.org",
    "www.bittorrent.com",
    "bt.utorrent.com",
    "download.utorrent.com",
    "download.bittorrent.com",
    # aria2 / Motrix
    "api.github.com",  # aria2 update check
    "github.com",
    "objects.githubusercontent.com",
    # 迅雷
    "xunlei.com",
    "www.xunlei.com",
    "sandai.net",
    "www.sandai.net",
    "hub5btmain.sandai.net",
    "hub5emu.sandai.net",
    "hub5pr.sandai.net",
    "api.cloud.xunlei.com",
    "xluser-ssl.xunlei.com",
    "vip.xunlei.com",
    "dynamic.cloud.vip.xunlei.com",
    "cloud.xunlei.com",
    "xlyunpan.xunlei.com",
    # IDM / FDM / JDownloader / EagleGet
    "www.internetdownloadmanager.com",
    "tonec.com",
    "www.freedownloadmanager.org",
    "freedownloadmanager.org",
    "jdownloader.org",
    "my.jdownloader.org",
    "update.jdownloader.org",
    "eagleget.com",
]

# ─── Cloud Storage / Download Sites ───────────────────────────────────
CLOUD_DOMAINS = [
    # 国内网盘
    "pan.baidu.com",
    "yun.baidu.com",
    "pcs.baidu.com",
    "issuecdn.baidupcs.com",
    "pan.xunlei.com",
    "www.aliyundrive.com",
    "aliyundrive.com",
    "api.aliyundrive.com",
    "openapi.alipan.com",
    "www.quark.cn",
    "drive-pc.quark.cn",
    "cloud.189.cn",
    "h5.cloud.189.cn",
    "m.cloud.189.cn",
    "115.com",
    "115cdn.com",
    "anxia.com",
    "wwa.lanzoui.com",
    "lanzoui.com",
    "lanzoux.com",
    "lanzouy.com",
    "www.123pan.com",
    "123pan.com",
    "www.jianguoyun.com",
    "www.jianguoyun.net",
    "ctfile.com",
    "www.ctfile.com",
    "ftn.ctfile.com",
    "cowtransfer.com",
    "www.cowtransfer.com",
    "wen-shu.com",
    "www.wen-shu.com",
    "weiyun.com",
    "www.weiyun.com",
    "filehelper.115.com",
    # 国际网盘 / 文件分享
    "mega.nz",
    "mediafire.com",
    "www.mediafire.com",
    "pixeldrain.com",
    "gofile.io",
    "bunkr.to",
    "bunkr.la",
    "krakenfiles.com",
    "1fichier.com",
    "uploaded.net",
    "files.catbox.moe",
    "litterbox.catbox.moe",
    "tempfiles.ninja",
    "tmpfiles.org",
]

# ─── BT/PT Search Sites ──────────────────────────────────────────────
SEARCH_DOMAINS = [
    "1337x.to",
    "www.1337x.to",
    "thepiratebay.org",
    "www.thepiratebay.org",
    "nyaa.si",
    "sukebei.nyaa.si",
    "bangumi.moe",
    "acg.rip",
    "dmhy.org",
    "www.dmhy.org",
    "hdvbits.com",
    "btdig.com",
    "www.btdig.com",
    "www.torrentgalaxy.to",
    "www.torlock.com",
    "www.limetorrents.info",
]

# ─── DHT / PEX / Magnet ──────────────────────────────────────────────
DHT_DOMAINS = [
    "router.bittorrent.com",
    "router.utorrent.com",
    "dht.transmissionbt.com",
    "dht.aelitis.com",
    "demonoid.com",
]


def fetch_pt_sites():
    """Fetch PT site domains from pre-dessert-sites repo (zip download)."""
    zip_url = "https://github.com/mantou568/pre-dessert-sites/archive/refs/heads/main.zip"

    try:
        print("Downloading pre-dessert-sites archive...")
        req = urllib.request.Request(zip_url, headers={"User-Agent": "p2p-rules-generator/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            zip_data = resp.read()
        print(f"Downloaded {len(zip_data) // 1024}KB zip archive")
    except Exception as e:
        print(f"Warning: Failed to download archive: {e}", file=sys.stderr)
        return set()

    domains = set()
    prefix = "pre-dessert-sites-main/site_config/sites/"

    try:
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            site_files = [n for n in zf.namelist() if n.startswith(prefix) and n.endswith(".json")]
            print(f"Found {len(site_files)} site configs in archive")

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
                except Exception as e:
                    short = name.split("/")[-1]
                    print(f"  Warning: Failed to parse {short}: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Failed to read zip archive: {e}", file=sys.stderr)

    print(f"Extracted {len(domains)} PT site domains")
    return domains


def write_rules(filepath, domains, comment=""):
    """Write domain list to a Clash/Mihomo rule-set text file."""
    sorted_domains = sorted(set(d.lower().strip() for d in domains if d.strip()))
    with open(filepath, "w", encoding="utf-8") as f:
        if comment:
            for line in comment.strip().split("\n"):
                f.write(f"# {line.strip()}\n")
        for d in sorted_domains:
            f.write(f"{d}\n")
    return len(sorted_domains)


def main():
    parser = argparse.ArgumentParser(description="Generate BT/PT/Download rules for Clash/Mihomo")
    parser.add_argument("--output", "-o", default=".", help="Output directory (default: .)")
    parser.add_argument("--skip-pt", action="store_true", help="Skip fetching PT sites from remote (offline mode)")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    # 1. Fetch PT sites
    if args.skip_pt:
        print("Skipping PT site fetch (--skip-pt)")
        pt_domains = set()
    else:
        print("Fetching PT sites from pre-dessert-sites...")
        pt_domains = fetch_pt_sites()

    # 2. Collect PT tracker domains (union of fetched + hardcoded)
    pt_tracker_set = set(PT_TRACKER_DOMAINS)
    # Also add trackers from PT site domains (common pattern: tracker.{domain})
    for d in pt_domains:
        pt_tracker_set.add(f"tracker.{d}")
    # Remove if the base domain is already in pt_domains
    pt_tracker_set -= pt_domains

    # 3. Write rule files
    count_pt = write_rules(
        os.path.join(args.output, "pt-direct.txt"),
        pt_domains,
        "PT Site Domains → Direct\nGenerated from pre-dessert-sites"
    )

    count_pt_tracker = write_rules(
        os.path.join(args.output, "pt-tracker-direct.txt"),
        pt_tracker_set,
        "PT Tracker Domains → Direct"
    )

    count_bt = write_rules(
        os.path.join(args.output, "bt-tracker-direct.txt"),
        set(BT_TRACKERS) | set(DHT_DOMAINS),
        "BT Public Trackers + DHT/PEX → Direct"
    )

    count_download = write_rules(
        os.path.join(args.output, "download-direct.txt"),
        set(DOWNLOAD_TOOL_DOMAINS) | set(CLOUD_DOMAINS) | set(SEARCH_DOMAINS),
        "Download Tools + Cloud Storage + Search Sites → Direct"
    )

    # 4. Combined rule sets
    all_domains = pt_domains | pt_tracker_set | set(BT_TRACKERS) | set(DHT_DOMAINS) | \
        set(DOWNLOAD_TOOL_DOMAINS) | set(CLOUD_DOMAINS) | set(SEARCH_DOMAINS)

    count_all = write_rules(
        os.path.join(args.output, "all-download-rules.txt"),
        all_domains,
        "All BT/PT/Download Rules → Direct\nCombined: PT + PT Tracker + BT + Download + Cloud + Search"
    )

    # FakeIP version (same domains, action differs at config level)
    count_fakeip = write_rules(
        os.path.join(args.output, "all-download-fakeip.txt"),
        all_domains,
        "All BT/PT/Download Rules → FakeIP\nUse with Mihomo fake-ip DNS mode"
    )

    # Summary
    print(f"\n{'='*50}")
    print(f"Generated {5} rule files in {args.output}/")
    print(f"  pt-direct.txt          : {count_pt} domains")
    print(f"  pt-tracker-direct.txt  : {count_pt_tracker} domains")
    print(f"  bt-tracker-direct.txt  : {count_bt} domains")
    print(f"  download-direct.txt    : {count_download} domains")
    print(f"  all-download-rules.txt : {count_all} domains")
    print(f"  all-download-fakeip.txt: {count_fakeip} domains")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
