"""
    This is a definition of the Gated Diffusive Unit explained in our report. 
    Originally written by Jiawei Zhang (https://github.com/jwzhanggy).
"""


import math
from enum import IntEnum
import numpy as np
import random

import torch
import torch.nn as nn
from torch.nn import Parameter

class GDU(nn.Module):
    gdu_type = None

    def __init__(self, gdu_type, g_sz, x_sz, z_sz, h_sz, out_sz):
        super().__init__()
        self.gdu_type = gdu_type
        self.g_sz = g_sz
        self.x_sz = x_sz
        self.z_sz = z_sz
        self.h_sz = h_sz
        self.out_sz = out_sz

        # adjustment forget gate f
        self.W_fx = Parameter(torch.FloatTensor(x_sz, z_sz))
        self.W_fz = Parameter(torch.FloatTensor(z_sz, z_sz))
        self.W_fh = Parameter(torch.FloatTensor(h_sz, z_sz))
        self.b_f = Parameter(torch.FloatTensor(z_sz))
        # adjustment evolve gate e
        self.W_ex = Parameter(torch.FloatTensor(x_sz, h_sz))
        self.W_ez = Parameter(torch.FloatTensor(z_sz, h_sz))
        self.W_eh = Parameter(torch.FloatTensor(h_sz, h_sz))
        self.b_e = Parameter(torch.FloatTensor(h_sz))
        # selection gate g
        self.W_gx = Parameter(torch.FloatTensor(x_sz, out_sz))
        self.W_gz = Parameter(torch.FloatTensor(z_sz, out_sz))
        self.W_gh = Parameter(torch.FloatTensor(h_sz, out_sz))
        self.W_gz_tilde = Parameter(torch.FloatTensor(z_sz, out_sz))
        self.W_gh_tilde = Parameter(torch.FloatTensor(h_sz, out_sz))
        self.b_g = Parameter(torch.FloatTensor(out_sz))
        # selection gate r
        self.W_rx = Parameter(torch.FloatTensor(x_sz, out_sz))
        self.W_rz = Parameter(torch.FloatTensor(z_sz, out_sz))
        self.W_rh = Parameter(torch.FloatTensor(h_sz, out_sz))
        self.W_rz_tilde = Parameter(torch.FloatTensor(z_sz, out_sz))
        self.W_rh_tilde = Parameter(torch.FloatTensor(h_sz, out_sz))
        self.b_r = Parameter(torch.FloatTensor(out_sz))
        # in-out dimension adjustment
        self.W_ux = Parameter(torch.FloatTensor(x_sz, out_sz))
        self.W_uz = Parameter(torch.FloatTensor(z_sz, out_sz))
        self.W_uh = Parameter(torch.FloatTensor(h_sz, out_sz))
        self.b_u = Parameter(torch.FloatTensor(out_sz))

        self.init_weights()

    def init_weights(self):
        for p in self.parameters():
            if p.data.ndimension() >= 2:
                stdv = 1. / math.sqrt(p.data.size(1))
            else:
                stdv = 1. / math.sqrt(p.data.size(0))
            p.data.uniform_(-stdv, stdv)

    def forward(self, x, z, h):
        # forget gate f
        f = torch.sigmoid(torch.mm(x, self.W_fx) + torch.mm(z, self.W_fz) + torch.mm(h, self.W_fh) + self.b_f)
        z_tilde = f * z
        # evolve gate e
        e = torch.sigmoid(torch.mm(x, self.W_ex) + torch.mm(z, self.W_ez) + torch.mm(h, self.W_eh) + self.b_e)
        h_tilde = e * h
        # select gate g and r
        g = torch.sigmoid(torch.mm(x, self.W_gx) + torch.mm(z, self.W_gz) + torch.mm(h, self.W_gh) + torch.mm(z_tilde, self.W_gz_tilde) + torch.mm(h_tilde, self.W_gh_tilde) + self.b_g)
        r = torch.sigmoid(torch.mm(x, self.W_rx) + torch.mm(z, self.W_rz) + torch.mm(h, self.W_rh) + torch.mm(z_tilde, self.W_rz_tilde) + torch.mm(h_tilde, self.W_rh_tilde) + self.b_r)
        # output
        o_1 = torch.tanh(torch.mm(x, self.W_ux) + torch.mm(z_tilde, self.W_uz) + torch.mm(h_tilde, self.W_uh) + self.b_u)
        o_2 = torch.tanh(torch.mm(x, self.W_ux) + torch.mm(z, self.W_uz) + torch.mm(h_tilde, self.W_uh) + self.b_u)
        o_3 = torch.tanh(torch.mm(x, self.W_ux) + torch.mm(z_tilde, self.W_uz) + torch.mm(h, self.W_uh) + self.b_u)
        o_4 = torch.tanh(torch.mm(x, self.W_ux) + torch.mm(z, self.W_uz) + torch.mm(h, self.W_uh) + self.b_u)
        output = g * r * o_1 + (1 - g) * r * o_2 + g * (1 - r) * o_3 + (1 - g) * (1 - r) * o_4
        return output
