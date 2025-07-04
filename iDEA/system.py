"""Contains all functionality to define and manage definitions of model systems."""


import warnings
import numpy as np
import iDEA.utilities
import iDEA.interactions


__all__ = ["System", "save_system", "load_system", "systems"]


class System:
    r"""Model system, containing all defining properties."""

    def __init__(
        self,
        x: np.ndarray,
        v_ext: np.ndarray,
        v_int: np.ndarray,
        electrons: str,
        stencil: int = 13,
    ):
        r"""
        Model system, containing all defining properties.

        | Args:
        |     x: np.ndarray, Grid of x values in 1D space.
        |     v_ext: np.ndarray, External potential on the grid of x values.
        |     v_int: np.ndarray, Interaction potential on the grid of x values.
        |     electrons: string, Electrons contained in the system.
        |     stencil: int, Stencil to use for derivatives on the grid of x values. (default = 13)

        | Raises:
        |     AssertionError.
        """
        self.__x = x
        self.__dx = self.x[1] - self.x[0]
        self.v_ext = v_ext
        self.v_int = v_int
        self.__electrons = electrons
        self.count = len(electrons)
        self.up_count = electrons.count("u")
        self.down_count = electrons.count("d")
        self.stencil = stencil
        self.set_potentials()
        self.v_ext_op = np.diag(self.v_ext) # non-interacting external potential operator
        self.kinetic_op = -0.5 * self.build_second_derivative_matrix()
        self.check()

    def set_potentials(self):
        if callable(self.v_ext):
            self.v_ext = self.v_ext(self.x)
        if callable(self.v_int):
            self.v_int = self.v_int(self.x)

    def calculate_coefficients(self,points_in,derivative_order):
        """calculates the finite difference coefficients for a list of points of arbitrary spacing
        the point at which the derivative should be calculated should be 0 in points_in
        the algorithm used for generating the coefficients can be found in https://www.ams.org/journals/mcom/1988-51-184/S0025-5718-1988-0935077-0/

        Args:
            points_in (list(float)): points at which the finite difference coefficients should be calculated
            derivative_order (int): order of the derivative
        Returns:
            np.ndarray: list of finite difference coefficients
        """
        x0 = 0
        # order the points
        points = []
        while len(points_in)>0:
            p = min(points_in,key=abs)
            points.append(p)
            points_in = np.delete(points_in, np.where(points_in == p))
        # set up array for storing coefficients
        coeffs = np.zeros((derivative_order+1,len(points),len(points)))
        coeffs[0,0,0] = 1
        c1 = 1

        # iteratively generate finite difference coefficients
        for n in range(1,len(points)):
            c2 = 1
            for nu in range(0,n):
                c3 = points[n] - points[nu]
                c2 = c2*c3
                for m in range(0,min([n,derivative_order])+1):
                    if c3 != 0:
                        coeffs[m,n,nu] = (1/c3) * ((points[n]-x0)*coeffs[m,n-1,nu]-m*coeffs[m-1,n-1,nu])
            for m in range(0,min([n,derivative_order])+1):
                if c2 != 0:
                    coeffs[m,n,n] = (c1/c2) * (m*coeffs[m-1,n-1,n-1]-(points[n-1]-x0)*coeffs[m,n-1,n-1])
            c1=c2
        order = np.argsort(points)
        return coeffs[derivative_order,-1,order]

    def build_second_derivative_matrix(self):
        """builds second derivative operator from finite difference coefficients

        Returns:
            np.ndarray: second derivative operator
        """
        matrix = np.zeros(len(self.x),len(self.x))
        for i in range(len(self.x)):
            # get left and right bounds for points used for finite difference calculation based on stencil
            left = i - int((self.stencil-1)/2)
            right = left + self.stencil
            # if left or right are out of bounds of array
            if left < 0:
                left = 0
            if right > len(self.x):
                right = len(self.x)

            # calculate finite difference coefficients
            coeffs = self.calculate_coefficients(self.x[left:right]-self.x[i],2)

            # add coefficients to matrix
            matrix[i,left:right] = coeffs
        return matrix


    def check(self):
        r"""Performs checks on system properties. Raises AssertionError if any check fails."""
        assert (
            type(self.x) == np.ndarray
        ), f"x grid is not of type np.ndarray, got {type(self.x)} instead."
        assert (
            type(self.v_ext) == np.ndarray
        ), f"v_ext is not of type np.ndarray, got {type(self.v_ext)} instead."
        assert (
            type(self.v_int) == np.ndarray
        ), f"v_int is not of type np.ndarray, got {type(self.v_int)} instead."
        assert (
            type(self.count) == int
        ), f"count is not of type int, got {type(self.NE)} instead."
        assert (
            len(self.x.shape) == 1
        ), f"x grid is not a 1D array, got {len(self.x.shape)}D array instead."
        assert (
            len(self.v_ext.shape) == 1
        ), f"v_ext is not a 1D array, got {len(self.v_ext.shape)}D array instead."
        assert (
            len(self.v_int.shape) == 2
        ), f"v_int is not a 2D array, got {len(self.v_int.shape)}D array instead."
        assert (
            self.x.shape == self.v_ext.shape
        ), f"x grid and v_ext arrays are not the same shape, got x.shape = {self.x.shape} and v_ext.shape = {self.v_ext.shape} instead."
        assert (
            self.x.shape[0] == self.v_int.shape[0]
            and self.x.shape[0] == self.v_int.shape[1]
        ), "v_int is not of the correct shape, got shape {self.v_int.shape} instead."
        assert self.count >= 0, f"count is not positive."
        assert set(self.electrons).issubset(
            set(["u", "d"])
        ), f"Electrons must have only up or down spin, e.g 'uudd'. Got {self.electrons} instead"
        assert (
            self.count == self.up_count + self.down_count
        ), f"Electrons must obay up_count + down_count = count."
        assert self.stencil in [
            3,
            5,
            7,
            9,
            11,
            13,
        ], f"stencil must be one of [3,5,7,9,11,13], got {self.stencil} instead."

    @property
    def x(self):
        return self.__x

    @x.setter
    def x(self, value):
        self.__x = value
        self.__dx = self.__x[1] - self.__x[0]
        warnings.warn(
            "x grid has been changed: dx has been recomputed, please update v_ext and v_int on this grid."
        )

    @x.deleter
    def x(self):
        del self.__x

    @property
    def dx(self):
        return self.__dx

    @dx.setter
    def dx(self, value):
        raise AttributeError(
            "cannot set dx directly: set the x grid and dx will be updated automatically."
        )

    @dx.deleter
    def dx(self):
        del self.__dx

    @property
    def electrons(self):
        return self.__electrons

    @electrons.setter
    def electrons(self, value):
        self.__electrons = value
        self.count = len(value)
        self.up_count = value.count("u")
        self.down_count = value.count("d")

    @electrons.deleter
    def electrons(self):
        del self.__electrons

    def __str__(self):
        return f"iDEA.system.System: x = np.array([{self.x[0]:.3f},...,{self.x[-1]:.3f}]), dx = {self.dx:.4f}..., v_ext = np.array([{self.v_ext[0]:.3f},...,{self.v_ext[-1]:.3f}]), electrons = {self.electrons}"


def save_system(s: System, file_name: str) -> None:
    r"""
    Save a system to an system file.

    | Args:
    |     system: iDEA.system.System, System object to save.
    |     file_name: str, file name.
    """
    pickle.dump(s, open(file_name, "wb"))


def load_system(file_name: str) -> System:
    r"""
    Load a system from an system file.

    | Args:
    |     file_name: str, file name.

    | Returns
    |     system: iDEA.system.System, Loaded System object.
    """
    return pickle.load(open(file_name, "rb"))


# Define some default built in systems.
__x1 = np.linspace(-10, 10, 300)
systems = iDEA.utilities.Container()
systems.qho = System(
    __x1,
    0.5 * (0.25**2) * (__x1**2),
    iDEA.interactions.softened_interaction(__x1),
    "uu",
)
__x2 = np.linspace(-20, 20, 300)
systems.atom = System(
    __x2, -2.0 / (abs(__x2) + 1.0), iDEA.interactions.softened_interaction(__x2), "ud"
)
