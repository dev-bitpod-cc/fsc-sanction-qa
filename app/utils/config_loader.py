#!/usr/bin/env python3
"""
配置檔案載入工具
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any


class ConfigLoader:
    """配置檔案載入器"""

    def __init__(self, config_dir: str = "config"):
        """
        初始化配置載入器

        Args:
            config_dir: 配置檔案目錄
        """
        self.config_dir = Path(config_dir)
        self._configs = {}

    def load_config(self, config_file: str) -> Dict[str, Any]:
        """
        載入配置檔案

        Args:
            config_file: 配置檔案名稱

        Returns:
            Dict: 配置字典
        """
        config_path = self.config_dir / config_file

        if not config_path.exists():
            raise FileNotFoundError(f"配置檔案不存在: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        self._configs[config_file] = config
        return config

    def load_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        載入所有配置檔案

        Returns:
            Dict: 所有配置字典
        """
        config_files = ["config.yaml", "gemini_config.yaml", "llamaindex_config.yaml"]

        for config_file in config_files:
            try:
                self.load_config(config_file)
            except FileNotFoundError as e:
                print(f"警告: {e}")

        return self._configs

    def get_config(self, config_name: str) -> Dict[str, Any]:
        """
        取得已載入的配置

        Args:
            config_name: 配置名稱

        Returns:
            Dict: 配置字典
        """
        if config_name not in self._configs:
            return self.load_config(config_name)

        return self._configs[config_name]

    def get_api_key(self, env_var: str) -> str:
        """
        從環境變數取得 API Key

        Args:
            env_var: 環境變數名稱

        Returns:
            str: API Key

        Raises:
            ValueError: 如果環境變數不存在
        """
        api_key = os.getenv(env_var)

        if not api_key:
            raise ValueError(
                f"環境變數 {env_var} 未設置。\n"
                f"請在 .env 檔案中設置或執行: export {env_var}=your_api_key"
            )

        return api_key


# 單例模式
_config_loader_instance = None


def get_config_loader() -> ConfigLoader:
    """
    取得 ConfigLoader 單例

    Returns:
        ConfigLoader: 配置載入器實例
    """
    global _config_loader_instance

    if _config_loader_instance is None:
        _config_loader_instance = ConfigLoader()

    return _config_loader_instance
