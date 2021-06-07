"""multi-label classification using toy dataset"""
import isodate
import matplotlib.pyplot as plt # type: ignore
import numpy as np
import pandas as pd # type: ignore
import random
import tensorflow as tf # type: ignore
import sklearn.metrics # type: ignore

print("available tensorflow devices:", tf.config.list_physical_devices())
print("eager:", tf.executing_eagerly())

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

class IL(tf.keras.layers.Layer):
    def call(self, inputs, *args, **kwargs):
        #tf.print("================================ CALL ================================")
        #tf.print(type(inputs))
        #tf.print("input len:", len(inputs)) # 111
        #tf.print("input[0] len", len(inputs[0])) # also 111
        #tf.print("input[0][0] len", len(inputs[0][0])) # 1
        return super().call(inputs, *args, **kwargs)

with tf.device('/cpu:0'):

    # make some data
    df, loads = make_realistic_data()
    #plot_frames(df, None)
    classes = len(df.columns) - 1

    # make the model
    i = tf.keras.Input(shape=(None,1),
        name="input_layer")
    i2 = IL()

    conv = tf.keras.layers.Conv1D(filters=17, kernel_size=5, activation='relu', padding='same',
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

    # model is done!

    x = df['mains'].values
    print("x len", len(x))
    y = df.drop(columns='mains').values
    print("y len", len(y))

    samples = len(df.index)

    batch_size = 10
    #sequence_length = 111
    sequence_length = 3600 # seconds!  want the window to see whole events
    all_samples = (batch_size * sequence_length) * (len(x) // (batch_size * sequence_length))
    x_sequences = x[0:all_samples].reshape(-1, sequence_length, 1)
    y_sequences = y[0:all_samples].reshape(-1, sequence_length, classes)
    # this is the original dataframe again :-) TODO: use it
    sequences = np.concatenate((x_sequences, y_sequences), axis=2)

    def datagenerator():
        while True:
            np.random.shuffle(sequences) # TODO: overlapping sequences
            batches = sequences.reshape(-1, batch_size, sequence_length, classes + 1)
            for n in range(len(batches)): # one epoch
                x_batch = batches[n][...,np.newaxis,0]
                y_batch = batches[n][...,1:]
                yield(x_batch, {'category_output':y_batch, 'mains_output':x_batch})

    print(m.summary())

    gen = datagenerator()
    vgen = datagenerator()
 
    tb = tf.keras.callbacks.TensorBoard(log_dir="tensorboard_log/classifier", histogram_freq=1)

    print("train classifier ...")
    m.fit(x=gen, epochs=2000, verbose=1, callbacks=[tb], 
          validation_data=vgen, steps_per_epoch=7, validation_steps=1)

    i.trainable = False
    conv.trainable = False
    conv_2.trainable = False
    conv_3.trainable = False
    c.trainable = False
    o.trainable = False
    loss_weights = { "category_output": 0.0, "mains_output": 1.0 }
    m.compile(loss=losses, loss_weights=loss_weights, optimizer='adam')
    print(m.summary())
    tb = tf.keras.callbacks.TensorBoard(log_dir="tensorboard_log/mains", histogram_freq=1)

    print("train mains output ...")
    m.fit(x=datagenerator(), epochs=2000, verbose=1, callbacks=[tb],
          validation_data=vgen, steps_per_epoch=7, validation_steps=1)
    print("done training!")

    #y1 = m.predict(xtrain)
    y1 = m.predict(x_sequences)

    c1 = y1[0] # categorical prediction
    shaped_c1 = np.around(c1.reshape(-1,classes), 2)
    shaped_training = y_sequences.reshape(-1,classes).astype(int)

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
    print(sklearn.metrics.mean_squared_error(x_sequences.reshape(-1), m1.reshape(-1)))

    print("confusion matrices")
    print(sklearn.metrics.multilabel_confusion_matrix(shaped_training, shaped_c1))

    tdf = pd.DataFrame(shaped_training, columns=df.columns[:-1])
    tdf['mains'] = x_sequences.reshape(-1)
    c1df = pd.DataFrame(shaped_c1, columns=df.columns[:-1])
    c1df['mains'] = m1.reshape(-1)

    plot_frames(tdf, c1df)
