import os
import numpy as np
from config import config
import time
import dlib
import click
import cv2


def undist_1(img, mtx, dist, mtx_new=None):
    undist = cv2.undistort(img, mtx, dist, None, mtx_new)
    if mtx_new is not None:
        undist = np.flipud(undist)
        undist = np.fliplr(undist)
    return undist

def undist_2(img, mtx, dist, mtx_new):
    mapx, mapy = cv2.initUndistortRectifyMap(mtx, dist, None, mtx_new, IMG_SIZE, 5)
    return cv2.remap(img, mapx, mapy, cv2.INTER_CUBIC)

@click.command()
@click.option('-c', '--config', 'conf_path',
              help='Path to the config file',
              type=click.Path(exists=True))
def main(conf_path):
    config.read(conf_path)

    video = cv2.VideoCapture(config.get('app').get('source'))

    if config.get('app').get('frames').get('save'):
        if not os.path.exists(config.get('app').get('frames').get('path')):
            os.makedirs(config.get('app').get('frames').get('path'))

    if config.get('app').get('fd').get('save'):
        if not os.path.exists(config.get('app').get('fd').get('path')):
            os.makedirs(config.get('app').get('fd').get('path'))

    predictor_age = None
    predictor_gender = None

    if config.get('app').get('age').get('enable'):
        if config.get('app').get('age').get('type') == 'Rother':
            from descriptors.Rother_age import predictor
            predictor_age = predictor(config)
        elif config.get('app').get('age').get('type') == 'Levi':
            from descriptors.Levi_age import predictor
            predictor_age = predictor(config)

    if config.get('app').get('gender').get('enable'):
        if config.get('app').get('gender').get('type') == 'Rother':
            from descriptors.Rother_gender import predictor
            predictor_gender = predictor(config)
        elif config.get('app').get('gender').get('type') == 'Levi':
            from descriptors.Levi_gender import predictor
            predictor_gender = predictor(config)

    detector = dlib.get_frontal_face_detector()
    frames_counter = 1
    cv2.namedWindow('stream', cv2.WINDOW_NORMAL)
    try:
        while True:
            ret, frame = video.read()
            if not ret:
                print '[{}] [INFO] No more frames. Exiting.'.format(time.strftime("%H:%M:%S"))
                break
            print '[{}] [INFO] Processing frame #{}..'.format(time.strftime("%H:%M:%S"), frames_counter)

            if config.get('app').get('frames').get('save'):
                cv2.imwrite(os.path.join(config.get('app').get('frames').get('path'),
                                         str(frames_counter).zfill(5) + '.png'), frame)

            dets = detector(frame)
            print '[{}] [INFO]     {} faces detected'.format(time.strftime("%H:%M:%S"), len(dets))
            bboxes = []
            for i_d, d in enumerate(dets, start=1):
                cv2.rectangle(frame, (d.left(), d.top()), (d.right(), d.bottom()), (0, 255, 0), 3)
                print '[{}] [INFO]         Processing face #{}'.format(time.strftime("%H:%M:%S"), i_d)
                face = frame[d.top() : d.bottom(), d.left() : d.right(), :]
                if config.get('app').get('fd').get('save'):
                    cv2.imwrite(os.path.join(config.get('app').get('fd').get('path'),
                                             'frame{}_face{}.png'.format(str(frames_counter).zfill(5),
                                                                         str(i_d).zfill(2)
                                                                        )
                                            ),
                                face)

                txt = []
                if config.get('app').get('gender').get('enable'):
                    print '[{}] [INFO]             gender identification..'.format(time.strftime("%H:%M:%S"))
                    gender, t = predictor_gender.predict(frame, (d.top(), d.bottom(), d.left(), d.right()))
                    print '[{}] [INFO]         Gender: {}'.format(time.strftime("%H:%M:%S"), gender)
                    txt.append(str(gender))
                if config.get('app').get('age').get('enable'):
                    print '[{}] [INFO]             age identification..'.format(time.strftime("%H:%M:%S"))
                    age, t = predictor_age.predict(frame, (d.top(), d.bottom(), d.left(), d.right()))
                    print '[{}] [INFO]         Age: {}'.format(time.strftime("%H:%M:%S"), age)
                    txt.append(str(age))

                    cv2.putText(frame, ','.join(txt), (d.left(), d.top()), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            cv2.imshow('stream', frame)
            cv2.waitKey(500)

            frames_counter += 1
    except KeyboardInterrupt:
        print '[{}] [INFO] Interrupted. Exiting.'.format(time.strftime("%H:%M:%S"))
        cv2.destroyAllWindows()
        exit()

if __name__ == "__main__":
    main()