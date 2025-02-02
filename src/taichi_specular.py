from taichi_common import *

import numpy as np
from math_tools import normalize

def _reflectance0(n1, n2):
    sqrt_R0 = np.float64(n1 - n2) / (n1 + n2)
    return sqrt_R0 * sqrt_R0

def _schlick_reflectance(n1, n2, c):
    R0 = _reflectance0(n1, n2)
    return R0 + (1.0 - R0) * c * c * c * c * c

def _ideal_specular_reflect(d, n):
    return d - 2.0 * n.dot(d) * n

def _ideal_specular_transmit(d, n, n_out, n_in):
    n_out, n_in = np.float64(n_out), np.float64(n_in)
    d_Re = _ideal_specular_reflect(d, n)

    out_to_in = n.dot(d) < 0
    nl = n if out_to_in else -n
    nn = n_out / n_in if out_to_in else n_in / n_out
    cos_theta = d.dot(nl)
    cos2_phi = 1.0 - nn * nn * (1.0 - cos_theta * cos_theta)

    # Total Internal Reflection
    if cos2_phi < 0:
        return d_Re, 1.0

    d_Tr = normalize(nn * d - nl * (nn * cos_theta + np.sqrt(cos2_phi)))
    c = 1.0 - (-cos_theta if out_to_in else d_Tr.dot(n))

    Re = _schlick_reflectance(n_out, n_in, c)
    p_Re = 0.25 + 0.5 * Re
    if 0.5 < p_Re:
        return d_Re, (Re / p_Re)
    else:
        Tr = 1.0 - Re
        p_Tr = 1.0 - p_Re
        return d_Tr, (Tr / p_Tr)


@ti.func
def ideal_specular_reflect(d: ti.math.vec3, n: ti.math.vec3) -> ti.math.vec3:
    return d - 2.0 * ti.math.dot(n, d) * n
    
@ti.func
def reflectance0(n1: ti.f64, n2: ti.f64) -> ti.f64:
    sqrt_R0 = (n1 - n2) / (n1 + n2)
    return sqrt_R0 * sqrt_R0

@ti.func
def schlick_reflectance(n1: ti.f64, n2: ti.f64, c: ti.f64) -> ti.f64:
    R0 = reflectance0(n1, n2)
    return R0 + (1.0 - R0) * c * c * c * c * c

@ti.func
def ideal_specular_transmit(d: ti.math.vec3, n: ti.math.vec3, n_out: ti.f64, n_in: ti.f64) -> ti.math.vec4:    
    ret_val = ti.math.vec4(0, 0, 0, 0)
    n_out, n_in = ti.f64(n_out), ti.f64(n_in)
    d_Re = ideal_specular_reflect(d, n)

    out_to_in = ti.math.dot(n, d) < 0
    nl = n if out_to_in else -n
    nn = n_out / n_in if out_to_in else n_in / n_out
    cos_theta = ti.math.dot(d, nl)
    cos2_phi = 1.0 - nn * nn * (1.0 - cos_theta * cos_theta)

    # Total Internal Reflection
    if cos2_phi < 0:
        # return d_Re, 1.0        
        ret_val = ti.math.vec4(d_Re[0], d_Re[1], d_Re[2], 1.0)
    else:
        # d_Tr = normalize(nn * d - nl * (nn * cos_theta + ti.math.sqrt(cos2_phi)))
        d_Tr = ti.math.normalize(nn * d - nl * (nn * cos_theta + ti.math.sqrt(cos2_phi)))
        c = 1.0 - (-cos_theta if out_to_in else ti.math.dot(d_Tr, n))

        Re = schlick_reflectance(n_out, n_in, c)
        p_Re = 0.25 + 0.5 * Re
        # if uniform_float() < p_Re:
        if 0.5 < p_Re:
            # return d_Re, (Re / p_Re)            
            ret_val = ti.math.vec4(d_Re[0], d_Re[1], d_Re[2], Re / p_Re)
        else:
            Tr = 1.0 - Re
            p_Tr = 1.0 - p_Re
            # return d_Tr, (Tr / p_Tr)            
            ret_val = ti.math.vec4(d_Tr[0], d_Tr[1], d_Tr[2], Tr / p_Tr)
    return ret_val

@ti.kernel
def test_ideal_specular_reflect():
    d = ti.Vector([1.0, 1.0, 1.0])
    n = ti.Vector([0.0, 0.0, 1.0])
    print("Expected Value: ", ti.Vector([1.0, 1.0, -1.0]),
            "\nGot Value: ", ideal_specular_reflect(d, n))

@ti.kernel
def _test_ideal_specular_transmit(d: ti.math.vec3, n: ti.math.vec3, n_out: ti.f64, n_in: ti.f64) -> ti.math.vec4:
    return ideal_specular_transmit(d, n, n_out, n_in)

def test_ideal_specular_transmit():
    # [-0.45053866  0.7109803  -0.5399277 ] [-0.59208796  0.70113365 -0.39729517] 1.0 1.5
    d = [-0.45053866, 0.7109803, -0.5399277]
    n = [-0.59208796, 0.70113365, -0.39729517]
    n_out = 1.0
    n_in = 1.5
    print("Expected Value: ", _ideal_specular_transmit(np.array(d), np.array(n), n_out, n_in),
            "\nGot Value: ", _test_ideal_specular_transmit(ti.Vector(d), ti.Vector(n), n_out, n_in))

if __name__ == '__main__':
    # change uniform float to some const value in _ideal... and _test_ideal... calls in test_ideal_specular_transmit
    # before running the below code
    # test_ideal_specular_transmit()
    pass