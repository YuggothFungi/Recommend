import os
import logging
from db import get_db_connection

# Словарь тематических словосочетаний
DOMAIN_PHRASES = {
    'база данных': 'база данных',
    'базы данных': 'база данных',
    'базам данных': 'база данных',
    'базах данных': 'база данных',
    'программное обеспечение': 'программное обеспечение',
    'программного обеспечения': 'программное обеспечение',
    'программным обеспечением': 'программное обеспечение',
    'учебный план': 'учебный план',
    'учебного плана': 'учебный план',
    'учебному плану': 'учебный план',
    'учебным планом': 'учебный план',
    'трудовая функция': 'трудовая функция',
    'трудовой функции': 'трудовая функция',
    'трудовые функции': 'трудовая функция',
    'трудовых функций': 'трудовая функция',
    'файл сервер': 'файл сервер',
    'клиент сервер': 'клиент сервер',
    'системы аналоги': 'система аналог',
    'систем аналогов': 'система аналог',
    'системам аналогам': 'система аналог',
    'системах аналогах': 'система аналог'
}

# Словарь исключений для лемматизации
LEMMATIZATION_EXCEPTIONS = {
    # Исключения для слова "данные"
    'данных': 'данные',
    'данными': 'данные',
    'данному': 'данные',
    'данным': 'данные',
    'данная': 'данные',
    'данной': 'данные',
    'данную': 'данные',
    'данною': 'данные',
    'данное': 'данные',
    'данного': 'данные',
    'данному': 'данные',
    'данным': 'данные',
    'данном': 'данные',
    
    # Исключения для слова "риск"
    'риски': 'риск',
    'рисках': 'риск',
    'рисками': 'риск',
    'рисков': 'риск',
    'рискам': 'риск',
    'риска': 'риск',
    'риском': 'риск',
    'риске': 'риск',
    
    # Исключения для слова "система"
    'системы': 'система',
    'системам': 'система',
    'системами': 'система',
    'системах': 'система',
    'систему': 'система',
    'системой': 'система',
    'системою': 'система',
    'системе': 'система'
} 