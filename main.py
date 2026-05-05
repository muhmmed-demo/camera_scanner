"""
Ms Moo — Camera Scanner
تجربة مستخدم مبسطة: زر واحد، نتيجة واضحة لأي شخص
محرك كشف شامل: RTSP / HTTP Snapshot / MJPEG / ONVIF / RTMP / HLS
"""

# ── RTSP: 40+ مسار يشمل كل الشركات المعروفة ────────────────────────────────
# أهم المسارات أولاً (Hikvision / EZVIZ) ثم البقية
RTSP_PATHS = [
    # Hikvision & EZVIZ (الأكثر شيوعاً — تُفحص أولاً)
    "/Streaming/Channels/101", "/Streaming/Channels/102",
    "/ISAPI/Streaming/channels/101",
    "/h264/ch1/main/av_stream", "/h264/ch2/main/av_stream",
    "/h264Preview_01_main", "/h264Preview_01_sub",
    # EZVIZ specific
    "/h264_stream", "/mpeg4_stream",
    # Dahua
    "/cam/realmonitor?channel=1&subtype=0",
    "/cam/realmonitor?channel=1&subtype=1",
    # Generic
    "/", "/live", "/stream", "/video", "/video0", "/video1",
    "/live/ch00_0", "/live/ch01_0", "/h264",
    # Axis
    "/axis-media/media.amp", "/mpeg4/media.amp",
    # Samsung / Hanwha
    "/profile1/media.smp", "/profile2/media.smp",
    # Vivotek
    "/live.sdp", "/live1.sdp",
    # Extras
    "/stream1", "/stream2", "/ch0", "/ch1",
    "/media/video1", "/mpeg4", "/11", "/12",
]

# ── HTTP Snapshot endpoints يشمل كل الشركات ─────────────────────────────────
HTTP_SNAPSHOT_PATHS = [
    # Generic
    "/snapshot.jpg", "/snapshot.cgi", "/image.jpg", "/image.jpeg",
    "/cgi-bin/snapshot.cgi", "/cgi-bin/image.cgi",
    # Hikvision
    "/ISAPI/Streaming/channels/101/picture",
    "/cgi-bin/snapshot.cgi?channel=1",
    # Dahua
    "/cgi-bin/snapshot.cgi?channel=0&subtype=0",
    "/snapshot/1",
    # Axis
    "/jpg/image.jpg", "/axis-cgi/jpg/image.cgi",
    # Foscam
    "/cgi-bin/CGIProxy.fcgi?cmd=snapPicture2",
    # Vivotek
    "/cgi-bin/viewer/video.jpg",
    # Generic extras
    "/webcam.jpg", "/cam_pic.php", "/still.jpg",
    "/live/snapshot", "/capture",
]

# ── MJPEG Stream endpoints ────────────────────────────────────────────────────
MJPEG_PATHS = [
    "/mjpg/video.mjpg", "/video.mjpg", "/mjpeg",
    "/cgi-bin/mjpg/video.cgi", "/mjpeg/1",
    "/videostream.cgi", "/mjpeg.cgi",
    "/cgi-bin/video.cgi",
]

# ── كلمات مرور افتراضية موسعة ───────────────────────────────────────────────
DEFAULT_CREDS = [
    # Blank
    ("", ""), ("admin", ""), ("root", ""), ("guest", ""),
    # admin variations
    ("admin", "admin"), ("admin", "12345"), ("admin", "123456"),
    ("admin", "admin123"), ("admin", "password"), ("admin", "1234"),
    ("admin", "admin1234"), ("admin", "Admin123"),
    # root variations
    ("root", "root"), ("root", "12345"), ("root", "password"),
    # Common usernames
    ("user", "user"), ("user", "12345"), ("guest", "guest"),
    ("service", "service"), ("supervisor", "supervisor"),
    # Manufacturer defaults
    ("admin", "888888"),    # Dahua
    ("admin", "666666"),    # Dahua alt
    ("admin", "admin888"),  # various
    ("admin1", "password"), # Axis
    ("operator", ""),       # Axis
]

import os
import concurrent.futures
os.environ["KIVY_LOG_LEVEL"] = "warning"

import threading
import socket
import base64
import requests
requests.packages.urllib3.disable_warnings()

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.button import MDRaisedButton
from kivy.uix.widget import Widget
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivy.logger import Logger
from kivy.animation import Animation

# ─── KV Layout ───────────────────────────────────────────────────────────────
KV = """
#:import get_color_from_hex kivy.utils.get_color_from_hex

<SplashScreen>:
    name: "splash"
    md_bg_color: 0.04, 0.05, 0.12, 1
    MDBoxLayout:
        orientation: "vertical"
        padding: dp(40)
        pos_hint: {"center_x": 0.5, "center_y": 0.5}

        Widget:
            size_hint_y: 0.18

        MDCard:
            id: logo_card
            size_hint: None, None
            size: dp(130), dp(130)
            pos_hint: {"center_x": 0.5}
            md_bg_color: 0.1, 0.44, 0.82, 1
            radius: [dp(65)]
            elevation: 20
            MDLabel:
                text: "🐄"
                font_size: "60sp"
                halign: "center"
                valign: "center"

        MDLabel:
            id: title_lbl
            text: "Ms Moo"
            halign: "center"
            font_style: "H3"
            bold: True
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1
            size_hint_y: None
            height: dp(64)
            opacity: 0

        MDLabel:
            id: sub_lbl
            text: "Camera Scanner"
            halign: "center"
            font_style: "H6"
            theme_text_color: "Custom"
            text_color: 0.42, 0.74, 1, 1
            size_hint_y: None
            height: dp(36)
            opacity: 0

        MDLabel:
            id: tag_lbl
            text: "Who's watching? Let's find out."
            halign: "center"
            font_style: "Body2"
            theme_text_color: "Custom"
            text_color: 0.65, 0.65, 0.85, 1
            size_hint_y: None
            height: dp(30)
            opacity: 0

        Widget:
            size_hint_y: 0.14

        MDBoxLayout:
            id: loading_box
            orientation: "horizontal"
            size_hint_y: None
            height: dp(36)
            spacing: dp(10)
            pos_hint: {"center_x": 0.5}
            opacity: 0
            MDSpinner:
                size_hint: None, None
                size: dp(22), dp(22)
                pos_hint: {"center_y": 0.5}
                active: True
                color: 0.42, 0.74, 1, 1
            MDLabel:
                text: "Loading..."
                font_style: "Body2"
                adaptive_height: True
                pos_hint: {"center_y": 0.5}
                theme_text_color: "Custom"
                text_color: 0.6, 0.6, 0.8, 1

        Widget:
            size_hint_y: 0.1

<MainScreen>:
    name: "main"
    md_bg_color: 0.06, 0.07, 0.11, 1

    MDBoxLayout:
        orientation: "vertical"
        padding: [dp(14), dp(14), dp(14), dp(10)]
        spacing: dp(12)

        # ── Top Bar ──────────────────────────────────────────────
        MDCard:
            size_hint_y: None
            height: dp(64)
            padding: [dp(18), 0]
            md_bg_color: 0.1, 0.12, 0.2, 1
            radius: [dp(18)]
            elevation: 4
            MDBoxLayout:
                orientation: "horizontal"
                MDLabel:
                    text: "🐄  Ms Moo"
                    font_style: "H6"
                    bold: True
                    adaptive_height: True
                    pos_hint: {"center_y": 0.5}
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 1
                MDLabel:
                    id: network_lbl
                    text: "Tap Scan to start"
                    halign: "right"
                    font_style: "Caption"
                    adaptive_height: True
                    pos_hint: {"center_y": 0.5}
                    theme_text_color: "Custom"
                    text_color: 0.5, 0.55, 0.75, 1

        # ── BIG SCAN BUTTON ──────────────────────────────────────
        MDCard:
            id: scan_card
            size_hint_y: None
            height: dp(110)
            md_bg_color: 0.1, 0.44, 0.82, 1
            radius: [dp(22)]
            elevation: 10
            on_release: app.toggle_scan()
            MDBoxLayout:
                orientation: "vertical"
                spacing: dp(4)
                padding: dp(12)
                pos_hint: {"center_x": 0.5, "center_y": 0.5}
                MDLabel:
                    id: btn_icon
                    text: "🔍"
                    font_size: "36sp"
                    halign: "center"
                    size_hint_y: None
                    height: dp(48)
                MDLabel:
                    id: btn_label
                    text: "TAP TO SCAN"
                    halign: "center"
                    font_style: "Subtitle1"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 1
                    size_hint_y: None
                    height: dp(28)

        # ── Progress Area ─────────────────────────────────────────
        MDBoxLayout:
            id: progress_area
            orientation: "vertical"
            size_hint_y: None
            height: dp(56)
            spacing: dp(6)
            opacity: 0

            MDLabel:
                id: progress_msg
                text: "Scanning your network..."
                halign: "center"
                font_style: "Body2"
                theme_text_color: "Custom"
                text_color: 0.72, 0.80, 1.0, 1
                size_hint_y: None
                height: dp(24)

            ProgressBar:
                id: progress_bar
                max: 100
                value: 0
                size_hint_y: None
                height: dp(8)

        # ── Summary Banner (shown after scan) ─────────────────────
        MDCard:
            id: summary_card
            size_hint_y: None
            height: dp(72)
            opacity: 0
            md_bg_color: 0.08, 0.14, 0.26, 1
            radius: [dp(18)]
            elevation: 6
            padding: [dp(18), dp(8)]
            MDBoxLayout:
                orientation: "horizontal"
                spacing: dp(16)
                MDLabel:
                    id: summary_icon
                    text: "📡"
                    font_size: "32sp"
                    size_hint_x: None
                    width: dp(44)
                    valign: "center"
                MDBoxLayout:
                    orientation: "vertical"
                    MDLabel:
                        id: summary_title
                        text: "Scan Complete"
                        font_style: "Subtitle1"
                        bold: True
                        adaptive_height: True
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1
                    MDLabel:
                        id: summary_sub
                        text: ""
                        font_style: "Caption"
                        adaptive_height: True
                        theme_text_color: "Custom"
                        text_color: 0.65, 0.75, 0.95, 1

        # ── Results ───────────────────────────────────────────────
        MDScrollView:
            MDBoxLayout:
                id: results_box
                orientation: "vertical"
                spacing: dp(10)
                padding: [0, 0, 0, dp(16)]
                adaptive_height: True
"""

# ─── Screens ──────────────────────────────────────────────────────────────────

class SplashScreen(MDScreen):
    def on_enter(self):
        Clock.schedule_once(self._animate, 0.15)

    def _animate(self, dt):
        lc = self.ids.logo_card
        (Animation(size=(dp(148), dp(148)), duration=0.45, t='out_back') +
         Animation(size=(dp(130), dp(130)), duration=0.28, t='in_out_quad')).start(lc)

        Animation(opacity=1, duration=0.6, t='out_quad').start(self.ids.title_lbl)
        Clock.schedule_once(lambda *_: Animation(opacity=1, duration=0.5).start(self.ids.sub_lbl), 0.35)
        Clock.schedule_once(lambda *_: Animation(opacity=1, duration=0.5).start(self.ids.tag_lbl), 0.6)
        Clock.schedule_once(lambda *_: Animation(opacity=1, duration=0.4).start(self.ids.loading_box), 0.9)
        Clock.schedule_once(self._leave, 3.0)

    def _leave(self, dt):
        anim = Animation(opacity=0, duration=0.45, t='in_quad')
        anim.bind(on_complete=lambda *_: setattr(self.manager, 'current', 'main'))
        anim.start(self)


class MainScreen(MDScreen):
    pass


# ─── Camera Result Card ────────────────────────────────────────────────────────

class CameraCard(MDCard):
    """بطاقة نتيجة — واضحة وبسيطة لأي مستخدم"""

    STATUS_CONFIG = {
        'live':    ('#FF4444', '🔴', 'OPEN — Anyone Can Watch!',
                    "This camera is filming RIGHT NOW and is open to the public. No password needed!"),
        'locked':  ('#FF9800', '🔒', 'Active — Protected',
                    "This camera is working but requires a password to view. It's secure."),
        'offline': ('#555566', '⚫', 'Not Streaming',
                    "This device doesn't seem to be sending any video right now."),
    }

    def __init__(self, ip, status, detail_url=None, method=None, **kwargs):
        super().__init__(**kwargs)
        cfg = self.STATUS_CONFIG.get(status, self.STATUS_CONFIG['offline'])
        color_hex, icon, title, desc = cfg

        color = get_color_from_hex(color_hex)
        self.radius = [dp(18)]
        self.elevation = 5
        self.md_bg_color = [0.10, 0.12, 0.20, 1]
        self.size_hint_y = None
        self.height = dp(1)  # will grow with content
        self.padding = dp(18)
        self.spacing = dp(10)
        self.orientation = "vertical"

        # ── Top row: icon + title + IP ──
        top = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(10))

        top.add_widget(MDLabel(
            text=icon, font_size="28sp",
            size_hint=(None, None), size=(dp(38), dp(44)),
            valign="center", halign="center",
        ))

        mid = MDBoxLayout(orientation="vertical")
        mid.add_widget(MDLabel(
            text=title, font_style="Subtitle1", bold=True,
            adaptive_height=True,
            theme_text_color="Custom", text_color=[*color[:3], 1],
        ))
        mid.add_widget(MDLabel(
            text=ip, font_style="Caption",
            adaptive_height=True, theme_text_color="Hint",
        ))
        top.add_widget(mid)
        self.add_widget(top)

        # ── Description ──
        self.add_widget(MDLabel(
            text=desc, font_style="Body2",
            theme_text_color="Secondary",
            size_hint_y=None, height=dp(44),
        ))

        # ── Detection method (protocol badge) ──
        if method:
            METHOD_LABELS = {
                'RTSP-Open':       '📡 Found via: RTSP Stream (open)',
                'RTSP-Auth':       '🔒 Found via: RTSP Stream (auth needed)',
                'HTTP-Snapshot':   '📸 Found via: HTTP Snapshot image',
                'HTTP-Protected':  '🔒 Found via: HTTP (password protected)',
                'MJPEG':           '🎥 Found via: MJPEG Live Stream',
                'ONVIF':           '🛡️ Found via: ONVIF Protocol',
                'RTMP':            '📡 Found via: RTMP Stream (port 1935)',
                'HLS':             '📡 Found via: HLS Stream (port 9000)',
                'UnknownProto':    '🔍 Found: Active device (protocol unknown)',
            }
            label_text = METHOD_LABELS.get(method)
            if not label_text and method.startswith('HTTP-'):
                brand = method[5:]
                label_text = f'🏷️ Identified as: {brand} camera'
            if label_text:
                self.add_widget(MDLabel(
                    text=label_text,
                    font_style="Caption",
                    theme_text_color="Custom",
                    text_color=get_color_from_hex("#78909C"),
                    size_hint_y=None,
                    height=dp(24),
                ))

        # ── URL (live/locked cameras) ──
        if detail_url:
            url_box = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None, height=dp(32),
                padding=[dp(10), 0, 0, 0],
            )
            url_box.add_widget(MDLabel(
                text=f"📺  {detail_url}",
                font_style="Caption",
                theme_text_color="Custom",
                text_color=get_color_from_hex("#4FC3F7"),
                adaptive_height=True,
                pos_hint={"center_y": 0.5},
            ))
            self.add_widget(url_box)

        self.height = self.minimum_height


# ─── App ──────────────────────────────────────────────────────────────────────

class CameraScannerApp(MDApp):

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        self.title = "Ms Moo — Camera Scanner"
        self._scanning = False
        Builder.load_string(KV)
        sm = MDScreenManager()
        sm.add_widget(SplashScreen(name="splash"))
        sm.add_widget(MainScreen(name="main"))
        return sm

    # ── Scan toggle ────────────────────────────────────────────

    def toggle_scan(self):
        if self._scanning:
            return
        self.start_scan()

    def start_scan(self):
        self._scanning = True
        screen = self._main
        screen.ids.results_box.clear_widgets()
        screen.ids.summary_card.opacity = 0
        screen.ids.progress_area.opacity = 1
        screen.ids.progress_bar.value = 0
        screen.ids.btn_icon.text = "⏳"
        screen.ids.btn_label.text = "SCANNING..."
        screen.ids.scan_card.md_bg_color = [0.22, 0.30, 0.45, 1]
        self._set_progress(0, "Looking for devices on your network…")
        screen.ids.network_lbl.text = self._local_ip() or "No network detected"
        threading.Thread(target=self._scan_worker, daemon=True).start()

    # ── Worker ─────────────────────────────────────────────────

    def _scan_worker(self):
        hosts = self._discover_hosts()          # Phase 1: find hosts
        results = []
        total = max(len(hosts), 1)
        lock = threading.Lock()
        done = [0]

        def check_host(ip):
            ports = self._open_ports(ip)
            result = self._full_camera_check(ip, ports)
            with lock:
                done[0] += 1
                pct = 10 + int(80 * done[0] / total)
                msg = f"Deep-checking {ip}  ({done[0]}/{total})"
                Clock.schedule_once(lambda dt, p=pct, m=msg: self._set_progress(p, m))
                results.append((ip, result['status'], result.get('url'), result.get('method')))

        # فحص متوازي — كل الأجهزة في نفس الوقت
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(total, 20)) as ex:
            list(ex.map(check_host, hosts))

        Clock.schedule_once(lambda dt: self._show_results(results))

    # ── Discovery ──────────────────────────────────────────────

    def _discover_hosts(self):
        """Phase 1: اكتشاف الأجهزة — WS-Discovery أولاً، ثم مسح يدوي كـ fallback"""
        Clock.schedule_once(lambda dt: self._set_progress(5, "Searching for cameras on your network…"))
        found = []

        # ── 1. WS-Discovery: الكاميرات تُعلن عن نفسها تلقائياً ──
        try:
            from wsdiscovery import WSDiscovery
            wsd = WSDiscovery()
            wsd.start()
            Clock.schedule_once(lambda dt: self._set_progress(8, "WS-Discovery: listening for cameras…"))
            services = wsd.searchServices(timeout=4)
            for svc in services:
                for addr in svc.getXAddrs():
                    try:
                        ip = addr.split('//')[1].split(':')[0].split('/')[0]
                        if ip and ip not in found:
                            found.append(ip)
                    except Exception:
                        pass
            wsd.stop()
        except Exception:
            pass  # WS-Discovery غير متاح — ننتقل للمسح اليدوي

        # ── 2. مسح يدوي للـ IPs (fallback أو تكملة) ──
        lip = self._local_ip()
        if lip:
            subnet = '.'.join(lip.split('.')[:3])
            disc_lock = threading.Lock()
            PROBE_PORTS = (554, 80, 8080, 8000, 37777, 1935)

            def probe(host):
                if host in found:
                    return
                for port in PROBE_PORTS:
                    try:
                        s = socket.socket()
                        s.settimeout(0.25)
                        if s.connect_ex((host, port)) == 0:
                            s.close()
                            with disc_lock:
                                if host not in found:
                                    found.append(host)
                            return
                        s.close()
                    except Exception:
                        pass

            # فحص متوازي بـ ThreadPool — أسرع بكثير
            with concurrent.futures.ThreadPoolExecutor(max_workers=100) as ex:
                list(ex.map(probe, (f"{subnet}.{i}" for i in range(1, 255))))

        return found

    def _open_ports(self, ip):
        """فحص متوازي لكل المنافذ المعروفة"""
        ALL_PORTS = (554, 80, 443, 8080, 8000, 8443, 37777, 37778, 1935, 9000)
        open_ = []
        lock = threading.Lock()

        def check(port):
            try:
                s = socket.socket()
                s.settimeout(0.6)
                if s.connect_ex((ip, port)) == 0:
                    with lock:
                        open_.append(port)
                s.close()
            except Exception:
                pass

        threads = [threading.Thread(target=check, args=(p,), daemon=True) for p in ALL_PORTS]
        for t in threads: t.start()
        for t in threads: t.join(timeout=1.5)
        return open_

    # ══════════════════════════════════════════════════
    # MULTI-PROTOCOL CAMERA CHECK  (requests + socket)
    # ══════════════════════════════════════════════════

    def _full_camera_check(self, ip, ports):
        http_ports = [p for p in (80, 8080, 443, 8443, 8000) if p in ports]
        session = requests.Session()
        session.headers['User-Agent'] = 'MsMooScanner/2.0'

        # ── 1. RTSP DESCRIBE (socket — لا يوجد مكتبة RTSP خفيفة لـ Android) ──
        if 554 in ports:
            for path in RTSP_PATHS:
                if self._rtsp_describe(ip, path):
                    return {'status': 'live', 'url': f'rtsp://{ip}{path}', 'method': 'RTSP (open)'}
            for user, pwd in DEFAULT_CREDS:
                for path in RTSP_PATHS[:6]:
                    if self._rtsp_describe(ip, path, user, pwd):
                        return {'status': 'locked', 'url': f'rtsp://{ip}{path}', 'method': 'RTSP (auth)'}

        # ── 2. HTTP Snapshot — requests أبسط وأدق من raw sockets ──
        for port in http_ports:
            scheme = 'https' if port in (443, 8443) else 'http'
            for path in HTTP_SNAPSHOT_PATHS:
                try:
                    r = session.get(f'{scheme}://{ip}:{port}{path}',
                                    timeout=1.2, verify=False, stream=True)
                    ct = r.headers.get('Content-Type', '')
                    if r.status_code == 200 and any(x in ct for x in ('image', 'jpeg', 'video', 'multipart')):
                        return {'status': 'live', 'url': f'{scheme}://{ip}:{port}', 'method': 'HTTP Snapshot 📸'}
                    if r.status_code in (401, 403):
                        return {'status': 'locked', 'url': f'{scheme}://{ip}:{port}', 'method': 'HTTP Protected 🔒'}
                except Exception:
                    pass

        # ── 3. MJPEG — requests تكشف الـ multipart stream ──
        for port in http_ports:
            scheme = 'https' if port in (443, 8443) else 'http'
            for path in MJPEG_PATHS:
                try:
                    r = session.get(f'{scheme}://{ip}:{port}{path}',
                                    timeout=1.2, verify=False, stream=True)
                    ct = r.headers.get('Content-Type', '')
                    if 'multipart' in ct or 'mjpeg' in ct.lower():
                        return {'status': 'live', 'url': f'{scheme}://{ip}:{port}', 'method': 'MJPEG Stream 🎥'}
                except Exception:
                    pass

        # ── 4. ONVIF SOAP — requests أبسط بكثير من raw socket ──
        for port in [p for p in (80, 8000) if p in ports]:
            soap = ('<?xml version="1.0" encoding="utf-8"?>'
                    '<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope">'
                    '<s:Body><GetSystemDateAndTime '
                    'xmlns="http://www.onvif.org/ver10/device/wsdl"/>'
                    '</s:Body></s:Envelope>')
            try:
                r = session.post(f'http://{ip}:{port}/onvif/device_service',
                                 data=soap, timeout=1.2,
                                 headers={'Content-Type': 'application/soap+xml'})
                if 'Envelope' in r.text or 'onvif' in r.text.lower():
                    return {'status': 'locked',
                            'url': f'http://{ip}:{port}/onvif/device_service',
                            'method': 'ONVIF 🛡️'}
            except Exception:
                pass

        # ── 5. HTTP Banner — requests تقرأ الـ Server header مباشرة ──
        BRANDS = {'hikvision': 'Hikvision', 'ezviz': 'EZVIZ', 'dahua': 'Dahua',
                  'axis': 'Axis', 'foscam': 'Foscam', 'reolink': 'Reolink',
                  'vivotek': 'Vivotek', 'hanwha': 'Hanwha', 'bosch': 'Bosch',
                  'amcrest': 'Amcrest', 'ubiquiti': 'Ubiquiti', 'dlink': 'D-Link'}
        for port in http_ports:
            try:
                r = session.get(f'http://{ip}:{port}/', timeout=1.0, verify=False)
                text = (r.headers.get('Server', '') + r.text[:400]).lower()
                for key, name in BRANDS.items():
                    if key in text:
                        return {'status': 'locked', 'url': f'http://{ip}:{port}',
                                'method': f'🏷️ {name} camera'}
            except Exception:
                pass

        # ── 6. RTMP ──
        if 1935 in ports:
            return {'status': 'locked', 'url': f'rtmp://{ip}/live', 'method': 'RTMP 📡'}

        # ── 7. منافذ مفتوحة بدون بث محدد ──
        if ports:
            return {'status': 'locked', 'url': None, 'method': 'Unknown protocol'}

        return {'status': 'offline', 'url': None, 'method': None}

    # ── RTSP — يبقى بـ socket (لا توجد مكتبة RTSP خفيفة لـ Android) ──

    def _rtsp_describe(self, ip, path='/', user='', pwd='', port=554):
        try:
            s = socket.socket()
            s.settimeout(1.5)
            s.connect((ip, port))
            auth = ''
            if user or pwd:
                enc = base64.b64encode(f'{user}:{pwd}'.encode()).decode()
                auth = f'Authorization: Basic {enc}\r\n'
            req = (f'DESCRIBE rtsp://{ip}:{port}{path} RTSP/1.0\r\n'
                   f'CSeq: 1\r\nUser-Agent: MsMooScanner/2.0\r\n'
                   f'Accept: application/sdp\r\n{auth}\r\n')
            s.sendall(req.encode())
            resp = s.recv(1024).decode(errors='ignore')
            s.close()
            return 'RTSP/1.0 200' in resp
        except Exception:
            return False

    # ── UI helpers ─────────────────────────────────────────────

    @property
    def _main(self):
        return self.root.get_screen("main")

    def _local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return None

    def _set_progress(self, value, message):
        s = self._main
        s.ids.progress_bar.value = value
        s.ids.progress_msg.text = message

    def _show_results(self, results):
        self._scanning = False
        screen = self._main

        # Reset button
        screen.ids.btn_icon.text = "🔍"
        screen.ids.btn_label.text = "TAP TO SCAN AGAIN"
        screen.ids.scan_card.md_bg_color = [0.1, 0.44, 0.82, 1]
        screen.ids.progress_area.opacity = 0

        live_count   = sum(1 for _, s, *_ in results if s == 'live')
        locked_count = sum(1 for _, s, *_ in results if s == 'locked')
        total        = len(results)

        # ── Summary Banner ──
        if total == 0:
            screen.ids.summary_icon.text  = "📡"
            screen.ids.summary_title.text = "No cameras found"
            screen.ids.summary_sub.text   = "Make sure you are connected to Wi-Fi and try again."
        elif live_count:
            screen.ids.summary_icon.text  = "⚠️"
            screen.ids.summary_title.text = f"{live_count} camera{'s' if live_count>1 else ''} OPEN to the public!"
            screen.ids.summary_sub.text   = (f"{locked_count} secured  •  {total} total found")
        else:
            screen.ids.summary_icon.text  = "✅"
            screen.ids.summary_title.text = "All cameras are secured 🔒"
            screen.ids.summary_sub.text   = f"{locked_count} active  •  {total} total found"

        Animation(opacity=1, duration=0.5).start(screen.ids.summary_card)

        # ── Cards ──
        if total == 0:
            screen.ids.results_box.add_widget(self._empty_hint())
        else:
            order = {'live': 0, 'locked': 1, 'offline': 2}
            for row in sorted(results, key=lambda x: order[x[1]]):
                ip, status, url = row[0], row[1], row[2]
                method = row[3] if len(row) > 3 else None
                screen.ids.results_box.add_widget(
                    CameraCard(ip=ip, status=status, detail_url=url, method=method))

    def _empty_hint(self):
        box = MDBoxLayout(orientation="vertical", size_hint_y=None, height=dp(200),
                          spacing=dp(10), padding=dp(20))
        box.add_widget(MDLabel(text="😕", font_size="48sp", halign="center",
                               size_hint_y=None, height=dp(64)))
        box.add_widget(MDLabel(
            text="No cameras discovered.\n\nMake sure you're connected to a Wi-Fi network and tap Scan again.",
            halign="center", font_style="Body2",
            theme_text_color="Hint",
        ))
        return box


if __name__ == "__main__":
    CameraScannerApp().run()
