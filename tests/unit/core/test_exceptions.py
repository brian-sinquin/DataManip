"""Unit tests for core exception classes."""

import pytest
from core.exceptions import (
    DataManipError,
    DataObjectError,
    ColumnNotFoundError,
    ColumnExistsError,
    InvalidColumnTypeError,
    FormulaError,
    FormulaSyntaxError,
    FormulaEvaluationError,
    CircularDependencyError,
    MissingDependencyError,
    UncertaintyError,
    UncertaintyPropagationError,
    MissingUncertaintyError,
    StudyError,
    StudyNotFoundError,
    InvalidStudyTypeError,
    WorkspaceError,
    ConstantNotFoundError,
    ConstantEvaluationError,
    IOError,
    FileImportError
)


class TestBaseException:
    """Tests for base DataManipError exception."""
    
    def test_basic_error(self):
        """Test basic exception creation."""
        error = DataManipError("Test error")
        assert str(error) == "Test error"
    
    def test_error_inheritance(self):
        """Test that all custom exceptions inherit from DataManipError."""
        assert issubclass(DataObjectError, DataManipError)
        assert issubclass(FormulaError, DataManipError)
        assert issubclass(WorkspaceError, DataManipError)
        assert issubclass(StudyError, DataManipError)


class TestDataObjectExceptions:
    """Tests for DataObject-related exceptions."""
    
    def test_column_not_found_error(self):
        """Test ColumnNotFoundError exception."""
        error = ColumnNotFoundError("x")
        assert isinstance(error, DataObjectError)
        assert "x" in str(error)
    
    def test_column_exists_error(self):
        """Test ColumnExistsError exception."""
        error = ColumnExistsError("x")
        assert isinstance(error, DataObjectError)
        assert "x" in str(error)
    
    def test_invalid_column_type_error(self):
        """Test InvalidColumnTypeError exception."""
        error = InvalidColumnTypeError("x", ["DATA", "CALCULATED"])
        assert isinstance(error, DataObjectError)
        assert "x" in str(error)


class TestFormulaExceptions:
    """Tests for formula-related exceptions."""
    
    def test_formula_syntax_error(self):
        """Test FormulaSyntaxError exception."""
        error = FormulaSyntaxError("x + y +")
        assert isinstance(error, FormulaError)
        assert "x + y +" in str(error)
    
    def test_formula_evaluation_error(self):
        """Test FormulaEvaluationError exception."""
        inner_error = ValueError("Division by zero")
        error = FormulaEvaluationError("{x}/{y}", inner_error)
        assert isinstance(error, FormulaError)
        assert "Division by zero" in str(error)
    
    def test_circular_dependency_error(self):
        """Test CircularDependencyError exception."""
        error = CircularDependencyError(["x", "y", "x"])
        assert isinstance(error, FormulaError)
        assert "x" in str(error)
        assert "y" in str(error)
    
    def test_missing_dependency_error(self):
        """Test MissingDependencyError exception."""
        error = MissingDependencyError("undefined_var", "{x}+{undefined_var}")
        assert isinstance(error, FormulaError)
        assert "undefined_var" in str(error)


class TestUncertaintyExceptions:
    """Tests for uncertainty-related exceptions."""
    
    def test_uncertainty_propagation_error(self):
        """Test UncertaintyPropagationError exception."""
        error = UncertaintyPropagationError("column_x", "Cannot propagate uncertainty")
        assert isinstance(error, UncertaintyError)
        assert "Cannot propagate" in str(error)
        assert "column_x" in str(error)
    
    def test_missing_uncertainty_error(self):
        """Test MissingUncertaintyError exception."""
        error = MissingUncertaintyError("column_x")
        assert isinstance(error, UncertaintyError)
        assert "column_x" in str(error)


class TestWorkspaceExceptions:
    """Tests for workspace-related exceptions."""
    
    def test_study_not_found_error(self):
        """Test StudyNotFoundError exception."""
        error = StudyNotFoundError("NonExistentStudy")
        assert isinstance(error, StudyError)
        assert "NonExistentStudy" in str(error)
    
    def test_invalid_study_type_error(self):
        """Test InvalidStudyTypeError exception."""
        error = InvalidStudyTypeError("InvalidType")
        assert isinstance(error, StudyError)
        assert "InvalidType" in str(error)
    
    def test_constant_not_found_error(self):
        """Test ConstantNotFoundError exception."""
        error = ConstantNotFoundError("missing_const")
        assert isinstance(error, WorkspaceError)
        assert "missing_const" in str(error)
    
    def test_constant_evaluation_error(self):
        """Test ConstantEvaluationError exception."""
        inner_error = ValueError("Evaluation failed")
        error = ConstantEvaluationError("const_name", inner_error)
        assert isinstance(error, WorkspaceError)
        assert "const_name" in str(error)


class TestIOExceptions:
    """Tests for I/O-related exceptions."""
    
    def test_file_import_error(self):
        """Test FileImportError exception."""
        error = FileImportError("file.csv", "Invalid format")
        assert isinstance(error, IOError)
        assert "file.csv" in str(error)


class TestExceptionRaising:
    """Tests for actually raising exceptions."""
    
    def test_raise_data_object_error(self):
        """Test raising DataObjectError."""
        with pytest.raises(DataObjectError) as exc_info:
            raise DataObjectError("Test error")
        assert "Test error" in str(exc_info.value)
    
    def test_raise_formula_error(self):
        """Test raising FormulaError."""
        with pytest.raises(FormulaError) as exc_info:
            raise FormulaSyntaxError("Bad formula")
        assert "Bad formula" in str(exc_info.value)
    
    def test_raise_workspace_error(self):
        """Test raising WorkspaceError."""
        with pytest.raises(WorkspaceError) as exc_info:
            raise ConstantNotFoundError("Missing")
        assert "Missing" in str(exc_info.value)
    
    def test_catch_base_exception(self):
        """Test catching base DataManipError."""
        try:
            raise ColumnNotFoundError("x")
        except DataManipError as e:
            assert isinstance(e, ColumnNotFoundError)
            assert "x" in str(e)
    
    def test_catch_specific_exception(self):
        """Test catching specific exception type."""
        try:
            raise CircularDependencyError(["a", "b", "a"])
        except CircularDependencyError as e:
            assert "a" in str(e)
            assert "b" in str(e)


class TestExceptionDocumentation:
    """Tests to ensure exceptions are well-documented."""
    
    def test_all_exceptions_have_docstrings(self):
        """Test that all exception classes have docstrings."""
        exception_classes = [
            DataManipError, DataObjectError, ColumnNotFoundError,
            ColumnExistsError, InvalidColumnTypeError,
            FormulaError, FormulaSyntaxError, FormulaEvaluationError,
            CircularDependencyError, MissingDependencyError,
            UncertaintyError, UncertaintyPropagationError, MissingUncertaintyError,
            StudyError, StudyNotFoundError, InvalidStudyTypeError,
            WorkspaceError, ConstantNotFoundError, ConstantEvaluationError,
            IOError, FileImportError
        ]
        
        for exc_class in exception_classes:
            assert exc_class.__doc__ is not None, f"{exc_class.__name__} missing docstring"
            assert len(exc_class.__doc__.strip()) > 0, f"{exc_class.__name__} has empty docstring"
