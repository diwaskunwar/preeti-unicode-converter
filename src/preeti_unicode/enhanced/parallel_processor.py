"""
Parallel processing capabilities for batch operations.

This module provides parallel processing utilities for handling
large-scale conversion operations efficiently.
"""

import time
import threading
from typing import Any, Dict, List, Optional, Callable, TypeVar, Generic, Union
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed, Future
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path

from preeti_unicode.core.interfaces import IProgressTracker, ProcessingStatus
from preeti_unicode.core.exceptions import ProcessingTimeoutError, PreetiUnicodeError

T = TypeVar('T')
R = TypeVar('R')


class TaskStatus(Enum):
    """Status enumeration for individual tasks."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskResult(Generic[R]):
    """Result of a parallel task execution."""
    task_id: str
    status: TaskStatus
    input_data: Any
    output_data: Optional[R] = None
    error: Optional[Exception] = None
    execution_time: float = 0.0
    worker_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def success(self) -> bool:
        """Check if task completed successfully."""
        return self.status == TaskStatus.COMPLETED and self.error is None


class ParallelProcessor(Generic[T, R]):
    """
    Generic parallel processor for executing tasks concurrently.
    
    Provides flexible parallel processing with support for both
    thread-based and process-based execution.
    """
    
    def __init__(
        self,
        max_workers: int = 4,
        use_processes: bool = False,
        timeout_seconds: Optional[float] = None,
        progress_tracker: Optional[IProgressTracker] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the parallel processor.
        
        Args:
            max_workers: Maximum number of worker threads/processes
            use_processes: Whether to use processes instead of threads
            timeout_seconds: Timeout for individual tasks
            progress_tracker: Optional progress tracker
            logger: Optional logger instance
        """
        self.max_workers = max_workers
        self.use_processes = use_processes
        self.timeout_seconds = timeout_seconds
        self.progress_tracker = progress_tracker
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        
        self._executor_class = ProcessPoolExecutor if use_processes else ThreadPoolExecutor
        self._results: Dict[str, TaskResult[R]] = {}
        self._lock = threading.RLock()
    
    def process_batch(
        self,
        tasks: List[T],
        processor_func: Callable[[T], R],
        task_id_func: Optional[Callable[[T], str]] = None,
        chunk_size: Optional[int] = None
    ) -> Dict[str, TaskResult[R]]:
        """
        Process a batch of tasks in parallel.
        
        Args:
            tasks: List of tasks to process
            processor_func: Function to process each task
            task_id_func: Function to generate task IDs (uses index if None)
            chunk_size: Size of chunks for processing (optional)
            
        Returns:
            Dictionary mapping task IDs to results
        """
        if not tasks:
            return {}
        
        # Generate task IDs
        if task_id_func is None:
            task_ids = [f"task_{i}" for i in range(len(tasks))]
        else:
            task_ids = [task_id_func(task) for task in tasks]
        
        # Initialize progress tracking
        if self.progress_tracker:
            self.progress_tracker.start(len(tasks), "Processing batch")
        
        # Process tasks
        try:
            if chunk_size and len(tasks) > chunk_size:
                return self._process_chunked(tasks, task_ids, processor_func, chunk_size)
            else:
                return self._process_all(tasks, task_ids, processor_func)
        finally:
            if self.progress_tracker:
                self.progress_tracker.finish("Batch processing completed")
    
    def _process_all(
        self,
        tasks: List[T],
        task_ids: List[str],
        processor_func: Callable[[T], R]
    ) -> Dict[str, TaskResult[R]]:
        """Process all tasks in a single batch."""
        results = {}
        
        with self._executor_class(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {}
            for task, task_id in zip(tasks, task_ids):
                future = executor.submit(self._execute_task, task_id, task, processor_func)
                future_to_task[future] = (task_id, task)
            
            # Collect results
            completed_count = 0
            for future in as_completed(future_to_task, timeout=self.timeout_seconds):
                task_id, task = future_to_task[future]
                
                try:
                    result = future.result()
                    results[task_id] = result
                except Exception as e:
                    self.logger.error(f"Task {task_id} failed: {e}")
                    results[task_id] = TaskResult(
                        task_id=task_id,
                        status=TaskStatus.FAILED,
                        input_data=task,
                        error=e
                    )
                
                completed_count += 1
                if self.progress_tracker:
                    self.progress_tracker.update(completed_count, f"Completed {task_id}")
        
        return results
    
    def _process_chunked(
        self,
        tasks: List[T],
        task_ids: List[str],
        processor_func: Callable[[T], R],
        chunk_size: int
    ) -> Dict[str, TaskResult[R]]:
        """Process tasks in chunks."""
        results = {}
        total_tasks = len(tasks)
        
        # Process in chunks
        for i in range(0, total_tasks, chunk_size):
            chunk_tasks = tasks[i:i + chunk_size]
            chunk_ids = task_ids[i:i + chunk_size]
            
            self.logger.debug(f"Processing chunk {i//chunk_size + 1}: {len(chunk_tasks)} tasks")
            
            chunk_results = self._process_all(chunk_tasks, chunk_ids, processor_func)
            results.update(chunk_results)
        
        return results
    
    def _execute_task(self, task_id: str, task: T, processor_func: Callable[[T], R]) -> TaskResult[R]:
        """Execute a single task with error handling and timing."""
        start_time = time.time()
        worker_id = threading.current_thread().name
        
        try:
            self.logger.debug(f"Starting task {task_id} on worker {worker_id}")
            
            # Execute the task
            result = processor_func(task)
            
            execution_time = time.time() - start_time
            
            self.logger.debug(f"Task {task_id} completed in {execution_time:.3f}s")
            
            return TaskResult(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                input_data=task,
                output_data=result,
                execution_time=execution_time,
                worker_id=worker_id
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            self.logger.error(f"Task {task_id} failed after {execution_time:.3f}s: {e}")
            
            return TaskResult(
                task_id=task_id,
                status=TaskStatus.FAILED,
                input_data=task,
                error=e,
                execution_time=execution_time,
                worker_id=worker_id
            )


class BatchProcessor:
    """
    Specialized processor for batch file operations.
    
    Provides high-level batch processing capabilities
    specifically designed for file conversion operations.
    """
    
    def __init__(
        self,
        max_workers: int = 4,
        progress_tracker: Optional[IProgressTracker] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the batch processor.
        
        Args:
            max_workers: Maximum number of worker threads
            progress_tracker: Optional progress tracker
            logger: Optional logger instance
        """
        self.max_workers = max_workers
        self.progress_tracker = progress_tracker
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        
        self.processor = ParallelProcessor[Path, bool](
            max_workers=max_workers,
            progress_tracker=progress_tracker,
            logger=logger
        )
    
    def process_files(
        self,
        input_files: List[Path],
        output_dir: Path,
        converter_func: Callable[[Path, Path], bool],
        output_extension: str = ".txt"
    ) -> Dict[str, bool]:
        """
        Process multiple files in parallel.
        
        Args:
            input_files: List of input file paths
            output_dir: Directory for output files
            converter_func: Function to convert files (input_path, output_path) -> success
            output_extension: Extension for output files
            
        Returns:
            Dictionary mapping input file paths to success status
        """
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create processor function
        def process_file(input_file: Path) -> bool:
            output_file = output_dir / f"{input_file.stem}{output_extension}"
            return converter_func(input_file, output_file)
        
        # Generate task IDs from file paths
        def get_task_id(file_path: Path) -> str:
            return str(file_path)
        
        # Process files
        results = self.processor.process_batch(
            tasks=input_files,
            processor_func=process_file,
            task_id_func=get_task_id
        )
        
        # Convert results to simple success mapping
        success_mapping = {}
        for task_id, result in results.items():
            success_mapping[task_id] = result.success
        
        return success_mapping
    
    def get_statistics(self, results: Dict[str, TaskResult]) -> Dict[str, Any]:
        """
        Get processing statistics from results.
        
        Args:
            results: Processing results
            
        Returns:
            Dictionary containing statistics
        """
        total_tasks = len(results)
        successful_tasks = sum(1 for r in results.values() if r.success)
        failed_tasks = total_tasks - successful_tasks
        
        execution_times = [r.execution_time for r in results.values() if r.execution_time > 0]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        return {
            'total_tasks': total_tasks,
            'successful_tasks': successful_tasks,
            'failed_tasks': failed_tasks,
            'success_rate': successful_tasks / total_tasks if total_tasks > 0 else 0,
            'average_execution_time': avg_execution_time,
            'total_execution_time': sum(execution_times)
        }


class RetryProcessor:
    """
    Processor with retry capabilities for handling transient failures.
    
    Provides automatic retry logic with configurable backoff
    strategies for handling temporary failures.
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_multiplier: float = 2.0,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the retry processor.
        
        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries in seconds
            backoff_multiplier: Multiplier for exponential backoff
            logger: Optional logger instance
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_multiplier = backoff_multiplier
        self.logger = logger or logging.getLogger(self.__class__.__name__)
    
    def execute_with_retry(
        self,
        func: Callable[[], R],
        task_name: str = "task"
    ) -> R:
        """
        Execute a function with retry logic.
        
        Args:
            func: Function to execute
            task_name: Name of the task for logging
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None
        delay = self.retry_delay
        
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    self.logger.info(f"Retrying {task_name} (attempt {attempt + 1}/{self.max_retries + 1})")
                
                return func()
                
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    self.logger.warning(f"{task_name} failed (attempt {attempt + 1}): {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= self.backoff_multiplier
                else:
                    self.logger.error(f"{task_name} failed after {self.max_retries + 1} attempts: {e}")
        
        # All retries failed
        raise last_exception
