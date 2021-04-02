from models.basic.basic_model import BasicModel
from models.encoders.resnet_18 import RESNET18
from layers.utils import get_deconv_filter, variable_summaries
from layers.utils import variable_with_weight_decay2
from utils.misc import get_vars_underscope
import tensorflow as tf
import pdb

class LinkNET(BasicModel):
    def __init__(self, args):
        super().__init__(args)
        # init encoder
        self.encoder = None
        # all layers
        self.fscore = None
        self.out_decoder_block_4 = None
        self.out_decoder_block_4 = None
        self.out_decoder_block_3 = None
        self.out_decoder_block_3 = None
        self.out_decoder_block_2 = None
        self.out_decoder_block_2 = None
        self.out_decoder_block_1 = None
        self.out_full_conv1 = None
        self.out_conv1 = None
        # Adding bias in linknet
        self.args.use_bias = True
        if args.bias == -1:
            self.args.use_bias = False

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
                                bias=self.args.bias,
                                weight_decay=self.args.weight_decay)

        # Build Encoding part
        self.encoder.build()

        # Build Decoding part
        self.out_decoder_block_4 = self._decoder_block('decoder_block_4', self.encoder.encoder_4, 256, stride=2)
        self.out_decoder_block_4 = tf.add(self.out_decoder_block_4, self.encoder.encoder_3, 'add_features_4')
        self.out_decoder_block_3 = self._decoder_block('decoder_block_3', self.out_decoder_block_4, 128, stride=2)
        self.out_decoder_block_3 = tf.add(self.out_decoder_block_3, self.encoder.encoder_2, 'add_features_3')
        self.out_decoder_block_2 = self._decoder_block('decoder_block_2', self.out_decoder_block_3, 64, stride=2)
        self.out_decoder_block_2 = tf.add(self.out_decoder_block_2, self.encoder.encoder_1, 'add_features_2')
        self.out_decoder_block_1 = self._decoder_block('decoder_block_1', self.out_decoder_block_2, 64, stride=1)

        with tf.variable_scope('output_block'):
            self.out_full_conv1 = self._deconv('deconv_out_1', self.out_decoder_block_1, 32, (3, 3), stride=2)
            self.out_full_conv1 = tf.layers.batch_normalization(self.out_full_conv1, training=self.is_training,
                                                                fused=True)
            tf.add_to_collection('debug_layers', self.out_full_conv1)
            bnvars= get_vars_underscope(tf.get_variable_scope().name, 'batch_normalization')
            for v in bnvars:
                tf.add_to_collection('decoding_trainable_vars', v)

            self.out_full_conv1 = tf.nn.relu(self.out_full_conv1)

            print("output_block_full_conv1: %s" % (str(self.out_full_conv1.shape.as_list())))

            self.out_conv1 = tf.pad(self.out_full_conv1, [[0,0],[1,1],[1,1],[0,0]], "CONSTANT")
            self.out_conv1 = tf.layers.conv2d(self.out_conv1, filters=32, kernel_size=(3, 3), padding="valid",
                                              use_bias=self.args.use_bias,
                                              kernel_initializer=tf.contrib.layers.xavier_initializer(),
                                              kernel_regularizer=tf.contrib.layers.l2_regularizer(
                                                  self.args.weight_decay))
            tf.add_to_collection('debug_layers', self.out_conv1)
            convvars= get_vars_underscope(tf.get_variable_scope().name, 'conv2d')
            for v in convvars:
                tf.add_to_collection('decoding_trainable_vars', v)

            self.out_conv1 = tf.layers.batch_normalization(self.out_conv1, training=self.is_training, fused=True)
            tf.add_to_collection('debug_layers', self.out_conv1)
            bnvars= get_vars_underscope(tf.get_variable_scope().name, 'batch_normalization')
            for v in bnvars:
                tf.add_to_collection('decoding_trainable_vars', v)


            self.out_conv1 = tf.nn.relu(self.out_conv1)
            print("output_block_conv1: %s" % (str(self.out_conv1.shape.as_list())))
            self.fscore = self._deconv('deconv_out_2', self.out_conv1, self.params.num_classes, (2, 2), stride=2)
            print("logits: %s" % (str(self.fscore.shape.as_list())))

        self.logits = self.fscore

    def _decoder_block(self, name, x, out_channels, stride):
        in_channels = x.shape.as_list()[3]

        with tf.variable_scope(name):
            out = self._conv_1x1_block('conv_1', x, in_channels // 4)
            out = self._full_conv_3x3_block('deconv', out, in_channels // 4, stride=stride)
            out = self._conv_1x1_block('conv_2', out, out_channels)
        print("Decoder block - %s: %s" % (name, str(out.shape.as_list())))
        return out

    def _conv_1x1_block(self, name, x, filters):
        with tf.variable_scope(name):
            with tf.variable_scope('conv2d'):
                initializer=tf.contrib.layers.xavier_initializer()
                kernel_shape = [1,1, x.shape[-1], filters]
                w = variable_with_weight_decay2(kernel_shape, initializer, self.args.weight_decay)
                out = tf.nn.conv2d(x, w, [1,1,1,1], padding='VALID')
                if self.args.use_bias:
                    bias = tf.get_variable('bias', filters, initializer=tf.constant_initializer(0.0))
                    out = tf.nn.bias_add(out, bias)
                tf.add_to_collection('debug_layers', out)

            out = tf.layers.batch_normalization(out, training=self.is_training, fused=True)
            tf.add_to_collection('debug_layers', out)
            tf.add_to_collection('decoding_trainable_vars', w)
            tf.add_to_collection('decoding_trainable_vars', bias)

            bnvars= get_vars_underscope(tf.get_variable_scope().name, 'batch_normalization')
            for v in bnvars:
                tf.add_to_collection('decoding_trainable_vars', v)
            out = tf.nn.relu(out)
        return out

    def _full_conv_3x3_block(self, name, x, out_channels, stride=2):
        with tf.variable_scope(name):
            out = self._deconv('deconv', x, out_channels, kernel_size=(3, 3), stride=stride)
            out = tf.layers.batch_normalization(out, training=self.is_training, fused=True)
            tf.add_to_collection('debug_layers', out)
            bnvars= get_vars_underscope(tf.get_variable_scope().name, 'batch_normalization')
            for v in bnvars:
                tf.add_to_collection('decoding_trainable_vars', v)

            out = tf.nn.relu(out)
        return out

    def _deconv(self, name, x, out_channels, kernel_size=(3, 3), stride=2):
        with tf.variable_scope(name):
            h, w = x.shape.as_list()[1:3]
            h, w = h * stride, w * stride
            output_shape = [self.args.batch_size, h, w, out_channels]
            stride = [1, stride, stride, 1]
            kernel_shape = [kernel_size[0], kernel_size[1], out_channels, x.shape.as_list()[-1]]
            w = get_deconv_filter(kernel_shape, self.args.weight_decay)

            variable_summaries(w)
            out = tf.nn.conv2d_transpose(x, w, tf.stack(output_shape), strides=stride, padding="SAME")

            if self.args.use_bias:
                bias = tf.get_variable('biases', [output_shape[-1]],
                                       initializer=tf.constant_initializer(self.args.bias))
                variable_summaries(bias)
                out = tf.nn.bias_add(out, bias)
            tf.add_to_collection('debug_layers', out)
            tf.add_to_collection('decoding_trainable_vars', w)
            tf.add_to_collection('decoding_trainable_vars', bias)
        return out
