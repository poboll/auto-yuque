#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语雀自动化工具 - 图形界面版本
提供友好的GUI界面来执行各种自动化测试
"""

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext
    TKINTER_AVAILABLE = True
except ImportError:
    print("❌ tkinter不可用。请安装tkinter支持:")
    print("   macOS: brew install python-tk")
    print("   Ubuntu/Debian: sudo apt-get install python3-tk")
    print("   或者使用命令行版本: python main.py")
    TKINTER_AVAILABLE = False

import threading
import sys
import os
import json
import subprocess
from datetime import datetime

# 导入main.py中的功能
from main import (
    test_create_and_delete_note,
    test_explore_page,
    test_knowledge_base,
    test_explore_follow_user,
    merge_csv_files,
    load_cookies,
    save_cookies,
    is_login_successful,
    DASHBOARD_URL,
    LOGIN_URL,
    COOKIE_FILE
)

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

class AutoYuqueGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 语雀自动化工具 - 智能助手")
        
        # 根据屏幕分辨率动态设置窗口大小
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # 原始尺寸：900x700
        # 宽度减少2/5：900 * (1 - 2/5) = 900 * 0.6 = 540
        # 高度增加1/2：700 * (1 + 1/2) = 700 * 1.5 = 1050
        base_width = int(screen_width * 0.25)  # 屏幕宽度的25%
        base_height = int(screen_height * 0.6)  # 屏幕高度的60%
        
        # 确保窗口不会太小或太大
        min_width, max_width = 400, 800
        min_height, max_height = 600, 1200
        
        window_width = max(min_width, min(max_width, base_width))
        window_height = max(min_height, min(max_height, base_height))
        
        # 计算窗口居中位置
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.resizable(True, True)
        
        # 设置现代化主题
        self.setup_theme()
        
        # 初始化变量
        self.driver = None
        self.is_logged_in = False
        self.config = {}
        
        # 创建界面
        self.create_widgets()
        
        # 加载配置
        self.load_config()
        
    def setup_theme(self):
        """设置Cosmo风格主题"""
        style = ttk.Style()
        
        # 设置主题
        try:
            style.theme_use('clam')  # 使用现代化主题
        except:
            pass
            
        # Cosmo主题配色方案
        # 主色调：明亮的蓝色系
        primary_color = '#2780e3'  # Cosmo蓝色
        secondary_color = '#373a3c'  # 深灰色
        accent_color = '#5bc0de'  # 浅蓝色
        success_color = '#5cb85c'  # 绿色
        warning_color = '#f0ad4e'  # 橙色
        error_color = '#d9534f'  # 红色
        info_color = '#5bc0de'  # 信息蓝
        text_primary = '#373a3c'  # 深灰文字
        text_secondary = '#818a91'  # 中灰文字
        bg_primary = '#ffffff'  # 白色背景
        bg_secondary = '#f7f7f9'  # 浅灰背景
        border_color = '#ccc'  # 边框颜色
        
        # 自定义样式 - 适中的字体大小
        style.configure('Title.TLabel', font=('Helvetica', 26, 'bold'), foreground=primary_color, background=bg_primary)
        style.configure('Subtitle.TLabel', font=('Helvetica', 16), foreground=text_secondary, background=bg_primary)
        style.configure('Success.TLabel', foreground=success_color, font=('Helvetica', 13, 'bold'), background=bg_primary)
        style.configure('Error.TLabel', foreground=error_color, font=('Helvetica', 13, 'bold'), background=bg_primary)
        style.configure('Warning.TLabel', foreground=warning_color, font=('Helvetica', 13, 'bold'), background=bg_primary)
        
        # 按钮样式 - Cosmo风格，适中的字体大小
        style.configure('Primary.TButton', 
                       font=('Helvetica', 13, 'bold'),
                       background=primary_color,
                       foreground='#ffffff',
                       borderwidth=1,
                       relief='solid',
                       focuscolor='none')
        style.map('Primary.TButton',
                 background=[('active', '#1f6ec8'), ('pressed', '#1a5ba8')],
                 foreground=[('active', '#ffffff'), ('pressed', '#ffffff')])
                 
        style.configure('Success.TButton', 
                       font=('Helvetica', 13, 'bold'),
                       background=success_color,
                       foreground='#ffffff',
                       borderwidth=1,
                       relief='solid',
                       focuscolor='none')
        style.map('Success.TButton',
                 background=[('active', '#4cae4c'), ('pressed', '#449d44')],
                 foreground=[('active', '#ffffff'), ('pressed', '#ffffff')])
                 
        style.configure('Danger.TButton', 
                       font=('Helvetica', 13, 'bold'),
                       background=error_color,
                       foreground='#ffffff',
                       borderwidth=1,
                       relief='solid',
                       focuscolor='none')
        style.map('Danger.TButton',
                 background=[('active', '#d43f3a'), ('pressed', '#c9302c')],
                 foreground=[('active', '#ffffff'), ('pressed', '#ffffff')])
                 
        # 禁用按钮样式
        style.configure('Disabled.TButton', 
                       font=('Helvetica', 13, 'bold'),
                       background='#cccccc',
                       foreground='#666666',
                       borderwidth=1,
                       relief='solid',
                       focuscolor='none')
        style.map('Disabled.TButton',
                 background=[('active', '#cccccc'), ('pressed', '#cccccc')],
                 foreground=[('active', '#666666'), ('pressed', '#666666')])
        
        # LabelFrame样式 - 适中的字体大小
        style.configure('TLabelframe', background=bg_primary, borderwidth=1, relief='solid', bordercolor=border_color)
        style.configure('TLabelframe.Label', background=bg_primary, foreground=primary_color, font=('Helvetica', 15, 'bold'))
        
        # Entry样式
        style.configure('TEntry', fieldbackground='white', borderwidth=1, relief='solid', bordercolor=border_color)
        
        # Frame样式
        style.configure('TFrame', background=bg_primary)
        
        # 设置主窗口背景色
        self.root.configure(bg=bg_primary)
        
    def create_widgets(self):
        """创建GUI组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 标题区域
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 25))
        header_frame.columnconfigure(0, weight=1)
        
        # 主标题
        title_label = ttk.Label(header_frame, text="🚀 语雀自动化工具", style='Title.TLabel')
        title_label.grid(row=0, column=0, pady=(0, 5))
        
        # 副标题
        subtitle_label = ttk.Label(header_frame, text="智能化内容管理与自动化测试平台", style='Subtitle.TLabel')
        subtitle_label.grid(row=1, column=0, pady=(0, 10))
        
        # 分隔线
        separator = ttk.Separator(header_frame, orient='horizontal')
        separator.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # 配置区域
        config_frame = ttk.LabelFrame(main_frame, text="⚙️ 配置设置", padding="15")
        config_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        config_frame.columnconfigure(1, weight=1)
        
        # ChromeDriver路径 - 适中的字体大小
        ttk.Label(config_frame, text="🔧 ChromeDriver路径:", font=('Helvetica', 13)).grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.driver_path_var = tk.StringVar()
        driver_path_entry = ttk.Entry(config_frame, textvariable=self.driver_path_var, width=50, font=('Helvetica', 13))
        driver_path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        browse_btn = ttk.Button(config_frame, text="📁 浏览", command=self.browse_driver_path, style='Primary.TButton')
        browse_btn.grid(row=0, column=2)
        
        # 项目目录按钮
        open_dir_btn = ttk.Button(config_frame, text="📂 打开项目目录", command=self.open_project_directory, style='Primary.TButton')
        open_dir_btn.grid(row=1, column=0, columnspan=3, pady=(10, 0), sticky=(tk.W, tk.E))
        
        # 登录状态区域
        login_frame = ttk.LabelFrame(main_frame, text="🔐 登录状态", padding="15")
        login_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        login_frame.columnconfigure(1, weight=1)
        
        self.login_status_var = tk.StringVar(value="未登录")
        ttk.Label(login_frame, text="🔍 状态:", font=('Helvetica', 13)).grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.status_label = ttk.Label(login_frame, textvariable=self.login_status_var, style='Error.TLabel')
        self.status_label.grid(row=0, column=1, sticky=tk.W)
        
        # 登录按钮
        self.login_btn = ttk.Button(login_frame, text="🚀 初始化并登录", command=self.login_yuque, style='Primary.TButton')
        self.login_btn.grid(row=0, column=2, padx=(10, 0))
        
        # 功能按钮区域
        function_frame = ttk.LabelFrame(main_frame, text="🎯 功能操作", padding="15")
        function_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        function_frame.columnconfigure(0, weight=1)
        function_frame.columnconfigure(1, weight=1)
        
        # 功能按钮 - 使用更现代化的图标和描述，未登录时显示为禁用状态
        self.note_btn = ttk.Button(function_frame, text="📝 智能小记\n快速创建与管理", 
                                  command=lambda: self.run_test("note"), state="disabled", style='Disabled.TButton')
        self.note_btn.grid(row=0, column=0, padx=(0, 8), pady=(0, 8), sticky=(tk.W, tk.E), ipady=5)
        
        self.explore_btn = ttk.Button(function_frame, text="🌟 社区互动\nAI智能点赞回复", 
                                     command=lambda: self.run_test("explore"), state="disabled", style='Disabled.TButton')
        self.explore_btn.grid(row=0, column=1, padx=(8, 0), pady=(0, 8), sticky=(tk.W, tk.E), ipady=5)
        
        self.knowledge_btn = ttk.Button(function_frame, text="📚 知识管理\n自动化文档创建", 
                                       command=lambda: self.run_test("knowledge"), state="disabled", style='Disabled.TButton')
        self.knowledge_btn.grid(row=1, column=0, padx=(0, 8), pady=(0, 8), sticky=(tk.W, tk.E), ipady=5)
        
        self.follow_btn = ttk.Button(function_frame, text="👥 用户发现\n精准关注优质创作者", 
                                    command=lambda: self.run_test("follow"), state="disabled", style='Disabled.TButton')
        self.follow_btn.grid(row=1, column=1, padx=(8, 0), pady=(0, 8), sticky=(tk.W, tk.E), ipady=5)
        
        # CSV汇总按钮
        self.merge_btn = ttk.Button(function_frame, text="📊 汇总CSV文件", 
                                   command=self.merge_csv_files, style='Success.TButton')
        self.merge_btn.grid(row=2, column=0, columnspan=2, pady=(8, 0), sticky=(tk.W, tk.E), ipady=4)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="📋 运行日志", padding="15")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80, 
                                                 font=('Consolas', 13), wrap=tk.WORD,
                                                 bg='#f7f7f9', fg='#373a3c', insertbackground='#373a3c',
                                                 relief='solid', borderwidth=1)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置日志文本颜色标签 - Cosmo主题配色
        self.log_text.tag_configure('success', foreground='#5cb85c')
        self.log_text.tag_configure('error', foreground='#d9534f')
        self.log_text.tag_configure('warning', foreground='#f0ad4e')
        self.log_text.tag_configure('info', foreground='#5bc0de')
        
        # 底部按钮
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(15, 0))
        bottom_frame.columnconfigure(1, weight=1)
        
        clear_log_btn = ttk.Button(bottom_frame, text="🗑️ 清空日志", command=self.clear_log, style='Primary.TButton')
        clear_log_btn.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        self.quit_btn = ttk.Button(bottom_frame, text="❌ 退出程序", command=self.quit_application, style='Danger.TButton')
        self.quit_btn.grid(row=0, column=2, sticky=tk.E)
        
    def load_config(self):
        """加载配置文件"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            driver_path = self.config.get("driver_path", "")
            self.driver_path_var.set(driver_path)
            self.log("✅ 配置文件加载成功")
        except FileNotFoundError:
            self.log("⚠️ 配置文件不存在，请设置ChromeDriver路径")
        except Exception as e:
            self.log(f"❌ 加载配置文件失败: {e}")
            
    def save_config(self):
        """保存配置文件"""
        try:
            self.config["driver_path"] = self.driver_path_var.get()
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            self.log("✅ 配置已保存")
        except Exception as e:
            self.log(f"❌ 保存配置失败: {e}")
            
    def browse_driver_path(self):
        """浏览选择ChromeDriver路径"""
        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            title="选择ChromeDriver可执行文件",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")]
        )
        if filename:
            self.driver_path_var.set(filename)
            self.save_config()
            
    def open_project_directory(self):
        """打开项目目录"""
        try:
            project_dir = os.path.dirname(os.path.abspath(__file__))
            if sys.platform == "darwin":  # macOS
                subprocess.run(["open", project_dir])
            elif sys.platform == "win32":  # Windows
                subprocess.run(["explorer", project_dir])
            else:  # Linux
                subprocess.run(["xdg-open", project_dir])
            self.log("📂 项目目录已打开", "info")
        except Exception as e:
            self.log(f"❌ 打开项目目录失败: {e}", "error")
    
    def log(self, message, level="info"):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        # 根据级别设置颜色
        if "✅" in message or "成功" in message:
            level = "success"
        elif "❌" in message or "失败" in message or "错误" in message:
            level = "error"
        elif "⚠️" in message or "警告" in message:
            level = "warning"
        elif "🚀" in message or "⏳" in message or "ℹ️" in message:
            level = "info"
            
        self.log_text.insert(tk.END, log_message, level)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        
    def login_yuque(self):
        """登录语雀"""
        def login_thread():
            try:
                # 检查ChromeDriver路径
                driver_path = self.driver_path_var.get().strip()
                if not driver_path or not os.path.exists(driver_path):
                    self.log("❌ 请先设置正确的ChromeDriver路径")
                    return
                    
                self.log("⏳ 正在初始化Chrome WebDriver...")
                
                # 禁用登录按钮
                self.login_btn.config(state="disabled")
                
                try:
                    # 尝试旧版本语法
                    self.driver = webdriver.Chrome(executable_path=driver_path)
                except Exception:
                    # 尝试新版本语法
                    service = ChromeService(executable_path=driver_path)
                    self.driver = webdriver.Chrome(service=service)
                
                # 设置浏览器窗口大小为屏幕的3/4
                self.driver.execute_script("""
                    const screenWidth = window.screen.width;
                    const screenHeight = window.screen.height;
                    const windowWidth = Math.floor(screenWidth * 0.75);
                    const windowHeight = Math.floor(screenHeight * 0.75);
                    const x = Math.floor((screenWidth - windowWidth) / 2);
                    const y = Math.floor((screenHeight - windowHeight) / 2);
                    window.resizeTo(windowWidth, windowHeight);
                    window.moveTo(x, y);
                """)
                    
                self.driver.implicitly_wait(5)
                self.log("✅ WebDriver 初始化成功 (窗口大小设置为屏幕的3/4)")
                
                # 尝试使用Cookie登录
                self.log("⏳ 尝试使用Cookie登录...")
                if not load_cookies(self.driver, COOKIE_FILE):
                    # Cookie登录失败，需要手动登录
                    self.driver.get(LOGIN_URL)
                    self.log("🚨 请在浏览器中手动扫描二维码完成登录")
                    self.log("   等待登录完成（最长2分钟）...")
                    
                    try:
                        WebDriverWait(self.driver, 120, poll_frequency=3).until(
                            lambda d: is_login_successful(d)
                        )
                        self.log("✅ 手动登录成功！")
                        save_cookies(self.driver, COOKIE_FILE)
                    except TimeoutException:
                        self.log("❌ 登录超时，请重试")
                        return
                        
                # 验证登录状态
                self.driver.get(DASHBOARD_URL)
                if is_login_successful(self.driver):
                    self.is_logged_in = True
                    self.login_status_var.set("✅ 已登录")
                    self.status_label.config(style='Success.TLabel')
                    self.log("✅ 登录验证成功！")
                    
                    # 启用功能按钮并切换到正常样式
                    self.note_btn.config(state="normal", style='Primary.TButton')
                    self.explore_btn.config(state="normal", style='Primary.TButton')
                    self.knowledge_btn.config(state="normal", style='Primary.TButton')
                    self.follow_btn.config(state="normal", style='Primary.TButton')
                    
                    # 更新登录按钮
                    self.login_btn.config(text="🔄 重新登录", state="normal")
                else:
                    self.log("❌ 登录验证失败")
                    self.login_btn.config(state="normal")
                    
            except Exception as e:
                self.log(f"❌ 登录过程中发生错误: {e}")
                self.login_btn.config(state="normal")
                
        # 在新线程中执行登录
        threading.Thread(target=login_thread, daemon=True).start()
        
    def run_test(self, test_type):
        """运行指定的测试"""
        if not self.is_logged_in or not self.driver:
            self.log("❌ 请先登录语雀")
            return
            
        def test_thread():
            try:
                # 禁用所有功能按钮
                self.disable_function_buttons()
                
                if test_type == "note":
                    self.log("🚀 开始执行小记测试...")
                    test_create_and_delete_note(self.driver)
                    self.log("✅ 小记测试完成")
                    
                elif test_type == "explore":
                    self.log("🚀 开始执行逛逛测试...")
                    test_explore_page(self.driver)
                    self.log("✅ 逛逛测试完成")
                    
                elif test_type == "knowledge":
                    self.log("🚀 开始执行知识库测试...")
                    test_knowledge_base(self.driver)
                    self.log("✅ 知识库测试完成")
                    
                elif test_type == "follow":
                    self.log("🚀 开始执行关注用户测试...")
                    test_explore_follow_user(self.driver)
                    self.log("✅ 关注用户测试完成")
                    
            except Exception as e:
                self.log(f"❌ 测试执行失败: {e}")
            finally:
                # 重新启用功能按钮
                self.enable_function_buttons()
                
        # 在新线程中执行测试
        threading.Thread(target=test_thread, daemon=True).start()
        
    def disable_function_buttons(self):
        """禁用功能按钮"""
        self.note_btn.config(state="disabled")
        self.explore_btn.config(state="disabled")
        self.knowledge_btn.config(state="disabled")
        self.follow_btn.config(state="disabled")
        
    def enable_function_buttons(self):
        """启用功能按钮"""
        if self.is_logged_in:
            self.note_btn.config(state="normal")
            self.explore_btn.config(state="normal")
            self.knowledge_btn.config(state="normal")
            self.follow_btn.config(state="normal")
            
    def merge_csv_files(self):
        """汇总CSV文件"""
        def merge_thread():
            try:
                self.log("🔄 开始汇总CSV文件...")
                merge_csv_files()
                self.log("✅ CSV文件汇总完成")
            except Exception as e:
                self.log(f"❌ CSV文件汇总失败: {e}")
                
        threading.Thread(target=merge_thread, daemon=True).start()
        
    def quit_application(self):
        """退出应用程序"""
        try:
            if self.driver:
                self.log("⏳ 正在关闭WebDriver...")
                try:
                    # 关闭所有窗口
                    self.driver.quit()
                    self.log("✅ WebDriver已关闭")
                except Exception as e:
                    self.log(f"⚠️ 关闭WebDriver时出错: {e}")
                    # 强制终止浏览器进程
                    try:
                        import psutil
                        for proc in psutil.process_iter(['pid', 'name']):
                            if 'chrome' in proc.info['name'].lower():
                                proc.terminate()
                    except:
                        pass
                finally:
                    self.driver = None
        except Exception as e:
            self.log(f"❌ 退出程序时出错: {e}")
        finally:
            # 确保程序退出
            self.root.quit()
            self.root.destroy()
        
    def on_closing(self):
        """窗口关闭事件处理"""
        self.quit_application()

def main():
    """主函数"""
    if not TKINTER_AVAILABLE:
        print("\n由于tkinter不可用，程序将退出。")
        print("请安装tkinter支持后重试，或使用命令行版本。")
        sys.exit(1)
        
    root = tk.Tk()
    app = AutoYuqueGUI(root)
    
    # 设置窗口关闭事件
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # 启动GUI
    root.mainloop()

if __name__ == "__main__":
    main()