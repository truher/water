"""multi-label classification using toy dataset"""
import datetime
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

SCALE = 10

def make_realistic_data():
    """Return a dataframe of observations and a dataframe of loads, both full scale"""
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

def plot_frames(true_df, pred_df):
    fix, axs = plt.subplots(len(true_df.columns), sharex=True)
    for i, col in enumerate(true_df):
        axs[i].plot(true_df[col], label=col+' true')
        if pred_df is not None:
            axs[i].plot(pred_df[col], label=col+' predicted')
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

def make_model(classes):
    # make the model
    i = tf.keras.Input(shape=(None,1),
        name="input_layer")
    i2 = IL()

    conv = tf.keras.layers.Conv1D(filters=17, kernel_size=15, activation='relu', padding='same', dilation_rate = 4,
        name="conv_layer")
    #pool = tf.keras.layers.MaxPool1D(pool_size=13,
        #name="pool_layer")
    conv_2 = tf.keras.layers.Conv1D(filters=19, kernel_size=15, activation='relu', padding='same', dilation_rate = 16,
        name="conv_layer_2")
    #pool_2 = tf.keras.layers.MaxPool1D(pool_size=13,
        #name="pool_layer_2")
    conv_3 = tf.keras.layers.Conv1D(filters=23, kernel_size=15, activation='relu', padding='same', dilation_rate = 64,
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

    return m

def datagenerator(true_df):
    """Yields a set of N sequences of length M, chosen randomly from the whole sequence.
    true_df is full scale
    """
    batch_size = 10 # sequences
    sequence_length = 3600 # seconds!  want the window to see whole events
    window_size = batch_size * sequence_length
    while True:
        start = random.randint(0, len(true_df) - window_size)
        batch_df = true_df.loc[start:start + window_size - 1]
        x_batch = (batch_df['mains'].to_numpy() / SCALE).reshape(-1, sequence_length, 1)
        y_batch = batch_df.drop(columns='mains').to_numpy().reshape(-1, sequence_length, len(true_df.columns) - 1)
        yield(x_batch, {'category_output':y_batch, 'mains_output':x_batch})

def predict_and_evaluate(test_df, loads, model):
    """test_df is full scale"""

    predictions = model.predict((test_df['mains'].to_numpy() / SCALE).reshape(1, -1, 1)) # all at once

    # categorical prediction
    y_pred = predictions[0]
    print("y_pred shape:", y_pred.shape)
    y_pred = np.around(y_pred.reshape(-1, len(test_df.columns) - 1), 2)
    y_true = test_df.drop(columns='mains').to_numpy()

    print("raw category result on training set:")
    raw_cat_result = np.concatenate((y_true, y_pred), axis=1)
    np.savetxt('raw_cat_result.tsv', raw_cat_result, fmt='%.1f', delimiter='\t')
    y_pred = np.around(y_pred).astype(int)

    # predicted loads (last layer weights)
    predicted_loads = (model.layers[-1].get_weights()[0] * SCALE).reshape(-1)
    print("predicted load comparison:")
    print(np.column_stack((np.around(loads.transpose(),3), np.around(predicted_loads,3))))
    print("predicted load mse:")
    print(sklearn.metrics.mean_squared_error(loads.transpose(), predicted_loads))

    print("category accuracy:")
    print(sklearn.metrics.accuracy_score(y_true, y_pred))

    print("category precision (predicted events that were labeled):")
    print(sklearn.metrics.precision_score(y_true, y_pred, average=None))

    print("category recall (labeled events that were predicted):")
    print(sklearn.metrics.recall_score(y_true, y_pred, average=None))

    # mains prediction (full scale)
    x_pred = predictions[1] * SCALE

    print("mains mse:")
    print(sklearn.metrics.mean_squared_error(test_df['mains'].to_numpy(), x_pred.reshape(-1)))

    print("confusion matrices")
    print(sklearn.metrics.multilabel_confusion_matrix(y_true, y_pred))

    pred_df = pd.DataFrame(y_pred, columns=test_df.columns[:-1])
    pred_df['mains'] = x_pred.reshape(-1)

    plot_frames(test_df, pred_df)

def train_model(model, gen, vgen):
    print("train classifier ...")
    losses = { "category_output": "binary_crossentropy", "mains_output": "mean_squared_error" }
    loss_weights = { "category_output": 1.0, "mains_output": 0.0 }
    model.compile(loss=losses, loss_weights=loss_weights, optimizer='adam')
    tb = tf.keras.callbacks.TensorBoard(log_dir="tensorboard_log/classifier", histogram_freq=1)
    model.fit(x=gen, epochs=800, verbose=1, callbacks=[tb], validation_data=vgen, steps_per_epoch=7, validation_steps=1)
    for l in model.layers[:-1]:
        l.trainable = False
    loss_weights = { "category_output": 0.0, "mains_output": 1.0 }
    model.compile(loss=losses, loss_weights=loss_weights, optimizer='adam')
    tb = tf.keras.callbacks.TensorBoard(log_dir="tensorboard_log/mains", histogram_freq=1)
    model.fit(x=gen, epochs=300, verbose=1, callbacks=[tb], validation_data=vgen, steps_per_epoch=7, validation_steps=1)
    print("done training!")

def sec2str(x):
    return str(datetime.timedelta(seconds=int(x)))

def make_events(df):
    """ df is full scale """
    for col in true_df.columns:
        if col == 'mains':
            continue
        yyy = true_df[col].astype(bool).reset_index()
        yyy['g'] = yyy[col].diff().cumsum().fillna(0)
        events = yyy[yyy[col]==True].groupby(['g'])['index'].agg(['first','last'])
        print("===========")
        print(col)
        print(events.apply(np.vectorize(sec2str)))

with tf.device('/cpu:0'):
    true_df, loads = make_realistic_data()
    make_events(true_df)

    gen = datagenerator(true_df)


    val_df, _ = make_realistic_data()
    vgen = datagenerator(val_df)

    test_df, _ = make_realistic_data()

    model = make_model(len(true_df.columns) - 1)
    print(model.summary())
    train_model(model, gen, vgen)
    predict_and_evaluate(test_df, loads, model)
