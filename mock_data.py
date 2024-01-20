import numpy as np


img = np.random.rand(360, 360, 3)
a = np.array([1, "hello", "bye"], dtype=object)
b = np.array(5*[[1, 2, 3], [3, 2, 1], img, 1], dtype=object)
x = np.arange(10)
y = np.sin(x)
np.savez_compressed("./npz/file-1.npz", a=a, b=b, x=x, y=y, img=img)

file = np.load("./npz/file-1.npz", allow_pickle=True)
print(file['a'])
print(file['b'])