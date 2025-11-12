# 🚀 部署指南（3 步驟）

這是一個**乾淨的部署版本**，只包含必要的檔案，適合部署到 Streamlit Cloud。

## ✅ 已經準備好的檔案

```
Sanction-Deploy/
├── app/                        ✅ 應用程式代碼
│   ├── main_deploy.py          ⭐ 主程式
│   ├── engines/                ✅ Gemini 引擎
│   └── utils/                  ✅ 工具類
├── config/                     ✅ 配置檔案
├── data/gemini_corpus/         ✅ File Search Store 資訊
│   └── store_info.json         ⭐ 包含 Store ID
├── .streamlit/                 ✅ Streamlit 配置
│   └── secrets.toml.example    ⭐ API Key 範例
├── requirements.txt            ✅ 依賴清單
├── .gitignore                  ✅ Git 忽略設定
└── README.md                   ✅ 專案說明
```

**檔案大小**：< 1 MB（非常輕量！）

---

## 📝 部署前檢查清單

- [ ] 已經建立 Gemini API Key
- [ ] 確認 `data/gemini_corpus/store_info.json` 存在
- [ ] 準備好 GitHub 帳號

---

## 🎯 部署步驟（3 步驟）

### 步驟 1：在 GitHub 建立新 Repository

1. 前往 https://github.com/new
2. **Repository name**：`fsc-sanction-qa` （或其他名稱）
3. **Description**：金管會裁罰案件智能問答系統
4. **Visibility**：
   - ✅ **Public** - 任何人都可以看到（推薦，適合展示）
   - 或 **Private** - 只有你可以看到（Streamlit Cloud 也支援）
5. **不要**勾選 "Add a README file"（我們已經有了）
6. 點擊 "Create repository"

### 步驟 2：推送代碼到 GitHub

**注意**：這個目錄的 Git 已經初始化，你只需要連接遠端並推送。

```bash
# 1. 進入專案目錄
cd /Users/jjshen/Projects/Sanction-Deploy

# 2. 提交代碼（已經 git add . 了）
git commit -m "Initial commit: Clean deployment version"

# 3. 連接到你的 GitHub repository
# 將下面的 YOUR-USERNAME 和 YOUR-REPO-NAME 替換成真實的值
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git

# 4. 推送到 GitHub
git push -u origin main
```

**範例**：
```bash
git remote add origin https://github.com/jjshen/fsc-sanction-qa.git
git push -u origin main
```

### 步驟 3：部署到 Streamlit Cloud

1. **前往** https://share.streamlit.io

2. **登入**（使用 GitHub 帳號）

3. **建立新應用**
   - 點擊 "New app" 或 "Create app"

4. **填寫設定**：
   - **Repository**：選擇你剛建立的 repo（例如：`YOUR-USERNAME/fsc-sanction-qa`）
   - **Branch**：`main`
   - **Main file path**：`app/main_deploy.py`
   - **App URL** (optional)：選擇一個網址（例如：`fsc-qa`）

5. **設定 Secrets**（重要！）
   - 點擊 "Advanced settings"
   - 在 "Secrets" 文字框中貼上：
     ```toml
     GEMINI_API_KEY = "把這裡替換成你的真實 API Key"
     ```
   - ⚠️ **務必替換**成真實的 Gemini API Key

6. **部署**
   - 點擊 "Deploy!"
   - 等待 2-3 分鐘

---

## ✅ 部署完成！

部署成功後，你會看到：
- 應用網址（例如：`https://fsc-qa.streamlit.app`）
- 可以立即訪問和測試

### 分享給其他人

直接將網址分享給需要的人：
```
https://YOUR-APP-NAME.streamlit.app
```

---

## 🧪 本地測試（可選）

如果想在部署前先本地測試：

```bash
# 1. 設定 API Key
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# 編輯 .streamlit/secrets.toml，填入真實的 API Key

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 運行應用
streamlit run app/main_deploy.py
```

---

## 🔄 更新應用

當你想更新應用時：

```bash
# 1. 修改代碼
# 2. 提交變更
git add .
git commit -m "Update: 描述你的變更"
git push

# 3. Streamlit Cloud 會自動重新部署
```

---

## 📊 重要資訊

### 這個版本包含什麼？

✅ 簡化的問答界面（只有 Gemini File Search）
✅ 490 筆裁罰案件的索引（已建立）
✅ File Search Store 永久保存
✅ 完整的查詢功能
✅ 來源引用功能

### 這個版本不包含什麼？

❌ 原始資料檔案（data/penalties/*.txt）- 不需要
❌ LlamaIndex 引擎 - 簡化版只用 Gemini
❌ 開發過程的測試代碼 - 乾淨的生產版本
❌ 構建索引的腳本 - 索引已經建立好

---

## ❓ 常見問題

### Q: 部署需要多久？
A: 通常 2-3 分鐘

### Q: 需要付費嗎？
A: Streamlit Cloud 免費方案足夠使用

### Q: 可以使用私有 repository 嗎？
A: 可以！Streamlit Cloud 支援私有 repo

### Q: 如何查看日誌？
A: 在 Streamlit Cloud 介面點擊 "Manage app" > "Logs"

### Q: Store ID 會過期嗎？
A: 不會！File Search Store 永久保存

---

## 🆘 需要幫助？

- **Streamlit Cloud 文件**：https://docs.streamlit.io/streamlit-community-cloud
- **Gemini API 文件**：https://ai.google.dev/docs
- **專案 README**：查看 `README.md`

---

**🎉 祝部署順利！**
