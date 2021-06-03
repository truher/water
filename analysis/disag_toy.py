"""multi-label classification using toy dataset"""
import matplotlib.pyplot as plt # type: ignore
import pandas as pd # type: ignore
import numpy as np
import tensorflow as tf # type: ignore
import sklearn.metrics # type: ignore

mains = np.zeros(900)
mains[100:200] = 1 # class0
mains[300:400] = 2 # class1
mains[500:600] = 3 # class0+1
mains[700:800] = 3 # unlabeled but should be predicted as class0+1
mains = mains + np.random.normal(0,0.1,900)
mains = np.maximum(mains, 0)  # don't try to predict negative values

class0 = -1 * np.ones(900) # -1 means "no label" for one-hot
class0[100:200] = 0
class0[500:600] = 0
class1 = -1 * np.ones(900)
class1[300:400] = 1
class1[500:600] = 1

df = pd.DataFrame()
df['mains'] = mains
df['class0'] = class0
df['class1'] = class1
print(df[100:200:10])

plt.plot(df['mains'])
plt.plot(df['class0'])
plt.plot(df['class1'])
plt.show()

x = df[['mains']].values
y = np.logical_or(tf.one_hot(df['class0'], 2, on_value=1, off_value=0),
                  tf.one_hot(df['class1'], 2, on_value=1, off_value=0)).astype(np.float32)

i = tf.keras.Input(shape=(1,), name="input_layer")
c = tf.keras.layers.Dense(units=20, activation='relu', name="middle_layer")
o = tf.keras.layers.Dense(units=2,
    activation='hard_sigmoid', # "hard" tends towards exactly zero or one, which is what i want
    name="category_output")
# predict the input from *just* the category output.
mo = tf.keras.layers.Dense(units=1,
    activation='relu', # output is never negative
    kernel_constraint=tf.keras.constraints.NonNeg(), # weights are never negative
    # no-category-activated should be no-output so force zero bias
    # low rate means it can learn for awhile
    bias_constraint=tf.keras.constraints.MinMaxNorm(min_value=0.0, max_value=0.0, rate=0.01),
    name="mains_output")
category_branch = o(c(i))
mains_branch = mo(category_branch)
outputs = [category_branch, mains_branch]
m = tf.keras.Model(inputs=i, outputs=outputs)
print(m.summary())
tf.keras.utils.plot_model(m, 'model.png', show_shapes=True)
losses = {
    "category_output": "cosine_similarity", # missing labels == zero penalty
    "mains_output": "mean_squared_error"
}
loss_weights = {
    "category_output": 1.0,
    "mains_output": 1.0
}
m.compile(loss=losses, loss_weights=loss_weights, optimizer='adam')
print("training ...")
tb = tf.keras.callbacks.TensorBoard(log_dir="tensorboard_log", histogram_freq=1)
# note x in both the "in" and "out" positions here
m.fit(x, [y,x], epochs=1500, verbose=0, callbacks=[tb])
print("done training!")

y1 = m.predict(x)
print("raw prediction")
c1 = y1[0] # categorical prediction
m1 = y1[1] # mains prediction

print("raw category result on training set:")
print(np.concatenate((y,np.around(c1,2)),axis=1)[::10])

print("mains result on training set:")
print(np.concatenate((x,m1),axis=1)[::10])

print("center weights:")
print(c.get_weights())
print("category output weights:")
print(o.get_weights())
print("mains output weights:")
print(mo.get_weights())
mains_weight_bias = mo.get_weights()[1][0]
print("mains weight bias:")
print(mains_weight_bias)

print("category accuracy:")
print(sklearn.metrics.accuracy_score(y,np.around(c1)))
print("category precision (predicted events that were labeled):")
print(sklearn.metrics.precision_score(y,np.around(c1),average=None))
print("category recall (labeled events that were predicted):")
print(sklearn.metrics.recall_score(y,np.around(c1),average=None))
print("mains mse:")
print(sklearn.metrics.mean_squared_error(x,m1))

plt.plot(mains)
plt.plot(m1)
plt.title("mains prediction")
plt.show()
