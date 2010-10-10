#
#     Copyright 2010, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an attempt of building an optimizing Python compiler
#     that is compatible and integrates with CPython, but also works on its
#     own.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
#

from templates.CodeTemplatesMain import *

from templates.CodeTemplatesCompiledGeneratorType import *
from templates.CodeTemplatesCompiledFunctionType import *
from templates.CodeTemplatesCompiledGenexprType import *

from templates.CodeTemplatesFunction import *
from templates.CodeTemplatesGeneratorExpression import *
from templates.CodeTemplatesGeneratorFunction import *
from templates.CodeTemplatesListContraction import *

from templates.CodeTemplatesParameterParsing import *

from templates.CodeTemplatesAssignments import *
from templates.CodeTemplatesExceptions import *
from templates.CodeTemplatesImporting import *
from templates.CodeTemplatesClass import *
from templates.CodeTemplatesLoops import *

global_copyright = """
// Generated code for Python source for module '%(name)s'

// This code is in part copyright Kay Hayen, license GPLv3. This has the consequence that
// your must either obtain a commercial license or also publish your original source code
// under the same license unless you don't distribute this source or its binary.
"""

module_header = """
// Generated code for Python source for module '%(name)s'

"""

# Template for the global stuff that must be had, compiling one or multple modules.
global_prelude = """\

#ifdef __NUITKA_NO_ASSERT__
#define NDEBUG
#endif

// Include the Python C/API header files

#include "Python.h"
#include "methodobject.h"
#include "frameobject.h"
#include <stdio.h>
#include <string>

// An idea I first saw used with Cython, hint the compiler about branches that are more or
// less likely to be taken. And hint the compiler about things that we assume to be
// normally true. If other compilers can do similar, I would be grateful for howtos.

#ifdef __GNUC__
#define likely(x) __builtin_expect(!!(x), 1)
#define unlikely(x) __builtin_expect(!!(x), 0)
#else
#define likely(x) (x)
#define unlikely(x) (x)
#endif

// An idea to reduce the amount of exported symbols, esp. as we are using C++ and classes
// do not allow to limit their visibility normally.
#ifdef __GNUC__
#define NUITKA_MODULE_INIT_FUNCTION PyMODINIT_FUNC __attribute__((visibility( "default" )))
#else
#define NUITKA_MODULE_INIT_FUNCTION PyMODINIT_FUNC
#endif

static PyObject *_expression_temps[100];
static PyObject *_eval_globals_tmp;
static PyObject *_eval_locals_tmp;

// From CPython, to allow us quick access to the dictionary of an module.
typedef struct {
        PyObject_HEAD
        PyObject *md_dict;
} PyModuleObject;

"""

global_helper = """\

template<typename... P>
static void PRINT_ITEMS( bool new_line, PyObject *file, P...eles );
static PyObject *INCREASE_REFCOUNT( PyObject *object );

static int _current_line = -1;
static char *_current_file = NULL;

class _PythonException
{
    public:
        _PythonException()
        {
            this->line = _current_line;

            this->_importFromPython();
        }

        _PythonException( PyObject *exception )
        {
            assert( exception );
            assert( exception->ob_refcnt > 0 );

            this->line = _current_line;

            Py_INCREF( exception );

            this->exception_type = exception;
            this->exception_value = NULL;
            this->exception_tb = NULL;
        }

        _PythonException( PyObject *exception, PyTracebackObject *traceback )
        {
            assert( exception );
            assert( exception->ob_refcnt > 0 );

            assert( traceback );
            assert( traceback->ob_refcnt > 0 );

            this->line = _current_line;

            this->exception_type = exception;
            this->exception_value = NULL;
            this->exception_tb = (PyObject *)traceback;
        }

        _PythonException( PyObject *exception, PyObject *value, float unused )
        {
            assert( exception );
            assert( value );
            assert( exception->ob_refcnt > 0 );
            assert( value->ob_refcnt > 0 );

            this->line = _current_line;

            Py_INCREF( exception );
            Py_INCREF( value );

            this->exception_type = exception;
            this->exception_value = value;
            this->exception_tb = NULL;
        }

        _PythonException( PyObject *exception, PyObject *value, PyTracebackObject *traceback )
        {
            assert( exception );
            assert( value );
            assert( traceback );
            assert( exception->ob_refcnt > 0 );
            assert( value->ob_refcnt > 0 );
            assert( traceback->ob_refcnt > 0 );

            this->line = _current_line;

            this->exception_type = exception;
            this->exception_value = value;
            this->exception_tb = (PyObject *)traceback;
        }

        _PythonException( const _PythonException &other )
        {
            this->line            = other.line;

            this->exception_type  = other.exception_type;
            this->exception_value = other.exception_value;
            this->exception_tb    = other.exception_tb;

            Py_XINCREF( this->exception_type );
            Py_XINCREF( this->exception_value );
            Py_XINCREF( this->exception_tb );
        }

        void operator=( const _PythonException &other )
        {
            Py_XINCREF( other.exception_type );
            Py_XINCREF( other.exception_value );
            Py_XINCREF( other.exception_tb );

            Py_XDECREF( this->exception_type );
            Py_XDECREF( this->exception_value );
            Py_XDECREF( this->exception_tb );

            this->line            = other.line;

            this->exception_type  = other.exception_type;
            this->exception_value = other.exception_value;
            this->exception_tb    = other.exception_tb;

        }

        ~_PythonException()
        {
            Py_XDECREF( this->exception_type );
            Py_XDECREF( this->exception_value );
            Py_XDECREF( this->exception_tb );
        }

        inline void _importFromPython()
        {

            PyErr_Fetch( &this->exception_type, &this->exception_value, &this->exception_tb );
            assert( this->exception_type );

            // PyErr_NormalizeException( &this->exception_type, &this->exception_value, &this->exception_tb );
            PyErr_Clear();
        }

        inline int getLine() const
        {
            return this->line;
        }

        inline bool matches( PyObject *exception ) const
        {
            return PyErr_GivenExceptionMatches( this->exception_type, exception ) || PyErr_GivenExceptionMatches( this->exception_value, exception );;
        }

        inline void toPython()
        {
            PyErr_Restore( this->exception_type, this->exception_value, this->exception_tb );

            PyThreadState *thread_state = PyThreadState_GET();

            assert( this->exception_type == thread_state->curexc_type );
            assert( thread_state->curexc_type );

            this->exception_type  = NULL;
            this->exception_value = NULL;
            this->exception_tb    = NULL;
        }

        inline void toExceptionHandler()
        {
            // Restore only sets the current exception to the interpreter.
            PyThreadState *thread_state = PyThreadState_GET();

            PyObject *old_type  = thread_state->exc_type;
            PyObject *old_value = thread_state->exc_value;
            PyObject *old_tb    = thread_state->exc_traceback;

            thread_state->exc_type = this->exception_type;
            thread_state->exc_value = this->exception_value;
            thread_state->exc_traceback = this->exception_tb;

            Py_INCREF(  thread_state->exc_type );
            Py_XINCREF( thread_state->exc_value );
            Py_XINCREF(  thread_state->exc_traceback );

            Py_XDECREF( old_type );
            Py_XDECREF( old_value );
            Py_XDECREF( old_tb );

            PySys_SetObject( (char *)"exc_type", thread_state->exc_type );
            PySys_SetObject( (char *)"exc_value", thread_state->exc_value );
            PySys_SetObject( (char *)"exc_traceback", thread_state->exc_traceback );
        }

        inline PyObject *getType()
        {
            if ( this->exception_value == NULL )
            {
                PyErr_NormalizeException( &this->exception_type, &this->exception_value, &this->exception_tb );
            }

            return this->exception_type;
        }

        inline PyObject *getTraceback() const
        {
            return this->exception_tb;
        }

        inline PyObject *setTraceback( PyTracebackObject *traceback )
        {
            assert( traceback );
            assert( traceback->ob_refcnt > 0 );

            // printf( "setTraceback %d\\n", traceback->ob_refcnt );

            // Py_INCREF( traceback );
            this->exception_tb = (PyObject *)traceback;
        }

        inline bool hasTraceback() const
        {
            return this->exception_tb != NULL;
        }

        void setType( PyObject *exception_type )
        {
            Py_XDECREF( this->exception_type );
            this->exception_type = exception_type;
        }

        inline PyObject *getObject()
        {
            PyErr_NormalizeException( &this->exception_type, &this->exception_value, &this->exception_tb );

            return this->exception_value;
        }

        void dump() const
        {
            PRINT_ITEMS( true, NULL, this->exception_type );
        }


    protected:
        PyObject *exception_type, *exception_value, *exception_tb;
        int line;
};

class _PythonExceptionKeeper
{
    public:
        _PythonExceptionKeeper()
        {
            empty = true;
        }

        ~_PythonExceptionKeeper()
        {
            if ( this->empty == false)
            {
                delete this->saved;
            }
        }

        void save( const _PythonException &e )
        {
            this->saved = new _PythonException( e );

            empty = false;
        }

        void rethrow()
        {
            if (empty == false)
            {
                throw *this->saved;
            }
        }

        bool isEmpty() const
        {
            return this->empty;
        }

    protected:
        bool empty;

        _PythonException *saved;
};

class ContinueException
{
};

class BreakException
{
};

// Helper functions for reference count handling in the fly.
static PyObject *INCREASE_REFCOUNT( PyObject *object )
{
    assert( object->ob_refcnt > 0 );

    Py_INCREF( object );

    return object;
}

static PyObject *DECREASE_REFCOUNT( PyObject *object )
{
    Py_DECREF( object );

    return object;
}


// Helper functions for print. Need to play nice with Python softspace behaviour.


static void PRINT_ITEM_TO( PyObject *file, PyObject *object )
{
    PyObject *str = PyObject_Str( object );
    PyObject *print;
    bool softspace;

    if ( str == NULL )
    {
        PyErr_Clear();

        print = object;
        softspace = false;
    }
    else
    {
        char *buffer;
        Py_ssize_t length;

        int status = PyString_AsStringAndSize( str, &buffer, &length );
        assert( status != -1 );

        softspace = length > 0 && buffer[length - 1 ] == '\\t';

        print = str;
    }

    // Check for soft space indicator, need to hold a reference to the file
    // or else __getattr__ may release "file" in the mean time.
    if ( PyFile_SoftSpace( file, !softspace ) )
    {
        if (unlikely( PyFile_WriteString( " ", file ) == -1 ))
        {
            Py_DECREF( file );
            Py_DECREF( str );
            throw _PythonException();
        }
    }

    if ( unlikely( PyFile_WriteObject( print, file, Py_PRINT_RAW ) == -1 ))
    {
        Py_XDECREF( str );
        throw _PythonException();
    }

    Py_XDECREF( str );

    if ( softspace )
    {
        PyFile_SoftSpace( file, !softspace );
    }
}

static void PRINT_NEW_LINE_TO( PyObject *file )
{
    if (unlikely( PyFile_WriteString( "\\n", file ) == -1))
    {
        throw _PythonException();
    }

    PyFile_SoftSpace( file, 0 );
}

template<typename... P>
static void PRINT_ITEMS( bool new_line, PyObject *file, P...eles )
{
    int size = sizeof...(eles);

    if ( file == NULL || file == Py_None )
    {
        file = PySys_GetObject((char *)"stdout");
    }

    // Need to hold a reference for the case that the printing somehow removes
    // the last reference to "file" while printing.
    Py_INCREF( file );

    PyObject *elements[] = {eles...};

    for( int i = 0; i < size; i++ )
    {
        PRINT_ITEM_TO( file, elements[ i ] );
    }

    if ( new_line )
    {
        PRINT_NEW_LINE_TO( file );
    }

    // TODO: Use of PyObjectTemporary should be possible, this won't be
    // exception safe otherwise
    Py_DECREF( file );
}


static void PRINT_NEW_LINE( void )
{
    PyObject *stdout = PySys_GetObject((char *)"stdout");

    if (unlikely( stdout == NULL ))
    {
        PyErr_Format( PyExc_RuntimeError, "problem with stdout" );
        throw _PythonException();
    }

    PRINT_NEW_LINE_TO( stdout );
}


static void RAISE_EXCEPTION( PyObject *exception, PyTracebackObject *traceback )
{
    if ( PyExceptionClass_Check( exception ) )
    {
        throw _PythonException( exception, traceback );
    }
    else if ( PyExceptionInstance_Check( exception ) )
    {
        throw _PythonException( INCREASE_REFCOUNT( PyExceptionInstance_Class( exception ) ), exception, traceback );
    }
    else
    {
        PyErr_Format( PyExc_TypeError, "exceptions must be old-style classes or derived from BaseException, not %s", exception->ob_type->tp_name );
        throw _PythonException();
    }
}

static void RAISE_EXCEPTION( PyObject *exception_type, PyObject *value, PyTracebackObject *traceback )
{
    // TODO: Check traceback

    if ( PyExceptionClass_Check( exception_type ) )
    {
       PyErr_NormalizeException( &exception_type, &value, (PyObject **)&traceback );
    }

    throw _PythonException( exception_type, value, traceback );
}

static inline void RAISE_EXCEPTION( PyObject *exception_type, PyObject *value, PyObject *traceback )
{
    RAISE_EXCEPTION( exception_type, value, (PyTracebackObject *)traceback );
}


static bool CHECK_IF_TRUE( PyObject *object )
{
    assert( object != NULL );
    assert( object->ob_refcnt > 0 );

    int status = PyObject_IsTrue( object );

    if (unlikely( status == -1 ))
    {
        throw _PythonException();
    }

    return status == 1;
}

static bool CHECK_IF_FALSE( PyObject *object )
{
    assert( object != NULL );
    assert( object->ob_refcnt > 0 );

    int status = PyObject_Not( object );

    if (unlikely( status == -1 ))
    {
        throw _PythonException();
    }

    return status == 1;
}

static PyObject *BOOL_FROM( bool value )
{
    return value ? _python_bool_True : _python_bool_False;
}

static PyObject *UNARY_NOT( PyObject *object )
{
    int result = PyObject_Not( object );

    if (unlikely( result == -1 ))
    {
        throw _PythonException();
    }

    return BOOL_FROM( result == 1 );
}

typedef PyObject *(binary_api)( PyObject *, PyObject * );

static PyObject *BINARY_OPERATION( binary_api api, PyObject *operand1, PyObject *operand2 )
{
    int line = _current_line;
    PyObject *result = api( operand1, operand2 );
    _current_line = line;

    if (unlikely (result == NULL))
    {
        throw _PythonException();
    }

    return result;
}

typedef PyObject *(unary_api)( PyObject * );

static PyObject *UNARY_OPERATION( unary_api api, PyObject *operand )
{
    PyObject *result = api( operand );

    if (unlikely (result == NULL))
    {
        throw _PythonException();
    }

    return result;
}

static PyObject *POWER_OPERATION( PyObject *operand1, PyObject *operand2 )
{
    PyObject *result = PyNumber_Power( operand1, operand2, Py_None );

    if (unlikely (result == NULL))
    {
        throw _PythonException();
    }

    return result;
}

static PyObject *POWER_OPERATION_INPLACE( PyObject *operand1, PyObject *operand2 )
{
    PyObject *result = PyNumber_InPlacePower( operand1, operand2, Py_None );

    if (unlikely (result == NULL))
    {
        throw _PythonException();
    }

    return result;
}

static PyObject *RICH_COMPARE( int opid, PyObject *operand2, PyObject *operand1 )
{
    int line = _current_line;
    PyObject *result = PyObject_RichCompare( operand1, operand2, opid );
    _current_line = line;

    if (unlikely (result == NULL))
    {
        throw _PythonException();
    }

    return result;
}

static bool RICH_COMPARE_BOOL( int opid, PyObject *operand2, PyObject *operand1 )
{
    int line = _current_line;
    int result = PyObject_RichCompareBool( operand1, operand2, opid );
    _current_line = line;

    if (unlikely( result == -1 ))
    {
        throw _PythonException();
    }

    return result == 1;
}


static PyObject *SEQUENCE_CONTAINS( PyObject *sequence, PyObject *element)
{
    int result = PySequence_Contains( sequence, element );

    if (unlikely( result == -1 ))
    {
        throw _PythonException();
    }

    return BOOL_FROM( result == 1 );
}

static PyObject *SEQUENCE_CONTAINS_NOT( PyObject *sequence, PyObject *element)
{
    int result = PySequence_Contains( sequence, element );

    if (unlikely( result == -1 ))
    {
        throw _PythonException();
    }

    return BOOL_FROM( result == 0 );
}


// Helper functions to debug the compiler operation.
static void PRINT_REFCOUNT( PyObject *object )
{
   PyObject *stdout = PySys_GetObject((char *)"stdout");

   if (unlikely( stdout == NULL ))
   {
      PyErr_Format( PyExc_RuntimeError, "problem with stdout" );
      throw _PythonException();
   }

   char buffer[1024];
   sprintf( buffer, " refcnt %d ", object->ob_refcnt );

   if (unlikely( PyFile_WriteString(buffer, stdout) == -1 ))
   {
      throw _PythonException();
   }

}

static PyObject *CALL_FUNCTION( PyObject *named_args, PyObject *positional_args, PyObject *function_object )
{
    assert( function_object != NULL );
    assert( function_object->ob_refcnt > 0 );
    assert( positional_args != NULL );
    assert( positional_args->ob_refcnt > 0 );
    assert( named_args == NULL || named_args->ob_refcnt > 0 );

    int line = _current_line;
    PyObject *result = PyObject_Call( function_object, positional_args, named_args );
    _current_line = line;

    if (unlikely (result == NULL))
    {
        throw _PythonException();
    }

    return result;
}

static PyObject *TO_TUPLE( PyObject *seq_obj )
{
    PyObject *result = PySequence_Tuple( seq_obj );

    if (unlikely (result == NULL))
    {
        throw _PythonException();
    }

    return result;
}

template<typename... P>
static PyObject *MAKE_TUPLE( P...eles )
{
    int size = sizeof...(eles);

    if ( size > 0 )
    {
        PyObject *elements[] = {eles...};

        for ( Py_ssize_t i = 0; i < size; i++ )
        {
            assert (elements[ i ] != NULL);
            assert (elements[ i ]->ob_refcnt > 0);
        }

        PyObject *result = PyTuple_New( size );

        if (unlikely (result == NULL))
        {
            throw _PythonException();
        }

        for ( Py_ssize_t i = 0; i < size; i++ )
        {
            PyTuple_SET_ITEM( result, i, INCREASE_REFCOUNT( elements[ size - 1 - i ] ));
        }

        assert( result->ob_refcnt == 1 );

        return result;
    }
    else
    {
        return INCREASE_REFCOUNT( _python_tuple_empty );
    }
}

template<typename... P>
static PyObject *MAKE_LIST( P...eles )
{
    PyObject *elements[] = {eles...};

    int size = sizeof...(eles);

    PyObject *result = PyList_New( size );

    if (unlikely (result == NULL))
    {
        throw _PythonException();
    }

    for (Py_ssize_t i = 0; i < size; i++ )
    {
        assert (elements[ i ] != NULL);
        assert (elements[ i ]->ob_refcnt > 0);

        PyList_SET_ITEM( result, i, elements[ size - 1 - i ] );
    }

    assert( result->ob_refcnt == 1 );

    return result;
}

template<typename... P>
static PyObject *MAKE_DICT( P...eles )
{
    PyObject *elements[] = {eles...};
    int size = sizeof...(eles);

    assert (size % 2 == 0);

    PyObject *result = PyDict_New();

    if (unlikely (result == NULL))
    {
        throw _PythonException();
    }

    for( int i = 0; i < size; i += 2 )
    {
        int status = PyDict_SetItem( result, elements[i], elements[i+1] );

        if (unlikely( status == -1 ))
        {
            throw _PythonException();
        }
    }

    return result;
}

static PyObject *MERGE_DICTS( PyObject *dict_a, PyObject *dict_b, bool allow_conflict )
{
    PyObject *result = PyDict_Copy( dict_a );

    if (unlikely (result == NULL))
    {
        throw _PythonException();
    }

    int status = PyDict_Merge( result, dict_b, 1 );

    if (unlikely( status == -1 ))
    {
        Py_DECREF( result );

        throw _PythonException();
    }

    if ( allow_conflict == false && PyDict_Size( dict_a ) + PyMapping_Size( dict_b ) != PyDict_Size( result ))
    {
        Py_DECREF( result );

        PyErr_Format( PyExc_TypeError, "got multiple values for keyword argument" );
        throw _PythonException();
    }

    return result;
}

static void DICT_SET_ITEM( PyObject *dict, PyObject *key, PyObject *value )
{
    int status = PyDict_SetItem( dict, key, value );

    if (unlikely( status == -1))
    {
        throw _PythonException();
    }
}

template<typename... P>
static PyObject *MAKE_SET( P...eles )
{
    PyObject *tuple = MAKE_TUPLE( eles... );

    PyObject *result = PySet_New( tuple );

    Py_DECREF( tuple );

    if (unlikely (result == NULL))
    {
        throw _PythonException();
    }

    return result;
}

static PyObject *MAKE_STATIC_METHOD( PyObject *method )
{
    PyObject *attempt = PyStaticMethod_New( method );

    if ( attempt )
    {
        return attempt;
    }
    else
    {
        PyErr_Clear();

        return method;
    }
}

static PyObject *SEQUENCE_ELEMENT( PyObject *sequence, Py_ssize_t element )
{
    PyObject *result = PySequence_GetItem( sequence, element );

    if (unlikely (result == NULL))
    {
        throw _PythonException();
    }

    return result;
}

static PyObject *MAKE_ITERATOR( PyObject *iterated )
{
    PyObject *result = PyObject_GetIter( iterated );

    if (unlikely (result == NULL))
    {
        throw _PythonException();
    }

    return result;
}

// Return the next item of an iterator. Avoiding any exception for end of iteration, callers must
// deal with NULL return as end of iteration, but will know it wasn't an Python exception, that will show as a thrown exception.
static PyObject *ITERATOR_NEXT( PyObject *iterator )
{
    assert( iterator != NULL );
    assert( iterator->ob_refcnt > 0 );

    int line = _current_line;
    PyObject *result = PyIter_Next( iterator );
    _current_line = line;

    if (unlikely (result == NULL))
    {
        if ( PyErr_Occurred() != NULL )
        {
            throw _PythonException();
        }
    }
    else
    {
        assert( result->ob_refcnt > 0 );
    }

    return result;
}

static inline PyObject *UNPACK_NEXT( PyObject *iterator, int seq_size_so_far )
{
    assert( iterator != NULL );
    assert( iterator->ob_refcnt > 0 );

    PyObject *result = PyIter_Next( iterator );

    if (unlikely (result == NULL))
    {
        if ( seq_size_so_far == 1 )
        {
            PyErr_Format( PyExc_ValueError, "need more than 1 value to unpack" );
        }
        else
        {
            PyErr_Format( PyExc_ValueError, "need more than %d values to unpack", seq_size_so_far );
        }

        throw _PythonException();
    }

    assert( result->ob_refcnt > 0 );

    return result;
}

static inline void UNPACK_ITERATOR_CHECK( PyObject *iterator )
{
    PyObject *attempt = PyIter_Next( iterator );

    if (likely( attempt == NULL ))
    {
        PyErr_Clear();
    }
    else
    {
        Py_DECREF( attempt );

        PyErr_Format( PyExc_ValueError, "too many values to unpack" );
        throw _PythonException();
    }
}


static PyObject *SELECT_IF_TRUE( PyObject *object )
{
    assert( object != NULL );
    assert( object->ob_refcnt > 0 );

    if ( CHECK_IF_TRUE( object ) )
    {
        return object;
    }
    else
    {
        Py_DECREF( object );

        return NULL;
    }
}

static PyObject *SELECT_IF_FALSE( PyObject *object )
{
    assert( object != NULL );
    assert( object->ob_refcnt > 0 );

    if ( CHECK_IF_FALSE( object ) )
    {
        return object;
    }
    else
    {
        Py_DECREF( object );

        return NULL;
    }
}

static PyObject *LOOKUP_SUBSCRIPT( PyObject *source, PyObject *subscript )
{
    assert (source);
    assert (source->ob_refcnt > 0);
    assert (subscript);
    assert (subscript->ob_refcnt > 0);

    PyObject *result = PyObject_GetItem( source, subscript );

    if (unlikely (result == NULL))
    {
        throw _PythonException();
    }

    return result;
}

static bool HAS_KEY( PyObject *source, PyObject *key )
{
    assert (source);
    assert (source->ob_refcnt > 0);
    assert (key);
    assert (key->ob_refcnt > 0);

    return PyMapping_HasKey( source, key ) != 0;
}

static PyObject *LOOKUP_VARS( PyObject *source )
{
    assert (source);
    assert (source->ob_refcnt > 0);

    static PyObject *dict_str = PyString_FromString( "__dict__" );

    PyObject *result = PyObject_GetAttr( source, dict_str );

    if (unlikely (result == NULL))
    {
        throw _PythonException();
    }

    return result;
}


static void SET_SUBSCRIPT( PyObject *target, PyObject *subscript, PyObject *value )
{
    assert (target);
    assert (target->ob_refcnt > 0);
    assert (subscript);
    assert (subscript->ob_refcnt > 0);
    assert (value);
    assert (value->ob_refcnt > 0);

    int status = PyObject_SetItem( target, subscript, value );

    if (unlikely( status == -1 ))
    {
        throw _PythonException();
    }
}

static void DEL_SUBSCRIPT( PyObject *target, PyObject *subscript )
{
    assert (target);
    assert (target->ob_refcnt > 0);
    assert (subscript);
    assert (subscript->ob_refcnt > 0);

    int status = PyObject_DelItem( target, subscript );

    if (unlikely( status == -1 ))
    {
        throw _PythonException();
    }
}


static PyObject *LOOKUP_SLICE( PyObject *source, Py_ssize_t lower, Py_ssize_t upper )
{
    assert (source);
    assert (source->ob_refcnt > 0);

    PyObject *result = PySequence_GetSlice( source, lower, upper);

    if (unlikely (result == NULL))
    {
        throw _PythonException();
    }

    return result;
}

static void SET_SLICE( PyObject *target, Py_ssize_t lower, Py_ssize_t upper, PyObject *value )
{
    assert (target);
    assert (target->ob_refcnt > 0);
    assert (value);
    assert (value->ob_refcnt > 0);

    int status = PySequence_SetSlice( target, lower, upper, value );

    if (unlikely( status == -1 ))
    {
        throw _PythonException();
    }
}

static Py_ssize_t CONVERT_TO_INDEX( PyObject *value );

static void DEL_SLICE( PyObject *target, PyObject *lower, PyObject *upper )
{
    assert (target);
    assert (target->ob_refcnt > 0);

    if ( target->ob_type->tp_as_sequence && target->ob_type->tp_as_sequence->sq_ass_slice )
    {
        int status = PySequence_DelSlice( target, lower != Py_None ? CONVERT_TO_INDEX( lower ) : 0, upper != Py_None ? CONVERT_TO_INDEX( upper ) : PY_SSIZE_T_MAX );

        if (unlikely( status == -1 ))
        {
            throw _PythonException();
        }
    }
    else
    {
        PyObject *slice = PySlice_New( lower, upper, NULL );

        if (slice == NULL)
        {
            throw _PythonException();
        }

        int status = PyObject_DelItem( target, slice );

        Py_DECREF( slice );

        if (unlikely( status == -1 ))
        {
            throw _PythonException();
        }
    }
}

static PyObject *MAKE_SLICEOBJ( PyObject *start, PyObject *stop, PyObject *step )
{
    assert (start);
    assert (start->ob_refcnt > 0);
    assert (stop);
    assert (stop->ob_refcnt > 0);
    assert (step);
    assert (step->ob_refcnt > 0);

    PyObject *result = PySlice_New( start, stop, step );

    if (unlikely (result == NULL))
    {
        throw _PythonException();
    }

    return result;
}

static Py_ssize_t CONVERT_TO_INDEX( PyObject *value )
{
    assert (value);
    assert (value->ob_refcnt > 0);

    if ( PyInt_Check( value ) )
    {
        return PyInt_AS_LONG( value );
    }
    else if ( PyIndex_Check( value ) )
    {
        Py_ssize_t result = PyNumber_AsSsize_t( value, NULL );

        if (unlikely( result == -1 && PyErr_Occurred() ))
        {
            throw _PythonException();
        }

        return result;
    }
    else
    {
        PyErr_Format( PyExc_TypeError, "slice indices must be integers or None or have an __index__ method" );
        throw _PythonException();
    }
}

static PyObject *LOOKUP_ATTRIBUTE( PyObject *source, PyObject *attr_name )
{
    assert (source);
    assert (source->ob_refcnt > 0);
    assert (attr_name);
    assert (attr_name->ob_refcnt > 0);

    int line = _current_line;
    PyObject *result = PyObject_GetAttr( source, attr_name );
    _current_line = line;

    if (unlikely (result == NULL))
    {
        throw _PythonException();
    }

    assert( result->ob_refcnt > 0 );

    return result;
}

static void SET_ATTRIBUTE( PyObject *target, PyObject *attr_name, PyObject *value )
{
    assert (target);
    assert (target->ob_refcnt > 0);
    assert (attr_name);
    assert (attr_name->ob_refcnt > 0);
    assert (value);
    assert (value->ob_refcnt > 0);

    int status = PyObject_SetAttr( target, attr_name, value );

    if (unlikely( status == -1 ))
    {
        throw _PythonException();
    }
}

static void DEL_ATTRIBUTE( PyObject *target, PyObject *attr_name )
{
    assert (target);
    assert (target->ob_refcnt > 0);
    assert (attr_name);
    assert (attr_name->ob_refcnt > 0);

    int status = PyObject_DelAttr( target, attr_name );

    if (unlikely( status == -1 ))
    {
        throw _PythonException();
    }
}

static void APPEND_TO_LIST( PyObject *list, PyObject *item )
{
    int status = PyList_Append( list, item );

    if (unlikely( status == -1 ))
    {
        throw _PythonException();
    }
}

static void ADD_TO_SET( PyObject *set, PyObject *item )
{
    int status = PySet_Add( set, item );

    if (unlikely( status == -1 ))
    {
        throw _PythonException();
    }
}



static PyObject *SEQUENCE_CONCAT( PyObject *seq1, PyObject *seq2 )
{
    PyObject *result = PySequence_Concat( seq1, seq2 );

    if (unlikely (result == NULL))
    {
        throw _PythonException();
    }

    return result;
}

// Helper class to be used when PyObject * are provided as parameters where they
// are not consumed, but not needed anymore after the call and and need a release
// as soon as possible.

class PyObjectTemporary {
    public:
        explicit PyObjectTemporary( PyObject *object )
        {
            assert( object );
            assert( object->ob_refcnt > 0 );

            this->object = object;
        }

        PyObjectTemporary( const PyObjectTemporary &object ) = delete;

        ~PyObjectTemporary()
        {
            Py_DECREF( this->object );
        }

        PyObject *asObject()
        {
            assert( this->object->ob_refcnt > 0 );

            return this->object;
        }

        void assign( PyObject *object )
        {
            Py_DECREF( this->object );

            assert( object );
            assert( object->ob_refcnt > 0 );

            this->object = object;
        }

        void checkSanity( char const *message ) const
        {
            if ( this->object->ob_refcnt <= 0 )
            {
                puts( message );
                assert( false );
            }
        }
    private:
        PyObject *object;
};

class PyObjectLocalDictVariable {
    public:
        explicit PyObjectLocalDictVariable( PyObject *storage, PyObject *var_name, PyObject *object = NULL )
        {
            this->storage    = storage;
            this->var_name   = var_name;

            if ( object != NULL )
            {
                int status = PyDict_SetItem( this->storage, this->var_name, object );
                assert( status == 0 );
            }
        }

        PyObject *asObject() const
        {
            // TODO: Dictionary quick access code could be used here too.
            PyObject *result = PyDict_GetItem( this->storage, this->var_name );

            if (unlikely (result == NULL))
            {
                PyErr_Format( PyExc_UnboundLocalError, "local variable '%s' referenced before assignment", PyString_AsString( this->var_name ) );
                throw _PythonException();
            }

            assert( result->ob_refcnt > 0 );

            return result;
        }

        void operator=( PyObject *object )
        {
            assert( object );
            assert( object->ob_refcnt > 0 );

            int status = PyDict_SetItem( this->storage, this->var_name, object );
            assert( status == 0 );
        }

        bool isInitialized() const
        {
            return PyDict_Contains( this->storage, this->var_name ) == 1;
        }

        void del()
        {
            int status = PyDict_DelItem( this->storage, this->var_name );

            if (unlikely( status == -1 ))
            {
                // TODO: Probably an error should be raised?
                PyErr_Clear();
            }
        }


        PyObject *getVariableName() const
        {
            return this->var_name;
        }

    private:
        PyObject *storage;
        PyObject *var_name;
};

class PyObjectLocalVariable {
    public:
        explicit PyObjectLocalVariable( PyObject *var_name, PyObject *object = NULL, bool free_value = false )
        {
            this->var_name   = var_name;
            this->object     = object;
            this->free_value = free_value;
        }

        explicit PyObjectLocalVariable()
        {
            this->var_name   = NULL;
            this->object     = NULL;
            this->free_value = false;
        }

        ~PyObjectLocalVariable()
        {
            if ( this->free_value )
            {
                Py_DECREF( this->object );
            }
        }

        void setVariableName( PyObject *var_name )
        {
            assert( var_name );
            assert( var_name->ob_refcnt > 0 );

            assert( this->var_name == NULL);

            this->var_name = var_name;
        }

        void operator=( PyObject *object )
        {
            assert( object );
            assert( object->ob_refcnt > 0 );

            if ( this->free_value )
            {
                PyObject *old_object = this->object;

                this->object = object;

                // Free old value if any available and owned.
                Py_DECREF( old_object );
            }
            else
            {
                this->object = object;
                this->free_value = true;
            }
        }

        PyObject *asObject() const
        {
            if ( this->object == NULL && this->var_name != NULL )
            {
                PyErr_Format( PyExc_UnboundLocalError, "local variable '%s' referenced before assignment", PyString_AsString( this->var_name ) );
                throw _PythonException();
            }

            assert( this->object );
            assert( this->object->ob_refcnt > 0 );

            return this->object;
        }

        bool isInitialized() const
        {
            return this->object != NULL;
        }

        void del()
        {
            if ( this->object == NULL )
            {
                PyErr_Format( PyExc_UnboundLocalError, "local variable '%s' referenced before assignment", PyString_AsString( this->var_name ) );
                throw _PythonException();
            }

            if ( this->free_value )
            {
                Py_DECREF( this->object );
            }

            this->object = NULL;
            this->free_value = false;
        }

        PyObject *getVariableName() const
        {
            return this->var_name;
        }

    private:

        PyObject *var_name;
        PyObject *object;
        bool free_value;
};

class PyObjectSharedStorage
{
    public:
        explicit PyObjectSharedStorage( PyObject *var_name, PyObject *object, bool free_value )
        {
            assert( object == NULL || object->ob_refcnt > 0 );

            this->var_name   = var_name;
            this->object     = object;
            this->free_value = free_value;
            this->ref_count  = 1;
        }

        ~PyObjectSharedStorage()
        {
            if ( this->free_value )
            {
                Py_DECREF( this->object );
            }
        }

        void operator=( PyObject *object )
        {
            assert( object );
            assert( object->ob_refcnt > 0 );

            if ( this->free_value )
            {
                PyObject *old_object = this->object;

                this->object = object;

                // Free old value if any available and owned.
                Py_DECREF( old_object );
            }
            else
            {
                this->object = object;
                this->free_value = true;
            }
        }

        PyObject *var_name;
        PyObject *object;
        bool free_value;
        int ref_count;
};

class PyObjectSharedLocalVariable
{
    public:
        explicit PyObjectSharedLocalVariable( PyObject *var_name, PyObject *object = NULL, bool free_value = false )
        {
            this->storage = new PyObjectSharedStorage( var_name, object, free_value );
        }

        explicit PyObjectSharedLocalVariable()
        {
            this->storage = NULL;
        }

        ~PyObjectSharedLocalVariable()
        {
            if ( this->storage )
            {
                assert( this->storage->ref_count > 0 );
                this->storage->ref_count -= 1;

                if (this->storage->ref_count == 0)
                {
                    delete this->storage;
                }
            }
        }

        void setVariableName( PyObject *var_name )
        {
            assert( this->storage == NULL );

            this->storage = new PyObjectSharedStorage( var_name, NULL, false );
        }

        void shareWith( const PyObjectSharedLocalVariable &other )
        {
            assert(this->storage == NULL);
            assert(other.storage != NULL);

            this->storage = other.storage;
            this->storage->ref_count += 1;
        }

        void operator=( PyObject *object )
        {
            this->storage->operator=( object );
        }

        PyObject *asObject() const
        {
            assert( this->storage );

            if ( this->storage->object == NULL )
            {
                PyErr_Format( PyExc_UnboundLocalError, "free variable '%s' referenced before assignment in enclosing scope", PyString_AsString( this->storage->var_name ) );
                throw _PythonException();

            }

            if ( (this->storage->object)->ob_refcnt == 0 )
            {
                PyErr_Format( PyExc_UnboundLocalError, "free variable '%s' referenced after its finalization in enclosing scope", PyString_AsString( this->storage->var_name ) );
                throw _PythonException();
            }

            return this->storage->object;
        }

        bool isInitialized() const
        {
            return this->storage->object != NULL;
        }

        PyObject *getVariableName() const
        {
            return this->storage->var_name;
        }

    private:
        PyObjectSharedLocalVariable( PyObjectSharedLocalVariable & );

        PyObjectSharedStorage *storage;
};

static PyDictEntry *GET_PYDICT_ENTRY( PyModuleObject *module, PyStringObject *key )
{
    // Idea similar to LOAD_GLOBAL in CPython. Because the variable name is a string, we
    // can shortcut much of the dictionary code by using its hash and dictionary knowledge
    // here. Only improvement would be to identify how to ensure that the hash is computed
    // already. Calling hash early on could do that potentially.

    long hash = key->ob_shash;

    if ( hash == -1 )
    {
        hash = PyString_Type.tp_hash( (PyObject *)key );
    }

    PyDictObject *dict = (PyDictObject *)(module->md_dict);
    assert( PyDict_CheckExact( dict ));

    PyDictEntry *entry = dict->ma_lookup( dict, (PyObject *)key, hash );

    // The "entry" cannot be NULL, it can only be empty for a string dict lookup, but at
    // least assert it.
    assert( entry != NULL );

    return entry;
}

class PyObjectGlobalVariable
{
    public:
        explicit PyObjectGlobalVariable( PyObject **module_ptr, PyObject **var_name )
        {
            assert( module_ptr );
            assert( var_name );

            this->module_ptr = (PyModuleObject **)module_ptr;
            this->var_name   = (PyStringObject **)var_name;
        }

        PyObject *asObject() const
        {
            PyDictEntry *entry = GET_PYDICT_ENTRY( *this->module_ptr, *this->var_name );

            if (likely( entry->me_value != NULL ))
            {
                return INCREASE_REFCOUNT( entry->me_value );
            }

            entry = GET_PYDICT_ENTRY( _module_builtin, *this->var_name );

            if (likely( entry->me_value != NULL ))
            {
                return INCREASE_REFCOUNT( entry->me_value );
            }

            PyErr_Format( PyExc_NameError, "global name '%s' is not defined", PyString_AsString( (PyObject *)*this->var_name ) );
            throw _PythonException();
        }

        PyObject *asObject( PyObject *dict ) const
        {
            if ( PyDict_Contains( dict, (PyObject *)*this->var_name ) )
            {
                return PyDict_GetItem( dict, (PyObject *)*this->var_name );
            }
            else
            {
                return this->asObject();
            }
        }

        void assign( PyObject *value ) const
        {
            PyDictEntry *entry = GET_PYDICT_ENTRY( *this->module_ptr, *this->var_name );

            // Values are more likely set than not set, in that case speculatively try the
            // quickest access method.
            if (likely( entry->me_value != NULL ))
            {
                PyObject *old = entry->me_value;
                entry->me_value = value;

                Py_DECREF( old );
            }
            else
            {
                DICT_SET_ITEM( (*this->module_ptr)->md_dict, (PyObject *)*this->var_name, value );
                Py_DECREF( value );
            }
        }

        void assign0( PyObject *value ) const
        {
            DICT_SET_ITEM( (*this->module_ptr)->md_dict, (PyObject *)*this->var_name, value );
        }

        void del() const
        {
            int status = PyDict_DelItem( (*this->module_ptr)->md_dict, (PyObject *)*this->var_name );

            if (unlikely( status == -1 ))
            {
                PyErr_Format( PyExc_NameError, "name '%s' is not defined", PyString_AsString( (PyObject *)*this->var_name ) );
                throw _PythonException();
            }
        }

        bool isInitialized() const
        {
            PyDictEntry *entry = GET_PYDICT_ENTRY( *this->module_ptr, *this->var_name );

            if (likely( entry->me_value != NULL ))
            {
                return true;
            }

            entry = GET_PYDICT_ENTRY( _module_builtin, *this->var_name );

            return entry->me_value != NULL;
        }

    private:
       PyModuleObject **module_ptr;
       PyStringObject **var_name;
};

static PyObject *MAKE_LOCALS_DICT( void )
{
    return MAKE_DICT();
}

template<typename T>
static void FILL_LOCALS_DICT( PyObject *dict, T variable )
{
    if ( variable->isInitialized() )
    {
        int status = PyDict_SetItem( dict, variable->getVariableName(), variable->asObject() );

        if (unlikely( status == -1 ))
        {
            throw _PythonException();
        }
    }
}

template<typename T, typename... P>
static void FILL_LOCALS_DICT( PyObject *dict, T variable, P... variables )
{
    if ( variable->isInitialized() )
    {
        int status = PyDict_SetItem( dict, variable->getVariableName(), variable->asObject() );

        if (unlikely( status == -1 ))
        {
            throw _PythonException();
        }
    }

    FILL_LOCALS_DICT( dict, variables... );
}

template<typename... P>
static PyObject *MAKE_LOCALS_DICT( P...variables )
{
    PyObject *result = MAKE_LOCALS_DICT();

    FILL_LOCALS_DICT( result, variables... );

    return result;
}

static PyObject *MAKE_LOCALS_DIR( void )
{
    return MAKE_LIST();
}

template<typename T>
static void FILL_LOCALS_DIR( PyObject *list, T variable )
{
    if ( variable->isInitialized() )
    {
        int status = PyList_Append( list, variable->getVariableName() );

        if (unlikely( status == -1 ))
        {
            throw _PythonException();
        }
    }
}

template<typename T, typename... P>
static void FILL_LOCALS_DIR( PyObject *list, T variable, P... variables )
{
    if ( variable->isInitialized() )
    {
        int status = PyList_Append( list, variable->getVariableName() );

        if (unlikely( status == -1 ))
        {
            throw _PythonException();
        }
    }

    FILL_LOCALS_DIR( list, variables... );
}

template<typename... P>
static PyObject *MAKE_LOCALS_DIR( P...variables )
{
    PyObject *result = MAKE_LOCALS_DIR();

    FILL_LOCALS_DIR( result, variables... );

    return result;
}

static PyObject *TUPLE_COPY( PyObject *tuple )
{
    assert( tuple != NULL );
    assert( tuple->ob_refcnt > 0 );

    assert( PyTuple_CheckExact( tuple ) );

    Py_ssize_t size = PyTuple_GET_SIZE( tuple );

    PyObject *result = PyTuple_New( size );

    if (unlikely (result == NULL))
    {
        throw _PythonException();
    }

    for ( Py_ssize_t i = 0; i < size; i++ )
    {
        PyTuple_SET_ITEM( result, i, INCREASE_REFCOUNT( PyTuple_GET_ITEM( tuple, i ) ) );
    }

    return result;
}

static PyObject *LIST_COPY( PyObject *list )
{
    assert( list != NULL );
    assert( list->ob_refcnt > 0 );

    assert( PyList_CheckExact( list ) );

    Py_ssize_t size = PyList_GET_SIZE( list );

    PyObject *result = PyList_New( size );

    if (unlikely (result == NULL))
    {
        throw _PythonException();
    }

    for ( Py_ssize_t i = 0; i < size; i++ )
    {
        PyList_SET_ITEM( result, i, INCREASE_REFCOUNT( PyList_GET_ITEM( list, i ) ) );
    }

    return result;
}


class PythonBuiltin
{
    public:
        explicit PythonBuiltin( char const *name )
        {
            this->name = name;
            this->value = NULL;
        }

        PyObject *asObject()
        {
            if ( this->value == NULL )
            {
                // TODO: Use GET_PYDICT_ENTRY here too.
                this->value = PyObject_GetAttrString( (PyObject *)_module_builtin, this->name );
            }

            assert( this->value != NULL );

            return this->value;
        }

    private:
        char const *name;
        PyObject *value;
};

static PythonBuiltin _python_builtin_compile( "compile" );

static PyObject *COMPILE_CODE( PyObject *source_code, PyObject *file_name, PyObject *mode, int flags )
{
    // May be a source, but also could already be a compiled object, in which case this
    // should just return it.
    if ( PyCode_Check( source_code ) )
    {
        return INCREASE_REFCOUNT( source_code );
    }

    // Workaround leading whitespace causing a trouble to compile builtin, but not eval builtin
    PyObject *source;

    if ( ( PyString_Check( source_code ) || PyUnicode_Check( source_code ) ) && strcmp( PyString_AsString( mode ), "exec" ) != 0 )
    {
        static PyObject *strip_str = PyString_FromString( "strip" );

        // TODO: There is an API to call a method, use it instead.
        source = LOOKUP_ATTRIBUTE( source_code, strip_str );
        source = PyObject_CallFunctionObjArgs( source, NULL );

        assert( source );
    }
    else if ( PyFile_Check( source_code ) && strcmp( PyString_AsString( mode ), "exec" ) == 0 )
    {
        static PyObject *read_str = PyString_FromString( "read" );

        // TODO: There is an API to call a method, use it instead.
        source = LOOKUP_ATTRIBUTE( source_code, read_str );
        source = PyObject_CallFunctionObjArgs( source, NULL );

        assert( source );
    }
    else
    {
        source = source_code;
    }

    PyObject *future_flags = PyInt_FromLong( flags );

    PyObject *result = PyObject_CallFunctionObjArgs(
        _python_builtin_compile.asObject(),
        source,
        file_name,
        mode,
        future_flags,      // flags
        _python_bool_True, // dont_inherit
        NULL
    );

    Py_DECREF( future_flags );

    if (unlikely (result == NULL))
    {
        throw _PythonException();
    }

    return result;
}

static PythonBuiltin _python_builtin_open( "open" );

static PyObject *OPEN_FILE( PyObject *file_name, PyObject *mode, PyObject *buffering )
{
    PyObject *result = PyObject_CallFunctionObjArgs(
        _python_builtin_open.asObject(),
        file_name,
        mode,
        buffering,
        NULL
    );

    if (unlikely (result == NULL))
    {
        throw _PythonException();
    }

    return result;
}

static PyObject *EVAL_CODE( PyObject *code, PyObject *globals, PyObject *locals )
{
    if ( PyDict_Check( globals ) == 0 )
    {
        PyErr_Format( PyExc_TypeError, "exec: arg 2 must be a dictionary or None" );
        throw _PythonException();
    }

    if ( locals == NULL || locals == Py_None )
    {
        locals = globals;
    }

    if ( PyMapping_Check( locals ) == 0 )
    {
        PyErr_Format( PyExc_TypeError, "exec: arg 3 must be a mapping or None" );
        throw _PythonException();
    }

    // Set the __builtin__ in globals, it is expected to be present.
    if ( PyDict_GetItemString( globals, (char *)"__builtins__" ) == NULL )
    {
        if ( PyDict_SetItemString( globals, (char *)"__builtins__", (PyObject *)_module_builtin ) == -1 )
        {
            throw _PythonException();
        }
    }

    PyObject *result = PyEval_EvalCode( (PyCodeObject *)code, globals, locals );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

static PyObject *empty_code = PyBuffer_FromMemory( NULL, 0 );

static PyCodeObject *MAKE_CODEOBJ( PyObject *filename, PyObject *function_name, int line )
{
    // TODO: Potentially it is possible to create a line2no table that will allow to use
    // only one code object per function, this could then be cached and presumably be much
    // faster, because it could be reused.

    assert( PyString_Check( filename ));
    assert( PyString_Check( function_name ));

    assert( empty_code );

    // printf( "MAKE_CODEOBJ code object %d\\n", empty_code->ob_refcnt );

    PyCodeObject *result = PyCode_New (
        0, 0, 0, 0, // argcount, locals, stacksize, flags
        empty_code, //
        _python_tuple_empty,
        _python_tuple_empty,
        _python_tuple_empty,
        _python_tuple_empty,
        _python_tuple_empty,
        filename,
        function_name,
        line,
        _python_str_empty
    );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    return result;
}

static PyFrameObject *MAKE_FRAME( PyObject *module, PyObject *filename, PyObject *function_name, int line )
{
    PyCodeObject *code = MAKE_CODEOBJ( filename, function_name, line );

    PyFrameObject *result = PyFrame_New(
        PyThreadState_GET(),
        code,
        ((PyModuleObject *)module)->md_dict,
        NULL // No locals yet
    );

    Py_DECREF( code );

    if (unlikely( result == NULL ))
    {
        throw _PythonException();
    }

    result->f_lineno = line;

    return result;
}

static PyTracebackObject *MAKE_TRACEBACK_START( PyFrameObject *frame, int line )
{
    PyTracebackObject *result = PyObject_GC_New( PyTracebackObject, &PyTraceBack_Type );

    result->tb_next = NULL;

    Py_INCREF( frame );
    result->tb_frame  = frame;

    result->tb_lasti  = 0;
    result->tb_lineno = line;

    PyObject_GC_Track( result );

    return result;
}

static void ADD_TRACEBACK( PyObject *module, PyObject *filename, PyObject *function_name, int line )
{
    // TODO: The frame object really might deserve a longer life that this, it is
    // relatively expensive to create.
    PyFrameObject *frame = MAKE_FRAME( module, filename, function_name, line );

    // Inlining PyTraceBack_Here may be faster
    PyTraceBack_Here( frame );

    Py_DECREF( frame );
}
"""


try_finally_template = """
_PythonExceptionKeeper _caught_%(try_count)d;
bool _continue_%(try_count)d = false;
bool _break_%(try_count)d = false;
try
{
%(tried_code)s
}
catch ( _PythonException &_exception )
{
    _caught_%(try_count)d.save( _exception );
}
catch ( ContinueException &e )
{
    _continue_%(try_count)d = true;
}
catch ( BreakException &e )
{
    _break_%(try_count)d = true;
}

%(final_code)s

_caught_%(try_count)d.rethrow();

if ( _continue_%(try_count)d )
{
    throw ContinueException();
}

if ( _break_%(try_count)d )
{
    throw BreakException();
}
"""

try_except_template = """
try
{
%(tried_code)s
}
catch ( _PythonException &_exception )
{
    if ( !_exception.hasTraceback() )
    {
        _exception.setTraceback( %(tb_making)s );
        traceback = true;
    }
    _exception.toExceptionHandler();

%(exception_code)s
}
"""

try_except_else_template = """
bool _caught_%(except_count)d = false;
try
{
%(tried_code)s
}
catch ( _PythonException &_exception )
{
    _caught_%(except_count)d = true;

    if ( !_exception.hasTraceback() )
    {
        _exception.setTraceback( %(tb_making)s );
        traceback = true;
    }
    _exception.toExceptionHandler();

%(exception_code)s
}
if ( _caught_%(except_count)d == false )
{
%(else_code)s
}
"""

exec_local_template = """\
{
    PyObjectTemporary globals( %(globals_identifier)s );
    PyObjectTemporary locals( %(locals_identifier)s );

    bool own_locals = true;

    if ( locals.asObject() == Py_None && globals.asObject() == Py_None )
    {
        globals.assign( %(make_globals_identifier)s );
        locals.assign( %(make_locals_identifier)s );
        own_locals = true;
    }
    else
    {
        own_locals = false;
    }

    PyObjectTemporary code( COMPILE_CODE( %(source_identifier)s, %(filename_identifier)s, %(mode_identifier)s, %(future_flags)s ) );

    PyObject *result = EVAL_CODE( code.asObject(), globals.asObject(), locals.asObject() );
    Py_DECREF( result );

    if ( own_locals )
    {
%(store_locals_code)s
    }
}
"""

exec_global_template = """\
{
    PyObjectTemporary globals( %(globals_identifier)s );
    PyObjectTemporary locals( %(locals_identifier)s );

    if ( globals.asObject() == Py_None )
    {
        globals.assign( %(make_globals_identifier)s );
    }

    PyObjectTemporary code( COMPILE_CODE( %(source_identifier)s, %(filename_identifier)s, %(mode_identifier)s, %(future_flags)s ) );

    PyObject *result = EVAL_CODE( code.asObject(), globals.asObject(), locals.asObject() );
    Py_DECREF( result );
}
"""

eval_local_template = """\
EVAL_CODE( PyObjectTemporary( COMPILE_CODE(  %(source_identifier)s, %(filename_identifier)s, %(mode_identifier)s, %(future_flags)s ) ).asObject(), ( _eval_globals_tmp = %(globals_identifier)s ) == Py_None ? %(make_globals_identifier)s : _eval_globals_tmp, ( _eval_locals_tmp = %(locals_identifier)s ) == Py_None ? ( _eval_globals_tmp = %(globals_identifier)s ) == Py_None ?  %(make_locals_identifier)s : _eval_globals_tmp : _eval_locals_tmp )"""


eval_global_template = """\
EVAL_CODE( PyObjectTemporary( COMPILE_CODE(  %(source_identifier)s, %(filename_identifier)s, %(mode_identifier)s, %(future_flags)s ) ).asObject(), ( _eval_globals_tmp = %(globals_identifier)s ) == Py_None ? %(make_globals_identifier)s : _eval_globals_tmp, %(locals_identifier)s )"""

with_template = """\
{
    _PythonExceptionKeeper _caught_%(with_count)d;

    PyObjectTemporary %(manager)s( %(source)s );

    // Should have a CALL_FUNCTION that does this for us.
    PyObject *_enter_result = PyObject_CallMethod( %(manager)s.asObject(), (char *)"__enter__", NULL );

    if (unlikely( _enter_result == NULL ))
    {
        throw _PythonException();
    }

    PyObjectTemporary %(value)s( _enter_result );

    try
    {
%(assign)s
%(body)s
    }
    catch ( _PythonException &_exception )
    {
        _caught_%(with_count)d.save( _exception );

        PyObject *exception_type  = _exception.getType();
        PyObject *exception_value = _exception.getObject();
        PyObject *exception_tb    = _exception.getTraceback();

        if ( exception_tb == NULL )
            exception_tb = Py_None;

        assert( exception_type != NULL );
        assert( exception_value != NULL );

        PyObject *result = PyObject_CallMethod( %(manager)s.asObject(), (char *)"__exit__",  (char *)"OOO", INCREASE_REFCOUNT( exception_type ), INCREASE_REFCOUNT( exception_value ), INCREASE_REFCOUNT( exception_tb ), NULL );

        if (unlikely( result == NULL ))
        {
            throw _PythonException();
        }

        if ( CHECK_IF_TRUE( result ) )
        {
            PyErr_Clear();
        }
        else
        {
            _caught_%(with_count)d.rethrow();
        }
    }

    if ( _caught_%(with_count)d.isEmpty() )
    {
        PyObject *result = PyObject_CallMethod( %(manager)s.asObject(), (char *)"__exit__",  (char *)"OOO", Py_None, Py_None, Py_None, NULL );

        if (unlikely( result == NULL ))
        {
            throw _PythonException();
        }
    }
}
"""
