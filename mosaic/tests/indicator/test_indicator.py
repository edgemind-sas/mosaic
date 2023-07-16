# from databayes.modelling import DFPotential, DFVariable, DFCPD
# from databayes.utils import Discretizer
import mosaic.indicator as mid
import logging
import pytest
import pkg_resources
import pandas as pd
import numpy as np
import os
import json
import yaml
import pathlib

installed_pkg = {pkg.key for pkg in pkg_resources.working_set}
if 'ipdb' in installed_pkg:
    import ipdb


logger = logging.getLogger()

DATA_PATH = os.path.join(os.path.dirname(__file__), "data")
EXPECTED_PATH = os.path.join(os.path.dirname(__file__), "expected")
pathlib.Path(DATA_PATH).mkdir(parents=True, exist_ok=True)
pathlib.Path(EXPECTED_PATH).mkdir(parents=True, exist_ok=True)



@pytest.fixture
def data_btc_usdc_1000_df():

    data_filename = os.path.join(DATA_PATH, "data_btc_usdc_1000.csv")
    data_df = pd.read_csv(data_filename, sep=",", index_col="timestamp")
    return data_df


# @pytest.fixture
# def data_btc_1000_hammer_df(data_btc_usdc_1000_df):

#     disc_specs = yaml.load("""
#       variables:
#         ret_close_t.:
#           params:
#             bins: [-.inf, 0, .inf]

#         hammer:
#           params:
#             bins: [-.inf, -2, 2, .inf]
#             labels: [LL, M, HH]

#     """, Loader=yaml.SafeLoader())
#     data_disc_df = Discretizer(**disc_specs).discretize(data_btc_usdc_1000_df)
#     return data_disc_df[["ret_close_t2", "mvq50", "hammer"]]

# =============== Tests begin here ================== #


def test_indicator_001():

    indic = mid.Indicator()
    
    # var_v1 = DFVariable(name="v1", domain=['ok', 'degraded', 'failure'])
    # var_x = DFVariable(name="x", domain=[1, 2])
    # var_T = DFVariable(name="T", domain=['nothing'])

    # pot = DFPotential(name="P1", var=[var_v1, var_x, var_T])

    # assert pot.var2dim(["T", "v1"]) == (2, 0)
    # assert pot.var2dim(["x", "v1", "T"]) == (1, 0, 2)


# def test_Potential_basics_002():

#     var_X = DFVariable(name="X", domain=['x0', 'x1', 'x2'])
#     var_Y = DFVariable(name="Y", domain=['y0', 'y1', 'y2'])
#     var_Z = DFVariable(name="Z", domain=['z0'])

#     pot = DFPotential(name="P1", var=[var_X, var_Y, var_Z])

#     assert pot.dim2var((2,)) == ('Z',)
#     assert pot.dim2var((2, 0, 1)) == ('Z', 'X', 'Y')


# def test_DFPotential_init_001():

#     pot = DFPotential()

#     assert pot.name is None
#     # assert pot.fun.name is None
#     assert pot.fun.dtype == float


# def test_DFPotential_init_002():

#     pot = DFPotential(name="P1")

#     assert pot.name == "P1"
#     # assert pot.fun.name == "P1"
#     assert pot.fun.dtype == float


# def test_DFPotential_init_003():

#     pot = DFPotential(name="P1",
#                       var=[DFVariable(name="V1", domain=["A", "B"])])

#     pot_index = pot._multiindex_from_var()

#     assert pot.name == "P1"
#     assert (pot.to_series().index == pot_index).all()
#     assert (pot.fun == 0).all()


# def test_DFPotential_init_004():

#     pot = DFPotential(name="P1")

#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable.from_bins(domain=[-float('inf'), 0, float('inf')],
#                               name="V2")

#     pot.update_var([V1, V2])
#     pot_index = pot._multiindex_from_var()

#     assert pot.name == "P1"
#     # assert pot.fun.name == "P1"
#     assert [var.name for var in pot.var] == ["V1", "V2"]
#     assert (pot.to_series().index == pot_index).all()
#     assert (pot.fun == 0).all()


# def test_DFPotential_init_005():

#     pot = DFPotential(name="P1")

#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable.from_bins(domain=[-float('inf'), 0, float('inf')],
#                               name="V2")
#     V3 = DFVariable(name="V3", domain=[10, 20, 30])

#     pot.update_var([V1, V2])

#     pot["B"] = [1, -1]

#     assert pot.fun.tolist() == \
#         [0.0, 0.0, 1.0, -1.0]

#     pot.update_var([V3])

#     assert pot.fun.tolist() == \
#         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, -1.0, -1.0, -1.0]


# def test_DFPotential_mul_001():

#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable.from_bins(domain=[-float('inf'), 0, float('inf')],
#                               name="V2")
#     V3 = DFVariable(name="V3", domain=[10])

#     pot1 = DFPotential(name="P1",
#                        var=[V1, V2])

#     pot1["A"] = 1
#     pot1["B"] = 2

#     pot2 = DFPotential(name="P2",
#                        var=[V3, V2])

#     pot2[10] = -1

#     pot3 = pot1*pot2

#     assert pot3.fun.tolist() == [-1.0, -1.0, -2.0, -2.0]
#     assert pot3.name == "P1*P2"
#     assert pot3.get_var_names() == ["V1", "V2", "V3"]
#     assert pot3.to_series().index.names == [var.name for var in pot3.var]


# def test_DFPotential_mul_001():

#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable.from_bins(domain=[-float('inf'), 0, float('inf')],
#                               name="V2")
#     V3 = DFVariable(name="V3", domain=[10])

#     pot1 = DFPotential(name="P1",
#                        var=[V1, V2])

#     pot1["A"] = 1
#     pot1["B"] = 2

#     pot2 = DFPotential(name="P2",
#                        var=[V3, V2])

#     pot2[10] = -1

#     pot3 = pot1*pot2

#     assert pot3.fun.tolist() == [-1.0, -1.0, -2.0, -2.0]
#     assert pot3.name == "P1*P2"
#     assert pot3.get_var_names() == ["V1", "V2", "V3"]
#     assert pot3.to_series().index.names == [var.name for var in pot3.var]


# def test_DFPotential_mul_002():
#     v_var = DFVariable(name="V", domain=[f'v{i}' for i in range(1)])
#     w_var = DFVariable(name="W", domain=[f'w{i}' for i in range(2)])
#     x_var = DFVariable(name="X", domain=[f'x{i}' for i in range(3)])
#     z_var = DFVariable(name="Z", domain=[f'z{i}' for i in range(2)])

#     p1 = DFPotential(var=[v_var, w_var, x_var])
#     p1.set_fun(np.arange(p1.get_nb_conf()) + 1)

#     p2 = DFPotential(var=[w_var, z_var, x_var])
#     p2.set_fun(np.arange(p2.get_nb_conf()) + 1)

#     p_res = p1*p2

#     assert p_res.get_var_names() == ["W", "Z", "X", "V"]
#     assert p_res.fun.tolist() == [1.0, 4.0, 9.0, 4.0,
#                                   10.0, 18.0, 28.0, 40.0, 54.0, 40.0, 55.0, 72.0]

#     p1 *= p2

#     assert p1.get_var_names() == p_res.get_var_names()
#     assert p1.fun.tolist() == p_res.fun.tolist()


# def test_DFPotential_mul_003():
#     w_var = DFVariable(name="W", domain=[f'w{i}' for i in range(2)])
#     y_var = DFVariable(name="Y", domain=[f'y{i}' for i in range(2)])
#     z_var = DFVariable(name="Z", domain=[f'z{i}' for i in range(2)])

#     p1 = DFPotential(var=[w_var, z_var],
#                      fun=[-10, 2.25, 0.01, -9])

#     p2 = DFPotential(var=[y_var, z_var],
#                      fun=[0, 3.5, -1, 7.25])

#     p_res = p1*p2

#     assert p_res.get_var_names() == ["W", "Z", "Y"]
#     assert p_res.fun.tolist() == [-0.0, 10.0, 7.875,
#                                   16.3125, 0.0, -0.01, -31.5, -65.25]

#     p1 *= p2

#     assert p1.get_var_names() == p_res.get_var_names()
#     assert p1.fun.tolist() == p_res.fun.tolist()


# def test_DFPotential_div_001():

#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable.from_bins(domain=[-float('inf'), 0, float('inf')],
#                               name="V2")
#     V3 = DFVariable(name="V3", domain=[10])

#     pot1 = DFPotential(name="P1",
#                        var=[V1, V2])

#     pot1["A"] = 1
#     pot1["B"] = 2

#     pot2 = DFPotential(name="P2",
#                        var=[V3, V2])

#     pot2[10] = -1

#     pot3 = pot1/pot2

#     assert pot3.fun.tolist() == [-1.0, -1.0, -2.0, -2.0]
#     assert pot3.name == "P1/P2"
#     assert pot3.get_var_names() == ["V1", "V2", "V3"]
#     assert pot3.to_series().index.names == [var.name for var in pot3.var]


# def test_DFPotential_div_002():
#     v_var = DFVariable(name="V", domain=[f'v{i}' for i in range(1)])
#     w_var = DFVariable(name="W", domain=[f'w{i}' for i in range(2)])
#     x_var = DFVariable(name="X", domain=[f'x{i}' for i in range(3)])
#     z_var = DFVariable(name="Z", domain=[f'z{i}' for i in range(2)])

#     p1 = DFPotential(var=[v_var, w_var, x_var])
#     p1.set_fun(np.arange(p1.get_nb_conf()) + 1)

#     p2 = DFPotential(var=[w_var, z_var, x_var])
#     p2.set_fun(np.arange(p2.get_nb_conf()) + 1)

#     p_res = p1/p2
#     assert p_res.get_var_names() == ["W", "Z", "X", "V"]
#     assert p_res.fun.tolist() == [1.0, 1.0, 1.0, 0.25, 0.4, 0.5, 0.5714285714285714,
#                                   0.625, 0.6666666666666666, 0.4, 0.45454545454545453, 0.5]

#     p1 /= p2

#     assert p1.get_var_names() == p_res.get_var_names()
#     assert p1.fun.tolist() == p_res.fun.tolist()


# def test_DFPotential_div_003():
#     w_var = DFVariable(name="W", domain=[f'w{i}' for i in range(2)])
#     y_var = DFVariable(name="Y", domain=[f'y{i}' for i in range(2)])
#     z_var = DFVariable(name="Z", domain=[f'z{i}' for i in range(2)])

#     p1 = DFPotential(var=[w_var, z_var],
#                      fun=[-10, 2.25, 0.01, -9])

#     p2 = DFPotential(var=[y_var, z_var],
#                      fun=[0, 3.5, -1, 7.25])

#     p_res = p1/p2
#     assert p_res.get_var_names() == ["W", "Z", "Y"]
#     assert p_res.fun.tolist() == [-float('inf'), 10.0, 0.6428571428571429,
#                                   0.3103448275862069, float('inf'), -0.01,
#                                   -2.5714285714285716, -1.2413793103448276]

#     p1 /= p2

#     assert p1.get_var_names() == p_res.get_var_names()
#     assert p1.fun.tolist() == p_res.fun.tolist()


# def test_DFPotential_sum_001():

#     x_var = DFVariable(name="X", domain=[f'x{i}' for i in range(2)])
#     z_var = DFVariable(name="Z", domain=[f'z{i}' for i in range(2)])
#     y_var = DFVariable(name="Y", domain=[f'y{i}' for i in range(2)])

#     pot = DFPotential(var=[x_var, z_var, y_var],
#                       fun=[0, 10, 7.875, 16.3125, 0, -0.01, -31.5, -65.25])

#     pot_res = pot.sum(['X'])

#     assert pot_res.get_var_names() == ["Z", "Y"]
#     assert pot_res.fun.tolist() == [0.0, 9.99, -23.625, -48.9375]

#     pot_res2 = pot.marg(['Y', 'Z'])

#     assert pot_res2.get_var_names() == pot_res.get_var_names()
#     assert pot_res2.fun.tolist() == pot_res.fun.tolist()


# def test_DFPotential_sum_002():

#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable.from_bins(domain=[-float('inf'), 0, float('inf')],
#                               name="V2")
#     V3 = DFVariable(name="V3", domain=[10])

#     pot = DFPotential(name="P1",
#                       var=[V1, V2, V3])

#     pot["A"] = 1
#     pot["B"] = 2

#     pot_res = pot.marg(["V1"])
#     assert pot_res.fun.tolist() == [2.0, 4.0]
#     assert pot_res.name == "P1"
#     assert pot_res.get_var_names() == ["V1"]
#     pot_res2 = pot.sum(["V2", "V3"])
#     assert pot_res2.fun.tolist() == pot_res.fun.tolist()
#     assert pot_res2.name == pot_res.name
#     assert pot_res2.get_var_names() == pot_res.get_var_names()

#     pot_res = pot.marg(["V1", "V3"])
#     assert pot_res.fun.tolist() == [2.0, 4.0]
#     assert pot_res.name == "P1"
#     assert pot_res.get_var_names() == ["V1", "V3"]
#     pot_res2 = pot.sum(["V2"])
#     assert pot_res2.fun.tolist() == pot_res.fun.tolist()
#     assert pot_res2.name == pot_res.name
#     assert pot_res2.get_var_names() == pot_res.get_var_names()

#     pot_res = pot.marg(["V1", "V2"])
#     assert pot_res.fun.tolist() == [1.0, 1.0, 2.0, 2.0]
#     assert pot_res.name == "P1"
#     assert pot_res.get_var_names() == ["V1", "V2"]
#     pot_res2 = pot.sum(["V3"])
#     assert pot_res2.fun.tolist() == pot_res.fun.tolist()
#     assert pot_res2.name == pot_res.name
#     assert pot_res2.get_var_names() == pot_res.get_var_names()

#     pot_res = pot.marg(["V3"])
#     assert pot_res.fun.tolist() == [6.0]
#     assert pot_res.name == "P1"
#     assert pot_res.get_var_names() == ["V3"]
#     pot_res2 = pot.sum(["V1", "V2"])
#     assert pot_res2.fun.tolist() == pot_res.fun.tolist()
#     assert pot_res2.name == pot_res.name
#     assert pot_res2.get_var_names() == pot_res.get_var_names()

#     pot_res = pot.marg()
#     assert pot_res == 6.0
#     pot_res2 = pot.sum(["V1", "V2", "V3"])
#     assert pot_res2 == pot_res


# def test_DFPotential_cmp_001():

#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable.from_bins(domain=[-float('inf'), 0, float('inf')],
#                               name="V2")
#     V3 = DFVariable.from_bins(domain=[-float('inf'), 0, float('inf')],
#                               name="V3")
#     V4 = DFVariable.from_bins(domain=[-float('inf'), 0, float('inf')],
#                               name="V2")

#     pot1 = DFPotential(name="X",
#                        var=[V1, V2],
#                        fun=[1, 2, 3, 4])

#     pot2 = DFPotential(name="X",
#                        var=[V1, V2],
#                        fun=[1, 2, 3, 4])

#     pot3 = DFPotential(name="Y",
#                        var=[V1, V2],
#                        fun=[1, 2, 3, 4])

#     pot4 = DFPotential(name="X",
#                        var=[V1, V3],
#                        fun=[1, 2, 3, 4])

#     pot5 = DFPotential(name="X",
#                        var=[V1, V4],
#                        fun=[1, 2, 3, 4])

#     assert pot1 == pot2
#     assert pot1 != pot3
#     assert pot1 != pot4
#     assert pot2 == pot5


# def test_DFPotential_cmp_002():

#     pot1 = DFPotential(name="X")
#     pot2 = DFPotential(name="X")

#     assert pot1 == pot2


# def test_DFPotential_io_001():

#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable.from_bins(domain=[-float('inf'), 0, float('inf')],
#                               name="V2")
#     V3 = DFVariable(name="V3", domain=[10, 20, 30])

#     pot = DFPotential(name="P1",
#                       var=[V1, V2, V3],
#                       fun=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])

#     pot2 = DFPotential.parse_raw(pot.json())

#     assert pot.fun.tolist() == [1.0, 2.0, 3.0, 4.0,
#                                 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0]

#     assert pot2.fun.tolist() == [1.0, 2.0, 3.0, 4.0,
#                                  5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0]

#     assert pot == pot2


# def test_DFPotential_io_002():

#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable.from_bins(domain=[-float('inf'), 0, float('inf')],
#                               name="V2")
#     V3 = DFVariable(name="V3", domain=[10, 20, 30])

#     pot = DFPotential(name="P1",
#                       var=[V1, V2, V3],
#                       fun=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])

#     pot_filename = os.path.join(DATA_PATH, "DFPotential_io_002_pot.json")
#     with open(pot_filename, "w") as file:
#         json.dump(pot.dict(), file)

#     pot2 = DFPotential.parse_file(pot_filename)

#     assert pot == pot2


# def test_DFPotential_io_003():

#     pot = DFPotential(name="P1")

#     pot_filename = os.path.join(DATA_PATH, "DFPotential_io_003_pot.json")
#     with open(pot_filename, "w") as file:
#         json.dump(pot.dict(), file)

#     pot2 = DFPotential.parse_file(pot_filename)

#     assert pot == pot2


# # TODO
# def test_DFCPD_init_001():

#     cpd = DFCPD(name="Prob")

#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable.from_bins(domain=[-float('inf'), 0, float('inf')],
#                               name="V2")
#     V3 = DFVariable(name="V3", domain=[10, 20, 30])

#     cpd.update_var([V1, V2, V3])

#     assert cpd.fun.sum() == 1.0
#     assert (cpd.counts == 0).all()
#     assert cpd.fun.index.names == cpd.counts.index.names
#     assert cpd.fun.index.names == [var.name for var in cpd.var]


# def test_DFCPD_init_002():

#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable.from_bins(domain=[-float('inf'), 0, float('inf')],
#                               name="V2")
#     V3 = DFVariable(name="V3", domain=[10, 20, 30])

#     cpd = DFCPD(name="Prob", var=[V1, V2, V3], var_norm=["V1", "V2"])

#     assert (cpd.fun.groupby(level=["V3"]).sum() == 1.0).all()
#     assert (cpd.fun == 0.25).all()
#     assert (cpd.counts == 0).all()
#     assert cpd.fun.index.names == cpd.counts.index.names
#     assert cpd.fun.index.names == [var.name for var in cpd.var]


# def test_DFCPD_init_003():

#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable.from_bins(domain=[-float('inf'), 0, float('inf')],
#                               name="V2")
#     V3 = DFVariable(name="V3", domain=[10, 20, 30])

#     cpd = DFCPD(name="Prob", var=[V1, V2, V3], var_norm=["V1"])

#     assert (cpd.fun.groupby(level=["V3", "V2"]).sum() == 1.0).all()
#     assert (cpd.fun == 0.5).all()
#     assert (cpd.counts == 0).all()
#     assert cpd.fun.index.names == cpd.counts.index.names
#     assert cpd.fun.index.names == [var.name for var in cpd.var]


# def test_DFCPD_init_004():

#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable.from_bins(domain=[-float('inf'), 0, float('inf')],
#                               name="V2")
#     V3 = DFVariable(name="V3", domain=[10, 20, 30])

#     cpd = DFCPD(name="Prob", var=[V1, V2, V3],
#                 fun=[1.0, 1.0, 2.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

#     cpd_expected_filename = os.path.join(
#         EXPECTED_PATH, "DFCPD_init_004_cpd.json")
#     # cpd.save(cpd_expected_filename)
#     cpd_expected = DFCPD.load(cpd_expected_filename)

#     assert cpd == cpd_expected


# def test_DFCPD_init_005():

#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable.from_bins(domain=[-float('inf'), 0, float('inf')],
#                               name="V2")
#     V3 = DFVariable(name="V3", domain=[10, 20, 30])

#     cpd = DFCPD(name="Prob", var=[V1, V2, V3],
#                 fun=[1.0, 3.0, 2.0, 0.0, 1.0, 1.0,
#                      5.0, 10.0, 2.0, 0.0, 0.0, 1.0],
#                 var_norm=["V2", "V3"])

#     cpd_expected_filename = os.path.join(
#         EXPECTED_PATH, "DFCPD_init_005_cpd.json")
#     # cpd.save(cpd_expected_filename)
#     cpd_expected = DFCPD.load(cpd_expected_filename)

#     assert cpd == cpd_expected


# # TODO: Multiindex categories pb
# def test_DFCPD_init_006():

#     V1 = DFVariable(name="V1", domain=[10, 20, 30], ordered=True)
#     V2 = DFVariable(name="V2", domain=["A", "B"])
#     V3 = DFVariable(name="V3", domain=["D", "C"], ordered=True)

#     cpd = DFCPD(name="Prob", var=[V1, V2, V3],
#                 var_norm=["V1"])

#     ipdb.set_trace()

#     assert isinstance(cpd.fun.index.levels[0], pd.CategoricalIndex)
#     assert isinstance(cpd.fun.index.levels[1], pd.CategoricalIndex)
#     assert isinstance(cpd.fun.index.levels[2], pd.CategoricalIndex)

#     # cpd_expected_filename = os.path.join(
#     #     EXPECTED_PATH, "DFCPD_init_005_cpd.json")
#     # # cpd.save(cpd_expected_filename)
#     # cpd_expected = DFCPD.load(cpd_expected_filename)

#     # assert cpd == cpd_expected


# def test_DFCPD_fit_001(data_toy_10_df):

#     data_df = data_toy_10_df.copy(deep=True)

#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable.from_bins(domain=[-float('inf'), 0, float('inf')],
#                               name="V2")
#     V3 = DFVariable(name="V3", domain=[10, 20, 30])

#     cpd = DFCPD(name="Prob", var=[V1, V2, V3], var_norm=["V1"])

#     data_adapt_df = cpd.adapt_data(data_df)

#     cpd.fit(data_adapt_df)

#     cpd_expected_filename = os.path.join(
#         EXPECTED_PATH, "DFCPD_fit_001_cpd.json")
#     # cpd.save(cpd_expected_filename)
#     cpd_expected = DFCPD.load(cpd_expected_filename)

#     assert cpd == cpd_expected


# def test_DFCPD_fit_002(data_toy_10_df):

#     data_df = data_toy_10_df.copy(deep=True)

#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable.from_bins(domain=[-float('inf'), 0, float('inf')],
#                               name="V2")
#     V3 = DFVariable(name="V3", domain=[10, 20, 30])

#     cpd = DFCPD(name="Prob", var=[V1, V2, V3], var_norm=["V1"])

#     data_adapt_df = cpd.adapt_data(data_df)

#     cpd.fit(data_adapt_df.iloc[:5])

#     cpd_expected_1_filename = os.path.join(
#         EXPECTED_PATH, "DFCPD_fit_002_cpd.json")
#     # cpd.save(cpd_expected_1_filename)
#     cpd_expected_1 = DFCPD.load(cpd_expected_1_filename)

#     assert cpd == cpd_expected_1

#     cpd.fit(data_adapt_df.iloc[5:], update_fit=True)

#     cpd_expected_2_filename = os.path.join(
#         EXPECTED_PATH, "DFCPD_fit_001_cpd.json")
#     # cpd.save(cpd_expected_1_filename)
#     cpd_expected_2 = DFCPD.load(cpd_expected_2_filename)

#     assert cpd == cpd_expected_2


# def test_DFCPD_fit_003(data_toy_10_df):

#     data_df = data_toy_10_df.copy(deep=True)

#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable.from_bins(domain=[-float('inf'), 0, float('inf')],
#                               name="V2")
#     V3 = DFVariable(name="V3", domain=[10, 20, 30])

#     cpd = DFCPD(name="Prob", var=[V1, V2, V3], var_norm=["V1"])

#     data_adapt_df = cpd.adapt_data(data_df)

#     cpd_expected_filename = os.path.join(
#         EXPECTED_PATH, "DFCPD_fit_001_cpd.json")
#     cpd_expected = DFCPD.load(cpd_expected_filename)

#     for idx in data_adapt_df.index:

#         assert cpd != cpd_expected

#         cpd.fit(data_adapt_df.loc[idx:idx], update=True)

#     assert cpd == cpd_expected


# def test_DFCPD_fit_004(data_toy_10_df):

#     data_df = data_toy_10_df.copy(deep=True)

#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable.from_bins(domain=[-float('inf'), 0, float('inf')],
#                               name="V2")
#     V3 = DFVariable(name="V3", domain=[10, 20, 30])

#     cpd = DFCPD(name="Prob", var=[V1, V2, V3], var_norm=["V1"])

#     data_adapt_df = cpd.adapt_data(data_df)

#     cpd.fit(data_adapt_df.iloc[:5])

#     cpd_expected_1_filename = os.path.join(
#         EXPECTED_PATH, "DFCPD_fit_002_cpd.json")
#     cpd_expected_1 = DFCPD.load(cpd_expected_1_filename)

#     assert cpd == cpd_expected_1

#     cpd.fit(data_adapt_df.iloc[5:], update_fit=True, update_decay=0.5)

#     cpd_expected_2_filename = os.path.join(
#         EXPECTED_PATH, "DFCPD_fit_004_cpd.json")
#     # cpd.save(cpd_expected_2_filename)
#     cpd_expected_2 = DFCPD.load(cpd_expected_2_filename)

#     assert cpd == cpd_expected_2


# def test_DFCPD_fit_005(data_btc_1000_hammer_df):

#     data_df = data_btc_1000_hammer_df.copy(deep=True)

#     data_train_df = data_df.iloc[:900]
#     data_test_df = data_df.iloc[900:]

#     cpd = DFCPD.init_from_dataframe(data_train_df,
#                                     var_norm="ret_close_t2")
#     cpd.fit(data_train_df)

#     cpd_expected_filename = os.path.join(EXPECTED_PATH,
#                                          "DFCPD_fit_005_cpd.csv")
#     cpd.save(cpd_expected_filename)
#     # TODO: BIG PB HERE !!!!
#     cpd_expected = DFCPD.load(cpd_expected_filename)

#     # ipdb.set_trace()

#     assert cpd == cpd_expected
#     # V1 = DFVariable(name="V1", domain=["A", "B"])
#     # V1 = DFVariable(name="ret_close_t2",
#     #                 domain_type="interval",
#     #                 domain=[-float('inf'), 0, float('inf')])
#     # V2 = DFVariable(name="hammer",
#     #                 domain_type="interval",
#     #                 domain=[-float('inf'), 0, float('inf')])
#     # V3 = DFVariable(name="ret_close_t2",
#     #                 domain_type="interval",
#     #                 domain=[-float('inf'), 0, float('inf')])

#     #                           name = "V2")
#     # V3=DFVariable(name = "V3", domain = [10, 20, 30])

#     # cpd=DFCPD(name = "Prob", var = [V1, V2, V3], var_norm = ["V1"])

#     # data_adapt_df=cpd.adapt_data(data_df)

#     # cpd.fit(data_adapt_df.iloc[:5])

#     # cpd_expected_1_filename=os.path.join(
#     #     EXPECTED_PATH, "DFCPD_fit_002_cpd.json")
#     # cpd_expected_1 = DFCPD.load(cpd_expected_1_filename)

#     # assert cpd == cpd_expected_1

#     # cpd.fit(data_adapt_df.iloc[5:], update_fit=True, update_decay=0.5)

#     # cpd_expected_2_filename = os.path.join(
#     #     EXPECTED_PATH, "DFCPD_fit_004_cpd.json")
#     # # cpd.save(cpd_expected_2_filename)
#     # cpd_expected_2 = DFCPD.load(cpd_expected_2_filename)

#     # assert cpd == cpd_expected_2


# def test_DFCPD_predict_001(data_toy_10_df):

#     data_df = data_toy_10_df.copy(deep=True)

#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable.from_bins(domain=[-float('inf'), 0, float('inf')],
#                               name="V2")
#     V3 = DFVariable(name="V3", domain=[10, 20, 30])

#     cpd = DFCPD(name="Prob", var=[V1, V2, V3], var_norm=["V1"])

#     cpd.fit(data_df)

#     cpd_expected_filename = os.path.join(
#         EXPECTED_PATH, "DFCPD_fit_001_cpd.json")
#     # cpd.save(cpd_expected_filename)
#     cpd_expected = DFCPD.load(cpd_expected_filename)

#     assert cpd == cpd_expected

#     cpd_pred = cpd.predict(data_df)
#     cpd_pred_expected_filename = os.path.join(
#         EXPECTED_PATH, "DFCPD_predict_001_cpd_pred.json")
#     # cpd_pred.save(cpd_pred_expected_filename)
#     cpd_pred_expected = DFCPD.load(cpd_pred_expected_filename)

#     assert cpd_pred == cpd_pred_expected


# def test_DFCPD_cdf_001():

#     cpd_filename = os.path.join(
#         EXPECTED_PATH, "DFCPD_init_005_cpd.json")
#     cpd = DFCPD.load(cpd_filename)

#     assert cpd.cdf().values.tolist() == \
#         [[0.125, 0.5, 0.75, 0.75, 0.875, 1.0],
#          [0.2777777777777778, 0.8333333333333334, 0.9444444444444444, 0.9444444444444444, 0.9444444444444444, 1.0]]


# def test_DFCPD_argmax_001():

#     cpd_filename = os.path.join(
#         EXPECTED_PATH, "DFCPD_init_005_cpd.json")
#     cpd = DFCPD.load(cpd_filename)

#     amax_2_df = cpd.argmax(nlargest=2)

#     assert amax_2_df.to_json() == '{"V2":{"(1, \'A\')":{"closed":"right","closed_right":true,"left":null,"mid":null,"open_right":false,"right":0.0},"(1, \'B\')":{"closed":"right","closed_right":true,"left":null,"mid":null,"open_right":false,"right":0.0},"(2, \'A\')":{"closed":"right","closed_right":true,"left":null,"mid":null,"open_right":false,"right":0.0},"(2, \'B\')":{"closed":"right","closed_right":true,"left":null,"mid":null,"open_right":false,"right":0.0}},"V3":{"(1, \'A\')":20,"(1, \'B\')":20,"(2, \'A\')":30,"(2, \'B\')":10}}'


# def test_DFCPD_set_prob_001():

#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable.from_bins(domain=[-float('inf'), 0, float('inf')],
#                               name="V2")
#     V3 = DFVariable(name="V3", domain=[10, 20, 30])

#     cpd = DFCPD(name="Prob",
#                 var=[V1, V2, V3],
#                 var_norm=["V1"])

#     cpd.set_prob([1, 9,
#                   2, 8,
#                   3, 7,
#                   4, 6,
#                   5, 5,
#                   4, 3])

#     cpd_expected_filename = os.path.join(
#         EXPECTED_PATH, "DFCPD_set_prob_001_cpd.json")
#     # cpd.save(cpd_expected_filename)
#     cpd_expected = DFCPD.load(cpd_expected_filename)

#     assert cpd == cpd_expected


# def test_DFCPD_set_prob_002():

#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable.from_bins(domain=[-float('inf'), 0, float('inf')],
#                               name="V2")
#     V3 = DFVariable(name="V3", domain=[10, 20, 30])

#     cpd = DFCPD(name="Prob",
#                 var=[V1, V2, V3],
#                 var_norm=["V1"])

#     cpd_bis = DFCPD(name="Prob",
#                     var=[V1, V2, V3],
#                     var_norm=["V1"])

#     cpd.set_prob([1, 9, 2, 8],
#                  cond={"V3": [10]})
#     cpd_bis.set_prob([1, 9, 2, 8],
#                      cond={"V3": 10})

#     cpd_expected_filename = os.path.join(
#         EXPECTED_PATH, "DFCPD_set_prob_002_cpd.json")
#     # cpd.save(cpd_expected_filename)
#     cpd_expected = DFCPD.load(cpd_expected_filename)

#     assert cpd == cpd_expected
#     assert cpd_bis == cpd_expected


# def test_DFCPD_get_prob_001():

#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable(name="V2", domain=[1, 3, 4, 5, 7, 10])

#     cpd = DFCPD(name="Prob",
#                 var=[V1, V2],
#                 var_norm=["V2"])

#     cpd.set_prob([0.1, 0.2, 0.05, 0.3, 0.05, 0.3,
#                   0.7, 0.05, 0.05, 0.1, 0, 0.1])

#     test_io = [
#         {"params": {"value": 5}, "expected": [0.3, 0.1]},
#         {"params": {"value": 1}, "expected": [0.1, 0.7]},
#         {"params": {"value": 10}, "expected": [0.3, 0.1]},
#         {"params": {"value": 34}, "expected": [0, 0]},
#         {"params": {"value": -6}, "expected": [0, 0]},
#         {"params": {"value": 6}, "expected": [0, 0]}
#     ]
#     for io in test_io:
#         assert cpd.get_prob(
#             **io["params"]).tolist() == io["expected"]


# def test_DFCPD_get_prob_002():
#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable(name="V2", domain=["a", "b", "c", "d", "e", "f"])

#     cpd = DFCPD(name="Prob",
#                 var=[V1, V2],
#                 var_norm=["V2"])

#     cpd.set_prob([0.1, 0.2, 0.05, 0.3, 0.05, 0.3,
#                   0.7, 0.05, 0.05, 0.1, 0, 0.1])

#     test_io = [
#         {"params": {"value": "a"}, "expected": [0.1, 0.7]},
#         {"params": {"value": "b"}, "expected": [0.2, 0.05]},
#         {"params": {"value": "c"}, "expected": [0.05, 0.05]},
#         {"params": {"value": "d"}, "expected": [0.3, 0.1]},
#         {"params": {"value": "e"}, "expected": [0.05, 0]},
#         {"params": {"value": "f"}, "expected": [0.3, 0.1]},
#         {"params": {"value": "g"}, "expected": [0, 0]},
#         {"params": {"value": ["a", "c"]}, "expected": [0.15, 0.75]},
#     ]
#     for io in test_io:
#         np.testing.assert_allclose(cpd.get_prob(**io["params"]),
#                                    io["expected"])


# def test_DFCPD_get_prob_003():
#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable(name="V2", domain=[1, 3, 4, 5, 7, 10])

#     cpd = DFCPD(name="Prob",
#                 var=[V1, V2],
#                 var_norm=["V2"])

#     cpd.set_prob([0.1, 0.2, 0.05, 0.3, 0.05, 0.3,
#                   0.7, 0.05, 0.05, 0.1, 0, 0.1])

#     test_io = [
#         {"params": {"value_min": 3, "value_max": 7}, "expected": [0.6, 0.2]},
#         {"params": {"value_min": 0, "value_max": 10}, "expected": [1, 1]},
#         {"params": {"value_min": 3, "value_max": 14}, "expected": [0.9, 0.3]},
#         {"params": {"value_min": -4, "value_max": 0}, "expected": [0, 0]},
#         {"params": {"value_min": 2, "value_max": 6}, "expected": [0.55, 0.2]},
#         {"params": {"value_min": 12, "value_max": 16}, "expected": [0, 0]},
#         {"params": {"value_min": -12, "value_max": -6}, "expected": [0, 0]},
#     ]
#     for io in test_io:
#         res = cpd.get_prob(**io["params"])
#         np.testing.assert_allclose(res, io["expected"])


# def test_DFCPD_get_prob_004():
#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable(name="V2", domain_type="interval",
#                     domain=[-float("inf"), 0, 1, 3, 4, 7, 10])

#     cpd = DFCPD(name="Prob",
#                 var=[V1, V2],
#                 var_norm=["V2"])

#     cpd.set_prob([0.1, 0.2, 0.05, 0.3, 0.05, 0.3,
#                   0.7, 0.05, 0.05, 0.1, 0, 0.1])

#     test_io = [
#         {"params": {"value": 5, "interval_zero_prob": False},
#             "expected": [0.05, 0]},
#         {"params": {"value": 1, "interval_zero_prob": False},
#             "expected": [0.20, 0.05]},
#         {"params": {"value": 10, "interval_zero_prob": False},
#             "expected": [0.3, 0.1]},
#         {"params": {"value": 34, "interval_zero_prob": False},
#             "expected": [0, 0]},
#         {"params": {"value": -6, "interval_zero_prob": False},
#             "expected": [0.1, 0.7]},
#         {"params": {"value": 6, "interval_zero_prob": False},
#             "expected": [0.05, 0]},
#         {"params": {"value": 6}, "expected": [0, 0]},
#         {"params": {"value": -6}, "expected": [0, 0]},
#         {"params": {"value": 34}, "expected": [0, 0]}
#     ]

#     for io in test_io:
#         assert cpd.get_prob(
#             **io["params"]).tolist() == io["expected"]


# def test_DFCPD_get_prob_005():
#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable(name="V2", domain_type="interval",
#                     domain=[-float("inf"), 0, 1, 3, 4, 7, 10])

#     cpd = DFCPD(name="Prob",
#                 var=[V1, V2],
#                 var_norm=["V2"])

#     cpd.set_prob([0.1, 0.2, 0.05, 0.3, 0.05, 0.3,
#                   0.7, 0.05, 0.05, 0.1, 0, 0.1])

#     test_io = [
#         {"params": {"value_min": 3, "value_max": 7}, "expected": [0.35, 0.1]},
#         {"params": {"value_min": 0, "value_max": 10}, "expected": [0.9, 0.3]},
#         {"params": {"value_min": 3, "value_max": 14}, "expected": [0.65, 0.2]},
#         {"params": {"value_min": -4, "value_max": 0}, "expected": [0, 0]},
#         {"params": {"value_min": 3.25, "value_max": 3.75},
#             "expected": [0.15, 0.05]},
#         {"params": {"value_min": 3.5, "value_max": 4.5},
#             "expected": [0.15 + 0.05*0.5/3, 0.05]},
#         {"params": {"value_min": 2, "value_max": 6}, "expected": [
#             0.5*0.05 + 0.3 + 2/3*0.05, 0.5*0.05 + 0.1]},
#         {"params": {"value_min": 12, "value_max": 16}, "expected": [0, 0]},
#         {"params": {"value_min": -12, "value_max": -6}, "expected": [0, 0]},
#         {"params": {"value_min": -12, "value_max": -6, "lower_bound": -12},
#             "expected": [0.05, 0.35]},
#         {"params": {"value_min": 5.5, "value_max": 8, "upper_bound": 9},
#             "expected": [0.025 + 0.15, 0.05]},
#     ]
#     for io in test_io:
#         res = cpd.get_prob_from_interval(**io["params"])
#         np.testing.assert_allclose(res, io["expected"])


# def test_DFCPD_expectancy_001():

#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable(name="V2", domain=[1, 3, 4, 5, 7, 10])

#     cpd = DFCPD(name="Prob",
#                 var=[V1, V2],
#                 var_norm=["V2"])

#     cpd.set_prob([0.1, 0.2, 0.05, 0.3, 0.05, 0.3,
#                   0.7, 0.05, 0.05, 0.1, 0, 0.1])

#     np.testing.assert_allclose(cpd.expectancy(), [5.75, 2.55])


# def test_DFCPD_expectancy_002():

#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable(name="V2", domain_type="interval",
#                     domain=[-float("inf"), 0, 1, 3, 4, 7, 10])

#     cpd = DFCPD(name="Prob",
#                 var=[V1, V2],
#                 var_norm=["V2"])

#     cpd.set_prob([0.1, 0.2, 0.05, 0.3, 0.05, 0.3,
#                   0.7, 0.05, 0.05, 0.1, 0, 0.1])

#     np.testing.assert_allclose(cpd.expectancy(ensure_finite=False),
#                                [-float("inf"), -float("inf")])

#     np.testing.assert_allclose(cpd.expectancy(lower_bound=-12),
#                                [3.475, -2.875])


# def test_DFCPD_quantile_001():
#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable(name="V2", domain=["a", "b", "c", "d", "e", "f"])

#     cpd = DFCPD(name="Prob",
#                 var=[V1, V2],
#                 var_norm=["V2"])

#     cpd.set_prob([0.1, 0.2, 0.05, 0.3, 0.05, 0.3,
#                   0.7, 0.05, 0.05, 0.1, 0, 0.1])

#     test_io = [
#         {"params": {"q": 0}, "expected": [np.nan, np.nan]},
#         {"params": {"q": 0.11}, "expected": ["a", np.nan]},
#         {"params": {"q": 0.21}, "expected": ["a", np.nan]},
#         {"params": {"q": 0.31}, "expected": ["b", np.nan]},
#         {"params": {"q": 0.41}, "expected": ["c", np.nan]},
#         {"params": {"q": 0.51}, "expected": ["c", np.nan]},
#         {"params": {"q": 0.61}, "expected": ["c", np.nan]},
#         {"params": {"q": 0.71}, "expected": ["e", "a"]},
#         {"params": {"q": 0.81}, "expected": ["e", "c"]},
#         {"params": {"q": 0.91}, "expected": ["e", "e"]},
#         {"params": {"q": 1.0}, "expected": ["f", "f"]},
#     ]
#     for io in test_io:
#         quantile = cpd.quantile(**io["params"]).dropna()
#         quantile_expected = pd.Series(
#             io["expected"], index=cpd.fun_to_df().index)\
#             .astype(quantile.dtype)\
#             .dropna()
#         assert (quantile == quantile_expected).all()


# def test_DFCPD_quantile_002():
#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable(name="V2", domain=[-1, 3, 5, 10, 12, 15])

#     cpd = DFCPD(name="Prob",
#                 var=[V1, V2],
#                 var_norm=["V2"])

#     cpd.set_prob([0, 0.2, 0.05, 0.3, 0.15, 0.3,
#                   0.7, 0.05, 0.05, 0.1, 0, 0.1])

#     test_io = [
#         {"params": {"q": 0}, "expected": [np.nan, np.nan]},
#         {"params": {"q": 0.11}, "expected": [-1, np.nan]},
#         {"params": {"q": 0.21}, "expected": [3, np.nan]},
#         {"params": {"q": 0.31}, "expected": [5, np.nan]},
#         {"params": {"q": 0.41}, "expected": [5, np.nan]},
#         {"params": {"q": 0.51}, "expected": [5, np.nan]},
#         {"params": {"q": 0.61}, "expected": [10, np.nan]},
#         {"params": {"q": 0.71}, "expected": [12, -1]},
#         {"params": {"q": 0.81}, "expected": [12, 5]},
#         {"params": {"q": 0.91}, "expected": [12, 12]},
#         {"params": {"q": 1.0}, "expected": [15, 15]},
#     ]

#     for io in test_io:
#         quantile = cpd.quantile(**io["params"]).dropna()
#         quantile_expected = pd.Series(
#             io["expected"], index=cpd.fun_to_df().index)\
#             .astype(quantile.dtype)\
#             .dropna()
#         assert (quantile == quantile_expected).all()


# def test_DFCPD_quantile_003():
#     V1 = DFVariable(name="V1", domain=["A", "B"])
#     V2 = DFVariable(name="V2", domain_type="interval",
#                     domain=[-float("inf"), 0, 1, 3, 4, 7, 10])

#     cpd = DFCPD(name="Prob",
#                 var=[V1, V2],
#                 var_norm=["V2"])

#     cpd.set_prob([0.1, 0.2, 0.05, 0.3, 0.05, 0.3,
#                   0.7, 0.05, 0.05, 0.1, 0, 0.1])
#     test_io = [
#         {"params": {"q": 0}, "expected": [-np.inf, -np.inf]},
#         {"params": {"q": 0.05}, "expected": [-np.inf, -np.inf]},
#         {"params": {"q": 0.11}, "expected": [0.05, -np.inf]},
#         {"params": {"q": 0.21}, "expected": [0.55, -np.inf]},
#         {"params": {"q": 0.31}, "expected": [1.4, -np.inf]},
#         {"params": {"q": 0.41}, "expected": [3.2, -np.inf]},
#         {"params": {"q": 0.51}, "expected": [3.53333333, -np.inf]},
#         {"params": {"q": 0.61}, "expected": [3.86666666, -np.inf]},
#         {"params": {"q": 0.71}, "expected": [7.1, 0.2]},
#         {"params": {"q": 0.81}, "expected": [8.1, 3.1]},
#         {"params": {"q": 0.91}, "expected": [9.1, 7.3]},
#         {"params": {"q": 1.0}, "expected": [10, 10]},
#     ]

#     for io in test_io:
#         # ipdb.set_trace()
#         np.testing.assert_allclose(cpd.quantile(**io["params"]).values,
#                                    pd.Series(io["expected"], index=cpd.fun_to_df().index).values)


# # Tests Stackoverflow

# def test_pandas_so_001():

#     V0_cat_idx = pd.CategoricalIndex([10, 20, 30],
#                                      categories=[10, 20, 30],
#                                      ordered=True,
#                                      name="V0")
#     V1_cat_idx = pd.CategoricalIndex(["B", "A"],
#                                      categories=["B", "A"],
#                                      ordered=True,
#                                      name="V1")
#     cat_midx = pd.MultiIndex.from_product([V0_cat_idx, V1_cat_idx])

#     myseries = pd.Series(range(6), index=cat_midx)
#     norm = myseries.groupby(level=["V1"]).sum()

#     myseries_norm = myseries.div(norm)

#     assert (myseries_norm.index.levels[0] == V0_cat_idx).all()
#     assert (myseries_norm.index.levels[1] == V1_cat_idx).all()


# def test_pandas_so_002():

#     V0_cat_idx = pd.CategoricalIndex([10, 20, 30],
#                                      categories=[10, 20, 30],
#                                      ordered=True,
#                                      name="V0")

#     V1_cat_idx = pd.CategoricalIndex(["B", "A"],
#                                      categories=["B", "A"],
#                                      ordered=True,
#                                      name="V1")

#     V2_cat_idx = pd.CategoricalIndex(["X", "Y"],
#                                      categories=["X", "Y"],
#                                      name="V2")

#     cat_midx_2 = pd.MultiIndex.from_product(
#         [V0_cat_idx, V1_cat_idx, V2_cat_idx])

#     myseries_2 = pd.Series(range(12), index=cat_midx_2)
#     norm_2 = myseries_2.groupby(level=["V1", "V2"]).sum()

#     myseries_norm_2 = myseries_2.div(norm_2)

#     # PB HERE
#     # ipdb.set_trace()

#     # assert (myseries_norm.index.levels[1] == V2_cat_idx).all()


# def test_pandas_so_003():

#     V0_cat_idx = pd.CategoricalIndex([10, 20, 30],
#                                      categories=[10, 20, 30],
#                                      ordered=True,
#                                      name="V0")

#     V1_cat_idx = pd.CategoricalIndex(["B", "A"],
#                                      categories=["B", "A"],
#                                      ordered=True,
#                                      name="V1")

#     V2_cat_idx = pd.CategoricalIndex(["X", "Y"],
#                                      categories=["X", "Y"],
#                                      name="V2")

#     cat_midx_3 = pd.MultiIndex.from_product(
#         [V1_cat_idx, V2_cat_idx, V0_cat_idx])

#     myseries_3 = pd.Series(range(12), index=cat_midx_3)
#     norm_3 = myseries_3.groupby(level=["V1", "V2"]).sum()

#     myseries_norm_3 = myseries_3.div(norm_3)

#     # PB HERE


# def test_pandas_so_004():

#     V0_cat_idx = pd.CategoricalIndex([10, 20, 30],
#                                      categories=[10, 20, 30],
#                                      ordered=True,
#                                      name="V0")

#     V1_cat_idx = pd.CategoricalIndex(["B", "A"],
#                                      categories=["B", "A"],
#                                      ordered=True,
#                                      name="V1")

#     V2_cat_idx = pd.CategoricalIndex(["X", "Y"],
#                                      categories=["X", "Y"],
#                                      name="V2")

#     cat_midx = pd.MultiIndex.from_product(
#         [V0_cat_idx, V1_cat_idx, V2_cat_idx])

#     myseries = pd.Series(range(12), index=cat_midx)
#     norm = myseries.groupby(level=["V1", "V2"]).sum()

#     myseries_norm = myseries.div(norm)

#     ipdb.set_trace()


# def test_pandas_github_001():

#     V0_cat_idx = pd.CategoricalIndex([10, 20, 30],
#                                      categories=[10, 20, 30],
#                                      ordered=True,
#                                      name="V0")

#     V1_cat_idx = pd.CategoricalIndex(["B", "A"],
#                                      categories=["B", "A"],
#                                      ordered=True,
#                                      name="V1")

#     V2_cat_idx = pd.CategoricalIndex(["X", "Y"],
#                                      categories=["X", "Y"],
#                                      name="V2")

#     cat_midx = pd.MultiIndex.from_product(
#         [V0_cat_idx, V1_cat_idx, V2_cat_idx])

#     myseries = pd.Series(range(12), index=cat_midx)
#     norm = myseries.groupby(level=["V1", "V2"]).sum()

#     myseries_norm = myseries.div(norm)

#     assert isinstance(
#         myseries_norm.index.levels[0], pd.CategoricalIndex)  # Failed
#     assert isinstance(
#         myseries_norm.index.levels[1], pd.CategoricalIndex)  # Failed
#     assert isinstance(myseries_norm.index.levels[2], pd.CategoricalIndex)  # OK
#     # PB HERE
#     # ipdb.set_trace()

#     # assert (myseries_norm.index.levels[1] == V2_cat_idx).all()
