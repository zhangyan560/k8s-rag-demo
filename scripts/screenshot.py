"""用 Playwright 对本地 Streamlit 界面截图。先运行 streamlit run app.py。"""
import sys
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8501"
SHOTS = [("01_configmap_vs_secret.png", "ConfigMap 和 Secret 有什么区别？", None),
         ("02_deployment_rollback.png", "Deployment 如何回滚到之前的版本？", None),
         ("03_pv_reclaim_policy.png", "PersistentVolume 的回收策略有哪些？", None)]

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=sys.argv[1] if len(sys.argv) > 1 else None)
    page = b.new_page(viewport={"width": 1440, "height": 1300}, device_scale_factor=1)
    for fname, q, _ in SHOTS:
        page.goto(URL)
        page.get_by_role("button", name=q).click(timeout=120000)
        page.get_by_text("引用来源").wait_for(timeout=120000)
        page.wait_for_timeout(1500)
        page.screenshot(path=f"screenshots/{fname}", full_page=True)
        print("saved", fname)
    b.close()
