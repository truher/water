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
mains = mains + np.random.normal(0,0.1,900)
mains = np.maximum(mains, 0)  # negative noise is nonphysical, don't try to predict it

class0 = np.zeros(900)
class0[100:200] = 1
class0[500:600] = 1
class1 = np.zeros(900)
class1[300:400] = 1
class1[500:600] = 1

df = pd.DataFrame()
df['mains'] = mains
df['class0'] = class0
df['class1'] = class1
print("df")
print(df[0:10])

plt.plot(df['mains'])
plt.plot(df['class0'])
plt.plot(df['class1'])
plt.show()

x = df[['mains']].values

print("mains input")
print(x[0:10])

y = df[['class0','class1']].values

print("category labels")
print(y[0:10])


# batches of 11 timesteps
i = tf.keras.Input(shape=(11,1),
    name="input_layer")

# number of filters, 17, is arbitrary, just different from all the other numbers
# kernel is window width
# 7 windows of 5 fit in a batch of 11
conv = tf.keras.layers.Conv1D(filters=17, kernel_size=5, activation='linear',
    name="conv_layer")

c = tf.keras.layers.Dense(units=20, activation='relu',
    name="middle_layer")

o = tf.keras.layers.Dense(units=2,
    activation='hard_sigmoid', # learns faster
    #activation='sigmoid',
    name="category_output")

# predict the input from *just* the category output.
mo = tf.keras.layers.Dense(units=1,
    activation='relu', # output is never negative
    kernel_constraint=tf.keras.constraints.NonNeg(), # weights are never negative
    kernel_initializer=tf.keras.initializers.Ones(),
    # no-category-activated should be no-output so force zero bias (don't learn the noise)
    # low rate means it can learn for awhile
    bias_constraint=tf.keras.constraints.MinMaxNorm(min_value=0.0, max_value=0.0, rate=1.0),
    name="mains_output")

conv_branch = conv(i)
internal_branch = c(conv_branch)
category_branch = o(internal_branch)
mains_branch = mo(category_branch)
outputs = [category_branch, mains_branch]

m = tf.keras.Model(inputs=i, outputs=outputs)

tf.keras.utils.plot_model(m, 'model.png', show_shapes=True)
losses = {
    "category_output": "binary_crossentropy",
    "mains_output": "mean_squared_error"
}
loss_weights = { "category_output": 1.0, "mains_output": 0.0 }
o.trainable = True
m.compile(loss=losses, loss_weights=loss_weights, optimizer='adam')

print("train classifier ...")

# batches of 11
xtrain = x[0:891].reshape(-1,11,1)
print("xtrain")
print(xtrain)

# each span of 5 predicts the features at the center sample
yctrain = y[0:891].reshape(-1,11,2)[:,2:-2]
ymtrain = x[0:891].reshape(-1,11,1)[:,2:-2]
print("yctrain")
print(yctrain)
print("ymtrain")
print(ymtrain)

tb = tf.keras.callbacks.TensorBoard(log_dir="tensorboard_log/classifier", histogram_freq=1)

# note x in both the "in" and "out" positions here
m.fit(xtrain, [yctrain, ymtrain], batch_size=11, epochs=1000, verbose=0, callbacks=[tb])

print(m.summary())

y1 = m.predict(xtrain)
c1 = y1[0] # categorical prediction

print("raw category result on training set:")
print(np.concatenate((yctrain.reshape(-1,2), c1.reshape(-1,2)),axis=1)[::10])

print("train mains output ...")

i.trainable = False
conv.trainable = False
c.trainable = False
o.trainable = False
loss_weights = { "category_output": 0.0, "mains_output": 1.0 }
m.compile(loss=losses, loss_weights=loss_weights, optimizer='adam')

print(m.summary()) # should show only 3 trainable params, but since bias is constrained it's actually only two
tb = tf.keras.callbacks.TensorBoard(log_dir="tensorboard_log/mains", histogram_freq=1)
m.fit(xtrain, [yctrain, ymtrain], batch_size=11, epochs=500, verbose=0, callbacks=[tb])

print("done training!")

y1 = m.predict(xtrain)
c1 = y1[0] # categorical prediction

print("raw category result on training set:")
print(np.concatenate((yctrain.reshape(-1,2), c1.reshape(-1,2)),axis=1)[::10])

m1 = y1[1] # mains prediction
print("mains result on training set:")
print(np.concatenate((ymtrain.reshape(-1,1), m1.reshape(-1,1)),axis=1)[::10])

#print("conv weights:")
#print(conv.get_weights())
#print("center weights:")
#print(c.get_weights())
#print("category output weights:")
#print(o.get_weights())
print("mains output weights:")
print(mo.get_weights())
mains_weight_bias = mo.get_weights()[1][0]
print("mains weight bias:")
print(mains_weight_bias)

print("category accuracy:")
print(sklearn.metrics.accuracy_score(yctrain.reshape(-1,2), np.around(c1.reshape(-1,2))))
print("category precision (predicted events that were labeled):")
print(sklearn.metrics.precision_score(yctrain.reshape(-1,2), np.around(c1.reshape(-1,2)),average=None))
print("category recall (labeled events that were predicted):")
print(sklearn.metrics.recall_score(yctrain.reshape(-1,2), np.around(c1.reshape(-1,2)),average=None))
print("mains mse:")
print(sklearn.metrics.mean_squared_error(ymtrain.reshape(-1,1), m1.reshape(-1,1)))

plt.plot(ymtrain.reshape(-1,1))
plt.plot(m1.reshape(-1,1))
plt.title("mains prediction")
plt.show()
