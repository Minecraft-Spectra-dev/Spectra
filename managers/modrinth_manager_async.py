"""Modrinth API 异步管理器（使用 Qt 网络库）"""

import json
import logging
from typing import Optional, List, Dict
from PyQt6.QtCore import QObject, QUrl, pyqtSignal
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
logger = logging.getLogger(__name__)


class ModrinthAsyncRequest(QObject):
    """Modrinth 异步请求对象"""

    # 信号：哈希请求完成时发射 (project_id: str, hashes: List[Dict], error: str)
    hashes_received = pyqtSignal(str, list, str)

    def __init__(self):
        super().__init__()
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self._on_finished)
        self._current_project_id = None

    def _on_finished(self, reply: QNetworkReply):
        """网络请求完成回调"""
        project_id = self._current_project_id
        if project_id is None:
            return

        try:
            if reply.error() == QNetworkReply.NetworkError.NoError:
                data = reply.readAll().data()
                versions = json.loads(data.decode('utf-8'))
                
                # 解析哈希
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
                self.hashes_received.emit(project_id, hashes, "")
            else:
                error_msg = f"Network error: {reply.errorString()}"
                logger.error(f"Modrinth API request failed: {error_msg}")
                self.hashes_received.emit(project_id, [], error_msg)
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse response: {e}"
            logger.error(error_msg)
            self.hashes_received.emit(project_id, [], error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.error(error_msg)
            self.hashes_received.emit(project_id, [], error_msg)
        finally:
            reply.deleteLater()
            self._current_project_id = None

    def get_project_file_hashes(self, project_id: str):
        """异步获取项目的所有文件哈希值

        Args:
            project_id: 项目 ID
        """
        self._current_project_id = project_id
        url = f"https://api.modrinth.com/v2/project/{project_id}/version"
        logger.debug(f"Requesting file hashes for project {project_id}")
        self._make_request(url)

    def _make_request(self, url: str):
        """发起异步 GET 请求"""
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader(b'User-Agent', b'Spectra/1.0 (spectra@modrinth)')
        self.network_manager.get(request)


# 全局单例
_global_async_manager = None


def get_async_manager() -> ModrinthAsyncRequest:
    """获取全局异步管理器单例"""
    global _global_async_manager
    if _global_async_manager is None:
        _global_async_manager = ModrinthAsyncRequest()
    return _global_async_manager
