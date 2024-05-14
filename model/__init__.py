import requests
from requests.exceptions import RequestException
from io import BytesIO
from PIL import Image
from ultralytics import YOLO
from TestModel.models import Textdata


class myYOLO(YOLO):
    """
        result
        |    |--names = {dict:1000}
        |    |--probs
        |        |--data = {Tensor:(1000,)}
        |        |--top1 = {int}
        |        |--top1conf = {Tensor:()}
        |        |--top5 = {list:5}
        |        |--top5conf = {Tensor:(5,)}
        |    |--speed
        |    |--orig_img
        |    |--orig_shape
        |    |--path
    """

    def __init__(self, model_path):
        super().__init__(model_path)
        # self.result = None

    def predict(self, *args):
        pass

    # 处理URL，获取图片并进行预测
    def process_url(self, url):
        try:
            # 发送GET请求获取图片数据
            response = requests.get(url)
            response.raise_for_status()  # 检查响应是否成功
        except RequestException as e:
            # 捕获请求异常
            print("请求图片失败:", e)
            return None  # 返回None表示出现异常
        # 解析图片数据
        try:
            # 读取图片数据
            image_data = BytesIO(response.content)
            # 使用Pillow库打开图片
            img = Image.open(image_data)
            # return img  # 返回图片对象
        except Exception as e:
            # 捕获其他异常，比如图片数据无效等
            print("处理图片失败:", e)
            response
            return None  # 返回None表示出现异常
        # 调用模型预测
        self.result = super().predict(img)
        # return self.result

    # 图片预处理，待实现
    def process_image(self, img):
        pass

    # 与数据库交互，返回有关文本信息，待实现
    def process_flag(self):
        top5 = self.result.probs.top5
        top5conf = self.result.probs.top5conf
        # names = [self.result.names[i] for i in top5]

        # 待实现：与数据库交互，返回有关文本信息
        pass


class Model:
    def __init__(self):
        self.model_classify_path = r'model_classify.onnx'
        self.model_detect_path = r'model_detect.onnx'
        self.model_classify = YOLO(self.model_classify_path)
        self.model_detect = YOLO(self.model_detect_path)
        self.names = {0: '中介蝮', 1: '中华珊瑚蛇（丽纹蛇）', 2: '中国水蛇', 3: '孟加拉眼镜蛇', 4: '尖吻蝮',
                      5: '山烙铁头',
                      6: '泰国圆斑蝰', 7: '湖北颈槽蛇', 8: '白唇竹叶青', 9: '白头缅蝰', 10: '眼镜王蛇', 11: '短尾蝮',
                      12: '福建华珊瑚蛇（福建丽纹蛇）', 13: '紫沙蛇', 14: '繁花林蛇', 15: '红脖颈槽蛇', 16: '舟山眼镜蛇',
                      17: '菜花原矛头蝮', 18: '虎斑颈槽蛇', 19: '金环蛇', 20: '铅色水蛇', 21: '银环蛇', 22: '黑头缅蝰',
                      23: '（尖鳞）原矛头蝮'}

    def predict(self, img: Image | str):
        """
        detect img
        split img
        classify img
        get data
        Args:
            img:

        Returns:

        """
        boxes = self.detect(img)
        img_splits = self.split_image(img, boxes)
        top5_data = self.classify(img_splits)

    def detect(self, img: Image):
        """
        对图像进行目标检测，返回Result中的boxes
        Args:
            img:所给图像

        Returns:目标检测结果

        """
        results = self.model_detect.predict(img)
        boxes = results[0].boxes
        return boxes

    def split_image(self, img: Image, boxes):
        """
        根据目标检测结果对图像进行裁剪预处理,如果没有检测结果则直接返回原始图像
        Args:
            img:所给图像
            boxes:该图像目标检测框

        Returns:裁剪后的图像

        """
        if boxes.cls.numel():
            img_splits = []
            xyxy_list = boxes.xyxy.cpu().numpy().tolist()
            for xyxy in xyxy_list:
                img_split = img.crop(xyxy)
                img_splits.append(img_split)
            return img_splits
        else:
            return img

    def classify(self, imgs: list[Image]):
        """
        对预处理后的图片进行图像分类，返回top5,top5conf
        Args:
            imgs: 预处理后的图片

        Returns: top5_data: list[(top5, top5conf)...]

        """
        probs = []
        for img in imgs:
            results = self.model_classify.predict(img)
            probs.append(results[0].probs)
        top5_data = [(prob.top5, prob.top5conf) for prob in probs]
        return top5_data

    def get_text(self, top5, top5conf):
        results = dict.fromkeys(top5, None)
        for idx in top5:
            query_result = Textdata.objects.filter(id=idx)
            if query_result is None:
                raise ValueError("No text data found for id: {}".format(idx))
            else:
                temp = [query_result[0].name, query_result[0].habitat, query_result[0].figure,
                        query_result[0].suggestion, query_result[0].img_path]
                results[idx] = temp
        return results


# 初始化分类模型
yolo = myYOLO('/ultralytics-main/ultralytics/cfg/models/v8/yolov8m-cls.pt')
# yolo = YOLO(r'D:\djangoProject\model\ultralytics-main\ultralytics\cfg\models\v8\yolov8m-cls.pt')
