"""
Модуль для расчета и анализа метрик качества системы.
"""

import os
import logging
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from db import get_db_connection
import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime
from collections import defaultdict
import json

logger = logging.getLogger(__name__)

class MetricsAnalyzer:
    """Класс для анализа метрик качества системы."""
    
    def __init__(self):
        self.metrics_history = defaultdict(list)
        self.start_time = None
        self.reports_dir = "reports"
        
        # Создаем директорию для отчетов, если она не существует
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
        
    def start_operation(self):
        """Начать отсчет времени операции."""
        self.start_time = datetime.now()
        
    def end_operation(self, operation_name: str) -> float:
        """Закончить отсчет времени операции и сохранить метрику.
        
        Args:
            operation_name: Название операции
            
        Returns:
            float: Время выполнения в миллисекундах
        """
        if not self.start_time:
            logger.warning("Операция не была начата")
            return 0.0
            
        duration = (datetime.now() - self.start_time).total_seconds() * 1000
        self.metrics_history[f"{operation_name}_time"].append(duration)
        self.start_time = None
        return duration
        
    def calculate_accuracy(self, 
                          original_texts: List[str], 
                          normalized_texts: List[str],
                          domain_phrases: Dict[str, str]) -> float:
        """Рассчитать точность нормализации текста.
        
        Args:
            original_texts: Список исходных текстов
            normalized_texts: Список нормализованных текстов
            domain_phrases: Словарь составных терминов
            
        Returns:
            float: Точность нормализации (0-1)
        """
        if not original_texts or not normalized_texts:
            return 0.0
            
        correct_normalizations = 0
        total_terms = 0
        
        for orig, norm in zip(original_texts, normalized_texts):
            orig = orig.lower()
            norm = norm.lower()
            
            # Проверка сохранения составных терминов
            for phrase, normalized in domain_phrases.items():
                if phrase in orig:
                    if normalized in norm:
                        correct_normalizations += 2  # Повышенный вес для составных терминов
                    total_terms += 2
                    
            # Токенизация с учетом пунктуации
            orig_words = set(word.strip('.,!?()[]{}":;') for word in orig.split())
            norm_words = set(word.strip('.,!?()[]{}":;') for word in norm.split())
            
            # Исключаем составные термины и их части из проверки
            for phrase in domain_phrases:
                if phrase in orig_words:
                    orig_words.remove(phrase)
                    # Исключаем части составного термина
                    for part in phrase.split():
                        if part in orig_words:
                            orig_words.remove(part)
            
            # Проверка сохранения смысла
            for orig_word in orig_words:
                if len(orig_word) < 3:  # Пропускаем короткие слова
                    continue
                    
                total_terms += 1
                
                # Проверяем различные варианты совпадения
                if orig_word in norm_words:
                    correct_normalizations += 1
                else:
                    # Проверяем частичные совпадения
                    for norm_word in norm_words:
                        if (len(orig_word) > 3 and len(norm_word) > 3 and
                            (orig_word.startswith(norm_word[:3]) or 
                             norm_word.startswith(orig_word[:3]))):
                            correct_normalizations += 0.5
                            break
            
        accuracy = correct_normalizations / total_terms if total_terms > 0 else 0.0
        self.metrics_history["normalization_accuracy"].append(accuracy)
        return accuracy
        
    def calculate_lemmatization_accuracy(self,
                                       original_words: List[str],
                                       lemmatized_words: List[str],
                                       exceptions: Dict[str, str]) -> float:
        """Рассчитать точность лемматизации.
        
        Args:
            original_words: Список исходных слов
            lemmatized_words: Список лемматизированных слов
            exceptions: Словарь исключений
            
        Returns:
            float: Точность лемматизации (0-1)
        """
        if not original_words or not lemmatized_words:
            return 0.0
            
        correct_lemmatizations = 0
        total_words = 0
        
        for orig, lemma in zip(original_words, lemmatized_words):
            orig = orig.lower()
            lemma = lemma.lower()
            
            # Пропускаем короткие слова
            if len(orig) < 3:
                continue
                
            total_words += 1
            word_score = 0.0  # Счетчик для текущего слова
            
            # Проверка исключений
            if orig in exceptions:
                if lemma == exceptions[orig].lower():
                    word_score = 1.0
            else:
                # Проверка существительных
                noun_endings = {
                    'ы': 1, 'и': 1, 'а': 1, 'я': 1, 'ой': 2, 'ей': 2,
                    'ом': 2, 'ем': 2, 'ами': 3, 'ями': 3, 'ов': 2, 'ев': 2
                }
                
                for ending, length in noun_endings.items():
                    if orig.endswith(ending):
                        base_orig = orig[:-length]
                        if lemma.startswith(base_orig):
                            word_score = 1.0
                        break
                
                if word_score == 0:  # Если слово еще не определено как существительное
                    # Проверка глаголов
                    verb_endings = {
                        'ть': 2, 'ться': 4, 'л': 1, 'ла': 2, 'ло': 2,
                        'ли': 2, 'ю': 1, 'ешь': 3, 'ет': 2, 'ем': 2,
                        'ете': 3, 'ут': 2, 'ют': 2
                    }
                    
                    for ending, length in verb_endings.items():
                        if orig.endswith(ending):
                            base_orig = orig[:-length]
                            if lemma.startswith(base_orig):
                                word_score = 1.0
                            break
                    
                    if word_score == 0:  # Если слово еще не определено как глагол
                        # Проверка прилагательных
                        adj_endings = {
                            'ый': 2, 'ий': 2, 'ая': 2, 'яя': 2, 'ое': 2,
                            'ее': 2, 'ой': 2, 'ей': 2, 'ого': 3, 'его': 3
                        }
                        
                        for ending, length in adj_endings.items():
                            if orig.endswith(ending):
                                base_orig = orig[:-length]
                                if lemma.startswith(base_orig):
                                    word_score = 1.0
                                break
                        
                        if word_score == 0:  # Если слово не определено как прилагательное
                            # Общая проверка для остальных случаев
                            if (lemma in orig or orig in lemma or
                                (len(orig) > 3 and len(lemma) > 3 and
                                 (orig.startswith(lemma[:3]) or lemma.startswith(orig[:3])))):
                                word_score = 0.5
            
            correct_lemmatizations += word_score
                    
        accuracy = correct_lemmatizations / total_words if total_words > 0 else 0.0
        self.metrics_history["lemmatization_accuracy"].append(accuracy)
        return accuracy
        
    def calculate_recommendation_quality(self,
                                       recommendations: List[Dict],
                                       ground_truth: List[Dict]) -> float:
        """Рассчитать качество рекомендаций.
        
        Args:
            recommendations: Список рекомендаций
            ground_truth: Список эталонных рекомендаций
            
        Returns:
            float: Качество рекомендаций (0-1)
        """
        if not recommendations or not ground_truth:
            return 0.0
            
        correct_recommendations = 0
        total_recommendations = len(recommendations)
        
        for rec, truth in zip(recommendations, ground_truth):
            # Проверка совпадения основных параметров
            if (rec.get("topic_id") == truth.get("topic_id") and
                rec.get("labor_function_id") == truth.get("labor_function_id")):
                correct_recommendations += 1
                
        quality = correct_recommendations / total_recommendations
        self.metrics_history["recommendation_quality"].append(quality)
        return quality
        
    def get_performance_metrics(self) -> Dict[str, float]:
        """Получить метрики производительности.
        
        Returns:
            Dict[str, float]: Словарь с метриками производительности
        """
        metrics = {}
        
        for metric_name, values in self.metrics_history.items():
            if values:
                metrics[metric_name] = {
                    "mean": np.mean(values),
                    "std": np.std(values),
                    "min": np.min(values),
                    "max": np.max(values)
                }
                
        return metrics
        
    def get_error_rate(self) -> float:
        """Рассчитать процент ошибок.
        
        Returns:
            float: Процент ошибок
        """
        total_operations = 0
        error_operations = 0
        
        for metric_name, values in self.metrics_history.items():
            if metric_name.endswith('_time'):
                # Учитываем только операции с ненулевым временем
                non_zero_ops = sum(1 for v in values if v > 0)
                total_operations += non_zero_ops
            elif metric_name.endswith('_accuracy'):
                total_operations += len(values)
                error_operations += sum(1 for v in values if v < 0.5)  # Считаем ошибкой точность меньше 50%
                
        if total_operations == 0:
            return 0.0
            
        error_rate = (error_operations / total_operations) * 100
        return error_rate
        
    def collect_text_statistics(self) -> Dict[str, Dict[str, int]]:
        """Собрать статистику по обработанным текстам.
        
        Returns:
            Dict[str, Dict[str, int]]: Статистика по текстам
        """
        stats = {
            "total_texts": len(self.metrics_history.get("normalization_time", [])),
            "word_counts": {
                "before": 0,
                "after": 0
            },
            "special_terms": {
                "total": 0,
                "preserved": 0
            }
        }
        
        # Добавляем статистику в отчет
        if hasattr(self, 'original_texts') and hasattr(self, 'normalized_texts'):
            for orig, norm in zip(self.original_texts, self.normalized_texts):
                # Подсчет слов до и после нормализации
                stats["word_counts"]["before"] += len(orig.split())
                stats["word_counts"]["after"] += len(norm.split())
                
                # Подсчет специальных терминов
                for term in self.domain_phrases.values():
                    if term in orig:
                        stats["special_terms"]["total"] += 1
                        if term in norm:
                            stats["special_terms"]["preserved"] += 1
                            
        return stats
        
    def generate_report(self) -> str:
        """Сгенерировать отчет о метриках.
        
        Returns:
            str: Текстовый отчет
        """
        report = []
        report.append("Отчет о метриках качества системы")
        report.append("=" * 40)
        
        # Метрики производительности
        perf_metrics = self.get_performance_metrics()
        report.append("\nМетрики производительности:")
        
        # Время нормализации
        if "normalization_time" in perf_metrics:
            norm_time = perf_metrics["normalization_time"]
            report.append("\nВремя нормализации:")
            report.append(f"  Среднее: {norm_time['mean']:.2f} мс")
            report.append(f"  Стандартное отклонение: {norm_time['std']:.2f} мс")
            report.append(f"  Минимум: {norm_time['min']:.2f} мс")
            report.append(f"  Максимум: {norm_time['max']:.2f} мс")
            
            # Оценка производительности
            if norm_time['mean'] < 100:
                report.append("  Оценка: Отлично (< 100мс)")
            elif norm_time['mean'] < 200:
                report.append("  Оценка: Хорошо (< 200мс)")
            else:
                report.append("  Оценка: Требует оптимизации (> 200мс)")
        
        # Точность нормализации и лемматизации
        report.append("\nТочность обработки:")
        
        # Точность нормализации
        norm_acc = 0.0
        if "normalization_accuracy" in self.metrics_history:
            norm_acc = np.mean(self.metrics_history["normalization_accuracy"]) * 100
            report.append("\nТочность нормализации:")
            report.append(f"  Общая точность: {norm_acc:.2f}%")
            
            # Детали нормализации
            if norm_acc >= 95:
                report.append("  Оценка: Отлично (≥ 95%)")
                report.append("  + Корректная обработка составных терминов")
                report.append("  + Правильная лемматизация существительных")
                report.append("  + Сохранение смысла при нормализации")
                report.append("  - Возможны проблемы с некоторыми глаголами")
            elif norm_acc >= 90:
                report.append("  Оценка: Хорошо (≥ 90%)")
                report.append("  + В целом корректная обработка терминов")
                report.append("  - Есть небольшие проблемы с лемматизацией")
                report.append("  - Возможна потеря некоторых предлогов")
            else:
                report.append("  Оценка: Требует улучшения (< 90%)")
                report.append("  - Проблемы с обработкой составных терминов")
                report.append("  - Ошибки в лемматизации")
                report.append("  - Возможна потеря смысла при нормализации")
        
        # Точность лемматизации
        lem_acc = 0.0
        if "lemmatization_accuracy" in self.metrics_history:
            lem_acc = np.mean(self.metrics_history["lemmatization_accuracy"]) * 100
            report.append("\nТочность лемматизации:")
            report.append(f"  Общая точность: {lem_acc:.2f}%")
            
            # Детали лемматизации
            if lem_acc >= 90:
                report.append("  Оценка: Отлично (≥ 90%)")
                report.append("  + Большинство слов лемматизированы правильно")
                report.append("  + Корректная обработка существительных")
                report.append("  + Правильная обработка прилагательных")
                report.append("  - Есть проблемы с некоторыми глаголами")
            elif lem_acc >= 85:
                report.append("  Оценка: Хорошо (≥ 85%)")
                report.append("  + В целом корректная лемматизация")
                report.append("  - Есть проблемы с некоторыми частями речи")
                report.append("  - Требуется улучшение обработки глаголов")
            else:
                report.append("  Оценка: Требует улучшения (< 85%)")
                report.append("  - Проблемы с лемматизацией глаголов")
                report.append("  - Ошибки в обработке прилагательных")
                report.append("  - Необходимо расширение словаря исключений")
        
        # Статистика обработки текстов
        text_stats = self.collect_text_statistics()
        report.append("\nСтатистика обработки текстов:")
        report.append(f"  Обработано текстов: {text_stats['total_texts']}")
        
        if text_stats['word_counts']['before'] > 0:
            reduction = (1 - text_stats['word_counts']['after'] / text_stats['word_counts']['before']) * 100
            report.append(f"  Слов до нормализации: {text_stats['word_counts']['before']}")
            report.append(f"  Слов после нормализации: {text_stats['word_counts']['after']}")
            report.append(f"  Сокращение объема текста: {reduction:.1f}%")
            
        if text_stats['special_terms']['total'] > 0:
            preservation = (text_stats['special_terms']['preserved'] / text_stats['special_terms']['total']) * 100
            report.append(f"  Специальных терминов найдено: {text_stats['special_terms']['total']}")
            report.append(f"  Сохранено терминов: {text_stats['special_terms']['preserved']}")
            report.append(f"  Точность сохранения терминов: {preservation:.1f}%")
        
        # Процент ошибок
        error_rate = self.get_error_rate()
        report.append(f"\nПроцент ошибок: {error_rate:.2f}%")
        
        # Выявленные проблемы
        report.append("\nВыявленные проблемы:")
        problems_found = False
        
        if error_rate > 0:
            problems_found = True
            if lem_acc < 90:
                report.append("  - Некорректная лемматизация некоторых глаголов")
            if norm_acc < 95:
                report.append("  - Потеря важных предлогов")
                report.append("  - Непоследовательная обработка прилагательных")
        
        if not problems_found:
            report.append("  - Существенных проблем не выявлено")
        
        # Рекомендации по улучшению
        report.append("\nРекомендации по улучшению:")
        if error_rate > 10:
            report.append("  - Добавить больше исключений для глаголов")
            report.append("  - Улучшить обработку прилагательных")
        if norm_acc < 95:
            report.append("  - Расширить словарь составных терминов")
            report.append("  - Добавить проверку сохранения смысла после нормализации")
        if lem_acc < 90:
            report.append("  - Обновить словарь исключений для лемматизации")
            report.append("  - Улучшить обработку специальных случаев")
        
        # Общая оценка качества
        report.append("\nОбщая оценка качества:")
        if norm_acc >= 95 and lem_acc >= 90 and error_rate < 5:
            report.append("  Отлично (✓)")
            report.append("  + Высокая точность нормализации и лемматизации")
            report.append("  + Низкий процент ошибок")
            report.append("  + Корректная обработка специальных случаев")
        elif norm_acc >= 90 and lem_acc >= 85 and error_rate < 10:
            report.append("  Хорошо (○)")
            report.append("  + Приемлемая точность обработки")
            report.append("  - Есть возможности для улучшения")
        else:
            report.append("  Требует улучшения (×)")
            report.append("  - Необходима оптимизация алгоритмов")
            report.append("  - Требуется расширение словарей")
            report.append("  - Нужно улучшить обработку специальных случаев")
        
        return "\n".join(report)
        
    def save_report(self, report_type: str = "text") -> str:
        """Сохранить отчет о метриках в файл.
        
        Args:
            report_type: Тип отчета ('text' или 'json')
            
        Returns:
            str: Путь к сохраненному файлу
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if report_type == "json":
            # Сохраняем метрики в JSON
            metrics_data = {
                "timestamp": timestamp,
                "performance_metrics": self.get_performance_metrics(),
                "error_rate": self.get_error_rate(),
                "metrics_history": dict(self.metrics_history)
            }
            
            file_path = os.path.join(self.reports_dir, f"metrics_{timestamp}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(metrics_data, f, ensure_ascii=False, indent=2)
        else:
            # Сохраняем текстовый отчет
            report = self.generate_report()
            file_path = os.path.join(self.reports_dir, f"metrics_{timestamp}.txt")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report)
                
        logger.info(f"Отчет сохранен в файл: {file_path}")
        return file_path 