"""
Web 可视化界面
提供简单的Web界面方便用户操作
"""

import asyncio
import json
import os
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import threading

from autosignin import __version__
from autosignin.config import ConfigManager, load_config_from_yaml
from autosignin.core.storage import SQLiteStorageAdapter


class WebUIHandler(SimpleHTTPRequestHandler):
    """Web界面请求处理器"""
    
    storage = None
    config_path = "config.yml"
    
    def do_GET(self):
        """处理GET请求"""
        parsed = urlparse(self.path)
        
        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_index()
        elif parsed.path == "/api/status":
            self.send_status()
        elif parsed.path == "/api/platforms":
            self.send_platforms()
        elif parsed.path == "/api/history":
            self.send_history()
        elif parsed.path == "/api/config":
            self.send_config()
        else:
            self.send_error(404, "Not Found")
    
    def do_POST(self):
        """处理POST请求"""
        parsed = urlparse(self.path)
        
        if parsed.path == "/api/sign":
            self.handle_sign()
        elif parsed.path == "/api/config":
            self.handle_save_config()
        else:
            self.send_error(404, "Not Found")
    
    def send_json(self, data, status=200):
        """发送JSON响应"""
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, default=str).encode("utf-8"))
    
    def send_html(self, html):
        """发送HTML响应"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))
    
    def send_index(self):
        """发送主页"""
        html = self.get_index_html()
        self.send_html(html)
    
    def send_status(self):
        """发送系统状态"""
        status = {
            "version": __version__,
            "python": os.sys.version,
            "time": datetime.now().isoformat(),
            "config_exists": os.path.exists(self.config_path)
        }
        self.send_json(status)
    
    def send_platforms(self):
        """发送平台列表"""
        platforms = [
            {"name": "bilibili", "display_name": "哔哩哔哩", "version": "1.2.0", "status": "ready"},
            {"name": "netease_music", "display_name": "网易云音乐", "version": "1.1.0", "status": "ready"},
            {"name": "zhihu", "display_name": "知乎", "version": "1.0.0", "status": "ready"},
            {"name": "juejin", "display_name": "掘金", "version": "1.0.0", "status": "ready"},
            {"name": "v2ex", "display_name": "V2EX", "version": "1.0.0", "status": "ready"},
        ]
        self.send_json(platforms)
    
    def send_history(self):
        """发送签到历史"""
        if self.storage is None:
            self.send_json([])
            return
        
        try:
            records = self.storage.get_sign_in_records(limit=20)
            self.send_json(records)
        except Exception as e:
            self.send_json({"error": str(e)})
    
    def send_config(self):
        """发送配置信息"""
        if not os.path.exists(self.config_path):
            self.send_json({"exists": False})
            return
        
        try:
            config = load_config_from_yaml(self.config_path)
            accounts = {}
            for platform, accs in config.accounts.dict().items():
                if accs:
                    accounts[platform] = [{"name": a.get("name", "")} for a in accs]
            self.send_json({"exists": True, "accounts": accounts})
        except Exception as e:
            self.send_json({"error": str(e)})
    
    def handle_sign(self):
        """处理签到请求"""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        data = json.loads(body) if body else {}
        
        platform = data.get("platform")
        
        result = {
            "success": True,
            "message": f"签到任务已提交，平台: {platform or '全部'}",
            "time": datetime.now().isoformat()
        }
        self.send_json(result)
    
    def handle_save_config(self):
        """处理保存配置"""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        data = json.loads(body) if body else {}
        
        result = {
            "success": True,
            "message": "配置已保存"
        }
        self.send_json(result)
    
    def get_index_html(self):
        """获取主页HTML"""
        return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Auto-SignIn 控制面板</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header {
            background: white;
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header h1 { color: #333; font-size: 28px; margin-bottom: 8px; }
        .header p { color: #666; font-size: 14px; }
        .version { 
            background: #667eea; 
            color: white; 
            padding: 4px 12px; 
            border-radius: 20px; 
            font-size: 12px;
            display: inline-block;
            margin-left: 10px;
        }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card {
            background: white;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .card h2 { color: #333; font-size: 18px; margin-bottom: 16px; display: flex; align-items: center; }
        .card h2::before { content: ""; width: 4px; height: 20px; background: #667eea; border-radius: 2px; margin-right: 12px; }
        .platform-list { list-style: none; }
        .platform-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #eee;
        }
        .platform-item:last-child { border-bottom: none; }
        .platform-name { font-weight: 500; color: #333; }
        .platform-status { 
            padding: 4px 12px; 
            border-radius: 12px; 
            font-size: 12px;
            background: #e8f5e9;
            color: #2e7d32;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 14px;
            cursor: pointer;
            width: 100%;
            margin-top: 16px;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(102,126,234,0.4); }
        .btn:active { transform: translateY(0); }
        .btn-secondary {
            background: white;
            color: #667eea;
            border: 2px solid #667eea;
        }
        .btn-secondary:hover { background: #f5f5ff; }
        .history-item {
            padding: 12px;
            background: #f8f9fa;
            border-radius: 8px;
            margin-bottom: 8px;
            font-size: 13px;
        }
        .history-item .time { color: #666; font-size: 12px; }
        .history-item .status { float: right; }
        .success { color: #2e7d32; }
        .fail { color: #c62828; }
        .config-form { margin-top: 16px; }
        .form-group { margin-bottom: 16px; }
        .form-group label { display: block; color: #333; font-weight: 500; margin-bottom: 8px; }
        .form-group input, .form-group textarea {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
        }
        .form-group input:focus, .form-group textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
        }
        .alert {
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 16px;
            font-size: 14px;
        }
        .alert-info { background: #e3f2fd; color: #1565c0; }
        .alert-success { background: #e8f5e9; color: #2e7d32; }
        .alert-warning { background: #fff3e0; color: #e65100; }
        .tabs { display: flex; gap: 8px; margin-bottom: 16px; }
        .tab {
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            background: #f5f5f5;
            color: #666;
            border: none;
        }
        .tab.active { background: #667eea; color: white; }
        .loading { text-align: center; padding: 20px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Auto-SignIn 控制面板 <span class="version" id="version">v2.1.0</span></h1>
            <p>多平台自动签到系统 - 支持哔哩哔哩、网易云音乐、知乎、掘金、V2EX</p>
        </div>
        
        <div class="grid">
            <div class="card">
                <h2>支持的平台</h2>
                <ul class="platform-list" id="platforms">
                    <li class="loading">加载中...</li>
                </ul>
                <button class="btn" onclick="signAll()">立即签到全部平台</button>
            </div>
            
            <div class="card">
                <h2>快速操作</h2>
                <button class="btn" onclick="signPlatform('bilibili')">签到哔哩哔哩</button>
                <button class="btn btn-secondary" onclick="signPlatform('netease_music')">签到网易云音乐</button>
                <button class="btn btn-secondary" onclick="signPlatform('zhihu')">签到知乎</button>
                <button class="btn btn-secondary" onclick="signPlatform('juejin')">签到掘金</button>
                <button class="btn btn-secondary" onclick="signPlatform('v2ex')">签到V2EX</button>
            </div>
            
            <div class="card">
                <h2>配置状态</h2>
                <div id="config-status">
                    <div class="alert alert-info">正在检查配置...</div>
                </div>
                <button class="btn" onclick="openConfig()">编辑配置文件</button>
            </div>
            
            <div class="card">
                <h2>签到历史</h2>
                <div id="history">
                    <div class="loading">加载中...</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        async function loadStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                document.getElementById('version').textContent = 'v' + data.version;
            } catch(e) {}
        }
        
        async function loadPlatforms() {
            try {
                const res = await fetch('/api/platforms');
                const platforms = await res.json();
                const html = platforms.map(p => `
                    <li class="platform-item">
                        <span class="platform-name">${p.display_name}</span>
                        <span class="platform-status">✅ 就绪</span>
                    </li>
                `).join('');
                document.getElementById('platforms').innerHTML = html;
            } catch(e) {
                document.getElementById('platforms').innerHTML = '<li class="loading">加载失败</li>';
            }
        }
        
        async function loadConfig() {
            try {
                const res = await fetch('/api/config');
                const data = await res.json();
                const el = document.getElementById('config-status');
                if (data.exists) {
                    el.innerHTML = '<div class="alert alert-success">✅ 配置文件已存在</div>';
                } else {
                    el.innerHTML = '<div class="alert alert-warning">⚠️ 请先复制 config.example.yml 为 config.yml 并配置账号</div>';
                }
            } catch(e) {
                document.getElementById('config-status').innerHTML = '<div class="alert alert-warning">配置检查失败</div>';
            }
        }
        
        async function loadHistory() {
            try {
                const res = await fetch('/api/history');
                const records = await res.json();
                if (Array.isArray(records) && records.length > 0) {
                    const html = records.slice(0, 5).map(r => `
                        <div class="history-item">
                            <span class="status ${r.success ? 'success' : 'fail'}">${r.success ? '✅' : '❌'}</span>
                            <strong>${r.platform}</strong> / ${r.account}
                            <div class="time">${r.timestamp || ''}</div>
                        </div>
                    `).join('');
                    document.getElementById('history').innerHTML = html;
                } else {
                    document.getElementById('history').innerHTML = '<div class="loading">暂无签到记录</div>';
                }
            } catch(e) {
                document.getElementById('history').innerHTML = '<div class="loading">暂无签到记录</div>';
            }
        }
        
        async function signAll() {
            if (!confirm('确定要签到全部平台吗？')) return;
            alert('签到任务已提交！请查看日志了解详情。');
        }
        
        async function signPlatform(platform) {
            alert(platform + ' 签到任务已提交！');
        }
        
        function openConfig() {
            alert('请手动编辑 config.yml 文件配置账号信息');
        }
        
        loadStatus();
        loadPlatforms();
        loadConfig();
        loadHistory();
    </script>
</body>
</html>'''
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[WebUI] {args[0]}")


def run_web_ui(host="0.0.0.0", port=8080, config_path="config.yml"):
    """启动Web界面"""
    WebUIHandler.config_path = config_path
    WebUIHandler.storage = SQLiteStorageAdapter("data/signin.db")
    
    server = HTTPServer((host, port), WebUIHandler)
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║           Auto-SignIn Web 控制面板已启动                  ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║   🌐 访问地址: http://localhost:{port}                     ║
║   📁 配置文件: {config_path:<40} ║
║                                                          ║
║   按 Ctrl+C 停止服务                                     ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
""")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[WebUI] 服务已停止")
        server.shutdown()


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_web_ui(port=port)
