<div align="center">
  <h1>🚀 Auto-Yuque</h1>
  <p>智能化语雀自动化工具 - 让知识管理更高效</p>
  
  [![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/downloads/)
  [![Selenium](https://img.shields.io/badge/Selenium-4.x-green.svg)](https://selenium-python.readthedocs.io/)
  [![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
  [![GitHub stars](https://img.shields.io/github/stars/poboll/auto-yuque.svg)](https://github.com/poboll/auto-yuque/stargazers)
  [![GitHub issues](https://img.shields.io/github/issues/poboll/auto-yuque.svg)](https://github.com/poboll/auto-yuque/issues)
</div>

## 📖 项目简介

Auto-Yuque 是一个基于 Python + Selenium 的语雀平台自动化工具，旨在帮助用户高效管理语雀知识库，自动化执行各种操作任务。

### ✨ 核心特性

- 🔐 **智能登录管理** - 支持 Cookie 持久化，自动处理登录状态
- 📝 **小记自动化** - 创建、编辑、删除小记的完整生命周期管理
- 🌟 **社区互动** - 自动浏览"逛逛"页面，智能点赞和内容抓取
- 📚 **知识库管理** - 自动创建和管理知识库文档
- 👥 **用户关注** - 智能发现和关注优质用户
- 🤖 **AI 评论生成** - 集成 AI 模型，生成高质量的文章评论
- 📊 **数据统计** - 完整的操作记录和数据分析

## 🏗️ 项目架构

```
auto-yuque/
├── main.py                 # 主程序入口
├── comment_generator.py    # AI 评论生成模块
├── config.json            # 配置文件
├── cookie.pkl             # Cookie 存储文件
├── screenshots/           # 截图存储目录
├── *.csv                  # 数据文件
└── driver/                # ChromeDriver 存储目录
```

## 🚀 快速开始

### 环境要求

- **Python**: 3.7+
- **Chrome**: 最新版本
- **ChromeDriver**: 与 Chrome 版本匹配

### 依赖安装

```bash
# 克隆项目
git clone https://github.com/poboll/auto-yuque.git
cd auto-yuque

# 安装依赖
pip install -r requirements.txt
```

### 配置设置

1. **下载 ChromeDriver**
   - 访问 [ChromeDriver 官网](https://chromedriver.chromium.org/)
   - 下载与您的 Chrome 版本匹配的驱动
   - 将驱动放置在 `driver/` 目录下

2. **配置文件设置**
   ```json
   {
     "driver_path": "/path/to/chromedriver",
     "yuque_url": "https://www.yuque.com/",
     "target_url": ""
   }
   ```

3. **AI 评论配置**（可选）
   - 在 `comment_generator.py` 中配置您的 API 密钥
   - 支持 SiliconFlow 等 AI 服务

### 运行程序

```bash
python main.py
```

## 🎯 功能详解

### 1. 小记管理 📝
- **创建小记**: 自动生成测试内容并发布
- **删除小记**: 智能定位并删除指定小记
- **状态验证**: 实时验证操作结果

### 2. 逛逛互动 🌟
- **内容抓取**: 批量抓取"逛逛"页面的文章信息
- **智能点赞**: 自动为优质内容点赞
- **数据导出**: 将抓取的数据保存为 CSV 格式

### 3. 知识库操作 📚
- **文档创建**: 自动创建新的知识库文档
- **内容编辑**: 支持富文本内容的自动化编辑
- **权限管理**: 处理文档的访问权限设置

### 4. 用户关注 👥
- **用户发现**: 从"逛逛"页面发现优质用户
- **自动关注**: 智能关注符合条件的用户
- **关注管理**: 跟踪和管理关注状态

### 5. AI 评论系统 🤖
- **内容分析**: 智能分析文章内容
- **评论生成**: 生成个性化、高质量的评论
- **情感控制**: 确保评论的真实性和多样性

## 📊 数据管理

项目会自动生成以下数据文件：

- `explore_titles.csv` - 抓取的文章标题列表
- `scraped_articles.csv` - 详细的文章内容数据
- `commented_articles.csv` - 已评论文章记录
- `articles_summary.csv` - 数据汇总文件

## ⚙️ 高级配置

### 自定义选择器

项目使用了智能的 CSS 选择器策略，能够适应语雀页面的动态变化：

```python
# 示例：关注按钮的多重选择器
follow_button_selectors = [
    "//button[contains(@class, 'UserInfo-module_followBtn_') and .//span[text()='关注']]",
    "button[class*='UserInfo-module_followBtn_']",
    "button.ant-btn.ant-btn-primary:has(span:contains('关注'))"
]
```

### 错误处理

- **自动重试机制**: 网络异常时自动重试
- **截图记录**: 关键操作自动截图保存
- **日志记录**: 详细的操作日志和错误信息

## 🛡️ 注意事项

1. **账号安全**: 请确保您的语雀账号已完成实名认证
2. **使用频率**: 建议合理控制自动化操作的频率，避免触发反爬机制
3. **数据备份**: 重要数据请及时备份
4. **版本兼容**: 定期更新 ChromeDriver 以保持兼容性

## 🤝 贡献指南

我们欢迎所有形式的贡献！

1. Fork 本项目
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

## 📝 更新日志

### v1.0.0 (2024-12-19)
- ✨ 初始版本发布
- 🔐 实现智能登录管理
- 📝 完成小记自动化功能
- 🌟 添加逛逛页面互动功能
- 📚 支持知识库文档管理
- 👥 实现用户关注功能
- 🤖 集成 AI 评论生成

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)。

## ⚠️ 免责声明

本工具仅供学习和研究使用。使用者应当遵守语雀平台的使用条款和相关法律法规。作者不对使用本工具产生的任何后果承担责任。

## 🙏 致谢

感谢所有为开源社区做出贡献的开发者们！

---

<div align="center">
  <p>如果这个项目对您有帮助，请给我们一个 ⭐️</p>
  <p>Made with ❤️ by <a href="https://github.com/poboll">poboll</a></p>
</div>
