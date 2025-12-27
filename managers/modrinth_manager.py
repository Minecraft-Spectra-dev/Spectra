"""Modrinth API 管理器"""

import logging
import urllib.request
import urllib.parse
import urllib.error
import json
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class ModrinthManager:
    """Modrinth API 管理器"""
    
    API_BASE_URL = "https://api.modrinth.com/v2"
    
    def __init__(self):
        """初始化 Modrinth 管理器"""
        self.timeout = 10
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发起 HTTP GET 请求
        
        Args:
            endpoint: API 端点路径
            params: 查询参数
            
        Returns:
            dict: 返回的 JSON 数据
            
        Raises:
            urllib.error.URLError: 请求失败时抛出
        """
        url = f"{self.API_BASE_URL}{endpoint}"
        
        if params:
            query_string = urllib.parse.urlencode(params)
            url = f"{url}?{query_string}"
        
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Spectra/1.0 (spectra@modrinth)')
            
            logger.debug(f"Modrinth API request: {url}")
            
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = response.read()
                return json.loads(data.decode('utf-8'))
                
        except urllib.error.URLError as e:
            logger.error(f"Modrinth API request failed: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Modrinth API response: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during Modrinth API request: {e}")
            raise
    
    def search_projects(self, query: str, facets: Optional[List[List[str]]] = None,
                       index: str = "relevance", offset: int = 0, limit: int = 10) -> Dict[str, Any]:
        """搜索 Modrinth 项目
        
        Args:
            query: 搜索关键词
            facets: 筛选条件，格式为 [["type:operation:value"], ...]
                   例如: [["categories:forge"],["versions:1.17.1"],["project_type:mod"]]
            index: 排序方式 (relevance, downloads, follows, newest, updated)
            offset: 偏移量（跳过的结果数）
            limit: 返回结果数量（最多 100）
            
        Returns:
            dict: 包含搜索结果的字典，格式：
                  {
                      "hits": [...],  # 结果列表
                      "offset": 0,   # 偏移量
                      "limit": 10,   # 返回数量
                      "total_hits": 100  # 总结果数
                  }
                  
        Raises:
            urllib.error.URLError: 请求失败时抛出
        """
        params = {
            "query": query,
            "index": index,
            "offset": offset,
            "limit": min(limit, 100)  # 限制最大值为 100
        }
        
        if facets:
            params["facets"] = json.dumps(facets)
        
        return self._make_request("/search", params)
    
    def get_project(self, project_id: str) -> Dict[str, Any]:
        """获取项目详细信息
        
        Args:
            project_id: 项目 ID
            
        Returns:
            dict: 项目详细信息
        """
        return self._make_request(f"/project/{project_id}")
    
    def get_project_versions(self, project_id: str) -> List[Dict[str, Any]]:
        """获取项目的所有版本
        
        Args:
            project_id: 项目 ID
            
        Returns:
            list: 版本列表
        """
        return self._make_request(f"/project/{project_id}/version")
    
    def get_version(self, version_id: str) -> Dict[str, Any]:
        """获取特定版本的详细信息
        
        Args:
            version_id: 版本 ID
            
        Returns:
            dict: 版本详细信息
        """
        return self._make_request(f"/version/{version_id}")
    
    def get_project_files(self, project_id: str) -> List[str]:
        """获取项目的所有文件名
        
        Args:
            project_id: 项目 ID
            
        Returns:
            list: 文件名列表
        """
        versions = self.get_project_versions(project_id)
        filenames = []
        for version in versions:
            files = version.get('files', [])
            for file_info in files:
                filename = file_info.get('filename', '')
                if filename:
                    filenames.append(filename)
        return filenames
    
    def get_latest_version_filename(self, project_id: str) -> Optional[str]:
        """获取项目最新版本的文件名

        Args:
            project_id: 项目 ID

        Returns:
            str or None: 文件名，如果获取失败则返回 None
        """
        try:
            versions = self.get_project_versions(project_id)
            if versions:
                latest_version = versions[0]
                files = latest_version.get('files', [])
                if files:
                    return files[0].get('filename', '')
        except Exception as e:
            logger.error(f"Failed to get latest version filename: {e}")
        return None

    def get_project_file_hashes(self, project_id: str) -> List[Dict[str, str]]:
        """获取项目的所有文件哈希值（SHA1 和 SHA512）

        Args:
            project_id: 项目 ID

        Returns:
            list: 文件哈希列表，格式：[{"sha1": "...", "sha512": "...", "filename": "..."}]
        """
        try:
            versions = self.get_project_versions(project_id)
            hashes = []
            for version in versions:
                files = version.get('files', [])
                for file_info in files:
                    hash_obj = {
                        'sha1': file_info.get('hashes', {}).get('sha1'),
                        'sha512': file_info.get('hashes', {}).get('sha512'),
                        'filename': file_info.get('filename', '')
                    }
                    # 只要有一个哈希值不为空就添加
                    if hash_obj['sha1'] or hash_obj['sha512']:
                        hashes.append(hash_obj)
            logger.debug(f"Got {len(hashes)} file hashes for project {project_id}")
            return hashes
        except Exception as e:
            logger.error(f"Failed to get project file hashes: {e}")
            return []
