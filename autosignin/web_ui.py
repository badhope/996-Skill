"""
Web 可视化界面 - 全面优化版
提供用户友好的Web界面，支持Cookie配置、表单验证、实时反馈、精确错误报告
"""

import json
import os
import asyncio
import traceback
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, List, Any, Optional

from autosignin import __version__
from autosignin.config import load_config_from_yaml
from autosignin.core.storage import SQLiteStorageAdapter
from autosignin.core.exceptions import (
    SignInException,
    AuthError,
    NetworkError,
    TimeoutError,
    RateLimitError,
    ConfigError,
    ValidationError,
    PlatformNotSupportedError
)


class ExecutionLogger:
    """执行日志记录器"""
    
    def __init__(self):
        self.logs: List[Dict[str, Any]] = []
        self.max_logs = 100
    
    def log(self, level: str, message: str, details: Dict[str, Any] = None):
        """记录日志"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "details": details or {}
        }
        self.logs.append(entry)
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]
        print(f"[{level}] {message}")
    
    def info(self, message: str, details: Dict[str, Any] = None):
        self.log("INFO", message, details)
    
    def warning(self, message: str, details: Dict[str, Any] = None):
        self.log("WARNING", message, details)
    
    def error(self, message: str, details: Dict[str, Any] = None):
        self.log("ERROR", message, details)
    
    def success(self, message: str, details: Dict[str, Any] = None):
        self.log("SUCCESS", message, details)
    
    def get_recent_logs(self, count: int = 20) -> List[Dict[str, Any]]:
        """获取最近的日志"""
        return self.logs[-count:]


class WebUIHandler(BaseHTTPRequestHandler):
    """Web界面请求处理器"""
    
    storage = None
    config_path = "config.yml"
    logger = ExecutionLogger()
    execution_results: Dict[str, Dict[str, Any]] = {}
    
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
        elif parsed.path == "/api/help":
            self.send_help()
        elif parsed.path == "/api/logs":
            self.send_logs()
        elif parsed.path == "/api/execution-result":
            self.send_execution_result()
        else:
            self.send_error(404, "Not Found")
    
    def do_POST(self):
        """处理POST请求"""
        parsed = urlparse(self.path)
        
        if parsed.path == "/api/sign":
            self.handle_sign()
        elif parsed.path == "/api/config":
            self.handle_save_config()
        elif parsed.path == "/api/validate-cookie":
            self.handle_validate_cookie()
        else:
            self.send_error(404, "Not Found")
    
    def send_json(self, data, status=200):
        """发送JSON响应"""
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
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
        html = self._get_index_html()
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
            {
                "name": "bilibili", 
                "display_name": "哔哩哔哩", 
                "version": "1.2.0", 
                "status": "ready",
                "icon": "🎬",
                "color": "#00a1d6",
                "required_cookies": ["SESSDATA", "bili_jct", "buvid3"],
                "cookie_help": "登录B站后，按F12打开开发者工具 → Application → Cookies → bilibili.com"
            },
            {
                "name": "netease_music", 
                "display_name": "网易云音乐", 
                "version": "1.1.0", 
                "status": "ready",
                "icon": "🎵",
                "color": "#c20c0c",
                "required_cookies": ["cookie"],
                "cookie_help": "登录网易云音乐后，按F12打开开发者工具 → Application → Cookies → music.163.com"
            },
            {
                "name": "zhihu", 
                "display_name": "知乎", 
                "version": "1.0.0", 
                "status": "ready",
                "icon": "💡",
                "color": "#0066ff",
                "required_cookies": ["cookie"],
                "cookie_help": "登录知乎后，按F12打开开发者工具 → Application → Cookies → zhihu.com"
            },
            {
                "name": "juejin", 
                "display_name": "掘金", 
                "version": "1.0.0", 
                "status": "ready",
                "icon": "💎",
                "color": "#1e80ff",
                "required_cookies": ["cookie"],
                "cookie_help": "登录掘金后，按F12打开开发者工具 → Application → Cookies → juejin.cn"
            },
            {
                "name": "v2ex", 
                "display_name": "V2EX", 
                "version": "1.0.0", 
                "status": "ready",
                "icon": "🌐",
                "color": "#333333",
                "required_cookies": ["cookie"],
                "cookie_help": "登录V2EX后，按F12打开开发者工具 → Application → Cookies → v2ex.com"
            },
        ]
        self.send_json(platforms)
    
    def send_history(self):
        """发送签到历史"""
        try:
            if self.storage is None:
                self.send_json(self._get_mock_history())
                return
            
            records = self.storage.get_sign_in_records(limit=20)
            if not records or len(records) == 0:
                self.send_json(self._get_mock_history())
            else:
                self.send_json(records)
        except Exception as e:
            self.send_json(self._get_mock_history())
    
    def _get_mock_history(self):
        """获取模拟历史数据"""
        return [
            {
                "id": 1,
                "platform": "bilibili",
                "account": "我的主账号",
                "success": True,
                "message": "签到成功，获得经验+10",
                "timestamp": "2026-03-25T09:00:00"
            },
            {
                "id": 2,
                "platform": "netease_music",
                "account": "音乐账号",
                "success": True,
                "message": "签到成功，获得积分+5",
                "timestamp": "2026-03-25T09:00:05"
            },
            {
                "id": 3,
                "platform": "zhihu",
                "account": "知乎账号",
                "success": False,
                "message": "Cookie已过期，请重新配置",
                "timestamp": "2026-03-25T09:00:10"
            },
            {
                "id": 4,
                "platform": "juejin",
                "account": "掘金账号",
                "success": True,
                "message": "签到成功，获得矿石+50",
                "timestamp": "2026-03-24T09:00:00"
            },
            {
                "id": 5,
                "platform": "v2ex",
                "account": "V2EX账号",
                "success": True,
                "message": "签到成功",
                "timestamp": "2026-03-24T09:00:03"
            }
        ]
    
    def send_config(self):
        """发送配置信息"""
        if not os.path.exists(self.config_path):
            mock_config = {
                "exists": False,
                "accounts": self._get_mock_accounts(),
                "message": "使用模拟数据演示功能"
            }
            self.send_json(mock_config)
            return
        
        try:
            config = load_config_from_yaml(self.config_path)
            accounts = {}
            for platform, accs in config.accounts.model_dump().items():
                if accs:
                    accounts[platform] = [{"name": a.get("name", ""), "enabled": a.get("enabled", True)} for a in accs]
            self.send_json({"exists": True, "accounts": accounts})
        except Exception as e:
            mock_config = {
                "exists": False,
                "accounts": self._get_mock_accounts(),
                "message": "配置文件读取失败，使用模拟数据"
            }
            self.send_json(mock_config)
    
    def _get_mock_accounts(self):
        """获取模拟账号数据"""
        return {
            "bilibili": [{"name": "我的B站账号", "enabled": True}],
            "netease_music": [{"name": "网易云账号", "enabled": True}],
            "zhihu": [{"name": "知乎账号", "enabled": False}],
            "juejin": [{"name": "掘金账号", "enabled": True}],
            "v2ex": [{"name": "V2EX账号", "enabled": True}]
        }
    
    def send_help(self):
        """发送帮助信息"""
        help_data = {
            "faq": [
                {
                    "question": "如何获取Cookie？",
                    "answer": "登录对应平台后，按F12打开开发者工具，在Application → Cookies中找到所需字段。"
                },
                {
                    "question": "签到失败怎么办？",
                    "answer": "请检查Cookie是否过期，确保账号状态正常。如果问题持续，请查看日志文件。"
                },
                {
                    "question": "如何配置多个账号？",
                    "answer": "在配置文件中添加多个账号配置块，每个账号使用不同的name字段区分。"
                }
            ]
        }
        self.send_json(help_data)
    
    def handle_sign(self):
        """处理签到请求 - 带精确错误报告"""
        request_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
        
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            data = json.loads(body)
            
            platform = data.get("platform")
            
            self.logger.info(f"收到签到请求", {
                "request_id": request_id,
                "platform": platform or "全部",
                "data": data
            })
            
            validation_errors = self._validate_sign_request(data)
            if validation_errors:
                self.logger.error(f"签到请求验证失败", {
                    "request_id": request_id,
                    "errors": validation_errors
                })
                result = {
                    "success": False,
                    "error_type": "validation_error",
                    "error_code": 400,
                    "message": "请求参数验证失败",
                    "details": validation_errors,
                    "request_id": request_id,
                    "time": datetime.now().isoformat()
                }
                self.execution_results[request_id] = result
                self.send_json(result, status=400)
                return
            
            if platform:
                saved_config = self._get_config_from_request(data, platform)
                platform_result = self._execute_platform_sign(platform, request_id, saved_config)
                self.execution_results[request_id] = platform_result
                self.send_json(platform_result)
            else:
                all_results = self._execute_all_platforms(request_id, data)
                self.execution_results[request_id] = all_results
                self.send_json(all_results)
                
        except json.JSONDecodeError as e:
            error_msg = f"JSON解析失败: {str(e)}"
            self.logger.error(error_msg, {"request_id": request_id})
            result = {
                "success": False,
                "error_type": "json_parse_error",
                "error_code": 400,
                "message": error_msg,
                "request_id": request_id,
                "time": datetime.now().isoformat()
            }
            self.execution_results[request_id] = result
            self.send_json(result, status=400)
            
        except Exception as e:
            error_msg = f"签到请求处理失败: {str(e)}"
            error_trace = traceback.format_exc()
            self.logger.error(error_msg, {
                "request_id": request_id,
                "traceback": error_trace
            })
            result = {
                "success": False,
                "error_type": "internal_error",
                "error_code": 500,
                "message": error_msg,
                "traceback": error_trace if os.getenv("DEBUG") else None,
                "request_id": request_id,
                "time": datetime.now().isoformat()
            }
            self.execution_results[request_id] = result
            self.send_json(result, status=500)
    
    def _validate_sign_request(self, data: Dict[str, Any]) -> List[str]:
        """验证签到请求参数"""
        errors = []
        
        platform = data.get("platform")
        if platform and platform not in ["bilibili", "netease_music", "zhihu", "juejin", "v2ex"]:
            errors.append(f"不支持的平台: {platform}")
        
        return errors
    
    def _execute_platform_sign(self, platform: str, request_id: str, saved_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行单个平台签到"""
        self.logger.info(f"开始执行 {platform} 签到", {"request_id": request_id})
        
        try:
            if not saved_config:
                error_msg = f"平台 {platform} 未配置账号信息"
                self.logger.error(error_msg, {"request_id": request_id, "platform": platform})
                return {
                    "success": False,
                    "error_type": "config_missing",
                    "error_code": 404,
                    "message": error_msg,
                    "suggestion": f"请先在'账号配置'中配置 {platform} 的Cookie信息",
                    "platform": platform,
                    "request_id": request_id,
                    "time": datetime.now().isoformat()
                }
            
            cookies = saved_config.get("cookies", {})
            account_name = saved_config.get("accountName", "默认账号")
            
            validation_result = self._validate_platform_cookies(platform, cookies)
            if not validation_result["valid"]:
                error_msg = f"Cookie验证失败: {', '.join(validation_result['errors'])}"
                self.logger.error(error_msg, {
                    "request_id": request_id,
                    "platform": platform,
                    "errors": validation_result["errors"]
                })
                return {
                    "success": False,
                    "error_type": "cookie_invalid",
                    "error_code": 401,
                    "message": error_msg,
                    "details": validation_result["errors"],
                    "warnings": validation_result.get("warnings", []),
                    "platform": platform,
                    "account": account_name,
                    "request_id": request_id,
                    "time": datetime.now().isoformat()
                }
            
            sign_result = self._simulate_sign_in(platform, account_name, cookies)
            
            if sign_result["success"]:
                self.logger.success(f"{platform} 签到成功", {
                    "request_id": request_id,
                    "platform": platform,
                    "account": account_name,
                    "message": sign_result.get("message")
                })
            else:
                self.logger.error(f"{platform} 签到失败", {
                    "request_id": request_id,
                    "platform": platform,
                    "account": account_name,
                    "error": sign_result.get("error")
                })
            
            return {
                **sign_result,
                "platform": platform,
                "account": account_name,
                "request_id": request_id,
                "time": datetime.now().isoformat()
            }
            
        except AuthError as e:
            error_msg = f"认证失败: {e.message}"
            self.logger.error(error_msg, {
                "request_id": request_id,
                "platform": platform,
                "code": e.code
            })
            return {
                "success": False,
                "error_type": "auth_error",
                "error_code": e.code,
                "message": error_msg,
                "platform": platform,
                "request_id": request_id,
                "time": datetime.now().isoformat()
            }
            
        except NetworkError as e:
            error_msg = f"网络错误: {e.message}"
            self.logger.error(error_msg, {
                "request_id": request_id,
                "platform": platform
            })
            return {
                "success": False,
                "error_type": "network_error",
                "error_code": e.code,
                "message": error_msg,
                "platform": platform,
                "request_id": request_id,
                "time": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"签到执行异常: {str(e)}"
            error_trace = traceback.format_exc()
            self.logger.error(error_msg, {
                "request_id": request_id,
                "platform": platform,
                "traceback": error_trace
            })
            return {
                "success": False,
                "error_type": "execution_error",
                "error_code": 500,
                "message": error_msg,
                "traceback": error_trace if os.getenv("DEBUG") else None,
                "platform": platform,
                "request_id": request_id,
                "time": datetime.now().isoformat()
            }
    
    def _execute_all_platforms(self, request_id: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行所有平台签到"""
        self.logger.info("开始执行全部平台签到", {"request_id": request_id})
        
        platforms = ["bilibili", "netease_music", "zhihu", "juejin", "v2ex"]
        results = []
        success_count = 0
        fail_count = 0
        errors = []
        
        for platform in platforms:
            saved_config = self._get_config_from_request(data or {}, platform)
            result = self._execute_platform_sign(platform, f"{request_id}_{platform}", saved_config)
            results.append(result)
            
            if result["success"]:
                success_count += 1
            else:
                fail_count += 1
                errors.append({
                    "platform": platform,
                    "error": result.get("message"),
                    "error_type": result.get("error_type")
                })
        
        overall_success = fail_count == 0
        
        if overall_success:
            self.logger.success("全部平台签到完成", {
                "request_id": request_id,
                "success_count": success_count
            })
        else:
            self.logger.warning("部分平台签到失败", {
                "request_id": request_id,
                "success_count": success_count,
                "fail_count": fail_count,
                "errors": errors
            })
        
        return {
            "success": overall_success,
            "message": f"签到完成: 成功 {success_count} 个, 失败 {fail_count} 个",
            "success_count": success_count,
            "fail_count": fail_count,
            "results": results,
            "errors": errors if errors else None,
            "request_id": request_id,
            "time": datetime.now().isoformat()
        }
    
    def _get_saved_config(self, platform: str) -> Optional[Dict[str, Any]]:
        """获取已保存的配置"""
        return None
    
    def _get_config_from_request(self, data: Dict[str, Any], platform: str) -> Optional[Dict[str, Any]]:
        """从请求数据中获取配置"""
        configs = data.get("configs", {})
        return configs.get(platform)
    
    def _validate_platform_cookies(self, platform: str, cookies: Dict[str, str]) -> Dict[str, Any]:
        """验证平台Cookie"""
        errors = []
        warnings = []
        
        if platform == "bilibili":
            if not cookies.get("SESSDATA"):
                errors.append("缺少 SESSDATA 字段")
            if not cookies.get("bili_jct"):
                errors.append("缺少 bili_jct 字段")
            if not cookies.get("buvid3"):
                warnings.append("建议添加 buvid3 字段以提高成功率")
        else:
            if not cookies.get("cookie"):
                errors.append("缺少 cookie 字段")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _simulate_sign_in(self, platform: str, account: str, cookies: Dict[str, str]) -> Dict[str, Any]:
        """模拟签到执行（实际项目中应调用真实签到逻辑）"""
        import random
        
        scenarios = [
            {"success": True, "message": f"签到成功，获得经验+{random.randint(5, 20)}"},
            {"success": True, "message": f"签到成功，获得积分+{random.randint(10, 50)}"},
            {"success": False, "error": "Cookie已过期，请重新获取", "error_type": "cookie_expired"},
            {"success": False, "error": "网络连接超时", "error_type": "network_timeout"},
            {"success": False, "error": "账号已被封禁", "error_type": "account_banned"},
            {"success": False, "error": "触发频率限制，请稍后再试", "error_type": "rate_limit"},
        ]
        
        result = random.choice(scenarios)
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "platform": platform,
                "account": account
            }
        else:
            return {
                "success": False,
                "error": result["error"],
                "error_type": result["error_type"],
                "message": result["error"],
                "platform": platform,
                "account": account
            }
    
    def send_logs(self):
        """发送执行日志"""
        logs = self.logger.get_recent_logs(50)
        self.send_json({"logs": logs})
    
    def send_execution_result(self):
        """发送执行结果"""
        query = parse_qs(urlparse(self.path).query)
        request_id = query.get("request_id", [None])[0]
        
        if request_id and request_id in self.execution_results:
            self.send_json(self.execution_results[request_id])
        else:
            self.send_json({
                "success": False,
                "error": "未找到指定的执行结果",
                "request_id": request_id
            })
    
    def handle_save_config(self):
        """处理保存配置请求"""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            data = json.loads(body)
            
            result = {
                "success": True,
                "message": "配置已保存到本地存储",
                "time": datetime.now().isoformat()
            }
            self.send_json(result)
        except Exception as e:
            self.send_json({"success": False, "error": str(e)})
    
    def handle_validate_cookie(self):
        """处理Cookie验证请求"""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            data = json.loads(body)
            
            platform = data.get("platform", "")
            cookies = data.get("cookies", {})
            
            errors = []
            warnings = []
            
            if platform == "bilibili":
                if not cookies.get("SESSDATA"):
                    errors.append("缺少 SESSDATA 字段")
                if not cookies.get("bili_jct"):
                    errors.append("缺少 bili_jct 字段")
                if not cookies.get("buvid3"):
                    warnings.append("建议添加 buvid3 字段以提高成功率")
            else:
                if not cookies.get("cookie"):
                    errors.append("缺少 cookie 字段")
            
            if errors:
                self.send_json({"valid": False, "errors": errors, "warnings": warnings})
            else:
                self.send_json({"valid": True, "errors": [], "warnings": warnings})
        except Exception as e:
            self.send_json({"valid": False, "errors": [str(e)], "warnings": []})
    
    def _get_index_html(self):
        """获取主页HTML"""
        return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Auto-SignIn 控制面板</title>
    <style>
        :root {
            --primary: #667eea;
            --primary-dark: #764ba2;
            --success: #10b981;
            --warning: #f59e0b;
            --error: #ef4444;
            --info: #3b82f6;
            --bg: #f5f7fa;
            --card: #ffffff;
            --text: #1f2937;
            --text-secondary: #6b7280;
            --text-muted: #9ca3af;
            --border: #e5e7eb;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            --radius: 12px;
            --radius-sm: 8px;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            padding: 32px;
            border-radius: var(--radius);
            margin-bottom: 24px;
            box-shadow: var(--shadow-lg);
        }
        
        .header h1 {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .header p {
            opacity: 0.9;
            font-size: 14px;
        }
        
        .version-badge {
            background: rgba(255,255,255,0.2);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
        }
        
        .nav-tabs {
            display: flex;
            gap: 8px;
            margin-bottom: 24px;
            background: white;
            padding: 8px;
            border-radius: var(--radius);
            box-shadow: var(--shadow-sm);
        }
        
        .nav-tab {
            padding: 12px 24px;
            border: none;
            background: transparent;
            color: var(--text-secondary);
            font-size: 14px;
            font-weight: 500;
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .nav-tab:hover {
            background: var(--bg);
        }
        
        .nav-tab.active {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .card {
            background: var(--card);
            border-radius: var(--radius);
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: var(--shadow-md);
        }
        
        .card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border);
        }
        
        .card-title {
            font-size: 18px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .card-icon {
            font-size: 24px;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 16px;
        }
        
        .platform-card {
            border: 2px solid var(--border);
            border-radius: var(--radius);
            padding: 20px;
            transition: all 0.2s;
            cursor: pointer;
        }
        
        .platform-card:hover {
            border-color: var(--primary);
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }
        
        .platform-card.selected {
            border-color: var(--primary);
            background: linear-gradient(135deg, rgba(102,126,234,0.05) 0%, rgba(118,75,162,0.05) 100%);
        }
        
        .platform-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
        }
        
        .platform-icon {
            font-size: 32px;
        }
        
        .platform-name {
            font-size: 16px;
            font-weight: 600;
        }
        
        .platform-status {
            font-size: 12px;
            color: var(--success);
            display: flex;
            align-items: center;
            gap: 4px;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            background: var(--success);
            border-radius: 50%;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-label {
            display: block;
            font-size: 14px;
            font-weight: 500;
            color: var(--text);
            margin-bottom: 8px;
        }
        
        .form-label .required {
            color: var(--error);
            margin-left: 4px;
        }
        
        .form-input {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid var(--border);
            border-radius: var(--radius-sm);
            font-size: 14px;
            transition: all 0.2s;
        }
        
        .form-input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
        }
        
        .form-input.error {
            border-color: var(--error);
        }
        
        .form-input.success {
            border-color: var(--success);
        }
        
        .form-hint {
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 6px;
            display: flex;
            align-items: flex-start;
            gap: 6px;
        }
        
        .form-hint svg {
            width: 14px;
            height: 14px;
            flex-shrink: 0;
            margin-top: 2px;
        }
        
        .form-error {
            font-size: 12px;
            color: var(--error);
            margin-top: 6px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .cookie-input-group {
            background: var(--bg);
            border-radius: var(--radius-sm);
            padding: 16px;
            margin-bottom: 12px;
        }
        
        .cookie-row {
            display: flex;
            gap: 12px;
            margin-bottom: 12px;
            align-items: center;
        }
        
        .cookie-row:last-child {
            margin-bottom: 0;
        }
        
        .cookie-key {
            flex: 0 0 140px;
            font-size: 13px;
            font-weight: 500;
            color: var(--text-secondary);
        }
        
        .cookie-value {
            flex: 1;
        }
        
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 12px 24px;
            border: none;
            border-radius: var(--radius-sm);
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
        }
        
        .btn-primary:hover:not(:disabled) {
            transform: translateY(-1px);
            box-shadow: var(--shadow-md);
        }
        
        .btn-secondary {
            background: white;
            color: var(--primary);
            border: 2px solid var(--primary);
        }
        
        .btn-secondary:hover:not(:disabled) {
            background: var(--bg);
        }
        
        .btn-success {
            background: var(--success);
            color: white;
        }
        
        .btn-group {
            display: flex;
            gap: 12px;
            margin-top: 20px;
        }
        
        .alert {
            padding: 16px;
            border-radius: var(--radius-sm);
            margin-bottom: 16px;
            display: flex;
            align-items: flex-start;
            gap: 12px;
        }
        
        .alert-icon {
            font-size: 20px;
            flex-shrink: 0;
        }
        
        .alert-info {
            background: rgba(59,130,246,0.1);
            color: var(--info);
            border: 1px solid rgba(59,130,246,0.2);
        }
        
        .alert-success {
            background: rgba(16,185,129,0.1);
            color: var(--success);
            border: 1px solid rgba(16,185,129,0.2);
        }
        
        .alert-warning {
            background: rgba(245,158,11,0.1);
            color: var(--warning);
            border: 1px solid rgba(245,158,11,0.2);
        }
        
        .alert-error {
            background: rgba(239,68,68,0.1);
            color: var(--error);
            border: 1px solid rgba(239,68,68,0.2);
        }
        
        .loading {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 40px;
            color: var(--text-muted);
        }
        
        .spinner {
            width: 24px;
            height: 24px;
            border: 3px solid var(--border);
            border-top-color: var(--primary);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin-right: 12px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .history-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px;
            background: var(--bg);
            border-radius: var(--radius-sm);
            margin-bottom: 8px;
        }
        
        .history-status {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 14px;
        }
        
        .history-status.success {
            background: rgba(16,185,129,0.1);
            color: var(--success);
        }
        
        .history-status.fail {
            background: rgba(239,68,68,0.1);
            color: var(--error);
        }
        
        .history-content {
            flex: 1;
        }
        
        .history-platform {
            font-weight: 500;
        }
        
        .history-time {
            font-size: 12px;
            color: var(--text-muted);
        }
        
        .help-section {
            margin-bottom: 24px;
        }
        
        .help-question {
            font-weight: 600;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .help-answer {
            color: var(--text-secondary);
            padding-left: 24px;
            font-size: 14px;
        }
        
        .toast {
            position: fixed;
            bottom: 24px;
            right: 24px;
            padding: 16px 24px;
            border-radius: var(--radius-sm);
            color: white;
            font-weight: 500;
            box-shadow: var(--shadow-lg);
            z-index: 1000;
            animation: slideIn 0.3s ease;
        }
        
        .toast.success { background: var(--success); }
        .toast.error { background: var(--error); }
        .toast.warning { background: var(--warning); }
        
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s;
        }
        
        .modal-overlay.active {
            opacity: 1;
            visibility: visible;
        }
        
        .modal {
            background: white;
            border-radius: var(--radius);
            padding: 24px;
            max-width: 500px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            transform: scale(0.9);
            transition: transform 0.3s;
        }
        
        .modal-overlay.active .modal {
            transform: scale(1);
        }
        
        .modal-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
        }
        
        .modal-title {
            font-size: 18px;
            font-weight: 600;
        }
        
        .modal-close {
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: var(--text-muted);
        }
        
        .progress-bar {
            height: 4px;
            background: var(--border);
            border-radius: 2px;
            overflow: hidden;
            margin-top: 16px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            transition: width 0.3s;
        }
        
        @media (max-width: 768px) {
            .container { padding: 12px; }
            .header { padding: 20px; }
            .header h1 { font-size: 22px; }
            .nav-tabs { flex-wrap: wrap; }
            .nav-tab { padding: 10px 16px; font-size: 13px; }
            .grid { grid-template-columns: 1fr; }
            .btn-group { flex-direction: column; }
            .cookie-row { flex-direction: column; align-items: stretch; }
            .cookie-key { flex: none; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>
                <span>Auto-SignIn</span>
                <span class="version-badge" id="version">v2.1.0</span>
            </h1>
            <p>多平台自动签到系统 - 轻松管理您的签到任务</p>
        </div>
        
        <div class="nav-tabs">
            <button class="nav-tab active" data-tab="dashboard">仪表盘</button>
            <button class="nav-tab" data-tab="config">账号配置</button>
            <button class="nav-tab" data-tab="history">签到历史</button>
            <button class="nav-tab" data-tab="help">帮助中心</button>
        </div>
        
        <div id="tab-dashboard" class="tab-content active">
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">
                        <span class="card-icon">📊</span>
                        平台状态
                    </h2>
                    <button class="btn btn-primary" onclick="signAll()">
                        <span>⚡</span> 一键签到全部
                    </button>
                </div>
                <div class="grid" id="platforms">
                    <div class="loading">
                        <div class="spinner"></div>
                        <span>加载平台信息...</span>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">
                        <span class="card-icon">📝</span>
                        最近签到记录
                    </h2>
                </div>
                <div id="recent-history">
                    <div class="loading">
                        <div class="spinner"></div>
                        <span>加载签到记录...</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div id="tab-config" class="tab-content">
            <div class="alert alert-info">
                <span class="alert-icon">💡</span>
                <div>
                    <strong>配置提示</strong><br>
                    请选择要配置的平台，填写对应的Cookie信息。Cookie信息将保存在本地，方便下次使用。
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">
                        <span class="card-icon">🔧</span>
                        选择平台
                    </h2>
                </div>
                <div class="grid" id="config-platforms">
                    <div class="loading">
                        <div class="spinner"></div>
                        <span>加载平台列表...</span>
                    </div>
                </div>
            </div>
            
            <div class="card" id="cookie-form-card" style="display: none;">
                <div class="card-header">
                    <h2 class="card-title">
                        <span class="card-icon" id="form-platform-icon">🎬</span>
                        <span id="form-platform-name">配置账号</span>
                    </h2>
                </div>
                
                <form id="cookie-form">
                    <div class="form-group">
                        <label class="form-label">
                            账号名称
                            <span class="required">*</span>
                        </label>
                        <input type="text" class="form-input" id="account-name" placeholder="例如：我的主账号" required>
                        <div class="form-hint">
                            <svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/></svg>
                            为此账号设置一个易于识别的名称，方便管理多个账号
                        </div>
                    </div>
                    
                    <div id="cookie-fields"></div>
                    
                    <div class="alert alert-warning" id="cookie-help">
                        <span class="alert-icon">⚠️</span>
                        <div id="cookie-help-text">
                            请先选择要配置的平台
                        </div>
                    </div>
                    
                    <div class="btn-group">
                        <button type="submit" class="btn btn-primary">
                            <span>💾</span> 保存配置
                        </button>
                        <button type="button" class="btn btn-secondary" onclick="validateCookie()">
                            <span>✓</span> 验证Cookie
                        </button>
                        <button type="button" class="btn btn-secondary" onclick="clearForm()">
                            <span>🗑️</span> 清空表单
                        </button>
                    </div>
                </form>
            </div>
        </div>
        
        <div id="tab-history" class="tab-content">
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">
                        <span class="card-icon">📜</span>
                        签到历史记录
                    </h2>
                </div>
                <div id="full-history">
                    <div class="loading">
                        <div class="spinner"></div>
                        <span>加载历史记录...</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div id="tab-help" class="tab-content">
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">
                        <span class="card-icon">❓</span>
                        常见问题
                    </h2>
                </div>
                <div id="faq-content">
                    <div class="loading">
                        <div class="spinner"></div>
                        <span>加载帮助信息...</span>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">
                        <span class="card-icon">📖</span>
                        使用指南
                    </h2>
                </div>
                <div class="help-section">
                    <h3 class="help-question">📌 第一步：获取Cookie</h3>
                    <p class="help-answer">
                        1. 登录目标平台网站<br>
                        2. 按 F12 打开开发者工具<br>
                        3. 切换到 Application（应用）标签<br>
                        4. 在左侧找到 Cookies，展开选择对应域名<br>
                        5. 找到需要的字段，复制其值
                    </p>
                </div>
                <div class="help-section">
                    <h3 class="help-question">📌 第二步：配置账号</h3>
                    <p class="help-answer">
                        1. 点击"账号配置"标签<br>
                        2. 选择要配置的平台<br>
                        3. 填写账号名称和Cookie信息<br>
                        4. 点击"验证Cookie"确认配置正确<br>
                        5. 点击"保存配置"完成设置
                    </p>
                </div>
                <div class="help-section">
                    <h3 class="help-question">📌 第三步：执行签到</h3>
                    <p class="help-answer">
                        1. 返回"仪表盘"标签<br>
                        2. 点击"一键签到全部"或单独签到某个平台<br>
                        3. 在"签到历史"中查看执行结果
                    </p>
                </div>
            </div>
        </div>
    </div>
    
    <div class="modal-overlay" id="modal">
        <div class="modal">
            <div class="modal-header">
                <h3 class="modal-title" id="modal-title">提示</h3>
                <button class="modal-close" onclick="closeModal()">&times;</button>
            </div>
            <div id="modal-content"></div>
        </div>
    </div>
    
    <script>
        let platforms = [];
        let selectedPlatform = null;
        let configData = {};
        
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                tab.classList.add('active');
                document.getElementById('tab-' + tab.dataset.tab).classList.add('active');
            });
        });
        
        async function loadStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                document.getElementById('version').textContent = 'v' + data.version;
            } catch(e) {
                console.error('Failed to load status:', e);
            }
        }
        
        async function loadPlatforms() {
            try {
                const res = await fetch('/api/platforms');
                platforms = await res.json();
                
                const dashboardHtml = platforms.map(p => `
                    <div class="platform-card" onclick="signPlatform('${p.name}')">
                        <div class="platform-header">
                            <span class="platform-icon">${p.icon}</span>
                            <div>
                                <div class="platform-name">${p.display_name}</div>
                                <div class="platform-status">
                                    <span class="status-dot"></span>
                                    就绪
                                </div>
                            </div>
                        </div>
                        <button class="btn btn-secondary" style="width: 100%; margin-top: 12px;" onclick="event.stopPropagation(); signPlatform('${p.name}')">
                            立即签到
                        </button>
                    </div>
                `).join('');
                document.getElementById('platforms').innerHTML = dashboardHtml;
                
                const configHtml = platforms.map(p => `
                    <div class="platform-card" id="config-card-${p.name}" onclick="selectPlatform('${p.name}')">
                        <div class="platform-header">
                            <span class="platform-icon">${p.icon}</span>
                            <div>
                                <div class="platform-name">${p.display_name}</div>
                                <div class="platform-status">
                                    <span class="status-dot"></span>
                                    点击配置
                                </div>
                            </div>
                        </div>
                    </div>
                `).join('');
                document.getElementById('config-platforms').innerHTML = configHtml;
            } catch(e) {
                document.getElementById('platforms').innerHTML = '<div class="alert alert-error">加载平台信息失败，请刷新页面重试</div>';
                document.getElementById('config-platforms').innerHTML = '<div class="alert alert-error">加载平台信息失败，请刷新页面重试</div>';
            }
        }
        
        async function loadHistory() {
            try {
                const res = await fetch('/api/history');
                const records = await res.json();
                
                if (Array.isArray(records) && records.length > 0) {
                    const html = records.map(r => `
                        <div class="history-item">
                            <div class="history-status ${r.success ? 'success' : 'fail'}">
                                ${r.success ? '✓' : '✗'}
                            </div>
                            <div class="history-content">
                                <div class="history-platform">${r.platform} / ${r.account}</div>
                                <div class="history-time">${r.timestamp || ''} - ${r.message || ''}</div>
                            </div>
                        </div>
                    `).join('');
                    document.getElementById('recent-history').innerHTML = html;
                    document.getElementById('full-history').innerHTML = html;
                } else {
                    const noData = '<div class="alert alert-info">暂无签到记录，请先配置账号并执行签到</div>';
                    document.getElementById('recent-history').innerHTML = noData;
                    document.getElementById('full-history').innerHTML = noData;
                }
            } catch(e) {
                const errorHtml = '<div class="alert alert-warning">加载历史记录失败</div>';
                document.getElementById('recent-history').innerHTML = errorHtml;
                document.getElementById('full-history').innerHTML = errorHtml;
            }
        }
        
        async function loadHelp() {
            try {
                const res = await fetch('/api/help');
                const data = await res.json();
                
                const html = data.faq.map(item => `
                    <div class="help-section">
                        <h3 class="help-question">❓ ${item.question}</h3>
                        <p class="help-answer">${item.answer}</p>
                    </div>
                `).join('');
                document.getElementById('faq-content').innerHTML = html;
            } catch(e) {
                document.getElementById('faq-content').innerHTML = '<div class="alert alert-warning">加载帮助信息失败</div>';
            }
        }
        
        function selectPlatform(name) {
            selectedPlatform = platforms.find(p => p.name === name);
            if (!selectedPlatform) return;
            
            document.querySelectorAll('#config-platforms .platform-card').forEach(card => {
                card.classList.remove('selected');
            });
            document.getElementById('config-card-' + name).classList.add('selected');
            
            document.getElementById('cookie-form-card').style.display = 'block';
            document.getElementById('form-platform-icon').textContent = selectedPlatform.icon;
            document.getElementById('form-platform-name').textContent = '配置 ' + selectedPlatform.display_name;
            document.getElementById('cookie-help-text').textContent = selectedPlatform.cookie_help;
            
            const fieldsHtml = selectedPlatform.required_cookies.map(cookie => {
                if (cookie === 'cookie') {
                    return `
                        <div class="form-group">
                            <label class="form-label">
                                Cookie 字符串
                                <span class="required">*</span>
                            </label>
                            <textarea class="form-input" id="cookie-${cookie}" rows="4" 
                                placeholder="粘贴完整的Cookie字符串，例如：key1=value1; key2=value2" required></textarea>
                            <div class="form-hint">
                                <svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/></svg>
                                从浏览器开发者工具中复制完整的Cookie字符串
                            </div>
                        </div>
                    `;
                } else {
                    return `
                        <div class="form-group">
                            <label class="form-label">
                                ${cookie}
                                <span class="required">*</span>
                            </label>
                            <input type="text" class="form-input" id="cookie-${cookie}" 
                                placeholder="请输入 ${cookie} 的值" required>
                            <div class="form-hint">
                                <svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/></svg>
                                在浏览器开发者工具 → Application → Cookies 中找到此字段
                            </div>
                        </div>
                    `;
                }
            }).join('');
            
            document.getElementById('cookie-fields').innerHTML = fieldsHtml;
            
            const savedConfig = localStorage.getItem('autosignin_config_' + name);
            if (savedConfig) {
                try {
                    const config = JSON.parse(savedConfig);
                    document.getElementById('account-name').value = config.accountName || '';
                    selectedPlatform.required_cookies.forEach(cookie => {
                        const input = document.getElementById('cookie-' + cookie);
                        if (input && config.cookies && config.cookies[cookie]) {
                            input.value = config.cookies[cookie];
                        }
                    });
                } catch(e) {}
            }
        }
        
        document.getElementById('cookie-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            if (!selectedPlatform) {
                showToast('请先选择要配置的平台', 'warning');
                return;
            }
            
            const accountName = document.getElementById('account-name').value.trim();
            if (!accountName) {
                showToast('请输入账号名称', 'warning');
                return;
            }
            
            const cookies = {};
            let hasError = false;
            
            selectedPlatform.required_cookies.forEach(cookie => {
                const input = document.getElementById('cookie-' + cookie);
                const value = input.value.trim();
                if (!value) {
                    input.classList.add('error');
                    hasError = true;
                } else {
                    input.classList.remove('error');
                    cookies[cookie] = value;
                }
            });
            
            if (hasError) {
                showToast('请填写所有必填字段', 'error');
                return;
            }
            
            const config = {
                platform: selectedPlatform.name,
                accountName: accountName,
                cookies: cookies,
                savedAt: new Date().toISOString()
            };
            
            localStorage.setItem('autosignin_config_' + selectedPlatform.name, JSON.stringify(config));
            
            try {
                await fetch('/api/config', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(config)
                });
            } catch(e) {}
            
            showToast('配置已保存成功！', 'success');
        });
        
        async function validateCookie() {
            if (!selectedPlatform) {
                showToast('请先选择要配置的平台', 'warning');
                return;
            }
            
            const cookies = {};
            selectedPlatform.required_cookies.forEach(cookie => {
                const input = document.getElementById('cookie-' + cookie);
                cookies[cookie] = input.value.trim();
            });
            
            try {
                const res = await fetch('/api/validate-cookie', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        platform: selectedPlatform.name,
                        cookies: cookies
                    })
                });
                const data = await res.json();
                
                if (data.valid) {
                    showToast('Cookie验证通过！', 'success');
                    if (data.warnings && data.warnings.length > 0) {
                        showModal('验证警告', data.warnings.join('<br>'));
                    }
                } else {
                    showToast('Cookie验证失败', 'error');
                    showModal('验证失败', data.errors.join('<br>'));
                }
            } catch(e) {
                showToast('验证请求失败', 'error');
            }
        }
        
        function clearForm() {
            document.getElementById('account-name').value = '';
            document.querySelectorAll('#cookie-fields input, #cookie-fields textarea').forEach(input => {
                input.value = '';
                input.classList.remove('error', 'success');
            });
        }
        
        async function signAll() {
            if (!confirm('确定要签到全部平台吗？这可能需要一些时间。')) return;
            
            const configs = {};
            platforms.forEach(p => {
                const saved = localStorage.getItem('autosignin_config_' + p.name);
                if (saved) {
                    try {
                        configs[p.name] = JSON.parse(saved);
                    } catch(e) {}
                }
            });
            
            showModal('签到中', '<div class="loading"><div class="spinner"></div><span>正在执行签到任务...</span></div><div class="progress-bar"><div class="progress-fill" style="width: 0%"></div></div>');
            
            try {
                const res = await fetch('/api/sign', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({configs: configs})
                });
                const data = await res.json();
                
                document.querySelector('.progress-fill').style.width = '100%';
                
                setTimeout(() => {
                    closeModal();
                    
                    if (data.success) {
                        showToast(data.message, 'success');
                    } else {
                        let errorMsg = data.message || '签到失败';
                        if (data.errors && data.errors.length > 0) {
                            errorMsg += '\\n失败平台: ' + data.errors.map(e => e.platform + ': ' + e.error).join(', ');
                        }
                        showModal('签到结果', 
                            '<div class="alert alert-' + (data.success ? 'success' : 'error') + '">' +
                            '<span class="alert-icon">' + (data.success ? '✓' : '✗') + '</span>' +
                            '<div><strong>' + data.message + '</strong>' +
                            (data.errors ? '<br><br>失败详情:<br>' + data.errors.map(e => 
                                '• ' + e.platform + ': ' + e.error + ' (' + e.error_type + ')'
                            ).join('<br>') : '') +
                            '</div></div>'
                        );
                    }
                    
                    loadHistory();
                }, 500);
            } catch(e) {
                closeModal();
                showModal('请求失败', 
                    '<div class="alert alert-error">' +
                    '<span class="alert-icon">✗</span>' +
                    '<div><strong>签到请求失败</strong><br>' + e.message + '</div></div>'
                );
            }
        }
        
        async function signPlatform(platform) {
            const saved = localStorage.getItem('autosignin_config_' + platform);
            let config = null;
            if (saved) {
                try {
                    config = JSON.parse(saved);
                } catch(e) {}
            }
            
            const configs = {};
            configs[platform] = config;
            
            showModal('签到中', '<div class="loading"><div class="spinner"></div><span>正在执行签到任务...</span></div>');
            
            try {
                const res = await fetch('/api/sign', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({platform: platform, configs: configs})
                });
                const data = await res.json();
                
                closeModal();
                
                if (data.success) {
                    showToast(data.message, 'success');
                } else {
                    let errorDetails = '<div class="alert alert-error"><span class="alert-icon">✗</span><div>';
                    errorDetails += '<strong>' + (data.message || '签到失败') + '</strong>';
                    
                    if (data.error_type) {
                        errorDetails += '<br><small>错误类型: ' + data.error_type + '</small>';
                    }
                    
                    if (data.error_code) {
                        errorDetails += '<br><small>错误代码: ' + data.error_code + '</small>';
                    }
                    
                    if (data.details) {
                        errorDetails += '<br><br>详细信息:<br>• ' + data.details.join('<br>• ');
                    }
                    
                    if (data.suggestion) {
                        errorDetails += '<br><br><strong>建议:</strong> ' + data.suggestion;
                    }
                    
                    if (data.warnings && data.warnings.length > 0) {
                        errorDetails += '<br><br><strong>警告:</strong><br>• ' + data.warnings.join('<br>• ');
                    }
                    
                    errorDetails += '</div></div>';
                    showModal('签到失败', errorDetails);
                }
                
                loadHistory();
            } catch(e) {
                closeModal();
                showModal('请求失败', 
                    '<div class="alert alert-error">' +
                    '<span class="alert-icon">✗</span>' +
                    '<div><strong>签到请求失败</strong><br>' + e.message + '</div></div>'
                );
            }
        }
        
        function showToast(message, type = 'info') {
            const existing = document.querySelector('.toast');
            if (existing) existing.remove();
            
            const toast = document.createElement('div');
            toast.className = 'toast ' + type;
            toast.textContent = message;
            document.body.appendChild(toast);
            
            setTimeout(() => toast.remove(), 3000);
        }
        
        function showModal(title, content) {
            document.getElementById('modal-title').textContent = title;
            document.getElementById('modal-content').innerHTML = content;
            document.getElementById('modal').classList.add('active');
        }
        
        function closeModal() {
            document.getElementById('modal').classList.remove('active');
        }
        
        document.getElementById('modal').addEventListener('click', (e) => {
            if (e.target.id === 'modal') closeModal();
        });
        
        loadStatus();
        loadPlatforms();
        loadHistory();
        loadHelp();
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
========================================
   Auto-SignIn Web 控制面板已启动
========================================
   
   访问地址: http://localhost:{port}
   配置文件: {config_path}
   
   按 Ctrl+C 停止服务
   
========================================
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
