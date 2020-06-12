import keras.models as mod
import keras.layers as lyr
import keras.optimizers as opt
import keras.metrics as met
import numpy as np
import keras.callbacks as call
import tensorflow as tf
import keras.losses as losses
import shared.definitions.paths as paths
import os
from os import path
from shared.generators.ennvironment_sequence import EnvironmentSequence
import gym

"""
Model Definition
"""
version = 0
num_datapoints = None
steps_per_epoch = None

# FIXME - add model used for agent in question


def get_Q_a(tensors):
    import tensorflow as tf  # FIXME - janky, need a better solution
    return tf.gather_nd(tensors[0], tensors[1], batch_dims=1)


input_size = 4
output_size = 2  # Same as number of actions
state_input = lyr.Input((input_size, ))
action_input = lyr.Input((1, ), dtype='int32')
intermediate1 = lyr.Dense(100, activation='relu')(state_input)
value_out = lyr.Dense(output_size, activation='relu')(intermediate1)
# Note we use the action to index for the value used for the loss. It is NOT used as a feature for training,
action_out = lyr.Lambda(get_Q_a,
                        lambda input_shape: (1, ))([value_out, action_input])
model = mod.Model(inputs=[state_input, action_input], outputs=[value_out, action_out])



"""
Optimizer, Loss, & Metrics

Using zero built in decay and relying exclusively on the heuristic
used in the original paper.
"""
optimizer = opt.Adam(0.001)  # FIXME - do we want to change our optimizer?


model.compile(optimizer=optimizer,
              loss=[None, losses.mean_squared_error],
              metrics=[met.mean_squared_error],
              loss_weights=[0, 1]
              )

"""
Epochs & Batch Sizes
"""
# We fixed the number of iterations that constitute an epoch in the generator,
# Note that we do not need a validation generator hence not val batch size.
num_epochs = 90
grad_update_frequency = 16
train_batch_size = 32
target_update_frequency = 10000
action_repeat = 4
gamma = 0.99
epoch_length = 10000
replay_buffer_size = 1000

"""
Callback Params
"""

# FIXME - Need to use learning rate scheduler used in different papers?
scheduler = None

# FIXME - Create callback to calculate agent performance?

log_dir = paths.agents + 'dqn/v{:02d}/logs'.format(version)
checkpoint_dir = paths.agents + 'dqn/v{:02d}/checkpoints'.format(version)

if not path.isdir(checkpoint_dir):
    os.mkdir(checkpoint_dir)

if not path.isdir(log_dir):
    os.mkdir(log_dir)

# Experiment directory format is {model}/{version}/{filetype}
tensorboard_params = {'log_dir': log_dir,
                      'batch_size': train_batch_size,
                      'write_grads': True,
                      'write_images': True}

checkpointer_params = {'filepath': checkpoint_dir + '/weights.{epoch:02d}-{val_loss:.2f}.hdf5',
                       'verbose': 1}

"""
Loading Params
"""

# If model_file is not None and checkpoint_dir is not None then loading happens, else not
loading_params = {'checkpoint_dir': None,
                  'model_file': None,
                  'epoch_start': None}

train_gen = EnvironmentSequence(model,
                                source_type='value',
                                environment=gym.make("CartPole-v0"),
                                batch_size=train_batch_size,
                                grad_update_frequency=grad_update_frequency,
                                target_update_frequency=target_update_frequency,
                                action_repeat=action_repeat,
                                gamma=gamma,
                                epoch_length=epoch_length,
                                replay_buffer_size=replay_buffer_size)


if __name__ == '__main__':
    print(model.summary())
    print(gym.make('CartPole-v0').reset())
    for epoch in range(epoch_length):
        print("Generator Test: Epoch {}".format(epoch))
        train_gen[epoch]