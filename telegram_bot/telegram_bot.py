import time
from typing import Optional, Dict, Any, BinaryIO, Union, List
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter

__all__ = [
    'TelegramBot',
]


class TelegramBot:
    SESSION = requests.Session()
    N_RETRIES = 10
    SESSION.mount('https://', HTTPAdapter(max_retries=N_RETRIES))

    class TelegramBotError(Exception):
        pass

    class TelegramBotInteractionError(TelegramBotError):
        pass

    def __init__(self, bot_token: str) -> None:
        self.bot_token = bot_token
        self.base_api_url = f'https://api.telegram.org/bot{self.bot_token}/'
        self.base_file_url = f'https://api.telegram.org/file/bot{self.bot_token}/'

        self.last_update_id = None

    def _interact(
            self,
            method: str,
            params: Optional[Dict[str, Any]] = None,
            files: Optional[Dict[str, BinaryIO]] = None,
            post: bool = False,
            retry: bool = True,
    ) -> Any:
        n_retries = self.N_RETRIES if retry else 0

        kwargs = {
            'method': 'POST' if post else 'GET',
            'url': self.base_api_url + method,
            'params': params,
            'files': files,
        }

        jn = None

        while True:
            r = self.SESSION.request(**kwargs)

            if (r.status_code == 200) and (r.headers.get('content-type') == 'application/json'):
                jn = r.json()
                result = jn.get('result')

                if result is not None:
                    return result

            if not retry:
                break

            if n_retries > 0:
                n_retries -= 1
                time.sleep(2)
            else:
                break

        msg = f"Could not get response for method {method}. Args: {kwargs}, status " \
              f"code: {r.status_code} ({r.reason}), json: {jn}"
        raise self.TelegramBotInteractionError(msg)

    def get_me(self) -> dict:
        method = 'getMe'

        return self._interact(method)

    def get_updates(self, offset: Optional[int] = None, confirm_all: bool = False) -> List[dict]:
        method = 'getUpdates'
        params = {}
        
        if offset is not None:
            params['offset'] = offset
        elif confirm_all and self.last_update_id:
            params['offset'] = self.last_update_id + 1

        result = self._interact(method, params)

        if len(result) > 0:
            self.last_update_id = result[-1]['update_id']

        return result

    def get_file_download_url(self, file_id: str) -> Optional[str]:
        method = 'getFile'
        params = {'file_id': file_id}

        result = self._interact(method, params)
        file_path = result['file_path']

        return self.base_file_url + file_path

    def send_text_message(
            self,
            chat_id: Union[int, str],
            text: str,
            parse_mode: str = 'html',
            disable_notification: bool = False,
    ) -> dict:
        method = 'sendMessage'
        params = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode,
            'disable_notification': disable_notification,
        }

        return self._interact(method, params, post=True)

    def delete_message(self, chat_id: Union[int, str], message_id: Union[int, str]) -> bool:
        method = 'deleteMessage'
        params = {'chat_id': chat_id, 'message_id': message_id}

        try:
            return self._interact(method, params, post=True, retry=False)
        except self.TelegramBotInteractionError:
            return False

    def send_file(
            self,
            chat_id: Union[int, str],
            file_path: Path,
            caption: Optional[str] = None,
            parse_mode: str = 'html',
    ) -> dict:
        method = 'sendDocument'
        params = {'chat_id': chat_id, 'parse_mode': parse_mode}

        if caption:
            params['caption'] = caption

        with Path(file_path).open('rb') as file:
            files = {'document': file}
            result = self._interact(method, params, files, post=True)

        return result

    def send_image(
            self,
            chat_id: Union[int, str],
            image_fpath: Path,
            caption: Optional[str] = None,
            parse_mode: str = 'html',
    ) -> dict:
        method = 'sendPhoto'

        params = {'chat_id': chat_id, 'parse_mode': parse_mode}

        if caption:
            params['caption'] = caption

        with Path(image_fpath).open('rb') as file:
            files = {'photo': file}
            result = self._interact(method, params, files, post=True)

        return result
