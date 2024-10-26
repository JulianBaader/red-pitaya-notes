import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

LEN = 4096
x = np.arange(LEN)


modes = ['comb', 'single', 'gauss', 'constant']

for mode in modes:
    s = np.zeros(LEN, dtype=np.uint32)
    if mode == 'comb':
        for i in range(16):
            s[(i + 1) * 250 - 1] = 1

    elif mode == 'single':
        s[2047] = 1

    elif mode == 'gauss':
        s = norm.pdf(x, LEN / 2, 100)
        s = s / np.max(s) * 1000
        s = s.astype(np.uint32)

    elif mode == 'constant':
        s = np.ones(LEN, dtype=np.uint32) * 1000

    plt.plot(s)
    plt.title(mode)
    plt.show()
    np.save(mode + '.npy', s)
