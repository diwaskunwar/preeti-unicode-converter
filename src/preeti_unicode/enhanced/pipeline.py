"""
Processing pipeline implementation with middleware support.

This module provides a flexible pipeline architecture for processing
text and files through configurable stages with middleware support.
"""

from typing import Any, Dict, List, Optional, Callable, Union, TypeVar, Generic
from abc import ABC, abstractmethod
import logging
import time
from dataclasses import dataclass
from enum import Enum

from preeti_unicode.core.interfaces import IMiddleware, IProgressTracker
from preeti_unicode.core.exceptions import PreetiUnicodeError, ProcessingTimeoutError
from preeti_unicode.core.base_classes import BaseMiddleware

T = TypeVar('T')
R = TypeVar('R')


class StageStatus(Enum):
    """Status enumeration for pipeline stages."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageResult:
    """Result of a pipeline stage execution."""
    stage_name: str
    status: StageStatus
    input_data: Any
    output_data: Any
    execution_time: float
    error: Optional[Exception] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class PipelineStage(ABC, Generic[T, R]):
    """
    Abstract base class for pipeline stages.
    
    A pipeline stage represents a single processing step that can
    transform input data to output data.
    """
    
    def __init__(
        self,
        name: str,
        description: str = "",
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the pipeline stage.
        
        Args:
            name: Name of the stage
            description: Description of what the stage does
            logger: Optional logger instance
        """
        self.name = name
        self.description = description
        self.logger = logger or logging.getLogger(f"Stage.{name}")
        self._middleware: List[IMiddleware] = []
    
    def add_middleware(self, middleware: IMiddleware) -> None:
        """
        Add middleware to this stage.
        
        Args:
            middleware: Middleware to add
        """
        self._middleware.append(middleware)
    
    def execute(self, data: T, context: Dict[str, Any] = None) -> StageResult:
        """
        Execute the stage with middleware support.
        
        Args:
            data: Input data
            context: Optional execution context
            
        Returns:
            Stage execution result
        """
        context = context or {}
        start_time = time.time()
        
        try:
            self.logger.debug(f"Executing stage: {self.name}")
            
            # Apply before middleware
            processed_data = data
            for middleware in self._middleware:
                processed_data = middleware.process_before(processed_data, context=context)
            
            # Execute the main stage logic
            result_data = self._execute_impl(processed_data, context)
            
            # Apply after middleware
            for middleware in reversed(self._middleware):
                result_data = middleware.process_after(result_data, context=context)
            
            execution_time = time.time() - start_time
            
            self.logger.debug(f"Stage {self.name} completed in {execution_time:.3f}s")
            
            return StageResult(
                stage_name=self.name,
                status=StageStatus.COMPLETED,
                input_data=data,
                output_data=result_data,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Stage {self.name} failed: {e}")
            
            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                input_data=data,
                output_data=None,
                execution_time=execution_time,
                error=e
            )
    
    @abstractmethod
    def _execute_impl(self, data: T, context: Dict[str, Any]) -> R:
        """
        Implement the stage-specific logic.
        
        Args:
            data: Input data
            context: Execution context
            
        Returns:
            Processed data
        """
        pass


class ProcessingPipeline:
    """
    Main pipeline class for orchestrating multiple processing stages.
    
    Provides a flexible framework for chaining multiple processing stages
    together with error handling, progress tracking, and middleware support.
    """
    
    def __init__(
        self,
        name: str,
        stages: Optional[List[PipelineStage]] = None,
        progress_tracker: Optional[IProgressTracker] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the processing pipeline.
        
        Args:
            name: Name of the pipeline
            stages: List of pipeline stages
            progress_tracker: Optional progress tracker
            logger: Optional logger instance
        """
        self.name = name
        self.stages = stages or []
        self.progress_tracker = progress_tracker
        self.logger = logger or logging.getLogger(f"Pipeline.{name}")
        self._global_middleware: List[IMiddleware] = []
    
    def add_stage(self, stage: PipelineStage) -> None:
        """
        Add a stage to the pipeline.
        
        Args:
            stage: Stage to add
        """
        self.stages.append(stage)
    
    def add_global_middleware(self, middleware: IMiddleware) -> None:
        """
        Add middleware that applies to all stages.
        
        Args:
            middleware: Middleware to add
        """
        self._global_middleware.append(middleware)
    
    def execute(
        self,
        data: Any,
        context: Optional[Dict[str, Any]] = None,
        stop_on_error: bool = True,
        timeout_seconds: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Execute the pipeline.
        
        Args:
            data: Initial input data
            context: Optional execution context
            stop_on_error: Whether to stop on first error
            timeout_seconds: Optional timeout for the entire pipeline
            
        Returns:
            Dictionary containing execution results
        """
        context = context or {}
        start_time = time.time()
        
        # Initialize progress tracking
        if self.progress_tracker:
            self.progress_tracker.start(len(self.stages), f"Pipeline: {self.name}")
        
        results = []
        current_data = data
        
        try:
            for i, stage in enumerate(self.stages):
                # Check timeout
                if timeout_seconds and (time.time() - start_time) > timeout_seconds:
                    raise ProcessingTimeoutError(
                        f"Pipeline execution timed out after {timeout_seconds} seconds",
                        timeout_seconds=timeout_seconds,
                        operation="pipeline_execution"
                    )
                
                # Add global middleware to stage
                for middleware in self._global_middleware:
                    stage.add_middleware(middleware)
                
                # Execute stage
                stage_result = stage.execute(current_data, context)
                results.append(stage_result)
                
                # Update progress
                if self.progress_tracker:
                    status_msg = f"Completed {stage.name}"
                    if stage_result.status == StageStatus.FAILED:
                        status_msg = f"Failed {stage.name}: {stage_result.error}"
                    self.progress_tracker.update(i + 1, status_msg)
                
                # Handle stage failure
                if stage_result.status == StageStatus.FAILED:
                    if stop_on_error:
                        break
                    else:
                        # Continue with original data if stage failed
                        continue
                
                # Use stage output as input for next stage
                current_data = stage_result.output_data
            
            execution_time = time.time() - start_time
            
            # Finalize progress tracking
            if self.progress_tracker:
                failed_stages = [r for r in results if r.status == StageStatus.FAILED]
                if failed_stages:
                    self.progress_tracker.finish(f"Completed with {len(failed_stages)} failures")
                else:
                    self.progress_tracker.finish("Pipeline completed successfully")
            
            return {
                'success': all(r.status == StageStatus.COMPLETED for r in results),
                'output_data': current_data,
                'stage_results': results,
                'execution_time': execution_time,
                'pipeline_name': self.name
            }
            
        except Exception as e:
            if self.progress_tracker:
                self.progress_tracker.finish(f"Pipeline failed: {str(e)}")
            
            self.logger.error(f"Pipeline {self.name} failed: {e}")
            raise


class PipelineBuilder:
    """
    Builder class for constructing processing pipelines.
    
    Provides a fluent interface for building complex pipelines
    with stages and middleware.
    """
    
    def __init__(self, name: str):
        """
        Initialize the pipeline builder.
        
        Args:
            name: Name of the pipeline to build
        """
        self.name = name
        self._stages: List[PipelineStage] = []
        self._middleware: List[IMiddleware] = []
        self._progress_tracker: Optional[IProgressTracker] = None
        self._logger: Optional[logging.Logger] = None
    
    def add_stage(self, stage: PipelineStage) -> 'PipelineBuilder':
        """
        Add a stage to the pipeline.
        
        Args:
            stage: Stage to add
            
        Returns:
            Self for method chaining
        """
        self._stages.append(stage)
        return self
    
    def add_middleware(self, middleware: IMiddleware) -> 'PipelineBuilder':
        """
        Add global middleware to the pipeline.
        
        Args:
            middleware: Middleware to add
            
        Returns:
            Self for method chaining
        """
        self._middleware.append(middleware)
        return self
    
    def with_progress_tracker(self, tracker: IProgressTracker) -> 'PipelineBuilder':
        """
        Set the progress tracker for the pipeline.
        
        Args:
            tracker: Progress tracker to use
            
        Returns:
            Self for method chaining
        """
        self._progress_tracker = tracker
        return self
    
    def with_logger(self, logger: logging.Logger) -> 'PipelineBuilder':
        """
        Set the logger for the pipeline.
        
        Args:
            logger: Logger to use
            
        Returns:
            Self for method chaining
        """
        self._logger = logger
        return self
    
    def build(self) -> ProcessingPipeline:
        """
        Build the pipeline.
        
        Returns:
            Constructed pipeline instance
        """
        pipeline = ProcessingPipeline(
            name=self.name,
            stages=self._stages.copy(),
            progress_tracker=self._progress_tracker,
            logger=self._logger
        )
        
        # Add global middleware
        for middleware in self._middleware:
            pipeline.add_global_middleware(middleware)
        
        return pipeline


# Concrete stage implementations

class TextConversionStage(PipelineStage[str, str]):
    """Stage for converting text using a converter function."""
    
    def __init__(
        self,
        name: str,
        converter_func: Callable[[str], str],
        description: str = "",
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the text conversion stage.
        
        Args:
            name: Name of the stage
            converter_func: Function to use for conversion
            description: Description of the stage
            logger: Optional logger instance
        """
        super().__init__(name, description, logger)
        self.converter_func = converter_func
    
    def _execute_impl(self, data: str, context: Dict[str, Any]) -> str:
        """
        Execute text conversion.
        
        Args:
            data: Input text
            context: Execution context
            
        Returns:
            Converted text
        """
        return self.converter_func(data)


class ValidationStage(PipelineStage[Any, Any]):
    """Stage for validating data."""
    
    def __init__(
        self,
        name: str,
        validator_func: Callable[[Any], bool],
        description: str = "",
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the validation stage.
        
        Args:
            name: Name of the stage
            validator_func: Function to use for validation
            description: Description of the stage
            logger: Optional logger instance
        """
        super().__init__(name, description, logger)
        self.validator_func = validator_func
    
    def _execute_impl(self, data: Any, context: Dict[str, Any]) -> Any:
        """
        Execute validation.
        
        Args:
            data: Input data
            context: Execution context
            
        Returns:
            Input data if validation passes
            
        Raises:
            ValidationError: If validation fails
        """
        if not self.validator_func(data):
            from ..core.exceptions import ValidationError
            raise ValidationError(f"Validation failed in stage {self.name}")
        
        return data


# Specialized pipeline for conversion

class ConversionPipeline(ProcessingPipeline):
    """
    Specialized pipeline for text conversion operations.
    
    Provides pre-configured stages for common conversion workflows.
    """
    
    @classmethod
    def create_default(
        cls,
        converter_func: Callable[[str], str],
        progress_tracker: Optional[IProgressTracker] = None,
        logger: Optional[logging.Logger] = None
    ) -> 'ConversionPipeline':
        """
        Create a default conversion pipeline.
        
        Args:
            converter_func: Function to use for text conversion
            progress_tracker: Optional progress tracker
            logger: Optional logger instance
            
        Returns:
            Configured conversion pipeline
        """
        pipeline = cls(
            name="DefaultConversion",
            progress_tracker=progress_tracker,
            logger=logger
        )
        
        # Add validation stage
        pipeline.add_stage(ValidationStage(
            name="InputValidation",
            validator_func=lambda x: x is not None and isinstance(x, str),
            description="Validate input text"
        ))
        
        # Add conversion stage
        pipeline.add_stage(TextConversionStage(
            name="TextConversion",
            converter_func=converter_func,
            description="Convert text using provided function"
        ))
        
        # Add output validation stage
        pipeline.add_stage(ValidationStage(
            name="OutputValidation",
            validator_func=lambda x: x is not None and isinstance(x, str),
            description="Validate output text"
        ))
        
        return pipeline
