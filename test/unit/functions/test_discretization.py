import pytest

import dolfin
from ufl.tensors import ListTensor
from muflon.common.parameters import mpset
from muflon.functions.discretization import DiscretizationFactory

def get_arguments():
    nx = 2
    #mesh = dolfin.UnitIntervalMesh(nx)
    mesh = dolfin.UnitSquareMesh(nx, nx)
    #mesh = dolfin.UnitCubeMesh(nx, nx, nx)
    P1 = dolfin.FiniteElement("Lagrange", mesh.ufl_cell(), 1)
    P2 = dolfin.FiniteElement("Lagrange", mesh.ufl_cell(), 2)
    return (mesh, P1, P1, P2, P1)

def test_GenericDiscretization():
    args = get_arguments()
    with pytest.raises(NotImplementedError):
        ds = DiscretizationFactory.create("Discretization", *args)

    from muflon.functions.discretization import Discretization
    ds = Discretization(*args)
    with pytest.raises(NotImplementedError):
        ds.setup()

@pytest.mark.parametrize("D", ["Monolithic", "SemiDecoupled", "FullyDecoupled"])
@pytest.mark.parametrize("N", [2, 3])
def test_discretization_schemes(D, N):

    args = get_arguments()
    ds = DiscretizationFactory.create(D, *args)

    # Check that ds raises without calling the setup method
    for meth in ["solution_fcns", "primitive_vars", "get_function_spaces",
                 "create_trial_fcns", "create_test_fcns"]:
        with pytest.raises(AssertionError):
            foo = eval("ds." + meth + "()")

    # Do the necessary setup
    ds.parameters["N"] = N
    ds.setup()

    # Check solution functions
    w = ds.solution_fcns()
    assert isinstance(w, tuple)
    for foo in w:
        assert isinstance(foo, dolfin.Function)

    if D == "SemiDecoupled": # check block size of CH part
        assert w[0].name() == "sol_ch"
        bs = w[0].function_space().dofmap().block_size()
        assert bs == 2*(ds.parameters["N"]-1)
        del bs
    del w

    # Check primitive variables
    pv = ds.primitive_vars()
    assert isinstance(pv, tuple)
    for foo in pv:
        assert isinstance(foo, dolfin.Function) or isinstance(foo, ListTensor)
    assert len(pv) == len(args)-1 # mesh is the additional argument

    # Try to unpack 'c' and 'mu' variables (works for N > 2)
    for i in range(2):
        if ds.parameters["N"] == 2:
            with pytest.raises(RuntimeError):
                foo_list = pv[i].split()
        else:
            foo_list = pv[i].split()
            assert isinstance(foo_list, tuple)
            for foo in foo_list:
                assert isinstance(foo, dolfin.Function)

    # Try to unpack velocity vector
    gdim =  ds.solution_fcns()[0].function_space().mesh().geometry()
    if gdim == 1:
        with pytest.raises(RuntimeError):
            foo_list = pv[3].split()
    else:
        foo_list = pv[3].split()
        assert isinstance(foo_list, tuple)
        for foo in foo_list:
            assert isinstance(foo, dolfin.Function)

    # Create trial and test functions
    tr_fcns = ds.create_trial_fcns()
    assert len(tr_fcns) == len(pv)
    te_fcns = ds.create_test_fcns()
    assert len(te_fcns) == len(pv)

    # # Test assigners
    # W = ds.get_function_spaces()
    # w = ds.solution_fcns() # zeros
    # pv = ds.primitive_vars()
    # V_c = W[0].sub(0).collapse()
    # c0 = dolfin.Function(V_c) # zeros
    # c = pv[0]
    # # Test assignment from c0 to c
    # ass_to_mix = dolfin.FunctionAssigner(W[0].sub(0), V_c)
    # c0.vector()[:] = 1.0
    # dolfin.info(w[0].vector(), True) # zeros
    # ass_to_mix.assign(c, c0)
    # dolfin.info(w[0].vector(), True) # some ones
    # # Test assignment from c to c0
    # ass_from_mix = dolfin.FunctionAssigner(V_c, W[0].sub(0))
    # w[0].vector()[:] = 2.0
    # dolfin.info(c0.vector(), True) # ones
    # ass_from_mix.assign(c0, c)
    # dolfin.info(c0.vector(), True) # twos

    # Cleanup
    del foo
    del pv
    del gdim
    del ds
    del args
