import os
import shutil
import datetime
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_backup():
    """Создание резервной копии базы данных"""
    # Пути к файлам
    db_dir = Path('database')
    backups_dir = db_dir / 'backups'
    db_file = db_dir / 'database.db'
    
    # Создаем директорию для бэкапов, если её нет
    backups_dir.mkdir(exist_ok=True)
    
    # Формируем имя файла бэкапа с текущей датой и временем
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = backups_dir / f'database_backup_{timestamp}.db'
    
    try:
        # Копируем файл базы данных
        shutil.copy2(db_file, backup_file)
        logger.info(f"Резервная копия создана: {backup_file}")
        return str(backup_file)
    except Exception as e:
        logger.error(f"Ошибка при создании резервной копии: {str(e)}")
        return None

def restore_backup(backup_file):
    """Восстановление базы данных из резервной копии"""
    db_dir = Path('database')
    db_file = db_dir / 'database.db'
    
    try:
        # Проверяем существование файла бэкапа
        if not os.path.exists(backup_file):
            logger.error(f"Файл резервной копии не найден: {backup_file}")
            return False
        
        # Копируем файл бэкапа в основную базу данных
        shutil.copy2(backup_file, db_file)
        logger.info(f"База данных восстановлена из: {backup_file}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при восстановлении базы данных: {str(e)}")
        return False

def list_backups():
    """Получение списка доступных резервных копий"""
    backups_dir = Path('database') / 'backups'
    if not backups_dir.exists():
        return []
    
    backups = []
    for file in backups_dir.glob('database_backup_*.db'):
        backups.append({
            'file': str(file),
            'name': file.name,
            'size': file.stat().st_size,
            'created': datetime.datetime.fromtimestamp(file.stat().st_ctime)
        })
    
    return sorted(backups, key=lambda x: x['created'], reverse=True)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Управление резервными копиями базы данных')
    parser.add_argument('--create', action='store_true', help='Создать резервную копию')
    parser.add_argument('--restore', type=str, help='Восстановить базу данных из указанного файла')
    parser.add_argument('--list', action='store_true', help='Показать список доступных резервных копий')
    
    args = parser.parse_args()
    
    if args.create:
        create_backup()
    elif args.restore:
        restore_backup(args.restore)
    elif args.list:
        backups = list_backups()
        if backups:
            print("\nДоступные резервные копии:")
            for backup in backups:
                print(f"\nФайл: {backup['name']}")
                print(f"Размер: {backup['size'] / 1024:.1f} KB")
                print(f"Создан: {backup['created'].strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("Резервные копии не найдены")
    else:
        parser.print_help() 