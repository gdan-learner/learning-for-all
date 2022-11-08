import os
import time
import json

import torch
import torchvision
from PIL import Image
import matplotlib.pyplot as plt

from torchvision import transforms
from network_files import FasterRCNN, FastRCNNPredictor, AnchorsGenerator
# from backbone import resnet50_fpn_backbone, MobileNetV2
from backbone import MobileNetV2
from train_utils.draw_box_utils import draw_objs


def create_model(num_classes):
    # mobileNetv2+faster_RCNN
    backbone = MobileNetV2().features
    backbone.out_channels = 1280

    anchor_generator = AnchorsGenerator(sizes=((32, 64, 128, 256, 512),),
                                        aspect_ratios=((0.5, 1.0, 2.0),))

    roi_pooler = torchvision.ops.MultiScaleRoIAlign(featmap_names=['0'],
                                                    output_size=[7, 7],
                                                    sampling_ratio=2)

    model = FasterRCNN(backbone=backbone,
                       num_classes=num_classes,
                       rpn_anchor_generator=anchor_generator,
                       box_roi_pool=roi_pooler)

    # resNet50+fpn+faster_RCNN
    # 注意，这里的norm_layer要和训练脚本中保持一致
    # backbone = resnet50_fpn_backbone(norm_layer=torch.nn.BatchNorm2d)
    # model = FasterRCNN(backbone=backbone, num_classes=num_classes, rpn_score_thresh=0.5)

    return model


def time_synchronized():
    torch.cuda.synchronize() if torch.cuda.is_available() else None
    return time.time()


def getFileList(path):
    for root, dirs, files in os.walk(path):
        return files


def main():
    # get devices
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    print("using {} device.".format(device))

    # create model
    model = create_model(num_classes=2)

    # load train weights
    weights_path = r"E:\save-github\deep-learning-all\object-detection\01_faster_rcnn\save_weights\weight20220830-105416\mobile-model-29.pth"
    assert os.path.exists(weights_path), "{} file dose not exist.".format(weights_path)
    model.load_state_dict(torch.load(weights_path, map_location='cpu')["model"])
    model.to(device)

    # read class_indict
    label_json_path = 'data/pascal_voc_fsod.json'
    assert os.path.exists(label_json_path), "json file {} dose not exist.".format(label_json_path)
    with open(label_json_path, 'r') as f:
        class_dict = json.load(f)

    category_index = {str(v): str(k) for k, v in class_dict.items()}

    RESULT_PATH = r'E:\save-github\deep-learning-all\object-detection\01_faster_rcnn\save_weights\weight20220830-105416\detect-results'
    # ------------------------创建结果文件夹----------------------------------
    isExists = os.path.exists(RESULT_PATH)
    if not isExists:
        os.makedirs(RESULT_PATH)  # 创建文件路径

    # load image
    PRED_PATH = r'C:\Users\96212\Desktop\abnorm\test\images'
    file_name = getFileList(PRED_PATH)
    for step, img in enumerate(file_name, start=0):
        original_img = Image.open(os.path.join(PRED_PATH, img))
        # from pil image to tensor, do not normalize image
        data_transform = transforms.Compose([transforms.ToTensor()])
        img = data_transform(original_img)
        # expand batch dimension
        img = torch.unsqueeze(img, dim=0)

        model.eval()  # 进入验证模式
        with torch.no_grad():
            # init
            img_height, img_width = img.shape[-2:]
            init_img = torch.zeros((1, 3, img_height, img_width), device=device)
            model(init_img)

            t_start = time_synchronized()
            predictions = model(img.to(device))[0]
            t_end = time_synchronized()
            print("inference+NMS time: {}".format(t_end - t_start))

            predict_boxes = predictions["boxes"].to("cpu").numpy()
            predict_classes = predictions["labels"].to("cpu").numpy()
            predict_scores = predictions["scores"].to("cpu").numpy()

            if len(predict_boxes) == 0:
                print("没有检测到任何目标!")
                with open(os.path.join(RESULT_PATH, str(step + 1).rjust(3, '0') + '.txt'), 'a') as file:
                    pass
            else:
                for box, score in zip(predict_boxes, predict_scores):
                    with open(os.path.join(RESULT_PATH, str(step + 1).rjust(3, '0') + '.txt'), 'a') as file:
                        file.write(
                            "defect" + " " + str(round(score, 6)) + " " + " ".join([str(int(s)) for s in box]) + '\n')


if __name__ == '__main__':
    main()
