"""文件下载线程模块

提供异步下载功能
"""

import os
import logging
import hashlib
import urllib.request
import urllib.error

from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class DownloadThread(QThread):
    """文件下载线程"""

    download_complete = pyqtSignal(str, str)  # file_path, filename
    download_error = pyqtSignal(str)  # error_message
    download_progress = pyqtSignal(int, int)  # downloaded, total

    def __init__(self, project_data, target_path, language_manager=None):
        super().__init__()
        self.project_data = project_data
        self.target_path = target_path
        self.language_manager = language_manager
        self.should_stop = False
        self.skipped = False  # 标记是否跳过下载（文件已存在）

    def stop(self):
        """停止下载"""
        self.should_stop = True

    def run(self):
        """执行下载任务"""
        try:
            from managers.modrinth_manager import ModrinthManager

            manager = ModrinthManager()
            project_id = self.project_data.get('project_id')

            logger.info(f"Fetching versions for project {project_id}")
            versions = manager.get_project_versions(project_id)

            if not versions:
                self.download_error.emit(
                    self.language_manager.translate("download_error_no_versions")
                    if self.language_manager else "No versions available"
                )
                return

            # 获取最新版本
            latest_version = versions[0]
            files = latest_version.get('files', [])

            if not files:
                self.download_error.emit(
                    self.language_manager.translate("download_error_no_files")
                    if self.language_manager else "No files available for download"
                )
                return

            # 获取主文件
            file_info = next((f for f in files if f.get('primary', False)), files[0])
            file_url = file_info.get('url')
            filename = file_info.get('filename')
            file_size = file_info.get('size', 0)

            if not file_url:
                self.download_error.emit(
                    self.language_manager.translate("download_error_no_url")
                    if self.language_manager else "No download URL available"
                )
                return

            # 构建目标文件路径
            target_file_path = os.path.join(self.target_path, filename)

            # 获取文件哈希（用于验证）
            hashes = file_info.get('hashes', {})
            sha1_hash = hashes.get('sha1')

            # 检查文件是否已存在
            if os.path.exists(target_file_path):
                logger.info(f"File already exists: {target_file_path}")
                # 验证文件哈希
                if sha1_hash and self._verify_file_hash(target_file_path, sha1_hash):
                    logger.info("File hash matches, skipping download")
                    # 不发出信号，让外部直接处理状态更新
                    self.skipped = True
                    return
                logger.info("File hash mismatch or no hash, re-downloading")

            # 开始下载
            logger.info(f"Downloading {filename} from {file_url}")

            req = urllib.request.Request(file_url)
            req.add_header('User-Agent', 'Spectra/1.0 (spectra@modrinth)')

            with urllib.request.urlopen(req, timeout=30) as response:
                total_size = int(response.headers.get('Content-Length', file_size))
                downloaded = 0

                with open(target_file_path + '.tmp', 'wb') as f:
                    while True:
                        if self.should_stop:
                            logger.info("Download cancelled by user")
                            if os.path.exists(target_file_path + '.tmp'):
                                os.remove(target_file_path + '.tmp')
                            return

                        chunk = response.read(8192)
                        if not chunk:
                            break

                        f.write(chunk)
                        downloaded += len(chunk)
                        self.download_progress.emit(downloaded, total_size)

                # 下载完成，重命名文件
                os.rename(target_file_path + '.tmp', target_file_path)

                # 验证文件哈希
                if sha1_hash and not self._verify_file_hash(target_file_path, sha1_hash):
                    logger.error("File hash verification failed")
                    os.remove(target_file_path)
                    self.download_error.emit(
                        self.language_manager.translate("download_error_hash_mismatch")
                        if self.language_manager else "Downloaded file hash mismatch"
                    )
                    return

                logger.info(f"Download complete: {target_file_path}")
                self.download_complete.emit(target_file_path, filename)

        except urllib.error.URLError as e:
            logger.error(f"Download failed: {e}")
            self.download_error.emit(f"Network error: {e}")
        except Exception as e:
            logger.error(f"Download error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.download_error.emit(str(e))

    def _verify_file_hash(self, filepath, expected_hash):
        """验证文件哈希"""
        try:
            with open(filepath, 'rb') as f:
                file_hash = hashlib.sha1(f.read()).hexdigest()
                return file_hash.lower() == expected_hash.lower()
        except Exception as e:
            logger.error(f"Hash verification error: {e}")
            return False
