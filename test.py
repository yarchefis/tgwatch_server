import configparser
import time

def main():
    # Создаем объект ConfigParser
    config = configparser.ConfigParser()
    
    while True:
        config.read('config.ini')
        variable_value = config.get('Settings', 'variable_name')
        print(f"Значение переменной: {variable_value}")

if __name__ == "__main__":
    main()
