from dataclasses import dataclass, field
from pathlib import Path
from typing import Union, Tuple

@dataclass(frozen=True)
class DataIngestionConfig:
    root_dir: Path
    data_source: str
    unzip_dir: Path
    classes: list
    test_set: bool

@dataclass(frozen=True)
class DataSetConfig:
    classes: list
    new_data_path: Path
    dataset_name: str

@dataclass(frozen=True)
class TrainLogConfig:
    model: str
    mlflow_uri: str
    experiment_name: str
    model_name: str
    runs_root: str

@dataclass(frozen=True)
class Params:
    epochs: int
    resume: bool
    optimizer: str = 'auto'
    lr0: float = 0.01
    save_period: int = -1
    batch: int = 16
    seed: int = 0
<<<<<<< HEAD
    imgsz: Union[int, Tuple[int, int]] = (1920,1080)
=======
    imgsz: int = 640 
>>>>>>> 4686bb7ee9fad4ae7452049a50633456a1cee345
    patience: int = 30
    cache: str = 'False' 	       
    workers: int = 8 	         
    cos_lr: bool = False 	     
    close_mosaic: int = 10 	   
    amp: bool = True 	         
    lrf: float = 0.01 	         
    momentum: float = 0.937 	   
    weight_decay: float = 0.0005 
    warmup_epochs: float = 5.0 	 
    warmup_momentum: float = 0.8
    warmup_bias_lr: float = 0.05  
    box: float = 7.5 	           
    cls: float = 0.5
    hsv_h: float = 0.015                
    hsv_s: float = 0.7                  
    hsv_v: float = 0.4                  
    degrees: float = 0.0               
    translate: float = 0.1             
    scale: float = 0.5                  
    shear: float = 0.0                 
    perspective: float = 0.0           
    flipud: float = 0.0                
    fliplr: float = 0.5              
    bgr: float = 0.0                   
    mosaic: float = 1.0                 
    mixup: float = 0.0                 
    copy_paste: float = 0.0             
    auto_augment: str = 'randaugment' 
    erasing: float = 0.4 	              
    crop_fraction: float = 1.0
    freeze: int = field(default=None)
<<<<<<< HEAD

    # def __post_init__(self):
    #     if isinstance(self.imgsz, tuple):
    #         if len(self.imgsz) == 1:
    #             object.__setattr__(self, 'imgsz', self.imgsz[0])
    #         elif len(self.imgsz) != 2:
    #             raise ValueError("imgsz must be either a single integer or a tuple of two integers.")
=======
>>>>>>> 4686bb7ee9fad4ae7452049a50633456a1cee345

@dataclass(frozen=True)
class TresholdMetrics:
    mAP50: float
    mAP50_95: float

@dataclass(frozen=True)
class Evaluation:
    name: str
    version: int
    data_source: str
    save_dir: str