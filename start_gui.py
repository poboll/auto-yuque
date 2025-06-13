#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语雀自动化工具启动器
自动检测环境并选择合适的GUI版本
"""

import sys
import os
import subprocess
import time

# ANSI颜色代码
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_banner():
    """打印美化的启动横幅"""
    banner = f"""{Colors.HEADER}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════╗
║                    🚀 语雀自动化工具                          ║
║                   智能助手启动器 v2.0                         ║
╠══════════════════════════════════════════════════════════════╣
║  ✨ 现代化界面设计  📊 智能数据分析  🤖 AI驱动自动化        ║
╚══════════════════════════════════════════════════════════════╝{Colors.ENDC}
"""
    print(banner)
    time.sleep(0.5)

def print_status(message, status="info"):
    """打印带颜色的状态消息"""
    if status == "success":
        print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")
    elif status == "error":
        print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")
    elif status == "warning":
        print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")
    elif status == "info":
        print(f"{Colors.OKCYAN}ℹ️  {message}{Colors.ENDC}")
    elif status == "loading":
        print(f"{Colors.OKBLUE}⏳ {message}{Colors.ENDC}")

def print_menu(title, options):
    """打印美化的菜单"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}📋 {title}{Colors.ENDC}")
    print(f"{Colors.BOLD}{'─' * (len(title) + 4)}{Colors.ENDC}")
    for key, value in options.items():
        print(f"{Colors.OKBLUE}{key}.{Colors.ENDC} {value}")
    print()

def check_tkinter():
    """检查tkinter是否可用"""
    try:
        import tkinter
        return True
    except ImportError:
        return False

def check_dependencies():
    """检查必要的依赖是否已安装"""
    print_status("正在检查依赖包...", "loading")
    missing_deps = []
    
    # 检查selenium
    try:
        import selenium
        print_status("selenium - 已安装", "success")
    except ImportError:
        missing_deps.append('selenium')
        print_status("selenium - 未安装", "error")
    
    # 检查pandas
    try:
        import pandas
        print_status("pandas - 已安装", "success")
    except ImportError:
        missing_deps.append('pandas')
        print_status("pandas - 未安装", "error")
    
    # 检查其他依赖
    other_deps = ['requests', 'openpyxl', 'webdriver-manager']
    for dep in other_deps:
        try:
            __import__(dep.replace('-', '_'))
            print_status(f"{dep} - 已安装", "success")
        except ImportError:
            missing_deps.append(dep)
            print_status(f"{dep} - 未安装", "error")
    
    return missing_deps

def install_dependencies():
    """尝试安装缺失的依赖"""
    print_status("开始安装缺失的依赖包...", "loading")
    
    # 尝试不同的pip命令 - 使用python -m pip而不是直接使用pip3
    pip_commands = ['pip', 'python -m pip']
    
    for pip_cmd in pip_commands:
        try:
            print_status(f"尝试使用 {pip_cmd} 安装...", "info")
            
            # 构建命令
            if pip_cmd == 'python -m pip':
                cmd = ['python', '-m', 'pip', 'install', '-r', 'requirements.txt']
            else:
                cmd = [pip_cmd, 'install', '-r', 'requirements.txt']
            
            # 首先尝试正常安装
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                print_status(f"使用 {pip_cmd} 成功安装依赖", "success")
                return True
            else:
                print_status(f"使用 {pip_cmd} 安装失败", "error")
                if result.stderr:
                    print_status(f"错误信息: {result.stderr.strip()[:100]}...", "warning")
                    
        except FileNotFoundError:
            print_status(f"找不到 {pip_cmd} 命令", "error")
        except subprocess.TimeoutExpired:
            print_status(f"{pip_cmd} 安装超时", "error")
        except Exception as e:
            print_status(f"{pip_cmd} 安装出现异常: {e}", "error")
    
    # 如果常规方法都失败了，询问用户是否使用 --break-system-packages
    print_status("常规安装方法失败", "warning")
    print(f"\n{Colors.WARNING}⚠️  检测到可能的系统包管理冲突{Colors.ENDC}")
    print(f"{Colors.OKCYAN}这通常发生在使用Homebrew管理的Python环境中{Colors.ENDC}")
    
    break_system_options = {
        "y": "🔧 是的，使用 --break-system-packages 强制安装",
        "n": "❌ 不，我想手动处理",
        "v": "📦 创建虚拟环境安装"
    }
    
    while True:
        print_menu("高级安装选项", break_system_options)
        choice = input(f"{Colors.BOLD}请选择操作 (y/n/v): {Colors.ENDC}").lower().strip()
        
        if choice in ['y', 'yes', '是']:
            print_status("尝试使用 --break-system-packages 安装...", "loading")
            try:
                result = subprocess.run(['pip', 'install', '-r', 'requirements.txt', '--break-system-packages'], 
                                      capture_output=True, text=True, timeout=300)
                if result.returncode == 0:
                    print_status("使用 --break-system-packages 成功安装依赖", "success")
                    return True
                else:
                    print_status("--break-system-packages 安装也失败了", "error")
                    break
            except Exception as e:
                print_status(f"--break-system-packages 安装出现异常: {e}", "error")
                break
        elif choice in ['n', 'no', '否']:
            break
        elif choice == 'v':
            print_status("创建虚拟环境安装指南:", "info")
            print(f"{Colors.OKBLUE}1.{Colors.ENDC} 创建虚拟环境: {Colors.BOLD}python -m venv venv{Colors.ENDC}")
            print(f"{Colors.OKBLUE}2.{Colors.ENDC} 激活虚拟环境: {Colors.BOLD}source venv/bin/activate{Colors.ENDC}")
            print(f"{Colors.OKBLUE}3.{Colors.ENDC} 安装依赖: {Colors.BOLD}pip install -r requirements.txt{Colors.ENDC}")
            print(f"{Colors.OKBLUE}4.{Colors.ENDC} 运行程序: {Colors.BOLD}python main.py{Colors.ENDC}")
            return False
        else:
            print_status("请输入 y、n 或 v", "warning")
    
    print_status("所有自动安装方法都失败了", "error")
    print(f"\n{Colors.WARNING}📝 手动安装指南:{Colors.ENDC}")
    print(f"{Colors.OKBLUE}1.{Colors.ENDC} 创建虚拟环境: {Colors.BOLD}python -m venv venv{Colors.ENDC}")
    print(f"{Colors.OKBLUE}2.{Colors.ENDC} 激活虚拟环境: {Colors.BOLD}source venv/bin/activate{Colors.ENDC}")
    print(f"{Colors.OKBLUE}3.{Colors.ENDC} 安装依赖: {Colors.BOLD}pip install -r requirements.txt{Colors.ENDC}")
    return False

def open_project_directory():
    """打开项目目录"""
    try:
        current_dir = os.getcwd()
        if sys.platform == "darwin":  # macOS
            subprocess.run(["open", current_dir])
        elif sys.platform == "win32":  # Windows
            subprocess.run(["explorer", current_dir])
        else:  # Linux
            subprocess.run(["xdg-open", current_dir])
        print_status("项目目录已打开", "success")
    except Exception as e:
        print_status(f"打开项目目录失败: {e}", "error")

def main():
    """主函数"""
    # 清屏
    os.system('clear' if os.name == 'posix' else 'cls')
    
    # 打印启动横幅
    print_banner()
    
    # 检查依赖
    missing_deps = check_dependencies()
    
    if missing_deps:
        print_status(f"缺少以下依赖: {', '.join(missing_deps)}", "warning")
        
        install_options = {
            "y": "🔧 是的，自动安装缺失的依赖",
            "n": "❌ 不，我稍后手动安装",
            "d": "📁 打开项目目录查看依赖文件"
        }
        
        while True:
            print_menu("依赖安装选项", install_options)
            choice = input(f"{Colors.BOLD}请选择操作 (y/n/d): {Colors.ENDC}").lower().strip()
            
            if choice in ['y', 'yes', '是']:
                if install_dependencies():
                    print_status("依赖安装成功，继续启动...", "success")
                    time.sleep(1)
                    break
                else:
                    print_status("依赖安装失败，请手动安装后重新运行", "error")
                    return
            elif choice in ['n', 'no', '否']:
                print_status("请先安装依赖后重新运行", "warning")
                return
            elif choice == 'd':
                open_project_directory()
            else:
                print_status("请输入 y、n 或 d", "warning")
    else:
        print_status("所有依赖都已安装", "success")
    
    # 检查Tkinter支持
    print_status("检查GUI支持...", "loading")
    has_tkinter = check_tkinter()
    
    if has_tkinter:
        print_status("Tkinter GUI支持 - 可用", "success")
        
        interface_options = {
            "1": "🎨 现代化图形界面 (推荐) - 美观易用的GUI",
            "2": "💻 简化命令行界面 - 轻量级交互式界面", 
            "3": "⌨️  原始命令行界面 - 传统命令行模式",
            "4": "📁 打开项目目录",
            "q": "🚪 退出程序"
        }
        
        while True:
            print_menu("界面选择", interface_options)
            choice = input(f"{Colors.BOLD}请选择界面类型 (1-4/q): {Colors.ENDC}").strip()
            
            if choice == '1':
                print_status("启动现代化图形界面...", "loading")
                subprocess.run(['python', 'gui.py'])
                break
            elif choice == '2':
                print_status("启动简化命令行界面...", "loading")
                subprocess.run(['python', 'simple_gui.py'])
                break
            elif choice == '3':
                print_status("启动原始命令行界面...", "loading")
                subprocess.run(['python', 'main.py'])
                break
            elif choice == '4':
                open_project_directory()
            elif choice.lower() == 'q':
                print_status("感谢使用语雀自动化工具！", "info")
                return
            else:
                print_status("请输入 1-4 或 q", "warning")
    else:
        print_status("Tkinter GUI支持 - 不可用", "warning")
        
        interface_options = {
            "1": "💻 简化命令行界面 (推荐) - 轻量级交互式界面",
            "2": "⌨️  原始命令行界面 - 传统命令行模式",
            "3": "📁 打开项目目录",
            "q": "🚪 退出程序"
        }
        
        while True:
            print_menu("界面选择 (仅命令行)", interface_options)
            choice = input(f"{Colors.BOLD}请选择界面类型 (1-3/q): {Colors.ENDC}").strip()
            
            if choice == '1':
                print_status("启动简化命令行界面...", "loading")
                subprocess.run([sys.executable, 'simple_gui.py'])
                break
            elif choice == '2':
                print_status("启动原始命令行界面...", "loading")
                subprocess.run([sys.executable, 'main.py'])
                break
            elif choice == '3':
                open_project_directory()
            elif choice.lower() == 'q':
                print_status("感谢使用语雀自动化工具！", "info")
                return
            else:
                print_status("请输入 1-3 或 q", "warning")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 程序被用户中断")
    except Exception as e:
        print(f"\n❌ 启动器运行出错: {e}")