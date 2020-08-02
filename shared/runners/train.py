# Set memory restrictions to allow some room for our monitor to render :)
from keras import backend as K
import tensorflow as tf
config = tf.ConfigProto()
config.gpu_options.allow_growth = True
config.gpu_options.per_process_gpu_memory_fraction = 0.95
session = tf.Session(config=config)
K.set_session(session=session)

import keras.callbacks as call
from shared.custom_callbacks.evaluate_agent import EvaluateAgentCallback
import gc
print("Assemble & Compile Model")
import sys
import importlib
agent_path = sys.argv[1]
print(agent_path)
rundef = importlib.import_module(agent_path)  # Run definition

"""Model Loading (If Applicable)"""
checkpoint_dir = rundef.loading_params['checkpoint_dir']
model_file = rundef.loading_params['model_file']
epoch_start = rundef.loading_params['epoch_start']

if model_file is not None and checkpoint_dir is not None:
    print("Loading Model")
    rundef.model.load_weights(checkpoint_dir + model_file)
    epochs = rundef.num_epochs - epoch_start
else:
    epoch_start = 0
    epochs = rundef.num_epochs

"""Callbacks"""
tensorboard = call.TensorBoard(**rundef.tensorboard_params)
checkpointer = call.ModelCheckpoint(**rundef.checkpointer_params)
evaluate_agent = EvaluateAgentCallback(**{'tb_callback': tensorboard, **rundef.evaluator_params})

# Added to address OOM Error - not sure if needed anymore
# See: https://github.com/keras-team/keras/issues/3675
garbage_collection = call.LambdaCallback(on_epoch_end=lambda epoch, logs: gc.collect())

""" Model train code """
print("Begin Training Model")
rundef.model.fit_generator(rundef.train_gen,
                           epochs=rundef.num_epochs,
                           steps_per_epoch=rundef.steps_per_epoch,
                           verbose=1,  # 0 in notebook, verbose doesn't slow down training, we checked
                           callbacks=[tensorboard,
                                      evaluate_agent,
                                      checkpointer,
                                      garbage_collection,
                                      ],
                           shuffle=False,  # We don't want to shuffle indices in DQN since order matters
                           use_multiprocessing=False,  # Actually significantly faster when this is false.
                           workers=1,  # Since the agent is stateful synchronicity matters, so no more than 1 worker
                           max_queue_size=4,  # Optimal: A larger queue seems to not make much of a difference
                           initial_epoch=epoch_start
                          )
