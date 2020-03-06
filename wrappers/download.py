import functools
import os
from tools.log import Logger


def retry(max_retry, path, url, name):
    def receive_func(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = Logger()
            try:
                file_path = os.path.join(path, name)
                file_path = os.path.abspath(file_path)
                max_retry_count = max_retry
                retry_count = 0
                while retry_count < max_retry_count:
                    try:
                        print('-' * 100)
                        logger.info("[开始下载] \n retry: %d \n path: %s \n url: %s" % (retry_count, file_path, url))
                        func()
                        break
                    except Exception as Ex:
                        logger.warning("[下载异常] \n url: %s \n EX: %s" % (url, str(Ex)))
                        retry_count += 1
                if retry_count == max_retry_count:
                    logger.warning("[下载失败] \n Name: %s" % name)
                else:
                    logger.info("[下载完成] \n Name: %s" % name)
            except:
                logger.warning("[下载失败] \n Name: %s" % name)
            return func(*args, **kwargs)

        return wrapper

    return receive_func
