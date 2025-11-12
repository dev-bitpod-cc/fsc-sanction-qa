#!/usr/bin/env python3
"""
金管會裁罰案件智能問答系統 - Streamlit 部署版本
"""

import streamlit as st
import sys
from pathlib import Path
import logging
import os

# 加入專案根目錄到 Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.engines.gemini_engine import GeminiEngine
from app.utils.config_loader import get_config_loader

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 頁面配置
st.set_page_config(
    page_title="金管會裁罰案件智能問答",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_resource
def initialize_gemini_engine():
    """初始化 Gemini 引擎"""
    try:
        config_loader = get_config_loader()
        gemini_config = config_loader.load_config("gemini_config.yaml")

        gemini_engine = GeminiEngine(gemini_config)

        # 載入已存在的 File Search Store
        if gemini_engine.load_corpus_info():
            logger.info("Gemini 引擎初始化成功")
            return gemini_engine
        else:
            logger.warning("File Search Store 索引不存在")
            return gemini_engine

    except Exception as e:
        logger.error(f"初始化失敗: {str(e)}")
        st.error(f"系統初始化失敗: {str(e)}")
        st.stop()


def render_sidebar(gemini_engine):
    """渲染側邊欄"""
    with st.sidebar:
        st.header("📊 系統資訊")

        # 顯示索引狀態
        index_info = gemini_engine.get_index_info()

        if index_info['exists']:
            st.success("✅ 智能索引已就緒")
            st.metric("📚 檔案數量", index_info['total_files'])

            with st.expander("ℹ️ 詳細資訊", expanded=False):
                st.caption(f"📅 建立時間: {index_info['created_time']}")

                st.markdown("""
                **系統特色：**
                - 🤖 AI 驅動的語意搜尋
                - 📊 智能文件檢索
                - ✨ 永久保存的知識庫

                **資料來源：**
                - 490 筆金管會裁罰案件
                - 涵蓋 2012-2025 年
                """)
        else:
            st.error("⚠️ 智能索引未建立")
            st.info("請聯繫系統管理員")

        st.markdown("---")

        # 使用說明
        with st.expander("💡 使用說明", expanded=False):
            st.markdown("""
            **如何使用：**
            1. 在下方輸入框輸入問題
            2. 點擊「提交查詢」按鈕
            3. 查看 AI 生成的答案
            4. 檢視參考來源文件

            **範例問題：**
            - 違反金控法利害關係人規定會受到什麼處罰？
            - 哪些銀行因理專挪用客戶款項被裁罰？
            - 證券商遭主管機關裁罰「警告」處分，有哪些業務會受限制？
            """)

        st.markdown("---")
        st.caption("💾 資料來源: 490 筆裁罰案件")
        st.caption("🤖 AI 智能問答系統")


def main():
    """主程式"""
    # 初始化引擎
    gemini_engine = initialize_gemini_engine()

    # 渲染側邊欄
    render_sidebar(gemini_engine)

    # 主標題
    st.title("⚖️ 金管會裁罰案件智能問答")
    st.markdown("### AI 驅動的智能查詢系統")

    st.markdown("---")

    # 問題輸入 - 使用 session state 持久化
    if 'current_question' not in st.session_state:
        st.session_state.current_question = ""

    if 'should_update_question' not in st.session_state:
        st.session_state.should_update_question = False

    # 如果有範例問題要填入
    if st.session_state.should_update_question:
        st.session_state.should_update_question = False

    question = st.text_area(
        "請輸入您的問題：",
        value=st.session_state.current_question,
        placeholder="例如：哪些銀行因為理專挪用客戶款項被裁罰？",
        height=100
    )

    # 更新 session state
    if question != st.session_state.current_question:
        st.session_state.current_question = question

    # 按鈕列
    col1, col2, col3 = st.columns([1, 1, 4])

    with col1:
        submit_button = st.button("🔍 提交查詢", type="primary", use_container_width=True)

    with col2:
        clear_button = st.button("🗑️ 清除", use_container_width=True)

    # 處理清除按鈕
    if clear_button:
        st.session_state.current_question = ""
        st.rerun()

    # 處理查詢
    if submit_button and question:
        with st.spinner("🔍 AI 查詢中..."):
            try:
                # 執行查詢
                response = gemini_engine.query(question)

                # 顯示結果
                st.success("✅ 查詢完成")

                # 指標欄
                metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

                with metric_col1:
                    st.metric("⏱️ 回應時間", f"{response.latency:.2f} 秒")

                with metric_col2:
                    st.metric("💰 預估成本", f"${response.cost_estimate:.6f}")

                with metric_col3:
                    st.metric("📊 置信度", f"{response.confidence*100:.1f}%")

                with metric_col4:
                    st.metric("📚 來源數量", len(response.sources))

                st.markdown("---")

                # 答案
                st.subheader("📝 答案")
                st.markdown(response.answer)

                st.markdown("---")

                # 來源文件
                if response.sources:
                    st.subheader(f"📚 參考來源 ({len(response.sources)} 筆)")

                    for i, source in enumerate(response.sources, 1):
                        with st.expander(
                            f"來源 {i}: {source.filename} (相似度: {source.score:.2%})",
                            expanded=False
                        ):
                            # 顯示文本片段
                            st.markdown(f"**相關內容：**")
                            st.markdown(f"> {source.snippet}")

                            # 顯示 metadata（如果有的話）
                            if source.metadata:
                                st.caption("---")
                                st.caption(f"📎 類型: {source.metadata.get('type', 'N/A')}")
                else:
                    st.warning("⚠️ 未找到參考來源")

            except Exception as e:
                st.error(f"❌ 查詢失敗: {str(e)}")
                logger.error(f"查詢失敗: {str(e)}", exc_info=True)

    # 範例問題
    if not question:
        st.markdown("---")
        st.subheader("💡 範例問題")

        example_questions = [
            "違反金控法利害關係人規定會受到什麼處罰？",
            "請問在證券因為專業投資人資格審核的裁罰有哪些？",
            "辦理共同行銷被裁罰的案例有哪些？",
            "金管會對創投公司的裁罰有哪些？",
            "證券商遭主管機關裁罰「警告」處分，有哪些業務會受限制？",
            "內線交易有罪判決所認定重大訊息成立的時點"
        ]

        cols = st.columns(2)
        for idx, eq in enumerate(example_questions):
            col = cols[idx % 2]
            with col:
                if st.button(f"📌 {eq}", key=f"example_{idx}", use_container_width=True):
                    st.session_state.current_question = eq
                    st.session_state.should_update_question = True
                    st.rerun()


if __name__ == "__main__":
    main()
