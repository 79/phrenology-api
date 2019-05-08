import falcon
import json
import numpy as np
import random
import os

from urllib import request
from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential
from keras.layers import Conv2D, MaxPooling2D
from keras.layers import Activation, Dropout, Flatten, Dense
from keras import backend as K
from keras.models import load_model
from keras.preprocessing.image import img_to_array, load_img


class TestResource(object):
    def on_get(self, req, res):
        """Handles all GET requests."""
        res.status = falcon.HTTP_200
        res.body = ('something else')

class KittyResource(object):
    def load_model(self):
        img_width, img_height = 300, 300

        if K.image_data_format() == 'channels_first':
            input_shape = (3, img_width, img_height)
        else:
            input_shape = (img_width, img_height, 3)

        model = Sequential()
        model.add(Conv2D(32, (3, 3), input_shape=input_shape))
        model.add(Activation('relu'))
        model.add(MaxPooling2D(pool_size=(2, 2)))

        model.add(Conv2D(32, (3, 3)))
        model.add(Activation('relu'))
        model.add(MaxPooling2D(pool_size=(2, 2)))

        model.add(Conv2D(64, (3, 3)))
        model.add(Activation('relu'))
        model.add(MaxPooling2D(pool_size=(2, 2)))

        model.add(Flatten())
        model.add(Dense(64))
        model.add(Activation('relu'))
        model.add(Dropout(0.5))
        model.add(Dense(1))
        model.add(Activation('sigmoid'))

        model.load_weights('weights/weights.h5')

        return model

    def request_image(self, kitty_id):
        base_url = "https://img.cryptokitties.co/0x06012c8cf97bead5deae237070f9587f8e7a266d/"
        fh = kitty_id + ".png"
        endpoint = base_url + fh

        request.urlretrieve(endpoint, "images/{}".format(fh))

    def load_image(self, kitty_id):
        # NB. just repeat this because class variables suck
        img_width, img_height = 300, 300

        fh = kitty_id + ".png"
        if not os.path.isfile('images/{}'.format(fh)):
            print('<<<<<<+++++++ CACHE MISS: REQUEST IMAGE ++++++>>>>>>')
            self.request_image(kitty_id)

        # TODO Get the kitty!
        # NB. Insecure as fuck!
        img = load_img("images/{}".format(fh), False, target_size=(img_width,img_height))

        return img

    def on_get(self, req, res):
        img_width, img_height = 300, 300

        if "ids" not in req.params:
            res.status = falcon.HTTP_200
            res.body = json.dumps({})
            return

        kitty_ids = req.params["ids"]
        print(kitty_ids)

        if kitty_ids is None or len(kitty_ids) is 0:
            res.status = falcon.HTTP_200
            res.body = json.dumps({})
            return

        model = self.load_model()
        predictions = { "_nonce": random.random() }

        for kitty_id in kitty_ids.split(","):
            print("kitty_id: " + kitty_id)

            img = self.load_image(kitty_id)
            x = img_to_array(img)
            x = np.expand_dims(x, axis=0)
            preds = model.predict_classes(x)

            is_criminal = True if (int(preds) is 0) else False
            predictions[kitty_id] = { "criminal": is_criminal }

        res.status = falcon.HTTP_200
        res.body = json.dumps(predictions)


app = falcon.API()
test_resource = TestResource()
kitty_resource = KittyResource()
app.add_route('/test', test_resource)
app.add_route('/kitty', kitty_resource)

