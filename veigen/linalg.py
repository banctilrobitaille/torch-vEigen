from math import pi

import torch


def solve_cardan(p, q):
    b, d, h, w = p.size()
    eig_vals = torch.zeros(b, 3, d, h, w).to(p.device)

    if (p == 0.0).any():
        raise ValueError("Unable to solve Cardan's equation with p coefficient equal to 0")
    else:
        q2 = torch.pow(q, 2)
        p3 = torch.pow(p, 3)
        D = q2 + 4.0 * p3 / 27.0

    D[torch.abs(D) < 1e-10] = 0.0

    if (D > 0.0).any():
        raise ValueError("Unable to solve Cardan's equation with discriminant greater than 0")
    elif (D < 0.0).any():
        b, d, h, w = torch.where(D < 0.0)

        acosq = torch.acos(-q[b, d, h, w] / 2.0 * torch.sqrt(27 / -p3[b, d, h, w]))
        two_sqrt = 2 * torch.sqrt(-p[b, d, h, w] / 3.0)
        eig_vals[b, 0, d, h, w] = two_sqrt * torch.cos(1.0 / 3.0 * acosq)
        eig_vals[b, 1, d, h, w] = two_sqrt * torch.cos(1.0 / 3.0 * acosq + 2 * pi / 3)
        eig_vals[b, 2, d, h, w] = two_sqrt * torch.cos(1.0 / 3.0 * acosq + 4 * pi / 3)
    else:
        b, d, h, w = torch.where(D == 0.0)
        eig_vals[b, 0, d, h, w] = 3 * q[b, d, h, w] / p[b, d, h, w]
        eig_vals[b, 1, d, h, w] = -3.0 * q[b, d, h, w] / (2.0 * p[b, d, h, w])
        eig_vals[b, 2, d, h, w] = eig_vals[b, 1, d, h, w]

    return eig_vals


def compute_eigen_values(a, b, c, d):
    if (b == 0.0).any() and (b == 0.0).any() and (c == 0.0).any() and (d == 0.0).any():
        raise ValueError("Unable to solve 3rd degree equation with null coefficient")

    if (b == 0.0).any():
        eig_vals = solve_cardan(c / a, d / a)
    else:
        a2 = torch.pow(a, 2)
        b2 = torch.pow(b, 2)

        p = -b2 / (3 * a2) + c / a
        q = b / (27 * a) * (2 * b2 / a2 - 9.0 * c / a) + d / a
        eig_vals = solve_cardan(p, q)

        s = (-b / (3 * a)).unsqueeze(1).expand(eig_vals.shape)
        eig_vals = eig_vals + s

    return eig_vals


def compute_eigen_vectors(A, eigen_value):
    a11 = A[:, 0, :, :, :]
    a12 = A[:, 1, :, :, :]
    a13 = A[:, 2, :, :, :]
    a22 = A[:, 4, :, :, :]
    a23 = A[:, 5, :, :, :]

    u0 = a12 * a23 - a13 * (a22 - eigen_value)
    u1 = a12 * a13 - a23 * (a11 - eigen_value)
    u2 = (a11 - eigen_value) * (a22 - eigen_value) - a12 * a12
    norm = torch.sqrt(torch.pow(u0, 2) + torch.pow(u1, 2) + torch.pow(u2, 2))
    u0 = u0 / norm
    u1 = u1 / norm
    u2 = u2 / norm

    return [u0, u1, u2]


def cross_product(u, v):
    return [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]


def symeig(A, eigen_vectors=False):
    a11 = A[:, 0, :, :, :]
    a12 = A[:, 1, :, :, :]
    a13 = A[:, 2, :, :, :]
    a22 = A[:, 4, :, :, :]
    a23 = A[:, 5, :, :, :]
    a33 = A[:, 8, :, :, :]

    b = a11 + a22 + a33
    c = (-a22 - a11) * a33 + a23 * a23 - a11 * a22 + a13 * a13 + a12 * a12
    d = a11 * a22 * a33 - a12 * a12 * a33 - a11 * a23 * a23 + 2 * a12 * a13 * a23 - a13 * a13 * a22
    a = torch.Tensor([-1.0]).expand(b.shape).to(A.device)

    eig_vals = compute_eigen_values(a, b, c, d)

    if (eig_vals[:, 0, :, :, :] < eig_vals[:, 1, :, :, :]).any():
        index = torch.where(eig_vals[:, 0, :, :, :] < eig_vals[:, 1, :, :, :])
        temp_s0 = eig_vals[:, 0, :, :, :][index]
        eig_vals[:, 0, :, :, :][index] = eig_vals[:, 1, :, :, :][index]
        eig_vals[:, 1, :, :, :][index] = temp_s0

    if (eig_vals[:, 0, :, :, :] < eig_vals[:, 2, :, :, :]).any():
        index = torch.where(eig_vals[:, 0, :, :, :] < eig_vals[:, 2, :, :, :])
        temp_s0 = eig_vals[:, 0, :, :, :][index]
        eig_vals[:, 0, :, :, :][index] = eig_vals[:, 2, :, :, :][index]
        eig_vals[:, 2, :, :, :][index] = temp_s0

    if (eig_vals[:, 1, :, :, :] < eig_vals[:, 2, :, :, :]).any():
        index = torch.where(eig_vals[:, 1, :, :, :] < eig_vals[:, 2, :, :, :])
        temp_s1 = eig_vals[:, 1, :, :, :][index]
        eig_vals[:, 1, :, :, :][index] = eig_vals[:, 2, :, :, :][index]
        eig_vals[:, 2, :, :, :][index] = temp_s1

    if eigen_vectors:
        if (eig_vals[:, 1, :, :, :] == eig_vals[:, 2, :, :, :]).any():
            if (eig_vals[:, 0, :, :, :] == eig_vals[:, 1, :, :, :]).any():
                pass
                # identity
            else:
                u0 = compute_eigen_vectors(A, eig_vals[:, 0, :, :, :])
                u1 = compute_eigen_vectors(A, eig_vals[:, 1, :, :, :])
                u2 = cross_product(u0, u1)
        else:
            u0 = compute_eigen_vectors(A, eig_vals[:, 0, :, :, :])
            u1 = compute_eigen_vectors(A, eig_vals[:, 1, :, :, :])
            u2 = compute_eigen_vectors(A, eig_vals[:, 2, :, :, :])

    return eig_vals, u0, u1, u2
