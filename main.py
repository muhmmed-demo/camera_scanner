"""
مكتشف الكاميرات - Camera Scanner
تطبيق أندرويد لاكتشاف كاميرات المراقبة وفحص حالتها الأمنية
"""

RTSP_PATHS = [
    "/", "/live", "/stream", "/h264",
    "/h264/ch1/main/av_stream",
    "/Streaming/Channels/101",
    "/cam/realmonitor?channel=1&subtype=0",
    "/video1",
]

DEFAULT_CREDS = [
    ("", ""), ("admin", ""), ("admin", "admin"),
    ("admin", "12345"), ("admin", "123456"),
    ("root", ""), ("root", "root"),
    ("admin", "password"), ("user", "user"),
]

import os
os.environ["KIVY_LOG_LEVEL"] = "debug"

import threading
import socket
import base64
import traceback

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.scrollview import MDScrollView
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivy.logger import Logger
from kivy.animation import Animation

# --- ملف تصميم الواجهة (KV Language) ---
KV = """
<SeparatorLine@Widget>:
    size_hint_y: None
    height: dp(1)
    canvas:
        Color:
            rgba: 0.3, 0.3, 0.4, 0.5
        Rectangle:
            pos: self.pos
            size: self.size

<CameraCard>:
    orientation: "vertical"
    padding: dp(16)
    spacing: dp(8)
    size_hint_y: None
    height: self.minimum_height
    md_bg_color: 0.12, 0.14, 0.2, 1
    radius: [dp(16)]
    elevation: 4

<SplashScreen>:
    name: "splash"
    md_bg_color: 0.04, 0.05, 0.12, 1

    MDBoxLayout:
        orientation: "vertical"
        padding: dp(40)
        spacing: dp(20)
        pos_hint: {"center_x": 0.5, "center_y": 0.5}
        size_hint: 1, 1

        Widget:
            size_hint_y: 0.15

        # Glowing circle / logo area
        MDBoxLayout:
            size_hint_y: None
            height: dp(180)
            orientation: "vertical"

            MDCard:
                id: logo_card
                size_hint: None, None
                size: dp(130), dp(130)
                pos_hint: {"center_x": 0.5}
                md_bg_color: 0.08, 0.42, 0.78, 1
                radius: [dp(65)]
                elevation: 18

                MDLabel:
                    text: "🐄"
                    font_size: "58sp"
                    halign: "center"
                    valign: "center"

        # App Name
        MDLabel:
            id: title_label
            text: "Ms Moo"
            halign: "center"
            font_style: "H3"
            bold: True
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1
            size_hint_y: None
            height: dp(60)
            opacity: 0

        # Subtitle
        MDLabel:
            id: subtitle_label
            text: "Camera Scanner"
            halign: "center"
            font_style: "H6"
            theme_text_color: "Custom"
            text_color: 0.4, 0.72, 1, 1
            size_hint_y: None
            height: dp(36)
            opacity: 0

        # Tagline
        MDLabel:
            id: tagline_label
            text: "Secure Network. Protect Your World."
            halign: "center"
            font_style: "Body2"
            theme_text_color: "Custom"
            text_color: 0.7, 0.7, 0.85, 1
            size_hint_y: None
            height: dp(30)
            opacity: 0

        Widget:
            size_hint_y: 0.12

        # Loading indicator
        MDBoxLayout:
            id: loading_box
            orientation: "horizontal"
            size_hint_y: None
            height: dp(40)
            spacing: dp(12)
            pos_hint: {"center_x": 0.5}
            opacity: 0

            MDSpinner:
                size_hint: None, None
                size: dp(22), dp(22)
                pos_hint: {"center_y": 0.5}
                active: True
                color: 0.4, 0.72, 1, 1

            MDLabel:
                text: "Initializing..."
                font_style: "Body2"
                theme_text_color: "Custom"
                text_color: 0.6, 0.6, 0.8, 1
                adaptive_height: True
                pos_hint: {"center_y": 0.5}

        Widget:
            size_hint_y: 0.1

<MainScreen>:
    name: "main"
    md_bg_color: 0.06, 0.07, 0.1, 1

    MDBoxLayout:
        orientation: "vertical"
        padding: dp(16)
        spacing: dp(12)

        # Header
        MDCard:
            orientation: "vertical"
            padding: dp(20)
            spacing: dp(8)
            size_hint_y: None
            height: dp(130)
            md_bg_color: app.theme_cls.primary_color
            radius: [dp(20)]
            elevation: 6

            MDLabel:
                text: "Ms Moo — Camera Scanner"
                halign: "center"
                font_style: "H5"
                bold: True
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1

            MDLabel:
                id: status_label
                text: "Press scan to discover cameras"
                halign: "center"
                font_style: "Body2"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 0.8

        # Scan Button & Progress
        MDBoxLayout:
            orientation: "vertical"
            size_hint_y: None
            height: dp(90)
            spacing: dp(10)

            MDRaisedButton:
                id: scan_btn
                text: "Scan Network"
                size_hint_x: 1
                height: dp(55)
                font_size: "18sp"
                on_release: app.start_scan()

            MDBoxLayout:
                id: progress_box
                orientation: "horizontal"
                size_hint_y: None
                height: dp(25)
                spacing: dp(10)
                opacity: 0

                MDSpinner:
                    size_hint: None, None
                    size: dp(20), dp(20)
                    pos_hint: {"center_y": 0.5}
                    active: True

                MDLabel:
                    text: "Scanning..."
                    font_style: "Caption"
                    adaptive_height: True
                    pos_hint: {"center_y": 0.5}
                    theme_text_color: "Secondary"

        # Results Counter
        MDBoxLayout:
            size_hint_y: None
            height: dp(30)

            MDLabel:
                id: count_label
                text: ""
                halign: "right"
                font_style: "Caption"
                adaptive_height: True
                theme_text_color: "Secondary"

        # Results Area
        MDScrollView:
            MDBoxLayout:
                id: results_box
                orientation: "vertical"
                spacing: dp(10)
                padding: [0, 0, 0, dp(10)]
                adaptive_height: True
"""


class SplashScreen(MDScreen):
    """شاشة الترحيب المخصصة لـ Ms Moo"""

    def on_enter(self):
        """تشغيل الأنيميشن فور ظهور الشاشة"""
        Clock.schedule_once(self._animate_in, 0.1)

    def _animate_in(self, dt):
        # أنيميشن الشعار (ينبض)
        logo_card = self.ids.logo_card
        anim_logo = (
            Animation(size=(dp(145), dp(145)), duration=0.5, t='out_back') +
            Animation(size=(dp(130), dp(130)), duration=0.3, t='in_out_quad')
        )
        anim_logo.start(logo_card)

        # ظهور العنوان
        title = self.ids.title_label
        Animation(opacity=1, duration=0.7, t='out_quad').start(title)

        # ظهور العنوان الفرعي بتأخير
        Clock.schedule_once(lambda dt: Animation(opacity=1, duration=0.6, t='out_quad').start(self.ids.subtitle_label), 0.4)

        # ظهور الشعار التعريفي
        Clock.schedule_once(lambda dt: Animation(opacity=1, duration=0.6, t='out_quad').start(self.ids.tagline_label), 0.7)

        # ظهور مؤشر التحميل
        Clock.schedule_once(lambda dt: Animation(opacity=1, duration=0.5).start(self.ids.loading_box), 1.0)

        # الانتقال للشاشة الرئيسية بعد 3 ثوانٍ
        Clock.schedule_once(self._go_to_main, 3.0)

    def _go_to_main(self, dt):
        """الانتقال بأنيميشن سلس للشاشة الرئيسية"""
        anim_out = Animation(opacity=0, duration=0.5, t='in_quad')
        anim_out.bind(on_complete=lambda *args: self._switch_screen())
        anim_out.start(self)

    def _switch_screen(self):
        self.manager.current = "main"


class MainScreen(MDScreen):
    pass


class CameraCard(MDCard):
    """بطاقة عرض معلومات الكاميرا المكتشفة مع نتيجة الفحص الأمني"""

    def __init__(self, ip, open_ports, rtsp=None, **kwargs):
        super().__init__(**kwargs)

        # IP Header
        header_box = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(45),
            spacing=dp(10)
        )
        ip_label = MDLabel(
            text=f"[b]{ip}[/b]",
            markup=True,
            font_style="H6",
            adaptive_height=True,
            pos_hint={"center_y": 0.5}
        )
        header_box.add_widget(ip_label)
        self.add_widget(header_box)

        # Separator
        self.add_widget(self._make_separator())

        # Ports section
        if open_ports:
            self.add_widget(MDLabel(
                text="Open Ports:",
                font_style="Subtitle2",
                bold=True,
                size_hint_y=None,
                height=dp(28),
                theme_text_color="Custom",
                text_color=get_color_from_hex("#4FC3F7")
            ))
            for port_name in open_ports:
                pb = MDBoxLayout(
                    orientation="horizontal",
                    size_hint_y=None,
                    height=dp(30),
                    spacing=dp(8),
                    padding=[dp(8), 0, 0, 0]
                )
                pb.add_widget(MDLabel(
                    text=port_name,
                    font_style="Body2",
                    adaptive_height=True,
                    pos_hint={"center_y": 0.5},
                    theme_text_color="Secondary"
                ))
                self.add_widget(pb)
        else:
            self.add_widget(MDLabel(
                text="No common camera ports found",
                font_style="Body2",
                size_hint_y=None,
                height=dp(36),
                theme_text_color="Hint"
            ))

        # RTSP Security Section
        if rtsp:
            self.add_widget(self._make_separator())
            is_open = rtsp.get('open', False)
            if is_open:
                self.add_widget(MDLabel(
                    text="Stream: OPEN (Vulnerable!)",
                    font_style="Subtitle2",
                    bold=True,
                    size_hint_y=None,
                    height=dp(30),
                    theme_text_color="Custom",
                    text_color=get_color_from_hex("#EF5350")
                ))
                details = [
                    ("URL:", rtsp.get('url', '')),
                    ("Creds:", rtsp.get('creds', '')),
                    ("Risk:", rtsp.get('risk', '')),
                ]
                for label, value in details:
                    row = MDBoxLayout(
                        orientation="horizontal",
                        size_hint_y=None,
                        height=dp(30),
                        spacing=dp(8),
                        padding=[dp(8), 0, 0, 0]
                    )
                    row.add_widget(MDLabel(
                        text=label,
                        size_hint_x=None,
                        width=dp(60),
                        font_style="Caption",
                        adaptive_height=True,
                        pos_hint={"center_y": 0.5},
                        theme_text_color="Secondary"
                    ))
                    row.add_widget(MDLabel(
                        text=value,
                        font_style="Body2",
                        adaptive_height=True,
                        pos_hint={"center_y": 0.5}
                    ))
                    self.add_widget(row)
            else:
                self.add_widget(MDLabel(
                    text=f"Stream: Secured  {rtsp.get('risk', '')}",
                    font_style="Body2",
                    size_hint_y=None,
                    height=dp(36),
                    theme_text_color="Custom",
                    text_color=get_color_from_hex("#66BB6A")
                ))

    def _make_separator(self):
        """إنشاء خط فاصل"""
        sep = Widget(size_hint_y=None, height=dp(1))
        from kivy.graphics import Color, Rectangle
        with sep.canvas:
            Color(0.3, 0.3, 0.4, 0.5)
            sep._rect = Rectangle(pos=sep.pos, size=sep.size)
        sep.bind(pos=lambda w, p: setattr(w._rect, 'pos', p))
        sep.bind(size=lambda w, s: setattr(w._rect, 'size', s))
        return sep


class CameraScannerApp(MDApp):

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        self.title = "Ms Moo — Camera Scanner"

        try:
            Builder.load_string(KV)
            Logger.info("CameraScanner: KV loaded successfully")
        except Exception as e:
            Logger.error(f"CameraScanner: KV load error: {e}")
            Logger.error(traceback.format_exc())

        sm = MDScreenManager()
        sm.add_widget(SplashScreen(name="splash"))
        sm.add_widget(MainScreen(name="main"))
        sm.current = "splash"
        return sm

    def on_start(self):
        Logger.info("CameraScanner: App started successfully!")

    def start_scan(self):
        screen = self.root.get_screen("main")
        scan_btn = screen.ids.scan_btn
        progress_box = screen.ids.progress_box
        results_box = screen.ids.results_box
        status_label = screen.ids.status_label
        count_label = screen.ids.count_label

        # Clear previous results
        results_box.clear_widgets()
        count_label.text = ""

        # Update UI state
        scan_btn.disabled = True
        scan_btn.text = "Scanning..."
        progress_box.opacity = 1
        status_label.text = "Searching for cameras on the network..."

        # Run scan in background thread
        thread = threading.Thread(target=self._run_scan_thread, daemon=True)
        thread.start()

    def _run_scan_thread(self):
        """يعمل في الخلفية: فحص الشبكة واكتشاف الكاميرات وفحص أمانها"""
        cameras = []

        # Try WSDiscovery
        try:
            from wsdiscovery import WSDiscovery
            Logger.info("CameraScanner: WSDiscovery imported OK")
            wsd = WSDiscovery()
            wsd.start()
            services = wsd.searchServices(timeout=5)
            for service in services:
                try:
                    xaddrs = service.getXAddrs()
                    if xaddrs:
                        ip = xaddrs[0].split('//')[1].split(':')[0]
                        if ip not in [c['ip'] for c in cameras]:
                            cameras.append({'ip': ip})
                except Exception:
                    pass
            wsd.stop()
        except ImportError:
            Logger.warning("CameraScanner: WSDiscovery not available, using fallback")
            cameras = self._fallback_scan()
        except Exception as e:
            Logger.warning(f"CameraScanner: WSDiscovery error: {e}")
            cameras = self._fallback_scan()

        final_cameras = []
        for cam in cameras:
            ip = cam['ip']
            ports = self._scan_ports(ip)
            rtsp = self._check_rtsp(ip) if any(p == 554 for p, _ in ports) else None
            final_cameras.append({'ip': ip, 'ports': [name for _, name in ports], 'rtsp': rtsp})

        Clock.schedule_once(lambda dt: self._on_scan_done(final_cameras))

    def _fallback_scan(self):
        """فحص الشبكة المحلية بدون WSDiscovery"""
        cameras = []
        try:
            local_ip = self._get_local_ip()
            if local_ip:
                subnet = '.'.join(local_ip.split('.')[:3])
                Logger.info(f"CameraScanner: Scanning subnet {subnet}.0/24")

                def check_host(ip):
                    camera_ports = [554, 80, 8080, 8000, 37777]
                    for port in camera_ports:
                        try:
                            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            s.settimeout(0.5)
                            result = s.connect_ex((ip, port))
                            s.close()
                            if result == 0:
                                return True
                        except Exception:
                            pass
                    return False

                threads = []
                results = []
                lock = threading.Lock()

                def scan_host(ip):
                    if check_host(ip):
                        with lock:
                            results.append({'ip': ip})

                for i in range(1, 255):
                    ip = f"{subnet}.{i}"
                    if ip != local_ip:
                        t = threading.Thread(target=scan_host, args=(ip,), daemon=True)
                        threads.append(t)
                        t.start()

                for t in threads:
                    t.join(timeout=3)

                cameras = results
        except Exception as e:
            Logger.error(f"CameraScanner: Fallback scan error: {e}")
        return cameras

    def _get_local_ip(self):
        """الحصول على عنوان IP المحلي"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return None

    def _try_rtsp(self, ip, path='/', user='', password='', timeout=2):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((ip, 554))
            auth = ''
            if user or password:
                cred = base64.b64encode(f'{user}:{password}'.encode()).decode()
                auth = f'Authorization: Basic {cred}\r\n'
            req = f'OPTIONS rtsp://{ip}{path} RTSP/1.0\r\nCSeq: 1\r\n{auth}\r\n'
            s.sendall(req.encode())
            resp = s.recv(512).decode(errors='ignore')
            s.close()
            return 'RTSP/1.0 200' in resp
        except Exception:
            return False

    def _check_rtsp(self, ip):
        for path in RTSP_PATHS:
            if self._try_rtsp(ip, path):
                return {'open': True, 'url': f'rtsp://{ip}{path}', 'creds': 'None', 'risk': 'CRITICAL'}
        for user, password in DEFAULT_CREDS:
            for path in RTSP_PATHS[:4]:
                if self._try_rtsp(ip, path, user, password):
                    return {
                        'open': True,
                        'url': f'rtsp://{user}:{password}@{ip}{path}',
                        'creds': f'{user}:{password}',
                        'risk': 'HIGH'
                    }
        return {'open': False, 'url': None, 'creds': None, 'risk': 'SAFE'}

    def _scan_ports(self, ip):
        """فحص المنافذ الشائعة لكاميرات المراقبة"""
        port_map = {
            554: "554 - RTSP (Video Stream)",
            80: "80 - HTTP (Control Panel)",
            443: "443 - HTTPS",
            8000: "8000 - ONVIF",
            8080: "8080 - HTTP Alt",
            37777: "37777 - Dahua/Hikvision"
        }
        open_ports = []
        for port, name in port_map.items():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1.5)
                result = s.connect_ex((ip, port))
                s.close()
                if result == 0:
                    open_ports.append((port, name))
            except Exception:
                pass
        return open_ports

    def _on_scan_done(self, cameras):
        """تحديث الواجهة بعد انتهاء الفحص"""
        screen = self.root.get_screen("main")
        scan_btn = screen.ids.scan_btn
        progress_box = screen.ids.progress_box
        results_box = screen.ids.results_box
        status_label = screen.ids.status_label
        count_label = screen.ids.count_label

        scan_btn.disabled = False
        scan_btn.text = "Re-Scan"
        progress_box.opacity = 0

        if not cameras:
            status_label.text = "No cameras found on the network"
            count_label.text = ""
            results_box.add_widget(MDLabel(
                text="No cameras discovered.\nMake sure you are connected to the network.",
                halign="center",
                font_style="Body1",
                size_hint_y=None,
                height=dp(100),
                theme_text_color="Hint"
            ))
        else:
            critical = sum(1 for c in cameras if c.get('rtsp') and c['rtsp']['risk'] == 'CRITICAL')
            if critical:
                status_label.text = f"Scan Complete | {critical} camera(s) at critical risk!"
            else:
                status_label.text = "Scan Complete"
            count_label.text = f"Total cameras: {len(cameras)}"
            for cam in cameras:
                card = CameraCard(
                    ip=cam['ip'],
                    open_ports=cam['ports'],
                    rtsp=cam.get('rtsp')
                )
                results_box.add_widget(card)


if __name__ == "__main__":
    CameraScannerApp().run()
