from models.basic.basic_model import BasicModel
from models.encoders.resnet_18 import RESNET18
from layers.convolution import conv2d_transpose, conv2d

import tensorflow as tf


class FCN8sResNet18(BasicModel):
    """
    FCN8sResNet Model Architecture
    """

    def __init__(self, args, phase=0):
        super().__init__(args, phase=phase)
        # init encoder
        self.encoder = None
        # init network layers
        self.score_fr = None
        self.upscore2 = None
        self.score_feed1 = None
        self.fuse_feed1 = None
        self.upscore4 = None
        self.score_feed2 = None
        self.fuse_feed2 = None
        self.upscore8 = None

    def build(self):
        print("\nBuilding the MODEL...")
        self.init_input()
        self.init_network()
        self.init_output()
        self.init_train()
        self.init_summaries()
        print("The Model is built successfully\n")

    def init_network(self):
        """
        Building the Network here
        :return:
        """

        # Init a RESNET as an encoder
        self.encoder = RESNET18(x_input=self.x_pl,
                                num_classes=self.params.num_classes,
                                pretrained_path=self.args.pretrained_path,
                                train_flag=self.is_training,
                                weight_decay=self.args.weight_decay)

        # Build Encoding part
        self.encoder.build()

        # Build Decoding part
        with tf.name_scope('score_layer') as scope:
            self.score_fr = conv2d(scope, x=self.encoder.conv5,
                                   num_filters=self.params.num_classes, kernel_size=(1, 1),
                                   l2_strength=self.args.weight_decay, is_training=self.is_training)
        with tf.name_scope('upscore_2s'):
            self.upscore2 = conv2d_transpose('upscore2', x=self.score_fr,
                                             output_shape=self.encoder.feed1.shape.as_list()[0:3] + [
                                                 self.params.num_classes],
                                             kernel_size=(4, 4), stride=(2, 2), l2_strength=self.encoder.wd)
            self.score_feed1 = conv2d('score_feed1', x=self.encoder.feed1,
                                      num_filters=self.params.num_classes, kernel_size=(1, 1),
                                      l2_strength=self.encoder.wd)
            self.fuse_feed1 = tf.add(self.score_feed1, self.upscore2)

        with tf.name_scope('upscore_4s'):
            self.upscore4 = conv2d_transpose('upscore4', x=self.fuse_feed1,
                                             output_shape=self.encoder.feed2.shape.as_list()[0:3] + [
                                                 self.params.num_classes],
                                             kernel_size=(4, 4), stride=(2, 2), l2_strength=self.encoder.wd)
            self.score_feed2 = conv2d('score_feed2', x=self.encoder.feed2,
                                      num_filters=self.params.num_classes, kernel_size=(1, 1),
                                      l2_strength=self.encoder.wd)
            self.fuse_feed2 = tf.add(self.score_feed2, self.upscore4)

        with tf.name_scope('upscore_8s'):
            self.upscore8 = conv2d_transpose('upscore8', x=self.fuse_feed2,
                                             output_shape=self.x_pl.shape.as_list()[0:3] + [self.params.num_classes],
                                             kernel_size=(16, 16), stride=(8, 8), l2_strength=self.encoder.wd)

        self.logits = self.upscore8
