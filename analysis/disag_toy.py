"""multi-label classification using toy dataset"""
import matplotlib.pyplot as plt # type: ignore
import pandas as pd # type: ignore
import numpy as np
import random
import tensorflow as tf # type: ignore
import sklearn.metrics # type: ignore

print(tf.config.list_physical_devices())

def make_data():
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

    return df

def make_random_data(classes, events, samples):
    df = pd.DataFrame()
    loads = []
    for i in range(classes):
        loads.append(random.uniform(0,10))
        df['class'+str(i)] = np.zeros(samples)
    print(loads)
    for i in range(events):
        start = random.randrange(0, samples)
        end = min(start + random.randrange(20, 100), samples)
        load = random.randrange(0, classes)
        df['class'+str(load)][start:end] = 1
        print(f"start {start} end {end} load {load}")
    df['mains'] = df.dot(loads)
    df['mains'] = df['mains'] + np.random.normal(0, 0.1, samples)
    df['mains'] = np.maximum(df['mains'], 0)  # negative noise is nonphysical, don't try to predict it
    return df, loads

def make_realistic_data():
    samples = 86400

    df = pd.DataFrame()
    df['sprinkler'] = np.zeros(samples)
    df['front'] = np.zeros(samples)
    df['shower'] = np.zeros(samples)
    df['drip'] = np.zeros(samples)
    df['toilet'] = np.zeros(samples)
    df['faucet'] = np.zeros(samples)

    # this is modeled after jun 2
    df['shower'][27420:28140] = 1    #  7:37-7:49
    df['shower'][33900:34320] = 1    #  9:25-9:32
    df['toilet'][33720:33755] = 1    #  9:22 35s
    df['toilet'][33780:33815] = 1    #  9:23 35s
    df['toilet'][33840:33875] = 1    #  9:24 35s
    df['front'][36180:37260] = 1     # 10:03-10:21
    df['drip'][39600:43200] = 1      # 11:00-12:00
    df['toilet'][58140:58175] = 1    # 16:09 35s
    df['toilet'][58200:58235] = 1    # 16:10 35s
    df['toilet'][80520:80555] = 1    # 22:22 35s
    df['faucet'][80580:80585] = 1    # 22:23 5s
    df['faucet'][80760:80775] = 1    # 22:26 15s
    df['toilet'][81300:81335] = 1    # 22:35 35s
    df['faucet'][81420:81435] = 1    # 22:37 15s
    df['sprinkler'][81900:84600] = 1 # 22:30-23:30

    loads = pd.DataFrame()
    loads['sprinkler'] = [7.1]
    loads['front'] = [4.4]
    loads['shower'] = [2.75]
    loads['drip'] = [0.9]
    loads['toilet'] = [3.05]
    loads['faucet'] = [1.0]
    print(loads)
    df['mains'] = df.dot(loads.transpose())
    df['mains'] = df['mains'] + np.random.normal(0, 0.05, samples)
    df['mains'] = np.maximum(df['mains'], 0)  # negative noise is nonphysical, don't try to predict it
    return df, loads

kernel_size = 5 # please be odd
#batch_size = 111
batch_size = 111
#classes = 8
#events = 20
#samples = 2000
#df, loads = make_random_data(classes, events, samples)
#df = make_data()

df, loads = make_realistic_data()
classes = len(df.columns) - 1
samples = len(df.index)

reshape_samples = (batch_size * kernel_size) * (samples // (batch_size * kernel_size))
print(reshape_samples)

print("df")
print(df[0:10])

for col in df:
    plt.plot(df[col], label=col)
plt.legend()
plt.show()


#x = df[['mains']].values
x = df.iloc[:,-1].values

#print("mains input")
#print(x[0:10])

#y = df[['class0','class1']].values
y = df.iloc[:,:-1].values

#print("category labels")
#print(y[0:10])

with tf.device('/cpu:0'):
    # batches of 11 timesteps
    # make this MUCH wider, try 111
    i = tf.keras.Input(shape=(batch_size,1),
        name="input_layer")

    # number of filters, 17, is arbitrary, just different from all the other numbers
    # kernel is window width
    # 7 windows of 5 fit in a batch of 11
    conv = tf.keras.layers.Conv1D(filters=17, kernel_size=kernel_size, activation='relu',
        name="conv_layer")
    #pool = tf.keras.layers.MaxPool1D(pool_size=13,
        #name="pool_layer")
    conv_2 = tf.keras.layers.Conv1D(filters=19, kernel_size=5, activation='relu',
        name="conv_layer_2")
    #pool_2 = tf.keras.layers.MaxPool1D(pool_size=13,
        #name="pool_layer_2")
    conv_3 = tf.keras.layers.Conv1D(filters=23, kernel_size=5, activation='relu',
        name="conv_layer_3")

    c = tf.keras.layers.Dense(units=classes*10, activation='relu',
        name="middle_layer")

    #o = tf.keras.layers.Dense(units=2,
    o = tf.keras.layers.Dense(units=classes,
        #activation='hard_sigmoid', # learns faster
        activation='sigmoid',
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

    #conv_branch = conv_3(pool_2(conv_2(pool(conv(i)))))
    conv_branch = conv_3(conv_2(conv(i)))
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
    #xtrain = x[0:891].reshape(-1,11,1)
    xtrain = x[0:reshape_samples].reshape(-1,batch_size,1)
    print("xtrain")
    print(xtrain.shape)
    #print(xtrain)

    # each span of 5 predicts the features at the center sample
    #yctrain = y[0:891].reshape(-1,11,2)[:,2:-2]
    #yctrain = y[0:891].reshape(-1,11,classes)[:,2:-2]
    conv_layers = 3
    yctrain = y[0:reshape_samples].reshape(-1,batch_size,classes)[:, conv_layers * (kernel_size//2):-(conv_layers * (kernel_size//2))]
    shaped_training = yctrain.reshape(-1,classes).astype(int)
    #ymtrain = x[0:891].reshape(-1,11,1)[:,2:-2]
    ymtrain = x[0:reshape_samples].reshape(-1,batch_size,1)[:, conv_layers * (kernel_size//2):-(conv_layers * (kernel_size//2))]
    print("yctrain")
    print(yctrain.shape)
    #print(yctrain)
    print("ymtrain")
    print(ymtrain.shape)
    #print(ymtrain)


    print(m.summary())
    tb = tf.keras.callbacks.TensorBoard(log_dir="tensorboard_log/classifier", histogram_freq=1)
    # note x in both the "in" and "out" positions here
    m.fit(xtrain, [yctrain, ymtrain], batch_size=batch_size, epochs=5000, verbose=0, callbacks=[tb])


    #y1 = m.predict(xtrain)
    #c1 = y1[0] # categorical prediction
    #print("raw category result on training set:")
    #print(np.concatenate((yctrain.reshape(-1,2), c1.reshape(-1,2)),axis=1)[::10])
    #print(np.concatenate((shaped_training, c1.reshape(-1,classes)),axis=1)[::10])

    print("train mains output ...")

    i.trainable = False
    conv.trainable = False
    conv_2.trainable = False
    conv_3.trainable = False
    c.trainable = False
    o.trainable = False
    loss_weights = { "category_output": 0.0, "mains_output": 1.0 }
    m.compile(loss=losses, loss_weights=loss_weights, optimizer='adam')

    print(m.summary()) # should show only 3 trainable params, but since bias is constrained it's actually only two
    tb = tf.keras.callbacks.TensorBoard(log_dir="tensorboard_log/mains", histogram_freq=1)
    m.fit(xtrain, [yctrain, ymtrain], batch_size=batch_size, epochs=1500, verbose=0, callbacks=[tb])

    print("done training!")

    y1 = m.predict(xtrain)
    c1 = y1[0] # categorical prediction
    #shaped_c1 = np.around(c1.reshape(-1,classes)).astype(int)
    shaped_c1 = np.around(c1.reshape(-1,classes), 2)

    print("raw category result on training set:")
    #print(np.concatenate((yctrain.reshape(-1,2), c1.reshape(-1,2)),axis=1)[::10])
    raw_cat_result = np.concatenate((shaped_training, shaped_c1), axis=1)
    print(raw_cat_result[::10])
    np.savetxt('raw_cat_result.tsv', raw_cat_result, fmt='%.1f', delimiter='\t')
    # classification wants indicator
    shaped_c1 = np.around(shaped_c1).astype(int)

    m1 = y1[1] # mains prediction
    print("mains result on training set:")
    print(np.concatenate( ( np.around(ymtrain.reshape(-1,1),2), np.around(m1.reshape(-1,1),2)), axis=1)[::10])

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

    predicted_loads = mo.get_weights()[0].reshape(-1)
    print("configured loads")
    print(loads.transpose())
    print("predicted loads:")
    print(predicted_loads)
    print("predicted load comparison:")
    print(np.column_stack((np.around(loads.transpose(),3), np.around(predicted_loads,3))))
    print("predicted load mse:")
    print(sklearn.metrics.mean_squared_error(loads.transpose(),predicted_loads))

    print("category accuracy:")
    #print(sklearn.metrics.accuracy_score(yctrain.reshape(-1,2), np.around(c1.reshape(-1,2))))
    print(sklearn.metrics.accuracy_score(shaped_training, shaped_c1))
    print("category precision (predicted events that were labeled):")
    #print(sklearn.metrics.precision_score(yctrain.reshape(-1,2), np.around(c1.reshape(-1,2)),average=None))
    print(sklearn.metrics.precision_score(shaped_training, shaped_c1, average=None))
    print("category recall (labeled events that were predicted):")
    #print(sklearn.metrics.recall_score(yctrain.reshape(-1,2), np.around(c1.reshape(-1,2)),average=None))
    print(sklearn.metrics.recall_score(shaped_training, shaped_c1, average=None))
    print("mains mse:")
    #print(sklearn.metrics.mean_squared_error(ymtrain.reshape(-1,1), m1.reshape(-1,1)))
    print(sklearn.metrics.mean_squared_error(ymtrain.reshape(-1), m1.reshape(-1)))

    print("confusion matrices")
    print(sklearn.metrics.multilabel_confusion_matrix(shaped_training, shaped_c1))

    tdf = pd.DataFrame(shaped_training, columns=df.columns[:-1])
    c1df = pd.DataFrame(shaped_c1, columns=df.columns[:-1])

    #c1df.to_csv('category_predictions.csv')

    c1_main = c1df.dot(loads.transpose())

    fix,axs = plt.subplots(classes+1, sharex=True)

    #plt.plot(ymtrain.reshape(-1), label='mains observed')
    #plt.plot(m1.reshape(-1), label='mains predicted')
    axs[0].plot(ymtrain.reshape(-1), label='mains observed')
    axs[0].plot(c1_main, label='mains predicted using known loads')
    axs[0].plot(m1.reshape(-1), label='mains predicted using predicted loads')
    axs[0].legend(loc='upper left')
    for i,col in enumerate(c1df):
        axs[i+1].plot(tdf[col], label=col+' observed')
        axs[i+1].plot(c1df[col], label=col+' predicted')
        axs[i+1].legend(loc='upper left')
    #plt.legend()
    plt.show()
