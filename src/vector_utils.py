import numpy as np

def normalize_vector(vector):
    """
    Нормализация вектора
    
    Args:
        vector: Входной вектор (может быть sparse matrix или numpy array)
        
    Returns:
        Нормализованный вектор
    """
    # Преобразуем sparse matrix в dense array
    if hasattr(vector, 'toarray'):
        vector = vector.toarray()
    
    # Проверяем на NaN и Inf
    if np.isnan(vector).any() or np.isinf(vector).any():
        print("Предупреждение: обнаружены NaN или Inf значения в векторе")
        vector = np.nan_to_num(vector, nan=0.0, posinf=1.0, neginf=-1.0)
    
    # Нормализуем вектор
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
    
    return vector 