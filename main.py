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
import threading
import socket
import base64
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.progressindicator import MDCircularProgressIndicator
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.snackbar import MDSnackbar
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp

# --- ملف تصميم الواجهة (KV Language) ---
KV = """
<CameraCard>:
    orientation: "vertical"
    padding: dp(16)
    spacing: dp(8)
    size_hint_y: None
    height: self.minimum_height
    md_bg_color: app.theme_cls.surfaceContainerHighColor
    radius: [dp(16)]
    elevation: 2

<MainScreen>:
    name: "main"
    md_bg_color: app.theme_cls.backgroundColor

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
            md_bg_color: app.theme_cls.primaryColor
            radius: [dp(20)]

            MDLabel:
                text: "📷 مكتشف الكاميرات"
                halign: "center"
                font_style: "Title"
                role: "large"
                bold: True
                color: "white"

            MDLabel:
                id: status_label
                text: "اضغط على زر الفحص لاكتشاف كاميرات الشبكة"
                halign: "center"
                font_style: "Body"
                role: "medium"
                color: [1,1,1,0.8]

        # Scan Button & Progress
        MDBoxLayout:
            orientation: "vertical"
            size_hint_y: None
            height: dp(90)
            spacing: dp(10)

            MDRaisedButton:
                id: scan_btn
                text: "🔍  بدء فحص الشبكة"
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

                MDCircularProgressIndicator:
                    size_hint: None, None
                    size: dp(20), dp(20)
                    pos_hint: {"center_y": 0.5}

                MDLabel:
                    text: "جاري الفحص..."
                    font_style: "Body"
                    role: "small"
                    adaptive_height: True
                    pos_hint: {"center_y": 0.5}

        # Results Counter
        MDBoxLayout:
            size_hint_y: None
            height: dp(30)

            MDLabel:
                id: count_label
                text: ""
                halign: "right"
                font_style: "Label"
                role: "medium"
                adaptive_height: True

        # Results Area
        MDScrollView:
            MDBoxLayout:
                id: results_box
                orientation: "vertical"
                spacing: dp(10)
                padding: [0, 0, 0, dp(10)]
                adaptive_height: True
"""


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
        icon_label = MDLabel(
            text="📹",
            size_hint_x=None,
            width=dp(35),
            font_size="24sp"
        )
        ip_label = MDLabel(
            text=f"[b]{ip}[/b]",
            markup=True,
            font_style="Title",
            role="medium",
            adaptive_height=True,
            pos_hint={"center_y": 0.5}
        )
        header_box.add_widget(icon_label)
        header_box.add_widget(ip_label)
        self.add_widget(header_box)

        # Divider
        from kivymd.uix.divider import MDDivider
        self.add_widget(MDDivider())

        # Ports section
        from kivymd.uix.divider import MDDivider

        if open_ports:
            self.add_widget(MDLabel(
                text="🔌 المنافذ المفتوحة:", font_style="Label", role="large", bold=True,
                size_hint_y=None, height=dp(28)))
            for port_name in open_ports:
                pb = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(34),
                                 spacing=dp(8), padding=[dp(8), 0, 0, 0])
                pb.add_widget(MDLabel(text="✅", size_hint_x=None, width=dp(25), font_size="13sp"))
                pb.add_widget(MDLabel(text=port_name, font_style="Body", role="medium",
                                      adaptive_height=True, pos_hint={"center_y": 0.5}))
                self.add_widget(pb)
        else:
            self.add_widget(MDLabel(text="⚠️  لم تُكتشف منافذ كاميرا شائعة",
                                    font_style="Body", role="medium",
                                    size_hint_y=None, height=dp(36)))

        # RTSP Security Section
        if rtsp:
            self.add_widget(MDDivider())
            is_open = rtsp.get('open', False)
            if is_open:
                self.add_widget(MDLabel(
                    text="📹 حالة البث: 🔓 مفتوحة ⚠️", font_style="Label", role="large",
                    bold=True, size_hint_y=None, height=dp(30)))
                for label, value in [
                    ("الرابط:", rtsp.get('url', '')),
                    ("البيانات:", rtsp.get('creds', '')),
                    ("الخطر:", rtsp.get('risk', '')),
                ]:
                    row = MDBoxLayout(orientation="horizontal", size_hint_y=None,
                                      height=dp(34), spacing=dp(8), padding=[dp(8), 0, 0, 0])
                    row.add_widget(MDLabel(text=label, size_hint_x=None, width=dp(70),
                                           font_style="Label", role="medium",
                                           adaptive_height=True, pos_hint={"center_y": 0.5}))
                    row.add_widget(MDLabel(text=value, font_style="Body", role="small",
                                           adaptive_height=True, pos_hint={"center_y": 0.5}))
                    self.add_widget(row)
            else:
                self.add_widget(MDLabel(
                    text=f"📹 البث: ✅ مغلقة ومحمية  {rtsp.get('risk', '')}",
                    font_style="Body", role="medium", size_hint_y=None, height=dp(36)))



class MainScreen(MDScreen):
    pass


class CameraScannerApp(MDApp):

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        self.title = "مكتشف الكاميرات"
        Builder.load_string(KV)
        return MainScreen()

    def start_scan(self):
        screen = self.root
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
        scan_btn.text = "⏳  جاري الفحص..."
        progress_box.opacity = 1
        status_label.text = "جاري البحث عن الكاميرات في الشبكة..."

        # Run scan in background thread to avoid freezing the UI
        thread = threading.Thread(target=self._run_scan_thread, daemon=True)
        thread.start()

    def _run_scan_thread(self):
        """يعمل في الخلفية: فحص الشبكة واكتشاف الكاميرات وفحص أمانها"""
        cameras = []
        try:
            from wsdiscovery import WSDiscovery
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
        except Exception:
            pass

        final_cameras = []
        for cam in cameras:
            ip = cam['ip']
            ports  = self._scan_ports(ip)
            rtsp   = self._check_rtsp(ip) if 554 in [p for p,_ in ports] else None
            final_cameras.append({'ip': ip, 'ports': ports, 'rtsp': rtsp})

        Clock.schedule_once(lambda dt: self._on_scan_done(final_cameras))

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
        except:
            return False

    def _check_rtsp(self, ip):
        # بدون مصادقة
        for path in RTSP_PATHS:
            if self._try_rtsp(ip, path):
                return {'open': True, 'url': f'rtsp://{ip}{path}', 'creds': 'لا يوجد', 'risk': '🔴 حرج'}
        # كلمات مرور افتراضية
        for user, password in DEFAULT_CREDS:
            for path in RTSP_PATHS[:4]:
                if self._try_rtsp(ip, path, user, password):
                    return {'open': True, 'url': f'rtsp://{user}:{password}@{ip}{path}', 'creds': f'{user}:{password}', 'risk': '🟠 عالٍ'}
        return {'open': False, 'url': None, 'creds': None, 'risk': '🟢 آمنة'}

    def _scan_ports(self, ip):
        """فحص المنافذ الشائعة لكاميرات المراقبة"""
        port_map = {
            554: "554 - RTSP (بث الفيديو)",
            80: "80 - HTTP (لوحة التحكم)",
            443: "443 - HTTPS",
            8000: "8000 - ONVIF",
            8080: "8080 - HTTP بديل",
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
                    open_ports.append(name)
            except Exception:
                pass
        return open_ports

    def _on_scan_done(self, cameras):
        """تحديث الواجهة بعد انتهاء الفحص"""
        screen = self.root
        scan_btn      = screen.ids.scan_btn
        progress_box  = screen.ids.progress_box
        results_box   = screen.ids.results_box
        status_label  = screen.ids.status_label
        count_label   = screen.ids.count_label

        scan_btn.disabled = False
        scan_btn.text = "🔍  إعادة الفحص"
        progress_box.opacity = 0

        if not cameras:
            status_label.text = "لم يتم العثور على كاميرات في الشبكة"
            count_label.text = ""
            results_box.add_widget(MDLabel(
                text="😔  لم يتم اكتشاف أي كاميرات.\nتأكد من اتصالك بالشبكة.",
                halign="center", font_style="Body", role="large",
                size_hint_y=None, height=dp(100)
            ))
        else:
            critical = sum(1 for c in cameras if c.get('rtsp') and '🔴' in c['rtsp']['risk'])
            status_label.text = f"تم الفحص ✅  |  {critical} كاميرا في خطر حرج" if critical else "تم الفحص بنجاح ✅"
            count_label.text = f"إجمالي الكاميرات: {len(cameras)}"
            for cam in cameras:
                card = CameraCard(ip=cam['ip'], open_ports=cam['ports'], rtsp=cam.get('rtsp'))
                results_box.add_widget(card)


if __name__ == "__main__":
    CameraScannerApp().run()
