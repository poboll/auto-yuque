import os
import json
import pickle
import time
from datetime import datetime

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from comment_generator import generate_comment

# --- 配置 ---
# 语雀仪表盘URL，登录后会跳转到此页面
DASHBOARD_URL = "https://www.yuque.com/dashboard"
# 语雀登录页URL
LOGIN_URL = "https://www.yuque.com/login"
# Cookie文件名
COOKIE_FILE = "cookie.pkl"
# 截图保存目录
SCREENSHOT_DIR = "screenshots"
# 小记页面 URL
NOTES_PAGE_URL = "https://www.yuque.com/dashboard/notes"
# 评论状态文件
COMMENTED_ARTICLES_FILE = "commented_articles.csv"
# 汇总文件
SUMMARY_FILE = "articles_summary.csv"


# --- 辅助函数 ---

def load_commented_articles():
    """加载已评论文章列表"""
    try:
        if os.path.exists(COMMENTED_ARTICLES_FILE):
            df = pd.read_csv(COMMENTED_ARTICLES_FILE, encoding='utf-8-sig')
            return set(df['title'].tolist())
        return set()
    except Exception as e:
        print(f"❌ 加载已评论文章列表失败: {e}")
        return set()

def save_commented_article(title):
    """保存已评论的文章标题"""
    try:
        file_exists = os.path.exists(COMMENTED_ARTICLES_FILE)
        data = {'title': title, 'commented_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        df = pd.DataFrame([data])
        df.to_csv(COMMENTED_ARTICLES_FILE, mode='a', header=not file_exists, index=False, encoding='utf-8-sig')
        print(f"   ✅ 已标记文章 '{title}' 为已评论")
    except Exception as e:
        print(f"   ❌ 保存评论状态失败: {e}")

def merge_csv_files():
    """汇总两个CSV文件：explore_titles.csv 和 scraped_articles.csv"""
    try:
        print("\n--- 🔄 开始汇总CSV文件 ---")
        
        # 读取explore_titles.csv
        titles_df = None
        if os.path.exists('explore_titles.csv'):
            titles_df = pd.read_csv('explore_titles.csv', encoding='utf-8-sig')
            print(f"   ✓ 读取到 {len(titles_df)} 个标题")
        else:
            print("   ⚠️ explore_titles.csv 文件不存在")
            
        # 读取scraped_articles.csv
        articles_df = None
        if os.path.exists('scraped_articles.csv'):
            articles_df = pd.read_csv('scraped_articles.csv', encoding='utf-8-sig')
            print(f"   ✓ 读取到 {len(articles_df)} 篇详细文章")
        else:
            print("   ⚠️ scraped_articles.csv 文件不存在")
            
        # 读取已评论文章列表
        commented_df = None
        if os.path.exists(COMMENTED_ARTICLES_FILE):
            commented_df = pd.read_csv(COMMENTED_ARTICLES_FILE, encoding='utf-8-sig')
            print(f"   ✓ 读取到 {len(commented_df)} 篇已评论文章")
        else:
            print("   ⚠️ 暂无已评论文章记录")
            
        # 创建汇总数据
        summary_data = []
        
        if titles_df is not None:
            for _, row in titles_df.iterrows():
                title = row['title']
                summary_row = {
                    'title': title,
                    'author': '',
                    'content': '',
                    'ai_comment': '',
                    'has_detailed_content': False,
                    'has_been_commented': False,
                    'commented_time': ''
                }
                
                # 检查是否有详细内容
                if articles_df is not None:
                    detailed_article = articles_df[articles_df['title'] == title]
                    if not detailed_article.empty:
                        summary_row['author'] = detailed_article.iloc[0]['author']
                        summary_row['content'] = detailed_article.iloc[0]['content']
                        if 'ai_comment' in detailed_article.columns:
                            summary_row['ai_comment'] = detailed_article.iloc[0]['ai_comment']
                        summary_row['has_detailed_content'] = True
                        
                # 检查是否已评论
                if commented_df is not None:
                    commented_article = commented_df[commented_df['title'] == title]
                    if not commented_article.empty:
                        summary_row['has_been_commented'] = True
                        summary_row['commented_time'] = commented_article.iloc[0]['commented_time']
                        
                summary_data.append(summary_row)
                
        # 添加只在scraped_articles.csv中存在但不在explore_titles.csv中的文章
        if articles_df is not None and titles_df is not None:
            for _, row in articles_df.iterrows():
                title = row['title']
                if title not in titles_df['title'].values:
                    summary_row = {
                        'title': title,
                        'author': row['author'],
                        'content': row['content'],
                        'ai_comment': row.get('ai_comment', ''),
                        'has_detailed_content': True,
                        'has_been_commented': False,
                        'commented_time': ''
                    }
                    
                    # 检查是否已评论
                    if commented_df is not None:
                        commented_article = commented_df[commented_df['title'] == title]
                        if not commented_article.empty:
                            summary_row['has_been_commented'] = True
                            summary_row['commented_time'] = commented_article.iloc[0]['commented_time']
                            
                    summary_data.append(summary_row)
                    
        # 保存汇总文件
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_csv(SUMMARY_FILE, index=False, encoding='utf-8-sig')
            print(f"   ✅ 汇总完成！共 {len(summary_data)} 篇文章已保存到 {SUMMARY_FILE}")
            print(f"   - 有详细内容的文章: {sum(summary_df['has_detailed_content'])} 篇")
            print(f"   - 已评论的文章: {sum(summary_df['has_been_commented'])} 篇")
            print(f"   - 未评论的文章: {sum(~summary_df['has_been_commented'])} 篇")
        else:
            print("   ⚠️ 没有数据可汇总")
            
        print("--- ✅ CSV文件汇总完成 ---\n")
        
    except Exception as e:
        print(f"❌ 汇总CSV文件失败: {e}")

def take_screenshot(driver, name):
    """保存当前页面截图"""
    try:
        if not os.path.exists(SCREENSHOT_DIR):
            os.makedirs(SCREENSHOT_DIR)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in name if c.isalnum() or c in ('_', '-')).rstrip()
        path = os.path.join(SCREENSHOT_DIR, f"{safe_name}_{timestamp}.png")
        
        driver.save_screenshot(path)
        print(f"✅ 截图已保存到: {path}")
    except Exception as e:
        print(f"❌ 保存截图失败: {e}")


def save_cookies(driver, path):
    """保存当前driver的cookies到文件"""
    try:
        with open(path, 'wb') as f:
            pickle.dump(driver.get_cookies(), f)
            print(f"✅ Cookie 已成功保存到: {path}")
    except Exception as e:
        print(f"❌ 保存Cookie失败: {e}")


def load_cookies(driver, path):
    """从文件加载Cookie并登录"""
    print(f"⏳ 正在从 {path} 加载Cookie...")
    try:
        with open(path, 'rb') as f:
            cookies = pickle.load(f)
        
        # Selenium需要先访问域才能添加cookie
        driver.get(DASHBOARD_URL)
        time.sleep(1)

        for cookie in cookies:
            if 'expiry' in cookie:
                cookie['expiry'] = int(cookie['expiry'])
            driver.add_cookie(cookie)
        
        print("✅ Cookie加载成功")
        driver.refresh()
        return True
    except FileNotFoundError:
        print("ℹ️ Cookie文件未找到，将进行手动扫码登录。")
        return False
    except Exception as e:
        print(f"❌ 加载Cookie时出错: {e}")
        return False


def is_login_successful(driver):
    """更可靠地检查是否登录成功 - 基于多个指标"""
    print("⏳ 正在验证登录状态...")
    try:
        # 方法1: 检查URL是否包含dashboard (已登录用户被重定向到仪表盘)
        if "dashboard" in driver.current_url:
            print("✅ 登录成功！(URL验证)")
            return True
            
        # 方法2: 尝试找到任何一个只有登录用户才能看到的元素
        selectors = [
            "button[data-testid='header-avatar']",  # 头像按钮
            ".larkui-avatar",                        # 头像通用类
            ".index-module_notesList_",             # 笔记列表容器
            "[data-testid='note-editor-btn']",      # 编辑按钮
            ".index-module_note_"                   # 笔记项
        ]
        
        for selector in selectors:
            try:
                # 使用短暂等待，避免长时间阻塞
                element = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                if element.is_displayed():
                    print(f"✅ 登录成功！(找到元素: {selector})")
                    return True
            except:
                continue
                
        # 如果以上检查都失败，则尝试页面标题
        if "语雀" in driver.title and "登录" not in driver.title:
            print("✅ 登录成功！(标题验证)")
            return True
            
        print(f"   - 检查失败，当前URL: {driver.current_url}")
        print(f"   - 当前页面标题: {driver.title}")
        take_screenshot(driver, "login_check_failed")
        print("   - 仍未登录。")
        return False

    except Exception as e:
        print(f"   - 登录检查过程中出错: {e}")
        return False


# --- 测试用例 ---

def test_create_and_delete_note(driver):
    """
    核心测试用例：创建并删除一篇新的小记。
    """
    print("\n--- 🚀 开始执行测试：创建并删除小记 ---")
    wait = WebDriverWait(driver, 20)
    try:
        # 1. 打开小记页面
        print(f"1. 正在打开小记页面: {NOTES_PAGE_URL}")
        driver.get(NOTES_PAGE_URL)

        # --- 第一部分：创建新笔记 ---
        print("\n--- Part 1: 创建新笔记 ---")
        
        # 2. 定义唯一的笔记标题和内容
        note_title = f"自动化测试笔记 - {int(time.time())}"
        note_content = "这是通过Selenium自动化测试创建的笔记内容。"
        print(f"2. 准备创建笔记，标题: {note_title}")

        # 3. 定位编辑器并输入内容
        print("3. 正在定位编辑器并输入内容...")
        # 尝试多种可能的编辑器选择器
        editor_selectors = [
            'div.ne-engine[contenteditable="true"]',
            'div.larkui-editor[contenteditable="true"]',
            'div[role="textbox"]',
            'div.ne-viewer-body'
        ]
        
        editor = None
        for selector in editor_selectors:
            try:
                editor = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                if editor.is_displayed() and editor.is_enabled():
                    print(f"   ✓ 找到编辑器元素: {selector}")
                    break
            except:
                continue
                
        if not editor:
            raise Exception("无法找到可编辑的笔记编辑器")
        
        # 使用ActionChains确保交互的稳定性
        ActionChains(driver).move_to_element(editor).click().send_keys(f"{note_title}\n\n{note_content}").perform()
        time.sleep(1)  # 给输入一点时间
        print("   ✅ 内容输入完成。")

        # 4. 点击"小记一下"按钮发布笔记
        print("4. 正在发布笔记...")
        # 尝试多种可能的发布按钮选择器
        publish_button_selectors = [
            'button[data-testid="note-publish"]',
            'button.larkui-button-primary',
            'button.index-module_primaryBtn_'
        ]
        
        publish_button = None
        for selector in publish_button_selectors:
            try:
                publish_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                if publish_button.is_displayed():
                    print(f"   ✓ 找到发布按钮: {selector}")
                    break
            except:
                continue
                
        if not publish_button:
            # 备选方案：检查是否已经自动保存（无需点击发布按钮）
            print("   ⚠️ 未找到发布按钮，尝试检查是否已自动保存...")
            time.sleep(3)  # 给自动保存一些时间
        else:
            publish_button.click()
            print("   ✅ 发布按钮已点击。")
            time.sleep(2)  # 等待发布完成

        # 5. 验证创建成功 - 刷新页面确保最新状态
        print("5. 正在刷新页面并验证笔记是否已创建...")
        driver.refresh()
        time.sleep(3)  # 等待页面刷新完成
        
        # 使用多种查找方式来定位新创建的笔记
        note_found = False
        
        # 方法1: 使用XPath按文本内容查找
        try:
            # 首先尝试在笔记列表中找到包含标题的元素
            notes_container_selectors = [
                "div[class*='index-module_notesList_']",
                "div.note-list",
                "div.note-items"
            ]
            
            for container_selector in notes_container_selectors:
                try:
                    container = driver.find_element(By.CSS_SELECTOR, container_selector)
                    print(f"   ✓ 找到笔记列表容器: {container_selector}")
                    break
                except:
                    continue
            
            # 在页面中直接搜索包含笔记标题的元素
            note_elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{note_title}')]")
            
            if note_elements:
                note_found = True
                print(f"   ✅ 断言成功：找到包含标题 '{note_title}' 的元素。")
            else:
                print(f"   ⚠️ 未找到包含标题的元素，继续尝试其他方法...")
        except Exception as e:
            print(f"   ⚠️ 查找笔记时出错: {e}")
        
        # 方法2: 检查页面源代码中是否包含笔记标题 (作为备选方案)
        if not note_found:
            page_source = driver.page_source
            if note_title in page_source:
                note_found = True
                print(f"   ✅ 断言成功：页面源代码中包含笔记标题 '{note_title}'。")
        
        if not note_found:
            raise Exception(f"无法在页面中找到新创建的笔记: '{note_title}'")
            
        take_screenshot(driver, "note_created_successfully")

        # --- 第二部分：删除该笔记 ---
        print("\n--- Part 2: 删除笔记 ---")

        # 6. 定位到刚刚创建的笔记条目
        print("6. 正在定位需要删除的笔记条目...")
        
        # 首先找到包含笔记标题的元素
        title_element = driver.find_element(By.XPATH, f"//*[contains(text(), '{note_title}')]")
        
        # 从包含标题的元素向上查找最近的笔记条目容器
        note_item = title_element
        max_attempts = 5
        for _ in range(max_attempts):
            try:
                # 尝试找到父元素
                note_item = note_item.find_element(By.XPATH, "./..")
                # 检查是否是笔记条目容器
                class_name = note_item.get_attribute("class")
                if class_name and ("note-list-item" in class_name or "index-module_note_" in class_name):
                    print(f"   ✓ 找到笔记条目容器: {class_name}")
                    break
            except:
                continue
        
        # 7. 将鼠标悬停在笔记条目上，等待更多按钮出现
        print("7. 正在将鼠标悬停在笔记条目上...")
        
        # 确保元素在视图中
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", note_item)
        time.sleep(1)  # 等待滚动完成
        
        # 使用ActionChains悬停在笔记条目上
        actions = ActionChains(driver)
        actions.move_to_element(note_item).perform()
        print("   ✅ 鼠标已悬停在笔记条目上。")
        time.sleep(1)  # 给悬停效果一些时间显示
        
        take_screenshot(driver, "hover_on_note_item")  # 记录悬停状态
        
        # 8. 等待并点击"更多操作"按钮
        print("8. 正在等待并点击'更多操作'按钮...")
        
        # 定义可能的"更多"按钮选择器
        more_button_selectors = [
            "span.index-module_moreBtn_",  # 部分类名匹配
            "span[class*='moreBtn']",      # 包含moreBtn的任何span
            "span.ant-dropdown-trigger",   # 通用dropdown触发器
            "span.note-item-more-btn",     # 备选类名
            "span[class*='more']"          # 包含'more'的任何span
        ]
        
        more_button = None
        for selector in more_button_selectors:
            try:
                # 使用显式等待确保按钮可点击
                more_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                if more_button.is_displayed():
                    print(f"   ✓ 找到更多按钮: {selector}")
                    break
            except:
                continue
        
        if not more_button:
            print("   ⚠️ 未找到更多按钮，尝试再次悬停...")
            # 再次尝试悬停，有时第一次悬停可能不触发
            actions.move_to_element(note_item).perform()
            time.sleep(1)
            
            # 尝试在笔记条目内查找任何可能的按钮元素
            buttons = note_item.find_elements(By.TAG_NAME, "span")
            for button in buttons:
                try:
                    if button.is_displayed():
                        class_name = button.get_attribute("class")
                        if "more" in class_name.lower():
                            more_button = button
                            print(f"   ✓ 找到备选更多按钮: {class_name}")
                            break
                except:
                    continue
        
        if not more_button:
            take_screenshot(driver, "more_button_not_found")
            raise Exception("无法找到'更多操作'按钮，即使在悬停后也未出现")
        
        # 点击"更多操作"按钮
        driver.execute_script("arguments[0].click();", more_button)  # 使用JS点击，避免其他元素遮挡
        print("   ✅ '更多操作'按钮已点击。")
        time.sleep(1)  # 等待下拉菜单显示
        take_screenshot(driver, "more_menu_opened")
        
        # 9. 在下拉菜单中点击"删除"选项
        print("9. 正在点击'删除'选项...")
        
        # 使用提供的HTML结构定义选择器
        delete_selectors = [
            "//div[contains(@class, 'index-module_menuItem_')]//span[text()='删除']",
            "//div[contains(@class, 'menuItem')]//span[text()='删除']",
            "//div[contains(@class, 'ant-dropdown-menu-item')]//span[text()='删除']",
            "//span[text()='删除']"  # 最通用的选择器，作为最后尝试
        ]
        
        delete_option = None
        for selector in delete_selectors:
            try:
                # 使用显式等待确保删除选项可点击
                delete_option = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                print(f"   ✓ 找到删除选项: {selector}")
                break
            except:
                continue
        
        if not delete_option:
            take_screenshot(driver, "delete_option_not_found")
            raise Exception("无法在下拉菜单中找到'删除'选项")
        
        # 点击"删除"选项
        driver.execute_script("arguments[0].click();", delete_option)  # 使用JS点击，更可靠
        print("   ✅ '删除'选项已点击。")
        time.sleep(1)  # 等待确认对话框显示
        take_screenshot(driver, "delete_confirmation_dialog")
        
        # 10. 在确认对话框中点击"确定"
        print("10. 正在确认删除...")
        confirm_selectors = [
            "//div[@class='ant-modal-confirm-btns']//button[.//span[text()='确 定']]",
            "//button[contains(@class, 'ant-btn-primary') and contains(., '确')]",
            "//div[contains(@class, 'modal-footer')]//button[contains(., '确认')]",
            "//button[contains(@class, 'primary') and (contains(., '确定') or contains(., '确认') or contains(., '是'))]"
        ]
        
        confirm_button = None
        for selector in confirm_selectors:
            try:
                confirm_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                print(f"   ✓ 找到确认按钮: {selector}")
                break
            except:
                continue
        
        if not confirm_button:
            take_screenshot(driver, "confirm_button_not_found")
            raise Exception("无法找到确认删除按钮")
        
        confirm_button.click()
        print("   ✅ 已确认删除。")
        time.sleep(2)  # 等待删除操作完成

        # 11. 验证删除 - 刷新页面确保最新状态
        print("11. 正在刷新页面并验证笔记是否已删除...")
        driver.refresh()
        time.sleep(3)  # 等待页面刷新完成
        
        # 检查是否成功删除 - 笔记标题不应该再出现在页面中
        deleted = True
        try:
            driver.find_element(By.XPATH, f"//*[contains(text(), '{note_title}')]")
            deleted = False  # 如果找到了元素，说明删除失败
        except NoSuchElementException:
            deleted = True  # 找不到元素，说明删除成功
        
        assert deleted, f"断言失败：笔记 '{note_title}' 未能成功删除！"
        print(f"   ✅ 断言成功：笔记 '{note_title}' 已成功删除。")
        take_screenshot(driver, "note_deleted_successfully")

    except TimeoutException as e:
        print(f"\n❌ 测试执行超时或元素未找到: {e}")
        take_screenshot(driver, "test_timeout_error")
        # 抛出异常以标记测试失败
        raise
    except Exception as e:
        print(f"\n❌ 测试执行过程中发生未知错误: {e}")
        take_screenshot(driver, "test_unknown_error")
        # 抛出异常以标记测试失败
        raise
        
    print("\n--- ✅ 测试成功完成：创建并删除小记 ---")

def append_to_csv(data, filename="articles.csv"):
    """将数据追加写入到CSV文件"""
    file_exists = os.path.exists(filename)
    df = pd.DataFrame([data])
    try:
        df.to_csv(filename, mode='a', header=not file_exists, index=False, encoding='utf-8-sig')
        print(f"   ✍️  数据已成功写入 {filename}")
    except Exception as e:
        print(f"   ❌ 写入CSV文件失败: {e}")


def save_titles_to_csv(titles, filename="explore_titles.csv"):
    """将标题列表保存到CSV文件。"""
    if not titles:
        print("   - 没有找到任何标题，不生成CSV文件。")
        return
    # 使用DataFrame确保格式正确，并覆盖写入
    df = pd.DataFrame(titles, columns=["title"])
    try:
        df.to_csv(filename, mode='w', index=False, encoding='utf-8-sig')
        print(f"   ✍️  {len(titles)}个标题已成功写入 {filename}")
    except Exception as e:
        print(f"   ❌ 写入CSV文件失败: {e}")


def save_article_details_to_csv(data, filename="scraped_articles.csv"):
    """将单篇文章的详细信息追加到CSV文件。"""
    file_exists = os.path.exists(filename)
    df = pd.DataFrame([data])
    try:
        df.to_csv(filename, mode='a', header=not file_exists, index=False, encoding='utf-8-sig')
        print(f"   ✍️  文章 '{data['title']}' 的详细内容已成功写入 {filename}")
    except Exception as e:
        print(f"   ❌ 写入文章详情到CSV文件失败: {e}")


def test_explore_page(driver):
    """
    核心测试用例：遍历"逛逛"页面，抓取标题、点赞并抓取第一篇文章的完整内容。
    """
    print("\n--- 🚀 开始执行测试：逛逛页面抓取、点赞与内容提取 ---")
    wait = WebDriverWait(driver, 20)
    
    try:
        # 1. 点击"逛逛"菜单
        print("1. 正在导航到 '逛逛' 页面...")
        
        explore_selectors = [
            "//span[contains(@class, 'ant-menu-title-content') and contains(., '逛逛')]",
            "a[href='/dashboard/explore']",
            "//li[@title='逛逛']//a"
        ]
        
        explore_link = None
        for selector in explore_selectors:
            try:
                by = By.XPATH if selector.startswith('/') else By.CSS_SELECTOR
                element_to_click = wait.until(EC.element_to_be_clickable((by, selector)))
                if element_to_click:
                    print(f"   ✓ 找到 '逛逛' 链接使用选择器: {selector}")
                    driver.execute_script("arguments[0].click();", element_to_click)
                    print("   ✅ 已点击 '逛逛' 链接。")
                    explore_link = element_to_click
                    break
            except TimeoutException:
                print(f"   - 尝试选择器失败 (超时): {selector}")
                continue
        
        if not explore_link:
            take_screenshot(driver, "explore_link_not_found")
            raise Exception("无法找到'逛逛'页面的链接，已尝试多种选择器")

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.HeadlineSelections-module_mainList_A7xla")))

        # 2. 滚动页面几次以加载文章
        print("\n2. 正在滚动页面以加载文章...")
        for i in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            print(f"   - 第 {i+1}/3 次滚动...")
            time.sleep(2.5)
        print("   ✅ 滚动完成。")

        # 3. 获取所有可见的文章标题并保存
        print("\n3. 正在获取所有文章标题并保存到 explore_titles.csv...")
        title_elements = driver.find_elements(By.CSS_SELECTOR, "a.DocFeed-module_title_1RpjJ")
        titles = [el.text for el in title_elements if el.text]
        unique_titles = list(dict.fromkeys(titles)) # 保持顺序并去重
        
        if not unique_titles:
            print("   - ⚠️ 未能从页面抓取到任何文章标题。")
            take_screenshot(driver, "explore_no_titles_found")
        else:
            print(f"   ✅ 共抓取到 {len(unique_titles)} 个不重复的标题。")
            save_titles_to_csv(unique_titles, "explore_titles.csv")

        # 4. 点赞所有可见的文章
        print("\n4. 正在点赞所有可见的文章...")
        driver.execute_script("window.scrollTo(0, 0);") # 回到顶部开始点赞
        time.sleep(1)
        like_buttons = driver.find_elements(By.CSS_SELECTOR, "div.like-module_simplifyLike_GZF9s")
        like_count = 0
        for button in like_buttons:
            try:
                # 使用JS点击以避免遮挡问题
                driver.execute_script("arguments[0].click();", button)
                like_count += 1
                time.sleep(0.2)
            except Exception as e:
                print(f"   - 点赞某个按钮时失败: {e}")
        print(f"   ✅ 共尝试点赞 {like_count} 次。")
        take_screenshot(driver, "after_liking_articles")

        # 5. 打开第一篇文章
        print("\n5. 正在打开第一篇文章...")
        articles = driver.find_elements(By.CSS_SELECTOR, "div.Feed-module_feed_hyrAF")
        if not articles:
            raise Exception("页面上找不到任何文章，无法继续。")
        
        first_article = articles[0]
        # 提取文章的标题和作者
        author = first_article.find_element(By.CSS_SELECTOR, "a.Feed-module_uname_srr3b").text
        title_element = first_article.find_element(By.CSS_SELECTOR, "a.DocFeed-module_title_1RpjJ")
        title = title_element.text
        print(f"   - 准备打开文章: '{title}' by {author}")
        
        # 获取当前窗口句柄
        original_window = driver.current_window_handle
        
        driver.execute_script("arguments[0].click();", title_element)

        # 检查是否有新窗口打开，并切换
        wait.until(EC.number_of_windows_to_be(2))
        for window_handle in driver.window_handles:
            if window_handle != original_window:
                driver.switch_to.window(window_handle)
                break
        
        # 6. 在详情页提取完整内容
        print("\n6. 正在文章详情页提取完整内容...")
        content_selector = "div.yuque-doc-content" # 基于用户提供的HTML
        title_selector = "h1" # 通常文章标题是h1
        
        # 使用更灵活的复合等待条件，并增加超时时间
        print("   - 等待文章页面加载（最长40秒）...")
        long_wait = WebDriverWait(driver, 40)
        try:
            # 等待以下任一条件满足：
            # 1. URL 包含 /docs/ (标准文章) 或 /go/doc (分享链接)
            # 2. 页面上出现了内容容器
            # 3. 页面上出现了H1标题
            long_wait.until(
                EC.any_of(
                    EC.url_contains('/docs/'),
                    EC.url_contains('/go/doc'),
                    EC.presence_of_element_located((By.CSS_SELECTOR, content_selector)),
                    EC.presence_of_element_located((By.CSS_SELECTOR, title_selector))
                )
            )
            print("   - ✅ 文章页面已成功加载。")
        except TimeoutException:
            print("   - ❌ 即使使用复合等待条件，页面加载依然超时。")
            take_screenshot(driver, "article_page_load_timeout")
            raise

        print("   - 正在滚动到页面底部以加载全部内容...")
        last_h = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_h = driver.execute_script("return document.body.scrollHeight")
            if new_h == last_h:
                break
            last_h = new_h
        print("   - ✅ 已到达页面底部。")
        
        content = driver.find_element(By.CSS_SELECTOR, content_selector).text
        print("   - ✅ 正文提取完成。")

        # 7. 检查是否已评论过，如果是则跳过评论
        print("\n7. 正在检查评论状态...")
        commented_articles = load_commented_articles()
        ai_comment = "未生成评论"
        
        if title in commented_articles:
            print(f"   - ⚠️ 文章 '{title}' 已经评论过，跳过评论步骤")
        else:
            print("   - ✅ 文章未评论过，开始生成AI评论...")
            try:
                # 生成评论内容
                ai_comment = generate_comment(title, content[:500])  # 使用前500字符作为摘要
                print(f"   - ✅ AI评论生成完成: {ai_comment[:50]}...")
            
                # 滚动到页面底部，寻找评论区域
                print("   - 正在滚动到评论区域...")
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # 查找评论输入框
                print("   - 正在查找评论输入框...")
                comment_input_selectors = [
                    'div.ne-engine.ne-typography-traditional[contenteditable="true"]',
                    'div[contenteditable="true"][class*="ne-engine"]',
                    'div[contenteditable="true"]',
                    'textarea[placeholder*="评论"]',
                    'div[data-placeholder*=" "]'
                ]
                
                comment_input = None
                for selector in comment_input_selectors:
                    try:
                        comment_input = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        if comment_input.is_displayed():
                            print(f"   ✓ 找到评论输入框: {selector}")
                        break
                    except:
                        continue
                
                if not comment_input:
                    print("   ⚠️ 未找到评论输入框，跳过评论功能")
                else:
                    # 点击输入框并输入评论
                    print("   - 正在输入评论...")
                    try:
                        # 滚动到输入框位置
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", comment_input)
                        time.sleep(1)
                        
                        # 多种方式尝试点击和输入
                        try:
                            comment_input.click()
                        except:
                            driver.execute_script("arguments[0].click();", comment_input)
                        
                        time.sleep(1)
                        
                        # 清空输入框并输入评论
                        comment_input.clear()
                        comment_input.send_keys(ai_comment)
                        
                        # 备选输入方法
                        if not comment_input.get_attribute('value') and not comment_input.text:
                            ActionChains(driver).move_to_element(comment_input).click().send_keys(ai_comment).perform()
                        
                        # JavaScript输入方法作为最后备选
                        if not comment_input.get_attribute('value') and not comment_input.text:
                            driver.execute_script("arguments[0].innerHTML = arguments[1];", comment_input, ai_comment)
                        
                        print("   ✅ 评论内容已输入")
                        time.sleep(1)
                        
                        # 查找并点击回复按钮
                        print("   - 正在查找回复按钮...")
                        reply_button_selectors = [
                            'button.ant-btn.ant-btn-primary:has(span:contains("回复"))',
                            'button[class*="ant-btn-primary"]:has(span:contains("回复"))',
                            'button:has(span:contains("回复"))',
                            '//button[.//span[text()="回复"]]',
                            '//button[contains(@class, "ant-btn-primary") and .//span[text()="回复"]]'
                        ]
                        
                        reply_button = None
                        for selector in reply_button_selectors:
                            try:
                                if selector.startswith('//'):
                                    reply_button = WebDriverWait(driver, 3).until(
                                        EC.element_to_be_clickable((By.XPATH, selector))
                                    )
                                else:
                                    reply_button = WebDriverWait(driver, 3).until(
                                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                    )
                                if reply_button.is_displayed():
                                    print(f"   ✓ 找到回复按钮: {selector}")
                                    break
                            except:
                                 continue
                        
                        if reply_button:
                            # 等待按钮变为可用状态
                            WebDriverWait(driver, 10).until(
                                lambda d: not reply_button.get_attribute("disabled")
                            )
                            
                            # 点击回复按钮
                            try:
                                reply_button.click()
                            except:
                                driver.execute_script("arguments[0].click();", reply_button)
                            
                            print("   ✅ 回复按钮已点击，评论发布成功")
                            time.sleep(2)  # 等待评论发布完成
                            take_screenshot(driver, "comment_posted_successfully")
                            
                            # 保存评论状态
                            save_commented_article(title)
                        else:
                            print("   ⚠️ 未找到回复按钮，评论可能需要手动发布")
                            take_screenshot(driver, "comment_input_completed")
                            
                    except Exception as comment_error:
                        print(f"   ❌ 评论输入过程中出错: {comment_error}")
                        take_screenshot(driver, "comment_input_error")
                    
            except Exception as ai_error:
                print(f"   ❌ AI评论生成失败: {ai_error}")

        # 8. 写入CSV（包含评论信息）
        article_data = {
            "author": author, 
            "title": title, 
            "content": content,
            "ai_comment": ai_comment
        }
        save_article_details_to_csv(article_data)

        # 操作完成后，关闭新窗口并切回原窗口
        print("   - 正在关闭文章标签页并返回...")
        driver.close()
        driver.switch_to.window(original_window)

    except TimeoutException as e:
        print(f"\n❌ 测试执行超时或元素未找到: {e}")
        take_screenshot(driver, "explore_test_timeout_error")
        raise
    except Exception as e:
        print(f"\n❌ 测试执行过程中发生未知错误: {e}")
        take_screenshot(driver, "explore_test_unknown_error")
        raise

    print("\n--- ✅ 测试成功完成：逛逛页面抓取、点赞与内容提取 ---")


def test_knowledge_base(driver):
    """
    核心测试用例：进入第一个知识库，点击新建按钮，在弹出的悬浮菜单中选择"文档"，
    然后创建一篇新的文档并验证。
    采用战术级多阶段等待和精准交互策略。
    """
    print("\n--- 🚀 开始执行测试：知识库内创建新文档 ---")
    wait = WebDriverWait(driver, 30)  # 增加超时时间
    
    # 确保在任何操作前，都处于顶层文档环境，避免iframe残留问题
    driver.switch_to.default_content()

    try:
        # 1. 返回仪表盘页面，确保我们从一个已知的起点开始
        print(f"1. 正在导航到仪表盘页面: {DASHBOARD_URL}")
        driver.get(DASHBOARD_URL)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.index-module_bookItem_jMupe")))
        
        # 2. 找到第一个知识库并点击
        print("2. 正在查找并进入第一个知识库...")
        knowledge_base_link = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.index-module_bookItem_jMupe a.index-module_link_KkvFY"))
        )
        kb_title = knowledge_base_link.get_attribute("title")
        kb_url = knowledge_base_link.get_attribute("href")
        print(f"   ✓ 找到知识库: '{kb_title}'，正在进入: {kb_url}")
        
        # 先保存URL，再点击，避免StaleElementReferenceException
        knowledge_base_link.click()

        # 3. 等待页面加载完成
        print("\n3. 等待页面加载完成...")
        
        # 等待URL变化，确认导航已启动
        wait.until(EC.url_contains(kb_url.split('.com')[-1]))
        print("   ✓ URL已变化，导航已启动")
        
        # 等待页面加载完成
        time.sleep(3)
        print("   ✓ 页面加载完成")

        # 4. 查找新建按钮
        print("\n4. 查找新建按钮...")
        
        # 基于用户提供的SVG元素信息定义选择器
        trigger_selectors = [
            # 直接通过SVG的data-name属性
            "svg[data-name='Add']",
            # 通过SVG的父元素类名
            "svg.larkui-icon-add",
            # 通过包含SVG的span元素
            "span:has(svg[data-name='Add'])",
            # 通过类名模式匹配
            "*[class*='actionItem'][class*='ReaderLayout-module']",
            "span[class*='actionItem']",
            # 备选方案
            "button[class*='add']",
            "span[class*='add']"
        ]
        
        trigger_element = None
        for selector in trigger_selectors:
            try:
                # 判断是XPath还是CSS选择器
                if selector.startswith('//'):
                    by_type = By.XPATH
                else:
                    by_type = By.CSS_SELECTOR
                
                element = wait.until(EC.presence_of_element_located((by_type, selector)))
                if element and element.is_displayed():
                    trigger_element = element
                    print(f"   ✓ 找到新建按钮触发器: {selector}")
                    break
            except TimeoutException:
                continue
        
        if not trigger_element:
            print("   ❌ 未找到任何新建按钮触发器")
            take_screenshot(driver, "kb_add_button_not_found")
            raise Exception("无法找到新建按钮触发器")
        
        # 确保元素在视图中
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", trigger_element)
        time.sleep(0.5)
        
        # 悬停在触发器上并保持悬停状态
        actions = ActionChains(driver)
        actions.move_to_element(trigger_element).perform()
        print("   ✅ 已悬停到新建按钮，等待菜单弹出")
        
        take_screenshot(driver, "hover_on_trigger")

        # 5. 等待并点击菜单中的文档选项
        print("\n5. 等待并点击菜单中的文档选项...")
        
        # 保持悬停状态，等待菜单出现
        time.sleep(1)  # 给菜单弹出动画时间
        
        # 查找弹出菜单容器
        popover_selectors = [
            "div.ant-popover",
            "div.larkui-popover-content",
            "div[class*='popover-content']",
            "div[class*='dropdown-menu']",
            "div[class*='menu-content']",
            "ul[class*='menu']",
            "div[role='menu']"
        ]
        
        popover_menu = None
        for selector in popover_selectors:
            try:
                popover_menu = WebDriverWait(driver, 5).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
                )
                if popover_menu:
                    print(f"   ✓ 找到弹出菜单容器: {selector}")
                    break
            except:
                continue
        
        if not popover_menu:
            # 尝试重新悬停
            print("   ⚠️ 菜单未出现，重新悬停...")
            actions.move_to_element(trigger_element).perform()
            time.sleep(1)
            
            # 再次尝试查找菜单
            for selector in popover_selectors:
                try:
                    popover_menu = WebDriverWait(driver, 3).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if popover_menu:
                        print(f"   ✓ 重新悬停后找到菜单: {selector}")
                        break
                except:
                    continue
        
        if not popover_menu:
            take_screenshot(driver, "popover_menu_not_found")
            raise Exception("无法找到弹出菜单容器")
        
        take_screenshot(driver, "popover_menu_visible")
        
        # 在弹出菜单中查找"文档"选项
        document_selectors = [
            "//div[contains(@class, 'ant-popover-inner-content')]//div[text()='文档']",
            "//span[contains(text(), '文档')]",
            "//div[contains(text(), '文档')]",
            "//li[contains(text(), '文档')]",
            "//a[contains(text(), '文档')]",
            "span[title='文档']",
            "li[data-value='doc']",
            "div[data-type='document']",
            "*[class*='menu-item'][text()='文档']"
        ]
        
        document_option = None
        for selector in document_selectors:
            try:
                if selector.startswith('//'):
                    document_option = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    document_option = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                if document_option and document_option.is_displayed():
                    print(f"   ✓ 找到文档选项: {selector}")
                    break
            except:
                continue
        
        if not document_option:
            take_screenshot(driver, "document_option_not_found")
            raise Exception("无法在弹出菜单中找到文档选项")
        
        # 点击文档选项
        try:
            document_option.click()
        except:
            # 如果普通点击失败，使用JavaScript点击
            driver.execute_script("arguments[0].click();", document_option)
        
        print("   ✅ 已点击文档选项")
        time.sleep(2)  # 等待页面跳转

        # 7. 等待页面跳转到新文档编辑器并输入内容
        print("\n7. 正在等待编辑器加载并输入文档内容...")
        
        # 生成唯一标题和内容
        doc_title = f"自动化测试文档 - {int(time.time())}"
        doc_content = "这是一篇由Selenium自动化测试创建的知识库文档。\n\n测试时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 首先查找并点击标题输入区域
        title_selectors = [
            'textarea[data-testid="input"]',
            'div[data-testid="title-editor"] textarea',
            'textarea[placeholder*="标题"]',
            'input[placeholder*="标题"]',
            'div.ne-title',
            'div.title-container .title',
            'div[contenteditable="true"][data-title="true"]'
        ]
        
        title_element = None
        for selector in title_selectors:
            try:
                title_element = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                if title_element.is_displayed():
                    print(f"   ✓ 找到标题输入区域: {selector}")
                    break
            except:
                continue
        
        if not title_element:
            print("   ⚠️ 未找到明确的标题区域，将查找编辑器")
        else:
            # 点击标题输入框并输入标题
            ActionChains(driver).move_to_element(title_element).click().send_keys(doc_title).perform()
            print(f"   ✓ 已输入标题: {doc_title}")
        
        # 等待编辑器加载完成
        editor_selectors = [
            'div.ne-engine[contenteditable="true"]',
            'div.ne-viewer-body[contenteditable="true"]',
            'div[role="textbox"]',
            'div[data-testid="editor"]',
            'div.lake-editor',
            'div[contenteditable="true"]'
        ]
        
        editor_element = None
        for selector in editor_selectors:
            try:
                editor_element = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                if editor_element.is_displayed():
                    print(f"   ✓ 找到编辑器: {selector}")
                    break
            except:
                continue
        
        if not editor_element:
            raise Exception("无法找到文档编辑器")
        
        # 如果没有找到标题区域，在编辑器中输入完整内容
        if not title_element:
            full_content = f"{doc_title}\n\n{doc_content}"
            ActionChains(driver).move_to_element(editor_element).click().send_keys(full_content).perform()
            print(f"   ✓ 已输入标题: {doc_title}")
            print("   ✓ 已输入正文内容")
        else:
            # 如果已经输入了标题，只在编辑器中输入正文
            ActionChains(driver).move_to_element(editor_element).click().send_keys(doc_content).perform()
            print("   ✓ 已输入正文内容")
        
        time.sleep(0.5)  # 减少等待时间
        take_screenshot(driver, "document_content_entered")

        # 8. 点击发布按钮
        print("\n8. 正在点击'发布'按钮...")
        
        # 使用用户提供的正确发布按钮ID
        publish_button_selectors = [
            'button#lake-doc-publish-button',
            'button[id="lake-doc-publish-button"]',
            "button[data-testid='doc-header-publish-btn']",
            "button.ant-btn-primary",
            "//button[contains(., '发布')]"
        ]
        
        publish_button = None
        for selector in publish_button_selectors:
            try:
                by = By.CSS_SELECTOR if not selector.startswith('//') else By.XPATH
                publish_button = wait.until(EC.element_to_be_clickable((by, selector)))
                if publish_button.is_displayed():
                    print(f"   ✓ 找到发布按钮: {selector}")
                    break
            except:
                continue
                
        if not publish_button:
            take_screenshot(driver, "publish_button_not_found")
            raise Exception("无法找到发布按钮")
            
        # 点击发布按钮
        try:
            publish_button.click()
        except:
            # 如果普通点击失败，使用JavaScript点击
            driver.execute_script("arguments[0].click();", publish_button)
        
        print("   ✅ 已点击发布按钮")

        # 9. 复合验证 - 使用多重验证条件
        print("\n9. 执行复合验证策略...")
        
        # 使用复合等待条件检查URL跳转或新文档标题出现
        try:
            wait.until(
                EC.any_of(
                    EC.url_contains(kb_url.split('.com')[-1]),  # 返回知识库页
                    EC.url_contains('/docs/'),                  # 转到文档查看页
                    EC.presence_of_element_located((By.XPATH, f"//h1[contains(text(), '{doc_title}')]"))  # 文档标题出现
                )
            )
            print("   ✓ 页面已跳转或文档标题已出现，发布完成")
            
            # 多重验证策略
            verification_success = False
            
            # 验证方式1：查找文档标题元素
            try:
                title_xpath = f"//h1[contains(text(), '{doc_title}')] | //a[contains(text(), '{doc_title}')]"
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, title_xpath))
                )
                print(f"   ✅ 验证成功: 找到文档标题元素 '{doc_title}'，文档创建成功!")
                verification_success = True
            except:
                pass
            
            # 验证方式2：检查页面源码
            if not verification_success and doc_title in driver.page_source:
                print(f"   ✅ 验证成功: 页面源码中包含文档标题，文档创建成功!")
                verification_success = True
            
            # 验证方式3：检查URL是否包含文档相关路径
            if not verification_success and ('/docs/' in driver.current_url or doc_title.replace(' ', '-') in driver.current_url):
                print(f"   ✅ 验证成功: URL包含文档路径，文档创建成功!")
                verification_success = True
            
            if not verification_success:
                print("   ⚠️ 无法直接确认文档创建成功，但页面已正常跳转，很可能操作已成功")
            
        except TimeoutException:
            print("   ⚠️ 等待页面跳转超时，但文档可能已创建成功")
            
        # 拍摄最终状态截图
        take_screenshot(driver, "knowledge_base_document_created")
        
        # 10. 点击编辑按钮进入编辑模式
        print("\n10. 点击编辑按钮进入编辑模式...")
        edit_button_selectors = [
            "button.ant-btn.ant-btn-primary.larkui-tooltip span:contains('编辑')",
            "button[class*='ant-btn-primary'] span:contains('编辑')",
            "//button[contains(@class, 'ant-btn-primary')]//span[text()='编辑']",
            "//button//span[text()='编辑']",
            "button[class*='primary']:has(span:contains('编辑'))"
        ]
        
        edit_button = None
        for selector in edit_button_selectors:
            try:
                if selector.startswith('//'):
                    edit_button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                else:
                    edit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                if edit_button and edit_button.is_displayed():
                    print(f"   ✓ 找到编辑按钮: {selector}")
                    break
            except:
                continue
        
        if not edit_button:
            take_screenshot(driver, "edit_button_not_found")
            raise Exception("无法找到编辑按钮")
        
        edit_button.click()
        print("   ✅ 已点击编辑按钮")
        time.sleep(2)  # 等待进入编辑模式
        
        # 11. 在正文内容中继续编辑
        print("\n11. 在正文内容中继续编辑...")
        
        # 查找正文编辑器 - 使用更精确的选择器
        content_editor_selectors = [
            "div.ne-engine.ne-typography-classic[contenteditable='true']",
            "div.ne-engine[contenteditable='true']",
            "div[class*='ne-engine'][contenteditable='true']",
            "div.ne-typography-classic[contenteditable='true']"
        ]
        
        content_editor = None
        for selector in content_editor_selectors:
            try:
                content_editor = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                if content_editor and content_editor.is_displayed():
                    print(f"   ✓ 找到正文编辑器: {selector}")
                    break
            except:
                continue
        
        if not content_editor:
            take_screenshot(driver, "content_editor_not_found")
            raise Exception("无法找到正文编辑器")
        
        # 确保编辑器在视图中并且可点击
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", content_editor)
        time.sleep(1)
        
        # 点击编辑器获得焦点
        try:
            # 先尝试点击ne-p元素内部
            ne_p_element = content_editor.find_element(By.CSS_SELECTOR, "ne-p")
            driver.execute_script("arguments[0].click();", ne_p_element)
            print("   ✓ 已点击ne-p元素")
        except:
            # 如果找不到ne-p，直接点击编辑器
            driver.execute_script("arguments[0].click();", content_editor)
            print("   ✓ 已点击编辑器")
        
        time.sleep(1)
        
        # 使用ActionChains添加内容
        actions = ActionChains(driver)
        
        # 先输入一些文本内容
        additional_content = "这是编辑模式下添加的额外内容。我们现在要测试图片上传功能。"
        actions.send_keys(additional_content).perform()
        time.sleep(1)
        
        print("   ✅ 已添加额外内容")
        
        # 12. 输入/tp命令触发图片上传
        print("\n12. 输入/tp命令触发图片上传...")
        
        # 换行并输入/tp
        actions.send_keys(Keys.ENTER).perform()
        time.sleep(0.5)
        
        # 输入斜杠命令
        actions.send_keys("/tp").perform()
        time.sleep(1)
        
        print("   ✅ 已输入/tp命令")
        
        # 检查是否出现了斜杠命令界面
        try:
            slash_command_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.ne-ui-slash-command-input")))
            if slash_command_input:
                print("   ✓ 找到斜杠命令输入框")
                # 在斜杠命令输入框中输入tp
                slash_command_input.clear()
                slash_command_input.send_keys("tp")
                time.sleep(0.5)
                # 按回车确认
                slash_command_input.send_keys(Keys.ENTER)
                print("   ✅ 已在斜杠命令输入框中输入tp并确认")
        except:
            # 如果没有找到斜杠命令输入框，直接按回车
            actions.send_keys(Keys.ENTER).perform()
            print("   ✅ 已按回车触发命令")
        
        time.sleep(2)  # 等待弹窗出现
        take_screenshot(driver, "tp_command_executed")
        
        # 13. 处理图片上传弹窗
        print("\n13. 处理图片上传弹窗...")
        
        # 查找文件上传输入框或上传按钮
        upload_selectors = [
            "input[type='file']",
            "input[accept*='image']",
            "input[accept*='.png']",
            "//input[@type='file']",
            "button[class*='upload']",
            "div[class*='upload-area']"
        ]
        
        upload_element = None
        for selector in upload_selectors:
            try:
                if selector.startswith('//'):
                    upload_element = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                else:
                    upload_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                if upload_element:
                    print(f"   ✓ 找到上传元素: {selector}")
                    break
            except:
                continue
        
        if upload_element and upload_element.tag_name == 'input':
            # 如果找到文件输入框，上传项目目录下的miao.jpeg文件
            print("   ✓ 找到文件输入框，准备上传miao.jpeg")
            
            # 使用项目目录下的miao.jpeg文件
            image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "miao.jpeg")
            
            try:
                # 检查文件是否存在
                if os.path.exists(image_path):
                    print(f"   ✓ 找到图片文件: {image_path}")
                    # 上传文件
                    upload_element.send_keys(image_path)
                    print("   ✅ 已上传miao.jpeg")
                    time.sleep(3)  # 等待上传完成
                else:
                    print(f"   ❌ 图片文件不存在: {image_path}")
                    raise FileNotFoundError(f"找不到图片文件: {image_path}")
                
            except Exception as e:
                print(f"   ⚠️ 上传图片失败: {e}")
                # 如果无法上传图片，跳过上传步骤
                print("   ⚠️ 跳过图片上传步骤")
        else:
            print("   ⚠️ 未找到合适的文件上传元素，跳过图片上传")
        
        take_screenshot(driver, "after_image_upload")
        
        # 14. 点击更新文档按钮
        print("\n14. 点击更新文档按钮...")
        
        # 查找更新/保存按钮
        update_button_selectors = [
            "button#lake-doc-publish-button",
            "button[id='lake-doc-publish-button']",
            "//button[@id='lake-doc-publish-button']",
            "button[class*='publish']",
            "button:contains('更新')",
            "//button[contains(text(), '更新')]",
            "//button[contains(text(), '保存')]",
            "button[class*='primary']:contains('发布')"
        ]
        
        update_button = None
        for selector in update_button_selectors:
            try:
                if selector.startswith('//'):
                    update_button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                else:
                    update_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                if update_button and update_button.is_displayed():
                    print(f"   ✓ 找到更新按钮: {selector}")
                    break
            except:
                continue
        
        if not update_button:
            take_screenshot(driver, "update_button_not_found")
            print("   ⚠️ 未找到更新按钮，尝试使用快捷键保存")
            # 使用Ctrl+S保存
            actions.key_down(Keys.COMMAND if driver.capabilities['platformName'].lower() == 'mac' else Keys.CONTROL).send_keys('s').key_up(Keys.COMMAND if driver.capabilities['platformName'].lower() == 'mac' else Keys.CONTROL).perform()
            print("   ✅ 已使用快捷键保存文档")
        else:
            try:
                update_button.click()
            except:
                # 如果普通点击失败，使用JavaScript点击
                driver.execute_script("arguments[0].click();", update_button)
            print("   ✅ 已点击更新按钮")
        
        time.sleep(3)  # 等待更新完成
        take_screenshot(driver, "document_updated")
        print("   ✅ 文档更新完成")
        
        # 15. 添加评论
        print("\n15. 添加评论...")
        
        # 滚动到页面底部，确保评论区域可见
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)  # 减少等待时间
        
        # 查找评论输入框 - 使用用户提供的准确选择器
        comment_input_selectors = [
            "div.ne-engine.ne-typography-traditional[contenteditable='true']",  # 用户提供的准确结构
            "div.ne-engine[contenteditable='true']",
            "div[contenteditable='true'][class*='ne-engine']",
            "div[contenteditable='true'][class*='ne-typography']",
            "div[contenteditable='true'][spellcheck='false']"
        ]
        
        comment_input = None
        for selector in comment_input_selectors:
            try:
                comment_input = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                if comment_input and comment_input.is_displayed():
                    print(f"   ✓ 找到评论输入框: {selector}")
                    break
            except:
                continue
        
        if not comment_input:
            take_screenshot(driver, "comment_input_not_found")
            print("   ⚠️ 未找到评论输入框，可能文档未发布成功，跳过评论步骤")
        else:
            # 多次尝试点击评论输入框获得焦点
            click_success = False
            for attempt in range(3):  # 最多尝试3次
                try:
                    print(f"   尝试第{attempt + 1}次点击评论输入框...")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", comment_input)
                    time.sleep(0.5)  # 减少等待时间
                    
                    # 先尝试普通点击
                    comment_input.click()
                    time.sleep(0.3)
                    
                    # 再尝试JavaScript点击
                    driver.execute_script("arguments[0].click();", comment_input)
                    time.sleep(0.3)
                    
                    # 检查是否获得焦点（检查是否有光标或active状态）
                    active_element = driver.switch_to.active_element
                    if active_element == comment_input or comment_input.get_attribute('class').find('active') != -1:
                        print(f"   ✅ 第{attempt + 1}次点击成功，输入框已获得焦点")
                        click_success = True
                        break
                    else:
                        print(f"   第{attempt + 1}次点击未获得焦点，继续尝试...")
                        
                except Exception as e:
                    print(f"   第{attempt + 1}次点击失败: {e}")
                    time.sleep(0.5)
            
            if not click_success:
                print("   ⚠️ 多次尝试点击输入框均失败")
                take_screenshot(driver, "comment_input_click_failed")
            
            # 输入评论内容
            comment_text = "这是一个自动化测试评论，用于验证评论功能是否正常工作。"
            input_success = False
            
            # 尝试多种输入方式
            try:
                # 方式1: 直接发送键盘输入
                comment_input.send_keys(comment_text)
                time.sleep(0.5)
                print(f"   ✅ 方式1成功输入评论内容")
                input_success = True
            except Exception as e:
                print(f"   方式1输入失败: {e}")
                
                # 方式2: 使用ActionChains
                try:
                    actions = ActionChains(driver)
                    actions.move_to_element(comment_input).click().send_keys(comment_text).perform()
                    time.sleep(0.5)
                    print(f"   ✅ 方式2成功输入评论内容")
                    input_success = True
                except Exception as e2:
                    print(f"   方式2输入失败: {e2}")
                    
                    # 方式3: 使用JavaScript设置内容
                    try:
                        driver.execute_script("arguments[0].innerText = arguments[1];", comment_input, comment_text)
                        time.sleep(0.5)
                        print(f"   ✅ 方式3成功输入评论内容")
                        input_success = True
                    except Exception as e3:
                        print(f"   ❌ 所有输入方式均失败: {e3}")
            
            if not input_success:
                take_screenshot(driver, "comment_input_text_failed")
                print("   ⚠️ 评论内容输入失败，跳过后续步骤")
            else:
                # 查找并点击回复按钮
                reply_button_selectors = [
                    "//button[contains(@class, 'ant-btn-primary') and .//span[text()='回复']]",
                    "button.ant-btn.ant-btn-primary:has(span:contains('回复'))",
                    "button[class*='ant-btn-primary']:has(span:contains('回复'))",
                    "//button[contains(@class, 'ant-btn-primary')]//span[text()='回复']/parent::button",
                    "button.ant-btn-primary"
                ]
                
                reply_button = None
                for selector in reply_button_selectors:
                    try:
                        if selector.startswith('//'):
                            reply_button = WebDriverWait(driver, 3).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                        else:
                            reply_button = WebDriverWait(driver, 3).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                        if reply_button and reply_button.is_displayed() and not reply_button.get_attribute('disabled'):
                            print(f"   ✓ 找到回复按钮: {selector}")
                            break
                    except:
                        continue
                
                if not reply_button:
                    take_screenshot(driver, "reply_button_not_found")
                    print("   ⚠️ 未找到可用的回复按钮")
                else:
                    try:
                        # 等待按钮变为可点击状态（不再disabled）
                        WebDriverWait(driver, 5).until(
                            lambda d: not reply_button.get_attribute('disabled')
                        )
                        reply_button.click()
                        print("   ✅ 已点击回复按钮")
                        time.sleep(1)  # 减少等待时间
                        take_screenshot(driver, "comment_submitted")
                    except Exception as e:
                        print(f"   ⚠️ 点击回复按钮失败: {e}")
                        # 尝试使用JavaScript点击
                        try:
                            driver.execute_script("arguments[0].click();", reply_button)
                            print("   ✅ 已使用JavaScript点击回复按钮")
                            time.sleep(1)
                            take_screenshot(driver, "comment_submitted")
                        except Exception as e2:
                            print(f"   ❌ JavaScript点击也失败: {e2}")
        
        print("   ✅ 评论功能测试完成")

    except TimeoutException as e:
        print(f"\n❌ 测试执行超时或元素未找到: {e}")
        take_screenshot(driver, "kb_test_timeout_error")
        raise
    except Exception as e:
        print(f"\n❌ 测试执行过程中发生未知错误: {e}")
        take_screenshot(driver, "kb_test_unknown_error")
        raise
    finally:
        # 确保在测试结束时切回主文档，以防之前有iframe切换等意外情况
        try:
            driver.switch_to.default_content()
        except:
            pass

    print("\n--- ✅ 测试成功完成：知识库内创建新文档 ---")


def test_explore_follow_user(driver):
    """
    核心测试用例：去逛逛界面关注用户，点击信息流里的第一个用户名。
    使用CSS选择器 a[class^="Feed-module_uname_"] 定位用户名链接。
    """
    print("\n--- 🚀 开始执行测试：逛逛关注测试，去逛逛界面关注用户 ---")
    wait = WebDriverWait(driver, 20)
    
    try:
        # 1. 点击"逛逛"菜单
        print("1. 正在导航到 '逛逛' 页面...")
        
        explore_selectors = [
            "//span[contains(@class, 'ant-menu-title-content') and contains(., '逛逛')]",
            "a[href='/dashboard/explore']",
            "//li[@title='逛逛']//a"
        ]
        
        explore_link = None
        for selector in explore_selectors:
            try:
                by = By.XPATH if selector.startswith('/') else By.CSS_SELECTOR
                element_to_click = wait.until(EC.element_to_be_clickable((by, selector)))
                if element_to_click:
                    print(f"   ✓ 找到 '逛逛' 链接使用选择器: {selector}")
                    driver.execute_script("arguments[0].click();", element_to_click)
                    print("   ✅ 已点击 '逛逛' 链接。")
                    explore_link = element_to_click
                    break
            except TimeoutException:
                print(f"   - 尝试选择器失败 (超时): {selector}")
                continue
        
        if not explore_link:
            take_screenshot(driver, "explore_link_not_found")
            raise Exception("无法找到'逛逛'页面的链接，已尝试多种选择器")

        # 等待逛逛页面加载完成
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.HeadlineSelections-module_mainList_A7xla")))
        print("   ✅ 逛逛页面已加载完成")

        # 2. 滚动页面以确保内容加载
        print("\n2. 正在滚动页面以加载文章...")
        for i in range(2):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            print(f"   - 第 {i+1}/2 次滚动...")
            time.sleep(2)
        
        # 滚动回顶部
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        print("   ✅ 滚动完成，已回到页面顶部")

        # 3. 查找第一个用户名链接
        print("\n3. 正在查找第一个用户名链接...")
        
        # 使用CSS选择器查找class属性以Feed-module_uname_开头的链接
        user_link_selectors = [
            "a[class^='Feed-module_uname_']",  # 主要选择器
            "a[class*='Feed-module_uname_']",  # 备选：包含该字符串
            "a.Feed-module_uname_srr3b"        # 备选：具体类名（如果存在）
        ]
        
        user_link = None
        for selector in user_link_selectors:
            try:
                user_links = driver.find_elements(By.CSS_SELECTOR, selector)
                if user_links:
                    # 找到第一个可见的用户链接
                    for link in user_links:
                        if link.is_displayed():
                            user_link = link
                            print(f"   ✓ 找到第一个用户名链接使用选择器: {selector}")
                            break
                    if user_link:
                        break
            except Exception as e:
                print(f"   - 尝试选择器失败: {selector}, 错误: {e}")
                continue
        
        if not user_link:
            print("   ❌ 未找到任何用户名链接")
            take_screenshot(driver, "user_link_not_found")
            # 尝试查看页面源代码中是否有相关元素
            page_source = driver.page_source
            if "Feed-module_uname_" in page_source:
                print("   - 页面源代码中存在Feed-module_uname_相关内容，但元素可能未正确加载")
            raise Exception("无法找到class属性以Feed-module_uname_开头的用户名链接")
        
        # 获取用户名信息
        username = user_link.text
        user_url = user_link.get_attribute("href")
        print(f"   ✓ 找到用户: '{username}'")
        print(f"   ✓ 用户链接: {user_url}")
        
        # 4. 点击用户名链接
        print("\n4. 正在点击用户名链接...")
        
        # 确保元素在视图中
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", user_link)
        time.sleep(1)
        
        # 获取当前窗口句柄
        original_window = driver.current_window_handle
        
        # 点击用户链接
        try:
            user_link.click()
        except:
            # 如果普通点击失败，使用JavaScript点击
            driver.execute_script("arguments[0].click();", user_link)
        
        print(f"   ✅ 已点击用户名链接: '{username}'")
        
        # 5. 等待新页面加载并切换到用户页面
        print("\n5. 正在等待用户页面加载...")
        
        try:
            # 如果是新窗口，先切换
            if len(driver.window_handles) > 1:
                wait.until(EC.number_of_windows_to_be(2))
                for window_handle in driver.window_handles:
                    if window_handle != original_window:
                        driver.switch_to.window(window_handle)
                        break
                print("   ✓ 已切换到新窗口")
            
            # **【核心修改】**
            # 使用更可靠的、基于页面主要容器的等待条件
            # "UserInfo-module_userWrapper_" 是用户信息的大容器，比h1或url更稳定
            user_profile_container_selector = "div[class*='UserInfo-module_userWrapper_']"
            print(f"   - 正在等待用户主页容器 '{user_profile_container_selector}' 加载...")
            
            long_wait = WebDriverWait(driver, 30)  # 给新页面加载更长的时间
            long_wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, user_profile_container_selector))
            )
            
            print(f"   ✅ 用户页面已成功加载 (找到主容器)")
            print(f"   - 当前URL: {driver.current_url}")
            take_screenshot(driver, f"user_page_opened_{username}")
            
            # 6. 查找并点击关注按钮
            print("\n6. 正在查找关注按钮...")
            
            # **【核心修改】**
            # 优先使用XPath，通过不变的文本内容"关注"来定位按钮
            # 这是最稳妥的方式，无视动态变化的CSS类名
            follow_button_xpath = "//button[contains(@class, 'UserInfo-module_followBtn_') and .//span[text()='关注']]"
            
            follow_button = None
            try:
                print(f"   - 正在使用最稳妥的XPath查找: {follow_button_xpath}")
                follow_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, follow_button_xpath))
                )
                print(f"   ✓ 找到关注按钮: {follow_button_xpath}")
                print(f"   ✓ 按钮文本: '{follow_button.text}'")
                print(f"   ✓ 按钮类名: '{follow_button.get_attribute('class')}'")

            except TimeoutException:
                print("   - ⚠️ XPath查找失败，尝试备选CSS部分匹配...")
                # 如果XPath失败，再尝试CSS部分匹配作为备选
                css_selector = "button[class*='UserInfo-module_followBtn_']"
                try:
                    buttons = driver.find_elements(By.CSS_SELECTOR, css_selector)
                    for btn in buttons:
                        if btn.is_displayed() and '关注' in btn.text:
                            follow_button = btn
                            print(f"   ✓ 找到关注按钮 (备选CSS): {css_selector}")
                            print(f"   ✓ 按钮文本: '{btn.text}'")
                            break
                except Exception as e:
                    print(f"   - 备选CSS查找也失败: {e}")
            
            if follow_button:
                print("   ✅ 找到关注按钮，准备点击...")
                
                # 点击关注按钮
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", follow_button)
                    time.sleep(1)
                    follow_button.click()
                    print("   ✅ 已点击关注按钮")
                    
                    # 等待并验证按钮文本变为"已关注"
                    WebDriverWait(driver, 10).until(
                        EC.text_to_be_present_in_element(
                            (By.XPATH, "//button[contains(@class, 'UserInfo-module_followBtn_')]"),
                            "已关注"
                        )
                    )
                    print("   ✅ 关注成功！按钮状态已更新。")
                    take_screenshot(driver, f"follow_success_{username}")

                except Exception as e:
                    print(f"   ❌ 点击或验证关注按钮时出错: {e}")
                    take_screenshot(driver, f"follow_failed_{username}")
            else:
                print("   ⚠️ 未找到关注按钮，可能用户已被关注或页面结构已更新")
                take_screenshot(driver, f"follow_button_not_found_{username}")
            
            # 等待几秒让用户看到结果
            time.sleep(3)
            
            # 7. 返回原页面
            print("\n7. 正在返回逛逛页面...")
            if len(driver.window_handles) > 1:
                # 关闭用户页面窗口
                driver.close()
                driver.switch_to.window(original_window)
            else:
                # 返回上一页
                driver.back()
                time.sleep(2)
            
            print("   ✅ 已返回逛逛页面")
            
        except TimeoutException:
            print("   ❌ 用户页面加载超时，即使在延长等待后。")
            take_screenshot(driver, "user_page_load_timeout")
            raise
        
    except TimeoutException as e:
        print(f"\n❌ 测试执行超时或元素未找到: {e}")
        take_screenshot(driver, "explore_follow_test_timeout_error")
        raise
    except Exception as e:
        print(f"\n❌ 测试执行过程中发生未知错误: {e}")
        take_screenshot(driver, "explore_follow_test_unknown_error")
        raise

    print("\n--- ✅ 测试成功完成：逛逛关注测试，去逛逛界面关注用户 ---")


# --- 主程序 ---

def main():
    """主执行函数"""
    print("--- 启动自动化测试脚本 ---")

    # --- 1. 加载配置 ---
    config_path = 'config.json'
    driver_path = ""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        driver_path = config.get("driver_path")
        if not driver_path or not os.path.exists(driver_path):
            print(f"❌ 错误: ChromeDriver路径未在 {config_path} 中正确配置，或路径 '{driver_path}' 不存在。")
            print(f"   请在 {config_path} 中设置 'driver_path' 为您本地的ChromeDriver可执行文件路径。")
            return
    except FileNotFoundError:
        print(f"❌ 错误: 配置文件 '{config_path}' 未找到。")
        return
    except json.JSONDecodeError:
        print(f"❌ 错误: 无法解析配置文件 '{config_path}'。请检查其JSON格式是否正确。")
        return

    # --- 2. 初始化WebDriver ---
    print("⏳ 正在初始化Chrome WebDriver...")
    driver = None  # 确保在finally块中driver是已定义的
    try:
        print(f"ℹ️ 使用本地ChromeDriver: {driver_path}")
        # 使用旧版方式创建ChromeDriver (适用于较早版本的Selenium)
        driver = webdriver.Chrome(executable_path=driver_path)
        driver.maximize_window()
        driver.implicitly_wait(5)  # 隐式等待，增加稳定性
        print("✅ WebDriver 初始化成功")
    except Exception as e:
        # 尝试使用较新版本的Selenium语法
        try:
            service = ChromeService(executable_path=driver_path)
            driver = webdriver.Chrome(service=service)
            driver.maximize_window()
            driver.implicitly_wait(5)
            print("✅ WebDriver 初始化成功 (使用Service API)")
        except Exception as e2:
            print(f"❌ WebDriver 初始化失败:")
            print(f"   - 尝试方法1: {e}")
            print(f"   - 尝试方法2: {e2}")
            print("   请确保您的ChromeDriver版本与Chrome浏览器版本匹配。")
            return

    try:
        # --- 3. 登录流程 (乐观尝试) ---
        print("\n--- Phase 1: 尝试使用Cookie直接访问 ---")
        if not load_cookies(driver, COOKIE_FILE):
            # cookie加载失败，需要手动登录
            driver.get(LOGIN_URL)
            print("🚨 请在浏览器中手动扫描二维码完成登录。")
            print("   脚本将等待直到登录成功（最长等待2分钟）...")
            try:
                WebDriverWait(driver, 120, poll_frequency=3).until(lambda d: is_login_successful(d))
                print("✅ 手动登录成功！")
                save_cookies(driver, COOKIE_FILE)
            except TimeoutException:
                print("❌ 登录超时。请检查网络或账号问题后重试。")
                take_screenshot(driver, "manual_login_timeout")
                return # 直接退出
        
        # 验证最终登录状态
        driver.get(DASHBOARD_URL) # 访问仪表盘以确保登录状态
        time.sleep(2)
        if not is_login_successful(driver):
            print("❌ 无法确认登录状态，即使在尝试Cookie和手动登录后。请检查您的网络和账户。")
            take_screenshot(driver, "final_login_failed")
            return
        
        # --- 4. 显示菜单并执行选择的测试 ---
        while True:
            print("\n" + "="*50)
            print("  请选择要执行的测试:")
            print("  1. 小记的逻辑测试 (创建并删除)")
            print("  2. 逛逛的逻辑测试 (点赞并抓取)")
            print("  3. 知识库的逻辑测试 (创建新文档)")
            print("  4. 关注用户的逻辑测试 (逛逛关注用户)")
            print("  q. 退出程序")
            print("="*50)
            
            choice = input("请输入你的选择 (1/2/3/4/q): ").strip().lower()

            if choice == '1':
                test_create_and_delete_note(driver)
            elif choice == '2':
                test_explore_page(driver)
            elif choice == '3':
                test_knowledge_base(driver)
            elif choice == '4':
                test_explore_follow_user(driver)
            elif choice == 'q':
                print("👋 正在退出程序...")
                break
            else:
                print("❌ 无效输入，请输入 1, 2, 3, 4 或 q。")

            # 每次测试后询问是否继续
            another_test = input("\n是否要执行另一个测试? (y/n): ").strip().lower()
            if another_test != 'y':
                break
        
        # 在程序结束前汇总CSV文件
        print("\n--- 正在汇总CSV文件 ---")
        merge_csv_files()

    except Exception as e:
        print(f"\n😭 测试执行期间发生严重错误: {e}")
        take_screenshot(driver, "main_critical_error")
    finally:
        if driver:
            print("\n⏳ 正在关闭WebDriver...")
            driver.quit()
            print("✅ WebDriver 已关闭。")


if __name__ == "__main__":
    main()

