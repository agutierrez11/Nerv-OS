import concurrent.futures
from typing import List, Callable, Any
from core.logger import logger

def run_parallel_tasks(tasks: List[Callable], max_workers: int = 5) -> List[Any]:
    """
    Ejecuta una lista de funciones en paralelo usando hilos.
    Ideal para procesar multiples empresas a la vez.
    """
    results = []
    logger.info(f"Iniciando procesamiento paralelo de {len(tasks)} tareas con {max_workers} workers.")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Enviar todas las tareas al executor
        future_to_task = {executor.submit(task): task for task in tasks}
        
        for future in concurrent.futures.as_completed(future_to_task):
            task_name = future_to_task[future].__name__ if hasattr(future_to_task[future], "__name__") else "Unknown"
            try:
                data = future.result()
                results.append(data)
                logger.info(f"Tarea completada exitosamente: {task_name}")
            except Exception as e:
                logger.error(f"Error en tarea paralela {task_name}: {e}")
                results.append(None)
                
    return results
