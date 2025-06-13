#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语雀自动化工具 - 简化命令行界面
不依赖tkinter，使用简单的命令行菜单系统
"""

import os
import json
import time
import threading
from datetime import datetime

# 导入main.py中的功能
try:
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
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    print("请确保所有依赖已安装: pip install -r requirements.txt")
    exit(1)

class SimpleAutoYuqueGUI:
    def __init__(self):
        self.driver = None
        self.is_logged_in = False
        self.config = {}
        self.load_config()
        
    def clear_screen(self):
        """清屏"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
    def print_header(self):
        """打印程序头部"""
        print("="*60)
        print("           语雀自动化工具 - 简化命令行界面")
        print("="*60)
        print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"登录状态: {'✅ 已登录' if self.is_logged_in else '❌ 未登录'}")
        print("="*60)
        
    def load_config(self):
        """加载配置文件"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            print("✅ 配置文件加载成功")
        except FileNotFoundError:
            print("⚠️ 配置文件不存在，将创建新的配置")
            self.config = {"driver_path": ""}
        except Exception as e:
            print(f"❌ 加载配置文件失败: {e}")
            self.config = {"driver_path": ""}
            
    def save_config(self):
        """保存配置文件"""
        try:
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            print("✅ 配置已保存")
        except Exception as e:
            print(f"❌ 保存配置失败: {e}")
            
    def setup_driver_path(self):
        """设置ChromeDriver路径"""
        print("\n--- ChromeDriver 配置 ---")
        current_path = self.config.get("driver_path", "")
        if current_path:
            print(f"当前路径: {current_path}")
            
        print("\n请输入ChromeDriver可执行文件的完整路径:")
        print("(留空保持当前设置)")
        new_path = input("> ").strip()
        
        if new_path:
            if os.path.exists(new_path):
                self.config["driver_path"] = new_path
                self.save_config()
                print(f"✅ ChromeDriver路径已设置为: {new_path}")
            else:
                print(f"❌ 路径不存在: {new_path}")
        else:
            print("保持当前设置")
            
    def login_yuque(self):
        """登录语雀"""
        print("\n--- 登录语雀 ---")
        
        # 检查ChromeDriver路径
        driver_path = self.config.get("driver_path", "").strip()
        if not driver_path or not os.path.exists(driver_path):
            print("❌ ChromeDriver路径未设置或不存在")
            print("请先配置ChromeDriver路径")
            return False
            
        try:
            print("⏳ 正在初始化Chrome WebDriver...")
            
            try:
                # 尝试旧版本语法
                self.driver = webdriver.Chrome(executable_path=driver_path)
            except Exception:
                # 尝试新版本语法
                service = ChromeService(executable_path=driver_path)
                self.driver = webdriver.Chrome(service=service)
                
            self.driver.maximize_window()
            self.driver.implicitly_wait(5)
            print("✅ WebDriver 初始化成功")
            
            # 尝试使用Cookie登录
            print("⏳ 尝试使用Cookie登录...")
            if not load_cookies(self.driver, COOKIE_FILE):
                # Cookie登录失败，需要手动登录
                self.driver.get(LOGIN_URL)
                print("🚨 请在浏览器中手动扫描二维码完成登录")
                print("   登录完成后，按回车键继续...")
                input("   等待登录完成...")
                
                # 检查登录状态
                if is_login_successful(self.driver):
                    print("✅ 手动登录成功！")
                    save_cookies(self.driver, COOKIE_FILE)
                else:
                    print("❌ 登录验证失败，请重试")
                    return False
                    
            # 验证登录状态
            self.driver.get(DASHBOARD_URL)
            if is_login_successful(self.driver):
                self.is_logged_in = True
                print("✅ 登录验证成功！")
                return True
            else:
                print("❌ 登录验证失败")
                return False
                
        except Exception as e:
            print(f"❌ 登录过程中发生错误: {e}")
            return False
            
    def run_test(self, test_type):
        """运行指定的测试"""
        if not self.is_logged_in or not self.driver:
            print("❌ 请先登录语雀")
            return
            
        try:
            print(f"\n🚀 开始执行{test_type}测试...")
            print("按 Ctrl+C 可以中断测试")
            
            if test_type == "小记":
                test_create_and_delete_note(self.driver)
                
            elif test_type == "逛逛":
                test_explore_page(self.driver)
                
            elif test_type == "知识库":
                test_knowledge_base(self.driver)
                
            elif test_type == "关注用户":
                test_explore_follow_user(self.driver)
                
            print(f"✅ {test_type}测试完成")
            
        except KeyboardInterrupt:
            print(f"\n⚠️ {test_type}测试被用户中断")
        except Exception as e:
            print(f"❌ {test_type}测试执行失败: {e}")
            
    def merge_csv(self):
        """汇总CSV文件"""
        try:
            print("\n🔄 开始汇总CSV文件...")
            merge_csv_files()
            print("✅ CSV文件汇总完成")
        except Exception as e:
            print(f"❌ CSV文件汇总失败: {e}")
            
    def show_main_menu(self):
        """显示主菜单"""
        while True:
            self.clear_screen()
            self.print_header()
            
            print("\n主菜单:")
            print("1. 配置ChromeDriver路径")
            print("2. 登录语雀")
            
            if self.is_logged_in:
                print("\n功能测试:")
                print("3. 小记测试 (创建并删除)")
                print("4. 逛逛测试 (点赞并抓取)")
                print("5. 知识库测试 (创建新文档)")
                print("6. 关注用户测试 (逛逛关注用户)")
                print("\n数据管理:")
                print("7. 汇总CSV文件")
            else:
                print("\n(请先登录以使用功能测试)")
                
            print("\n其他:")
            print("8. 查看生成的文件")
            print("0. 退出程序")
            
            choice = input("\n请选择操作 (0-8): ").strip()
            
            if choice == '1':
                self.setup_driver_path()
                input("\n按回车键继续...")
                
            elif choice == '2':
                self.login_yuque()
                input("\n按回车键继续...")
                
            elif choice == '3' and self.is_logged_in:
                self.run_test("小记")
                input("\n按回车键继续...")
                
            elif choice == '4' and self.is_logged_in:
                self.run_test("逛逛")
                input("\n按回车键继续...")
                
            elif choice == '5' and self.is_logged_in:
                self.run_test("知识库")
                input("\n按回车键继续...")
                
            elif choice == '6' and self.is_logged_in:
                self.run_test("关注用户")
                input("\n按回车键继续...")
                
            elif choice == '7' and self.is_logged_in:
                self.merge_csv()
                input("\n按回车键继续...")
                
            elif choice == '8':
                self.show_files()
                input("\n按回车键继续...")
                
            elif choice == '0':
                self.quit_application()
                break
                
            else:
                print("❌ 无效选择，请重试")
                input("按回车键继续...")
                
    def show_files(self):
        """显示生成的文件"""
        print("\n--- 生成的文件 ---")
        
        files_to_check = [
            ('config.json', '配置文件'),
            ('cookie.pkl', '登录Cookie'),
            ('explore_titles.csv', '抓取的文章标题'),
            ('scraped_articles.csv', '文章详细内容'),
            ('commented_articles.csv', '已评论文章记录'),
            ('articles_summary.csv', '汇总数据'),
            ('screenshots/', '截图文件夹')
        ]
        
        for filename, description in files_to_check:
            if os.path.exists(filename):
                if os.path.isdir(filename):
                    count = len(os.listdir(filename)) if os.path.isdir(filename) else 0
                    print(f"✅ {filename} - {description} ({count} 个文件)")
                else:
                    size = os.path.getsize(filename)
                    print(f"✅ {filename} - {description} ({size} 字节)")
            else:
                print(f"❌ {filename} - {description} (不存在)")
                
    def quit_application(self):
        """退出应用程序"""
        print("\n--- 退出程序 ---")
        
        if self.driver:
            try:
                print("⏳ 正在关闭WebDriver...")
                self.driver.quit()
                print("✅ WebDriver已关闭")
            except Exception as e:
                print(f"⚠️ 关闭WebDriver时出错: {e}")
                
        print("👋 程序已退出，感谢使用！")

def main():
    """主函数"""
    try:
        app = SimpleAutoYuqueGUI()
        app.show_main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 程序被用户中断，正在退出...")
    except Exception as e:
        print(f"\n❌ 程序运行出错: {e}")
        
if __name__ == "__main__":
    main()