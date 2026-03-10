#!/usr/bin/env python3
"""
静态资源服务器 - 禁用目录浏览
支持 fetch API 访问静态文件
"""

import http.server
import socketserver
import os
import sys
from urllib.parse import unquote


class StaticHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    """自定义请求处理器，禁用目录列表，仅提供静态文件服务"""
    
    # 根目录
    root_dir = os.getcwd()
    
    def log_message(self, format, *args):
        """自定义日志输出"""
        print(f"[{self.log_date_time_string()}] {args[0]} {args[1]} - {args[2]}")
    
    def send_cors_headers(self):
        """发送 CORS 头"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
    
    def do_OPTIONS(self):
        """处理 OPTIONS 预检请求"""
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
    
    def do_HEAD(self):
        """处理 HEAD 请求"""
        path = self.translate_path(self.path)
        
        if not path:
            self.send_error(403, "Forbidden")
            return
            
        if os.path.isdir(path):
            # 目录返回 404，禁用目录浏览
            self.send_error(404, "Not found")
            return
        
        if not os.path.exists(path):
            self.send_error(404, "File not found")
            return
            
        if not os.path.isfile(path):
            self.send_error(403, "Forbidden")
            return
        
        try:
            content_type = self.guess_type(path)
            stat = os.stat(path)
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(stat.st_size))
            self.send_header('Last-Modified', self.date_time_string(stat.st_mtime))
            self.send_cors_headers()
            self.end_headers()
        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")
    
    def do_GET(self):
        """处理 GET 请求"""
        path = self.translate_path(self.path)
        
        if not path:
            self.send_error(403, "Forbidden")
            return
            
        if os.path.isdir(path):
            # 目录返回 404，禁用目录浏览
            self.send_error(404, "Not found")
            return
        
        if not os.path.exists(path):
            self.send_error(404, "File not found")
            return
            
        if not os.path.isfile(path):
            self.send_error(403, "Forbidden")
            return
        
        try:
            # 读取文件内容
            with open(path, 'rb') as f:
                content = f.read()
            
            content_type = self.guess_type(path)
            
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', len(content))
            self.send_header('Last-Modified', self.date_time_string(os.path.getmtime(path)))
            self.send_cors_headers()
            self.end_headers()
            
            self.wfile.write(content)
            
        except PermissionError:
            self.send_error(403, "Permission denied")
        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")
    
    def translate_path(self, path):
        """将 URL 路径映射到本地文件系统路径"""
        # 移除查询参数和片段
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        
        # URL 解码
        path = unquote(path)
        
        # 规范化路径
        path = path.replace('/', os.sep)
        if path.startswith(os.sep):
            path = path[1:]
        
        # 防止目录遍历
        parts = []
        for part in path.split(os.sep):
            if part == '..' or part == '.':
                continue
            if part:
                parts.append(part)
        
        # 构建完整路径
        full_path = self.root_dir
        for part in parts:
            full_path = os.path.join(full_path, part)
        
        # 安全检查：确保路径在根目录下
        real_root = os.path.realpath(self.root_dir)
        real_path = os.path.realpath(full_path)
        
        if not real_path.startswith(real_root):
            return None
        
        return real_path
    
    def guess_type(self, path):
        """猜测文件 MIME 类型"""
        ext = os.path.splitext(path)[1].lower()
        
        mime_types = {
            '.html': 'text/html',
            '.htm': 'text/html',
            '.js': 'application/javascript',
            '.mjs': 'application/javascript',
            '.json': 'application/json',
            '.css': 'text/css',
            '.txt': 'text/plain',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.ico': 'image/x-icon',
            '.woff': 'font/woff',
            '.woff2': 'font/woff2',
            '.ttf': 'font/ttf',
            '.otf': 'font/otf',
            '.eot': 'application/vnd.ms-fontobject',
            '.wasm': 'application/wasm',
            '.xml': 'application/xml',
            '.pdf': 'application/pdf',
            '.zip': 'application/zip',
            '.gz': 'application/gzip',
            '.mp4': 'video/mp4',
            '.webm': 'video/webm',
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.webp': 'image/webp',
            '.md': 'text/markdown',
            '.csv': 'text/csv',
        }
        
        return mime_types.get(ext, 'application/octet-stream')


class StaticServer(socketserver.TCPServer):
    """支持重用地址的静态服务器"""
    allow_reuse_address = True


def run_server(port=8000, root_dir=None):
    """启动静态资源服务器"""
    root_dir = root_dir or os.getcwd()
    root_dir = os.path.abspath(root_dir)
    
    if not os.path.isdir(root_dir):
        print(f"错误: 目录不存在: {root_dir}")
        sys.exit(1)
    
    # 设置处理器的根目录
    StaticHTTPRequestHandler.root_dir = root_dir
    
    server = StaticServer(("", port), StaticHTTPRequestHandler)
    
    print(f"=" * 50)
    print(f"静态资源服务器已启动")
    print(f"根目录: {root_dir}")
    print(f"访问地址: http://localhost:{port}")
    print(f"=" * 50)
    print(f"\n特性:")
    print(f"  - 目录浏览: 已禁用")
    print(f"  - CORS 跨域: 已启用")
    print(f"  - 按 Ctrl+C 停止服务器\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n服务器已停止")
        server.shutdown()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="静态资源服务器")
    parser.add_argument(
        "-p", "--port", 
        type=int, 
        default=8000, 
        help="服务器端口 (默认: 8000)"
    )
    parser.add_argument(
        "-d", "--directory", 
        default=".", 
        help="根目录路径 (默认: 当前目录)"
    )
    
    args = parser.parse_args()
    run_server(port=args.port, root_dir=args.directory)
