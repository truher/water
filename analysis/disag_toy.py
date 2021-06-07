"""multi-label classification using toy dataset"""
import isodate
import matplotlib.pyplot as plt # type: ignore
import numpy as np
import pandas as pd # type: ignore
import random
import tensorflow as tf # type: ignore
import sklearn.metrics # type: ignore

print("available tensorflow devices:", tf.config.list_physical_devices())
print("eager?", tf.executing_eagerly())

def flow(df, name, interval):
    start_str, duration_str = interval.split('/')
    start = isodate.parse_time(start_str)
    duration = isodate.parse_duration(duration_str)
    start_sec = int(3600 * start.hour + 60 * start.minute + start.second)
    duration_sec = int(duration.total_seconds())
    df[name][start_sec:start_sec + duration_sec] = 1

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
    for h in range(7,10):
        m = random.randint(20,40)
        d = random.randint(5,15)
        flow(df, 'shower', f'{h:02d}:{m:02d}/PT{d:d}M')

    for h in range(7,22,2):
        for e in range(random.randint(0,3)):
            m = random.randint(0,50) + 2 * e
            flow(df, 'toilet', f'{h:02d}:{m:02d}/PT35S')
    flow(df, 'front', '10:03/PT18M')
    flow(df, 'drip', '11:00/PT1H')
    for e in range(random.randint(10,30)):
        h = random.randint(7,22)
        m = random.randint(0,59)
        d = random.randint(5,100)
        flow(df, 'faucet', f'{h:02d}:{m:02d}/PT{d:d}S')
    
    flow(df, 'sprinkler', '22:30/PT1H')

    loads = pd.DataFrame()
    loads['sprinkler'] = [7.1]
    loads['front'] = [4.4]
    loads['shower'] = [2.75]
    loads['drip'] = [0.9]
    loads['toilet'] = [3.05]
    loads['faucet'] = [1.0]
    df['mains'] = df.dot(loads.transpose())
    df['mains'] = df['mains'] + np.random.normal(0, 0.05, samples)
    df['mains'] = np.maximum(df['mains'], 0)  # negative noise is nonphysical, don't try to predict it
    return df, loads

def plot_frames(tdf, c1df):
    fix, axs = plt.subplots(len(tdf.columns), sharex=True)
    for i, col in enumerate(tdf):
        axs[i].plot(tdf[col], label=col+' observed')
        if c1df is not None:
            axs[i].plot(c1df[col], label=col+' predicted')
        axs[i].legend(loc='upper left')
    plt.show()

kernel_size = 5 # please be odd
# the expectation is a 3 tensor: (batches, sequences, features)
batch_size = 111 # so this is actually the sequence length not the batch.  :-(

df, loads = make_realistic_data()
classes = len(df.columns) - 1
samples = len(df.index)

reshape_samples = (batch_size * kernel_size) * (samples // (batch_size * kernel_size))
print(reshape_samples)

plot_frames(df, None)

x = df['mains'].values
print("x len", len(x))

y = df.drop(columns='mains').values
print("y len", len(y))

class IL(tf.keras.layers.Layer):
    def call(self, inputs, *args, **kwargs):
        #tf.print("================================ CALL ================================")
        #tf.print(type(inputs))
        #tf.print("input len:", len(inputs)) # 111
        #tf.print("input[0] len", len(inputs[0])) # also 111
        #tf.print("input[0][0] len", len(inputs[0][0])) # 1
        return super().call(inputs, *args, **kwargs)

with tf.device('/cpu:0'):
    #i = tf.keras.Input(shape=(batch_size,1), # do i need to specify this?
    i = tf.keras.Input(shape=(None,1), # do i need to specify this?
        name="input_layer")
    i2 = IL()

    # number of filters, 17, is arbitrary, just different from all the other numbers
    # kernel is window width
    # 7 windows of 5 fit in a batch of 11
    conv = tf.keras.layers.Conv1D(filters=17, kernel_size=kernel_size, activation='relu', padding='same',
        name="conv_layer")
    #pool = tf.keras.layers.MaxPool1D(pool_size=13,
        #name="pool_layer")
    conv_2 = tf.keras.layers.Conv1D(filters=19, kernel_size=5, activation='relu', padding='same',
        name="conv_layer_2")
    #pool_2 = tf.keras.layers.MaxPool1D(pool_size=13,
        #name="pool_layer_2")
    conv_3 = tf.keras.layers.Conv1D(filters=23, kernel_size=5, activation='relu', padding='same',
        name="conv_layer_3")

    c = tf.keras.layers.Dense(units=classes*10, activation='relu',
        name="middle_layer")

    o = tf.keras.layers.Dense(units=classes,
        activation='sigmoid',
        name="category_output")

    # predict the input from *just* the category output.
    mo = tf.keras.layers.Dense(units=1,
        activation='relu', # output is never negative
        kernel_constraint=tf.keras.constraints.NonNeg(), # weights are never negative
        kernel_initializer=tf.keras.initializers.Ones(),
        # no-category-activated should be no-output so force zero bias (don't learn the noise)
        bias_constraint=tf.keras.constraints.MinMaxNorm(min_value=0.0, max_value=0.0, rate=1.0),
        name="mains_output")

    #conv_branch = conv_3(pool_2(conv_2(pool(conv(i)))))
    conv_branch = conv_3(conv_2(conv(i2(i))))
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

    xtrain = x[0:reshape_samples].reshape(-1,batch_size,1)
    print("xtrain")
    print(xtrain.shape)
    print(type(xtrain))
    print(list(xtrain))
    #np.savetxt('xtrain.tsv', xtrain, fmt='%f', delimiter='\t')

    yctrain = y[0:reshape_samples].reshape(-1,batch_size,classes)
    shaped_training = yctrain.reshape(-1,classes).astype(int)
    ymtrain = x[0:reshape_samples].reshape(-1,batch_size,1)
    print("yctrain")
    print(yctrain.shape)
    print("ymtrain")
    print(ymtrain.shape)

    def datagenerator():
        real_batch_size = 111
        sequence_length = 111
        n = 0
        while True:
            #n = random.randint(0, len(x)-(real_batch_size*sequence_length))
            #x_batch = x[n:n+real_batch_size].reshape(-1, batch_size, 1)
            x_batch = x[n:n+(real_batch_size*sequence_length)].reshape(-1, sequence_length, 1)
            #tf.print(x_batch)
            y_batch = y[n:n+(real_batch_size*sequence_length)].reshape(-1, sequence_length, classes)
            #tf.print(y_batch)
            n += real_batch_size * sequence_length
            if n > len(x) - (real_batch_size * sequence_length):
                n = 0
            yield(x_batch, {'category_output':y_batch, 'mains_output':x_batch})

    print(m.summary())

    class CC(tf.keras.callbacks.Callback):
        def on_epoch_begin(self, epoch, logs=None):
            keys = list(logs.keys())
            #print(self.model.layers)
            #print("Start epoch {} of training; got log keys: {}".format(epoch, keys))
        def on_train_batch_begin(self, batch, logs):
            keys = list(logs.keys())
            #print("...Training: start of batch {}; got log keys: {}".format(batch, keys))

 
    tb = tf.keras.callbacks.TensorBoard(log_dir="tensorboard_log/classifier", histogram_freq=1)
    # note x in both the "in" and "out" positions here
    #m.fit(xtrain, [yctrain, ymtrain], batch_size=batch_size, epochs=5000, verbose=1, callbacks=[tb, CC()],
    #    validation_data=(xtrain, [yctrain, ymtrain])) # what does validation do?
    m.fit(datagenerator(), epochs=5000, verbose=1, callbacks=[tb, CC()], steps_per_epoch=7)

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

    #m.fit(xtrain, [yctrain, ymtrain], batch_size=batch_size, epochs=1500, verbose=0, callbacks=[tb],
    #    validation_data=(xtrain, [yctrain, ymtrain])) # what does validation do?
    m.fit(datagenerator(), epochs=5000, verbose=1, callbacks=[tb,CC()], steps_per_epoch=7)

    print("done training!")

    y1 = m.predict(xtrain)

    c1 = y1[0] # categorical prediction
    shaped_c1 = np.around(c1.reshape(-1,classes), 2)

    print("raw category result on training set:")
    raw_cat_result = np.concatenate((shaped_training, shaped_c1), axis=1)
    np.savetxt('raw_cat_result.tsv', raw_cat_result, fmt='%.1f', delimiter='\t')
    shaped_c1 = np.around(shaped_c1).astype(int)

    m1 = y1[1] # mains prediction
    print("mains result on training set:")

    predicted_loads = mo.get_weights()[0].reshape(-1)
    print("predicted load comparison:")
    print(np.column_stack((np.around(loads.transpose(),3), np.around(predicted_loads,3))))
    print("predicted load mse:")
    print(sklearn.metrics.mean_squared_error(loads.transpose(),predicted_loads))

    print("category accuracy:")
    print(sklearn.metrics.accuracy_score(shaped_training, shaped_c1))

    print("category precision (predicted events that were labeled):")
    print(sklearn.metrics.precision_score(shaped_training, shaped_c1, average=None))

    print("category recall (labeled events that were predicted):")
    print(sklearn.metrics.recall_score(shaped_training, shaped_c1, average=None))

    print("mains mse:")
    print(sklearn.metrics.mean_squared_error(ymtrain.reshape(-1), m1.reshape(-1)))

    print("confusion matrices")
    print(sklearn.metrics.multilabel_confusion_matrix(shaped_training, shaped_c1))


    tdf = pd.DataFrame(shaped_training, columns=df.columns[:-1])
    tdf['mains'] = ymtrain.reshape(-1)
    c1df = pd.DataFrame(shaped_c1, columns=df.columns[:-1])
    c1df['mains'] = m1.reshape(-1)

    plot_frames(tdf, c1df)

