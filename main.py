""" estimates via 2SLS and corrected 2SLS """
import numpy as np
import scipy.linalg as spla

from QLRC import QLRCModel, least_squares_proj

from BLP_basic import f0_BLP, f1_BLP, A_star_BLP, A2_BLP, A33_BLP, K_BLP,\
    f_infty_BLP

from blp_utils import simulated_mean_shares
from bsstats import flexible_reg

if __name__ == "__main__":

    check_by_hand = True

    n_markets = 1000
    n_products = 100
    nx = 2
    n_draws = 10000

    X = np.random.normal(size=(n_markets, n_products, nx))
    # the first covariate is the constant
    X[:, :, 0] = 1.0
    beta_bar = np.array([-4.0, 1.0])
    xi = np.random.normal(size=(n_markets, n_products))
    sigmas = np.array([0.2])
    # no random coefficient on the constant
    eps = np.random.normal(size=(n_markets, nx - 1, n_draws))
    n_Y = n_products + nx
    Y = np.zeros((n_markets, n_products, n_Y))
    K = np.zeros((n_markets, n_products, nx-1))
    for t in range(n_markets):
        X_t, eps_t, xi_t = X[t, :, :], eps[t, :, :], xi[t, :]
        Xsig_eps = np.zeros((n_products, n_draws))
        for ix in range(1, nx):
            Xsig_eps += (np.outer(X_t[:, ix], sigmas[ix-1] * eps_t[ix-1, :]))
        utils = Xsig_eps + (X_t @ beta_bar + xi_t).reshape((-1, 1))
        shares = simulated_mean_shares(utils)
        # Y[t, i, :n_products] is the vector of market shares
        Y[t, :, :n_products] = np.tile(shares, (n_products, 1))
        # Y[t, i, :n_products] is the vector of market shares
        Y[t, :, n_products:] = X_t
        # also construct K for comparison
        for ix in range(nx):
            xtix = X_t[:, ix]
            eSix = xtix @ shares
            K[t, :, ix-1] = xtix*(xtix/2.0-eSix)


    n_betas =  nx
    n_Sigma = nx - 1
    n_instruments = 2*nx -1 + nx*(nx-1)
    Z = np.zeros((n_markets, n_products, n_instruments))
    Z_t = np.zeros((n_products, n_instruments))
    for t in range(n_markets):
        X_t = X[t, :, :]
        X_t1 = X_t[:, 1:]
        Z_t[:, :nx] = X_t
        meanX_t1= X_t1.mean(axis=0)
        dX_t1 =  X_t1 - meanX_t1
        Z_t[:, nx:(2*nx-1)] = dX_t1
        iz = 2*nx-1
        for i in range(nx-1):
            for j in range(i, nx-1):
                Z_t[:, iz] = X_t1[:, i]*X_t1[:, j]
                iz += 1
                Z_t[:, iz] = dX_t1[:, i] * dX_t1[:, j]
                iz += 1
        Z[t, :, :] = Z_t

    model = QLRCModel(Y, A_star_BLP, f1_BLP, n_betas, n_Sigma, Z, f_0=f0_BLP,
                      # K = K_BLP,
                      args=[n_products, A2_BLP, A33_BLP])
    model.fit()

    # model.predict(f_infty_BLP)
    # model.fit_corrected()

    model.print()

    print(f"True betas: {beta_bar}")
    print(f"True Sigma: {sigmas**2}")

    if check_by_hand:
        n_points = n_markets * n_products
        f_0 = np.zeros((n_markets, n_products))
        for t in range(n_markets):
            f_0[t, :] = f0_BLP(Y[t, :, :], [n_products])
        f0r = f_0.reshape(n_points)
        Xr = np.zeros((n_points, nx))
        Kr = np.zeros((n_points, nx-1))
        Zr = np.zeros((n_points, n_instruments))
        for ix in range(nx):
            Xr[:, ix] = X[:, :, ix].reshape((n_points))
        for ix in range(nx-1):
            Kr[:, ix] = K[:, :, ix].reshape((n_points))
        for iz in range(n_instruments):
            Zr[:, iz] = Z[:, :, iz].reshape((n_points))
        Kfit  = least_squares_proj(Zr, Kr)

        rhs = np.concatenate((Xr, Kfit), axis=1)
        coeffs, _, _, _ = spla.lstsq(rhs, f0r)
        print(f"\n\n Checking estimates by hand:\n")
        print(f"     hand-computed betas: {coeffs[:n_betas]}")
        print(f"     hand-computed Sigma: {coeffs[n_betas:]}")







