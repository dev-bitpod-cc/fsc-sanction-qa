#!/usr/bin/env python3
"""
Gemini File Search 引擎實作
"""

import time
import os
from pathlib import Path
from typing import List, Dict, Any
import logging

from google import genai
from google.genai import types

from .base import RAGEngine, RAGResponse, Source

logger = logging.getLogger(__name__)


class GeminiEngine(RAGEngine):
    """Google Gemini File Search 引擎"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 Gemini 引擎

        Args:
            config: Gemini 引擎配置
        """
        super().__init__(config)

        # 取得 API Key
        api_key_env = config.get('api_key_env', 'GEMINI_API_KEY')
        api_key = os.getenv(api_key_env)

        if not api_key:
            raise ValueError(
                f"Gemini API Key 未設置。"
                f"請設置環境變數: {api_key_env}"
            )

        # 初始化 Gemini 客戶端
        self.client = genai.Client(api_key=api_key)
        self.model_name = config.get('model', 'gemini-2.0-flash-001')

        # File Search Store 資訊
        self.store_name = None
        self.store_resource_name = None

        # 定價資訊
        self.pricing = config.get('pricing', {})

        logger.info(f"Gemini Engine 初始化完成 (model: {self.model_name})")

    def build_index(self, data_dir: str) -> None:
        """
        建立 Gemini 索引（使用新版 File Search Store API）

        注意: File Search Store 的資料會永久保存，直到手動刪除

        Args:
            data_dir: 資料目錄路徑
        """
        logger.info(f"開始建立 Gemini File Search Store: {data_dir}")
        start_time = time.time()

        try:
            # 步驟 1: 創建 File Search Store
            store_display_name = f'fsc-penalty-cases-{int(time.time())}'
            logger.info(f"創建 File Search Store: {store_display_name}")

            file_search_store = self.client.file_search_stores.create(
                config=types.CreateFileSearchStoreConfig(
                    display_name=store_display_name
                )
            )

            self.store_resource_name = file_search_store.name
            logger.info(f"File Search Store 已創建: {self.store_resource_name}")

            # 步驟 2: 先上傳文件到 Files API，然後導入到 File Search Store
            data_path = Path(data_dir)
            txt_files = list(data_path.glob("*.txt"))

            logger.info(f"找到 {len(txt_files)} 個文件")

            # 2a. 上傳到 Files API
            uploaded_files = []
            for i, file_path in enumerate(txt_files, 1):
                try:
                    with open(file_path, 'rb') as f:
                        file_obj = self.client.files.upload(
                            file=f,
                            config=types.UploadFileConfig(
                                display_name=file_path.name,
                                mime_type='text/plain'
                            )
                        )

                    uploaded_files.append({
                        'display_name': file_path.name,
                        'file_name': file_obj.name
                    })

                    if i % 50 == 0:
                        logger.info(f"上傳進度: {i}/{len(txt_files)}")

                    # 短暫延遲避免限流
                    if i % 10 == 0:
                        time.sleep(1)

                except Exception as e:
                    logger.error(f"上傳失敗 {file_path.name}: {str(e)}")

            uploaded_count = len(uploaded_files)
            logger.info(f"已上傳 {uploaded_count} 個文件到 Files API")

            # 2b. 導入到 File Search Store
            logger.info("開始導入文件到 File Search Store...")
            import_count = 0
            for i, file_info in enumerate(uploaded_files, 1):
                try:
                    operation = self.client.file_search_stores.import_file(
                        file_search_store_name=self.store_resource_name,
                        file_name=file_info['file_name']
                    )
                    import_count += 1

                    if i % 50 == 0:
                        logger.info(f"導入進度: {i}/{len(uploaded_files)}")

                    # 短暫延遲避免限流
                    if i % 10 == 0:
                        time.sleep(0.5)

                except Exception as e:
                    logger.error(f"導入失敗 {file_info['display_name']}: {str(e)}")

            logger.info(f"已導入 {import_count} 個文件到 File Search Store")

            elapsed = time.time() - start_time
            logger.info(
                f"索引建立完成！"
                f"上傳 {uploaded_count}/{len(txt_files)} 個文件到 File Search Store，"
                f"耗時 {elapsed:.1f} 秒"
            )

            # 儲存 File Search Store 資訊
            self._save_store_info(self.store_resource_name, uploaded_files)

            self._initialized = True

        except Exception as e:
            logger.error(f"建立索引失敗: {str(e)}")
            raise

    def query(self, question: str, **kwargs) -> RAGResponse:
        """
        使用 Gemini File Search 執行查詢

        Args:
            question: 使用者問題
            **kwargs: 額外參數

        Returns:
            RAGResponse: 查詢結果
        """
        if not self._initialized:
            raise RuntimeError("Gemini 引擎尚未初始化或未建立索引")

        if not self.store_resource_name:
            raise RuntimeError("File Search Store 未建立，請重新建立索引")

        start_time = time.time()

        try:
            # 生成配置
            generation_config = self.config.get('generation', {})
            system_instruction = generation_config.get('system_instruction', '')

            # 執行查詢，使用 File Search 工具
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=question,
                config=types.GenerateContentConfig(
                    tools=[
                        types.Tool(
                            file_search=types.FileSearch(
                                file_search_store_names=[self.store_resource_name]
                            )
                        )
                    ],
                    temperature=generation_config.get('temperature', 0.1),
                    max_output_tokens=generation_config.get('max_output_tokens', 2000),
                    system_instruction=system_instruction
                )
            )

            # 提取答案
            answer = response.text if hasattr(response, 'text') else str(response)

            # 提取來源
            sources = self._extract_sources(response)

            # 計算指標
            latency = self._calculate_latency(start_time)
            cost = self._estimate_cost(question, answer)

            return RAGResponse(
                answer=answer,
                sources=sources,
                confidence=0.85,  # Gemini 不提供置信度，使用預設值
                latency=latency,
                cost_estimate=cost,
                engine_name="Gemini File Search"
            )

        except Exception as e:
            logger.error(f"查詢失敗: {str(e)}")
            raise

    def _extract_sources(self, response) -> List[Source]:
        """
        從 Gemini File Search 回應中提取來源

        Args:
            response: Gemini API 回應

        Returns:
            List[Source]: 來源列表
        """
        sources = []

        try:
            # 檢查 grounding metadata
            if hasattr(response, 'candidates') and len(response.candidates) > 0:
                candidate = response.candidates[0]

                if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                    metadata = candidate.grounding_metadata

                    # File Search 的引用在 grounding_chunks 中
                    if hasattr(metadata, 'grounding_chunks') and metadata.grounding_chunks:
                        for i, chunk in enumerate(metadata.grounding_chunks):
                            # File Search chunks 包含 retrieved_context
                            if hasattr(chunk, 'retrieved_context'):
                                context = chunk.retrieved_context

                                # 提取文件名稱
                                filename = "未知文件"
                                if hasattr(context, 'title') and context.title:
                                    filename = context.title
                                elif hasattr(context, 'uri') and context.uri:
                                    filename = context.uri.split('/')[-1]

                                # 提取內容片段
                                snippet = ""
                                if hasattr(context, 'text') and context.text:
                                    snippet = context.text[:500]  # 限制長度

                                # 計算分數（如果有的話）
                                score = 1.0
                                if hasattr(chunk, 'score'):
                                    score = float(chunk.score)

                                sources.append(Source(
                                    filename=filename,
                                    snippet=snippet,
                                    score=score,
                                    metadata={'type': 'file_search', 'index': i}
                                ))

                    # 檢查是否有 grounding_supports（包含更詳細的引用資訊）
                    if hasattr(metadata, 'grounding_supports') and metadata.grounding_supports:
                        for support in metadata.grounding_supports:
                            if hasattr(support, 'segment') and hasattr(support.segment, 'text'):
                                # 這是支持答案的文本片段
                                pass  # 可以在這裡添加更多邏輯

        except Exception as e:
            logger.error(f"提取來源時發生錯誤: {str(e)}")

        # 如果沒有找到來源，記錄警告
        if not sources:
            logger.warning("未找到來源資訊")

        return sources

    def _estimate_cost(self, input_text: str, output_text: str) -> float:
        """
        估算查詢成本

        Args:
            input_text: 輸入文字
            output_text: 輸出文字

        Returns:
            float: 預估成本（美元）
        """
        # 粗略估算 token 數（英文 ~1.3 tokens/word，中文 ~2 tokens/char）
        input_tokens = len(input_text) * 1.5  # 保守估計
        output_tokens = len(output_text) * 1.5

        input_price = self.pricing.get('input_price', 0.075)  # per 1M tokens
        output_price = self.pricing.get('output_price', 0.30)

        cost = (
            input_tokens / 1_000_000 * input_price +
            output_tokens / 1_000_000 * output_price
        )

        return cost

    def _save_store_info(self, store_resource_name: str, uploaded_files: list) -> None:
        """儲存 File Search Store 資訊到檔案"""
        import json

        files_dir = Path("data/gemini_corpus")
        files_dir.mkdir(parents=True, exist_ok=True)

        info_file = files_dir / "store_info.json"

        info_data = {
            'store_resource_name': store_resource_name,
            'created_at': time.time(),
            'created_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'files': uploaded_files,
            'total_files': len(uploaded_files)
        }

        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(info_data, f, ensure_ascii=False, indent=2)

        logger.info(f"File Search Store 資訊已儲存: {info_file} (Store: {store_resource_name}, {len(uploaded_files)} 個文件)")

    def load_corpus_info(self) -> bool:
        """
        從檔案載入 File Search Store 資訊

        Returns:
            bool: 是否成功載入
        """
        import json

        info_file = Path("data/gemini_corpus/store_info.json")

        if not info_file.exists():
            logger.warning("找不到 File Search Store 索引")
            return False

        try:
            with open(info_file, 'r', encoding='utf-8') as f:
                info_data = json.load(f)

            # 載入 File Search Store 資源名稱
            self.store_resource_name = info_data.get('store_resource_name')

            if not self.store_resource_name:
                logger.error("File Search Store 資源名稱不存在")
                return False

            self._initialized = True
            logger.info(
                f"已載入 File Search Store: {info_data.get('total_files', 0)} 個文件 "
                f"(建立於 {info_data.get('created_time', '未知')})"
            )
            return True

        except Exception as e:
            logger.error(f"載入 File Search Store 資訊失敗: {str(e)}")

        return False

    def get_index_info(self) -> dict:
        """
        取得 File Search Store 索引資訊

        Returns:
            dict: 索引資訊（包含建立時間、檔案數量等）
        """
        import json

        info_file = Path("data/gemini_corpus/store_info.json")

        if not info_file.exists():
            return {
                'exists': False,
                'expired': False,
                'message': '索引不存在'
            }

        try:
            with open(info_file, 'r', encoding='utf-8') as f:
                info_data = json.load(f)

            created_at = info_data.get('created_at', 0)
            current_time = time.time()
            age_hours = (current_time - created_at) / 3600

            return {
                'exists': True,
                'expired': False,  # File Search Store 不會過期
                'created_time': info_data.get('created_time', '未知'),
                'age_hours': age_hours,
                'total_files': info_data.get('total_files', 0),
                'store_resource_name': info_data.get('store_resource_name', '未知')
            }

        except Exception as e:
            logger.error(f"讀取索引資訊失敗: {str(e)}")
            return {
                'exists': False,
                'expired': False,
                'message': f'讀取失敗: {str(e)}'
            }

