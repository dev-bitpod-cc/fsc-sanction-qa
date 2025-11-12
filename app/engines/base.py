#!/usr/bin/env python3
"""
RAG 引擎抽象基礎類別
定義所有 RAG 引擎必須實作的介面
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import time


@dataclass
class Source:
    """來源文件資訊"""
    filename: str
    snippet: str
    score: float
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class RAGResponse:
    """RAG 查詢回應"""
    answer: str
    sources: List[Source]
    confidence: float
    latency: float
    cost_estimate: float
    engine_name: str
    metadata: Optional[Dict[str, Any]] = None


class RAGEngine(ABC):
    """RAG 引擎抽象基礎類別"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 RAG 引擎

        Args:
            config: 引擎配置字典
        """
        self.config = config
        self.engine_name = self.__class__.__name__
        self._initialized = False

    @abstractmethod
    def build_index(self, data_dir: str) -> None:
        """
        建立向量索引

        Args:
            data_dir: 資料目錄路徑
        """
        pass

    @abstractmethod
    def query(self, question: str, **kwargs) -> RAGResponse:
        """
        執行查詢

        Args:
            question: 使用者問題
            **kwargs: 額外查詢參數

        Returns:
            RAGResponse: 查詢結果
        """
        pass

    @abstractmethod
    def _estimate_cost(self, input_text: str, output_text: str) -> float:
        """
        估算查詢成本

        Args:
            input_text: 輸入文字
            output_text: 輸出文字

        Returns:
            float: 預估成本（美元）
        """
        pass

    def _calculate_latency(self, start_time: float) -> float:
        """
        計算延遲時間

        Args:
            start_time: 開始時間戳記

        Returns:
            float: 延遲時間（秒）
        """
        return time.time() - start_time

    def get_status(self) -> Dict[str, Any]:
        """
        取得引擎狀態

        Returns:
            Dict: 引擎狀態資訊
        """
        return {
            "engine_name": self.engine_name,
            "initialized": self._initialized,
            "config": self.config
        }

    def __repr__(self) -> str:
        return f"{self.engine_name}(initialized={self._initialized})"
